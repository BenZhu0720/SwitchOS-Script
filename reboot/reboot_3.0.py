#修改成多台设备同时进行测试，且设备通过独立文件获取连接信息

import paramiko
from paramiko_expect import SSHClientInteraction
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import time
import datetime

from convert_seconds import convert_seconds



""" 
读取设备信息,从devices.txt文件中,和测试脚本在同一路径下 
各个设备信息的格式如下:IP地址,登录用户名,登录密码，重启次数
192.168.0.1,python,123,3
192.168.0.2,python,123,3
192.168.0.3,python,123,3
"""

def read_devices(filename):
    devices = []
    with open(filename, 'r') as file:
        for line in file:
            hostname, username, password, reboot_count = line.strip().split(',')
            devices.append({
                'hostname': hostname,
                'username': username,
                'password': password,
                'reboot_count': reboot_count
            })
    return devices

script_dir = os.path.dirname(os.path.abspath(__file__))
device_file_path = os.path.join(script_dir, 'devices.txt')
devices = read_devices(device_file_path)

# 初始化成功和失败次数的计数器,详细失败次数的数组
success_count = 0
failure_count = 0
fail_list = []


#记录交换机的SN号
def switch_informational(devices):
    """
    使用SSH连接到交换机,执行'show version'命令以获取序列号（SN）。

    参数:
    devices (list): 交换机设备列表，每个设备是一个字典，包含 'ip', 'username', 'password' 字段。

    返回:
    dict: 键为交换机的IP地址,值为对应的序列号或错误信息。
    """
    sn_dict = {}
    for device in devices:
        hostname = device.get('hostname')
        username = device.get('username')
        password = device.get('password')
        if not hostname or not username or not password:
            sn_dict[hostname] = "缺少设备信息"
            continue
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname, username=username, password=password, timeout=10)
            stdin, stdout, stderr = client.exec_command('show version')
            output = stdout.read().decode('utf-8')
            client.close()
            # 假设序列号在输出中的某一行，通过关键字查找
            sn = next((line for line in output.splitlines() if 'Serial Number' in line), '').split(':')[-1].strip()
            sn_dict[hostname] = sn if sn else "序列号未找到"
        except Exception as e:
            sn_dict[hostname] = f"错误: {str(e)}"
    return sn_dict

         


