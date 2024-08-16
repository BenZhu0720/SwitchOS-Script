import paramiko
import time

max_retries = 40 #最大的尝试连接次数
retry_interval = 3 #每次尝试之间的间隔时间(秒)
#定义一个尝试连接交换机的函数
def try_connect(client, hostname, port, username, password):
    for attempt in range(max_retries):
        try:
            client.connect(hostname, port=port, username=username,password=password)
            return True
        except (paramiko.AuthenticationException, paramiko.SSHException):
            print(f"尝试连接失败，正在重试...（第{attempt + 1}次）")
            time.sleep(retry_interval)
    return False