import paramiko
from paramiko_expect import SSHClientInteraction
import os
import time
import datetime

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

#循环执行重启操作
for i in range(reboot_count):
    #尝试重启交换机
    try:
        #创建ssh客户端
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        #连接交换机
        ssh.connect(device['hostname'], username=device['username'], password=device['password'], allow_agent=False, look_for_keys=False)

        #创建交换式会话
        interaction = SSHClientInteraction(ssh, timeout=5, display=True)

        #进入特权模式
        interaction.send('enable\n')
    
        #发送重启命令
        prompt = 'Switch#'
        interaction.send('reboot\n')
        time.sleep(10)
        interaction.send('y\n')
        interaction.expect(prompt)

        #等待交换机重启(时间以秒为单位)
        print(f"等待交换机重启......")
        time.sleep(177)

        #在循环内获取每次重启时当前的时间戳
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #尝试重新连接到交换机以检查其状态
        try:
            ssh.connect(device['hostname'], username=device['username'], password=device['password'])
            #如果能够重新连接，则认为重启成功
            success_count += 1
            result = "交换机重启成功"
        except Exception as e:
            #如果无法重新连接，则认为重启失败
            print(f"无法重新连接到交换机：{e}")
            failure_count += 1
            result = "交换机重启失败"
            #暂停测试并等待用户继续输入测试
            input("按Enter键继续测试......")
    
    except paramiko.AuthenticationException as e:
        #处理认证失败的异常
        print(f"认证失败： {e}")
        failure_count += 1
        result = "登入认证失败"
        #暂停测试并等待用户继续输入测试
        input("按Enter键继续测试......")
    except paramiko.SSHException as e:
        #处理ssh异常
        print(f"SSH ERROR: {e}")
        failure_count += 1
        result = "登入SSH ERROR"
        #暂停测试并等待用户继续输入测试
        input("按Enter键继续测试......")
    except Exception as e:
        #处理其他异常
        print(f"连接到交换机时出错： {e}")
        failure_count += 1
        result = "登入其他异常"
        #暂停测试并等待用户继续输入测试
        input("按Enter键继续测试......")

    #将每次重启的结果保存到文件
    with open(f"{result_folder}/reboot_result_{current_date}.txt",'a') as file:
        file.write(f"第{i+1}次软重启测试-{current_time}:{result}\n")

#打印成功和失败次数
print(f"重启成功次数: {success_count}")
print(f"重启失败次数: {failure_count}")