#交换机重启脚本
def reboot_script(devices, reboot_number, result_folder, current_date):
     
    global success_count, failure_count, fail_list   #继承函数外的声明，并在内部更新
    sn = switch_informational(devices)
    local_success_count = 0
    local_failure_count = 0
    local_fail_list = []

    try:
         # 在循环内获取每次重启时当前的时间戳
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 创建ssh客户端
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # 连接交换机
        ssh.connect(devices['hostname'], username=devices['username'], password=devices['password'], allow_agent=False, look_for_keys=False)
            
        # 记录重启前的时间戳
        start_time = time.time()

        # 创建交换式会话
        interaction = SSHClientInteraction(ssh, timeout=5, display=True)

        # 进入特权模式
        interaction.send('enable')

        #保存配置
        time.sleep(1)
        interaction.send('write')
        interaction.expect([])
        
        if interaction.last_match[0] == 0:
            interaction.send('yes')
            interaction.expect("#")

        # 发送重启命令
        time.sleep(1)
        interaction.send('reboot')
        interaction.expect([])

        if interaction.last_match[0] == 0:
            interaction.send('yes')
            print(f"开始重启设备 {devices['hostname']} 第 {i+1} 次")


        # 等待交换机重启(时间以秒为单位)
        print(f"共{devices['reboot_count']}次软重启，等待第{reboot_number+1}次交换机重启......")
        # 等待一分钟后开始检测是否重启成功
        time.sleep(70)

        # 尝试重新连接到交换机以检查其状态
        retry_count = 13  # 设置重试次数
        for retry in range(retry_count):
            try:
                ssh.connect(devices['hostname'], username=devices['username'], password=devices['password'], timeout=7)
                # 如果能够重新连接，则认为重启成功
                local_success_count += 1
                end_time = time.time()
                result = "交换机重启成功"
                print(f"重试{retry+1}/{retry_count} - 成功重新连接到交换机")
                # ... 在重启逻辑中 ...
                print(f"设备 {devices['hostname']} 第 {reboot_number+1} 次重启完成")
                break
            except Exception as e:
                # 如果无法重新连接，继续尝试
                print(f"重试{retry+1}/{retry_count} - 无法重新连接到交换机：{e}")
                if retry < retry_count - 1:
                    time.sleep(3)  # 等待一段时间后重试
                else:
                    # 如果重试次数耗尽，则认为重启失败
                    local_failure_count += 1
                    end_time = time.time()
                    result = "交换机重启失败"
                    local_fail_list.append(f"{devices['hostname']}-第{i+1}次")
        
        reboot_time = end_time - start_time
        time.sleep(7)        
         
        with open(f"{script_dir}/{result_folder}/switch_SN_{sn}_reboot_result_{current_date}.txt", 'a') as file:
            file.write(f"{devices['hostname']}-第{reboot_number+1}次软重启测试-{current_time}:{result},重启耗时：{reboot_time:.2f}秒\n")
        
        success_count += local_success_count
        failure_count += local_failure_count
        fail_list.extend(local_fail_list)
        return local_success_count, local_failure_count, local_fail_list
          
    except paramiko.AuthenticationException as e:
         # 处理认证失败的异常
        print(f"用户名/密码错误认证失败： {e}")
        failure_count += 1
        result = "用户名/密码错误SSH登入认证失败"
        fail_list.append(f"{devices['hostname']}-第{i+1}次")
    except paramiko.SSHException as e:
        # 处理ssh异常
        print(f"SSH CONNECT ERROR: {e}")
        failure_count += 1
        result = "SSH CONNECT ERROR"
        fail_list.append(f"{devices['hostname']}-第{i+1}次")
    except Exception as e:
        # 处理其他异常
        print(f"OTHER ERROR: {e}")
        failure_count += 1
        result = f"ERROR: {str(e)}"
        fail_list.append(f"{devices['hostname']}-第{i+1}次")

        reboot_time = end_time - start_time
        time.sleep(7)

        with open(f"{script_dir}/{result_folder}/switch_SN_{sn}_reboot_result_{current_date}.txt", 'a') as file:
            file.write(f"{devices['hostname']}-第{reboot_number+1}次软重启测试-{current_time}:{result},重启耗时：{reboot_time:.2f}秒\n")

        return success_count, failure_count, fail_list


# 创建一个文件夹来存储每次重启的结果
result_folder = "switch_reboot_result"
if not os.path.exists(result_folder):
    os.makedirs(result_folder)


# 获取当前日期的时间戳
current_date = datetime.datetime.now().strftime("%d%m%Y")
start_test = time.time()

# 使用线程池来并行重启设备
with ThreadPoolExecutor(max_workers=len(devices)) as executor:
    futures = []
    for i in range(devices['reboot_count']):
        for device in devices:
            future = executor.submit(reboot_script, device, i, result_folder, current_date)
            futures.append(future)

    # 等待所有任务完成
    for future in as_completed(futures):
        success, failure, fails = future.result()
        success_count += success
        failure_count += failure
        fail_list.extend(fails)

end_test = time.time()
all_test_time = end_test - start_test
days, hours, minutes, seconds = convert_seconds(all_test_time)
avg_test_time = all_test_time / (devices['reboot_count'] * len(devices))
sn = switch_informational(devices)
with open(f"{script_dir}/{result_folder}/switch_SN_{sn}_reboot_result_{current_date}.txt", 'a') as file:
    file.write(f"\n\n\n#######\n本次软重启测试,一共耗时:{days:.0f}天,{hours:.0f}小时,{minutes:.0f}分钟,{seconds:.2f}秒\n平均每次重启耗时:{avg_test_time:.2f}秒\n#######\n")
    if (failure_count > 0):
        file.write(f"\n#######\n本次软重启测试一共出现{failure_count}次失败；\n重启失败在{fail_list}")

# 打印成功和失败次数
print(f"重启成功次数: {success_count}")
print(f"重启失败次数: {failure_count}")
