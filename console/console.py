import serial
import time

port = "COM4" #接口为COM3的串口线
baudrate = "115200" #GDLINK的波特率为115200

#连接串口
ser = serial.Serial(port, baudrate)

#输入交换机CLI命令

ser.write(b"enable\n")
ser.write(b"config terminal\n")

#设置管理口IP地址
ser.write(b"no management ip address dhcp\n")
time.sleep(7)
ser.write(b"management ip address 192.168.0.123/24\n")

#创建ssh保密文件
ser.write(b"rsa key a generate\n")
ser.write(b"rsa key a export url flash:/a.pri private ssh2\n")
time.sleep(7)
ser.write(b"yes\n")
ser.write(b"rsa key a export url flash:/a.pub public ssh2\n")
time.sleep(7)
ser.write(b"yes\n")
ser.write(b"rsa key importKey import url flash:/a.pub public ssh2\n")
ser.write(b"username python privilege 4 password 123456\n")
ser.write(b"username python assign rsa key importKey\n")
ser.write(b"ip ssh server version all \n")
ser.write(b"ip ssh server enable \n")

#查看命令输入的结果
ser.write(b"end\n")
ser.write(b"wr\n")
ser.write(b"show running-config\n")
for i in range(20):
    ser.write(b" ")
    time.sleep(1)

#读取输出结果
output = ser.read_all().decode('utf-8')

#输出结果
print(output)

#关闭串口
ser.close