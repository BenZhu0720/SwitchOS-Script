import paramiko
from paramiko_expect import SSHClientInteraction
import os
import time
import datetime


max_retries = 40 #最大的尝试连接次数
retry_interval = 3 #每次尝试之间的间隔时间(秒)

device={
    'hostname': '192.168.1.123',
    'username': 'python',
    'password': '123456',

}

#设置重启次数
reboot_count = 10

#创建一个文件夹来存储每次重启的结果
result_folder = "reboot_result"
if not os.path.exists(result_folder):
    os.makedirs(result_folder)

#初始化成功和失败次数的计数器
success_count = 0
failure_count = 0

#获取当前日期的时间戳
current_date = datetime.datetime.now().strftime("%d%m%Y")
start_test = time.time()

#循环执行重启操作
for i in range(reboot_count):
    #尝试重启交换机
    try:
         #在循环内获取每次重启时当前的时间戳
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        #创建ssh客户端
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        #连接交换机
        ssh.connect(device['hostname'], username=device['username'], password=device['password'], allow_agent=False, look_for_keys=False)
          
        #记录重启前的时间戳
        start_time = time.time()

        #创建交换式会话
        interaction = SSHClientInteraction(ssh, timeout=5, display=True)

        #进入特权模式
        interaction.send('enable')
    
        #发送重启命令
        time.sleep(1)
        interaction.send('reboot')
        time.sleep(1)
        interaction.send('yes')
        time.sleep(7)
        interaction.expect(' ')


        #等待交换机重启(时间以秒为单位)
        print(f"等待交换机重启......")
        #等待一分钟后开始检测是否重启成功
        time.sleep(70)

        #尝试重新连接到交换机以检查其状态
        retry_count = 18  # 设置重试次数
        for retry in range(retry_count):
            try:
                ssh.connect(device['hostname'], username=device['username'], password=device['password'])
                # 如果能够重新连接，则认为重启成功
                success_count += 1
                result = "交换机重启成功"
                break
            except Exception as e:
                # 如果无法重新连接，继续尝试
                print(f"重试{retry+1}/{retry_count} - 无法重新连接到交换机：{e}")
                if retry < retry_count - 1:
                    time.sleep(5)  # 等待一段时间后重试
                else:
                    # 如果重试次数耗尽，则认为重启失败
                    failure_count += 1
                    result = "交换机重启失败"
        
        end_time = time.time()
        reboot_time = end_time - start_time

    except paramiko.AuthenticationException as e:
        #处理认证失败的异常
        print(f"初次认证失败： {e}")
        failure_count += 1
        result = "初次登入认证失败"
        #暂停测试并等待用户继续输入测试
        input("请解决初次认证失败问题,按Enter键继续测试......")
    except paramiko.SSHException as e:
        #处理ssh异常
        print(f"FIRST SSH CONNECT ERROR: {e}")
        failure_count += 1
        result = "初次登入SSH ERROR"
        #暂停测试并等待用户继续输入测试
        input("请解决连接SSH失败问题,按Enter键继续测试......")
    except Exception as e:
        #处理其他异常
        print(f"初次连接到交换机时出错： {e}")
        failure_count += 1
        result = "初次登入其他异常"
        #暂停测试并等待用户继续输入测试
        input("请解决其他初次登入问题,按Enter键继续测试......")

    #将每次重启的结果保存到文件
    with open(f"{result_folder}/reboot_result_{current_date}.txt",'a') as file:
        file.write(f"第{i+1}次软重启测试-{current_time}:{result},重启耗时：{reboot_time:.2f}秒\n")

end_test = time.time()
all_test_time = end_time - start_test
avg_test_time = all_test_time / reboot_count
with open(f"{result_folder}/reboot_result_{current_date}.txt",'a') as file:
        file.write(f"\n\n\n本次软重启测试,一共耗时:{all_test_time:.2f}秒\n大约平均每次重启耗时:{avg_test_time}秒\n")
#打印成功和失败次数
print(f"重启成功次数: {success_count}")
print(f"重启失败次数: {failure_count}")