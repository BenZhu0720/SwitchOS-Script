import paramiko
from paramiko_expect import SSHClientInteraction
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import re
import time
import datetime

from convert_seconds import convert_seconds  # 确保这个模块存在

def read_devices(filename):
    devices = []
    with open(filename, 'r') as file:
        for line in file:
            hostname, username, password, reboot_count = line.strip().split(',')
            devices.append({
                'hostname': hostname,
                'username': username,
                'password': password,
                'reboot_count': int(reboot_count)
            })
    return devices

script_dir = os.path.dirname(os.path.abspath(__file__))
device_file_path = os.path.join(script_dir, 'devices.txt')
devices = read_devices(device_file_path)

result_folder = f"{script_dir}/switch_reboot_result"
if not os.path.exists(result_folder):
    os.makedirs(result_folder)

current_date = datetime.datetime.now().strftime("%Y%m%d")

def get_device_sn(device):
    """获取设备序列号"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(device['hostname'], username=device['username'],
                    password=device['password'], timeout=10)
        
        with SSHClientInteraction(ssh, timeout=5, display=False) as interaction:
            interaction.send('show version')
            interaction.expect('--More--|#', timeout=5)
            output = interaction.current_output_clean
            
            # 尝试匹配常见SN格式
            sn_patterns = [
                r'SN:\s+(\S+)',
                r'Processor board ID (\S+)',          # Cisco格式
                r'Serial Number\s*:\s*(\S+)',         # 华为/H3C格式
                r'Serial num\s*:\s*(\S+)',            # 其他格式
                r'[Ss]erial\s*[Nn]umber\s*:\s*(\S+)',# 通用格式
            ]
            
            for pattern in sn_patterns:
                match = re.search(pattern, output)
                if match:
                    return match.group(1).strip()
            
        return 'UNKNOWN'
    except Exception as e:
        print(f"获取 {device['hostname']} SN失败: {str(e)}")
        return 'ERROR'
    finally:
        if ssh:
            ssh.close()

def reboot_script(device, reboot_number, sn, result_folder, current_date):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ssh = None
    success = 0
    failure = 0
    fail_list = []
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(device['hostname'], username=device['username'], password=device['password'], timeout=10)
        
        start_time = time.time()
        with SSHClientInteraction(ssh, timeout=5, display=False) as interaction:
            interaction.send('enable')
            time.sleep(1)
            interaction.send('reboot')
            time.sleep(1)
            interaction.send('yes')
            time.sleep(7)
            interaction.expect(' ')
        print(f"设备 {device['hostname']} (SN: {sn})第 {reboot_number+1} 次重启指令已发送")
        time.sleep(70)

        # 验证重启是否成功
        for retry in range(13):
            try:
                ssh.connect(device['hostname'], username=device['username'],
                          password=device['password'], timeout=15)
                success = 1
                break
            except Exception:
                if retry == 12:
                    failure = 1
                    fail_list.append(f"{device['hostname']}-第{reboot_number+1}次")
                time.sleep(3)
                
        # 记录单次重启结果
        reboot_time = time.time() - start_time
        result = "成功" if success else "失败"
        log_header = f"{device['hostname']} (SN: {sn})"
        with open(f"{result_folder}/{device['hostname']}_SN_{sn}_reboot_log_{current_date}.txt", 'a') as f:
            f.write(f"[{current_time}] {device['hostname']} {log_header} 第{reboot_number+1}次重启 {result} 耗时: {reboot_time:.2f}s\n")
            
    except paramiko.AuthenticationException:
        error_msg = "认证失败"
        failure = 1
        fail_list.append(f"{device['hostname']}-第{reboot_number+1}次")
        with open(f"{result_folder}/{device['hostname']}_SN_{sn}_reboot_log_{current_date}.txt", 'a') as f:
            f.write(f"[{current_time}] {device['hostname']} {log_header} 第{reboot_number+1}次重启 {error_msg}\n")
    except Exception as e:
        error_msg = f"其他错误: {str(e)}"
        failure = 1
        fail_list.append(f"{device['hostname']}-第{reboot_number+1}次")
        with open(f"{result_folder}/{device['hostname']}_SN_{sn}_reboot_log_{current_date}.txt", 'a') as f:
            f.write(f"[{current_time}] {device['hostname']} {log_header} 第{reboot_number+1}次重启 {error_msg}\n")
    finally:
        if ssh:
            ssh.close()
    
    return success, failure, fail_list

def process_device(device, result_folder, current_date):
    total_success = 0
    total_failure = 0
    all_fails = []
    start_time = time.time()

    # 首先获取SN号
    sn = get_device_sn(device)
    print(f"开始测试设备 {device['hostname']} (SN: {sn})")
    
    # 创建带SN的日志文件头
    log_header = f"设备 {device['hostname']} 序列号: {sn}\n"
    with open(f"{result_folder}/{device['hostname']}_SN_{sn}_reboot_log_{current_date}.txt", 'a') as f:
        f.write(log_header)
        f.write(f"测试开始时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    start_time = time.time()
    
    for i in range(device['reboot_count']):
        s, f, fl = reboot_script(device, i, sn, result_folder, current_date)
        total_success += s
        total_failure += f
        all_fails.extend(fl)
        time.sleep(7)
    
    # 记录设备总结信息
    total_time = time.time() - start_time
    days, hours, mins, secs = convert_seconds(total_time)
    summary = [
        "\n测试总结:",
        f"设备信息: {device['hostname']} (SN: {sn})",
        f"总重启次数: {device['reboot_count']}",
        f"成功次数: {total_success}",
        f"失败次数: {total_failure}",
        f"成功率: {total_success/device['reboot_count']*100:.1f}%",
        f"总耗时: {days}d {hours}h {mins}m {secs:.1f}s"
    ]
    
    if all_fails:
        summary.append(f"失败的重启次数: {', '.join(all_fails)}")
    
    with open(f"{result_folder}/{device['hostname']}_SN_{sn}_reboot_log_{current_date}.txt", 'a') as f:
        f.write('\n'.join(summary))
        f.write('\n\n')
    
    return total_success, total_failure, all_fails

if __name__ == "__main__":
    total_success = 0
    total_failure = 0
    all_fails = []
    
    with ThreadPoolExecutor(max_workers=len(devices)) as executor:
        futures = {executor.submit(process_device, dev, result_folder, current_date): dev for dev in devices}
        
        for future in as_completed(futures):
            dev = futures[future]
            try:
                s, f, fl = future.result()
                total_success += s
                total_failure += f
                all_fails.extend(fl)
                print(f"设备 {dev['hostname']} 测试完成: 成功 {s} 次，失败 {f} 次")
            except Exception as e:
                print(f"处理设备 {dev['hostname']} 时发生未捕获的异常: {str(e)}")
    
    print(f"\n全局统计:")
    print(f"总成功次数: {total_success}")
    print(f"总失败次数: {total_failure}")
    print(f"失败列表: {all_fails}")
    print(f"详细日志请查看目录: {result_folder}")