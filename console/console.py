import serial
import time

port = "COM3" #接口为COM3的串口线
baudrate = "115200" #GDLINK的波特率为115200

#连接串口
ser = serial.Serial(port, baudrate)

#输入交换机CLI命令

ser.write(b"enable\n")
ser.write(b"config terminal\n")
ser.write(b"rsa key a generate\n")
ser.write(b"rsa key a export url flash:/a.pri private ssh2\n")
ser.write(b"rsa key a export url flash:/a.pub public ssh2\n")
ser.write(b"rsa key importKey import url flash:/a.pub public ssh2\n")
ser.write(b"username aaa privilege 4 password abc\n")
ser.write(b"username aaa assign rsa key importKey\n")
ser.write(b"ip ssh server version all \n")
ser.write(b"ip ssh server enable \n")

#查看命令输入的结果
ser.write(b"end\n")
ser.write(b"show running-confg\n")
for i in range(13):
    ser.write(b"\t")
    time.sleep(1)

#读取输出结果
output = ser.read_all().decode('utf-8')

#输出结果
print(output)

#关闭串口
ser.close