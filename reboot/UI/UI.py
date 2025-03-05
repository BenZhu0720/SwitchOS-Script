import tkinter as tk
from tkinter import ttk
import serial.tools.list_ports
import threading

# 初始化串口
ser = None

# 界面布局
class SerialConfigApp:
    def __init__(self, root):
        self.root = root
        self.root.title("串口配置界面")

        # 串口配置
        self.create_serial_config()

        # 管理口配置
        self.create_management_config()

        # 控制按钮
        self.create_control_buttons()

    def create_serial_config(self):
        # 串口选择
        tk.Label(self.root, text="串口:").grid(row=0, column=0, padx=10, pady=10)
        self.serial_port = ttk.Combobox(self.root, values=self.list_serial_ports())
        self.serial_port.grid(row=0, column=1, padx=10, pady=10)

        # 波特率选择
        tk.Label(self.root, text="波特率:").grid(row=1, column=0, padx=10, pady=10)
        self.baud_rate = ttk.Combobox(self.root, values=['9600', '19200', '38400', '57600', '115200'])
        self.baud_rate.grid(row=1, column=1, padx=10, pady=10)
        self.baud_rate.current(0)

    def create_management_config(self):
        # 管理口IP地址
        tk.Label(self.root, text="管理口IP地址:").grid(row=2, column=0, padx=10, pady=10)
        self.management_ip = tk.Entry(self.root)
        self.management_ip.grid(row=2, column=1, padx=10, pady=10)

        # 用户名
        tk.Label(self.root, text="用户名:").grid(row=3, column=0, padx=10, pady=10)
        self.username = tk.Entry(self.root)
        self.username.grid(row=3, column=1, padx=10, pady=10)

        # 密码
        tk.Label(self.root, text="密码:").grid(row=4, column=0, padx=10, pady=10)
        self.password = tk.Entry(self.root, show='*')
        self.password.grid(row=4, column=1, padx=10, pady=10)

    def create_control_buttons(self):
        # 开始按钮
        self.start_button = tk.Button(self.root, text="开始", command=self.start_serial)
        self.start_button.grid(row=5, column=0, padx=10, pady=10)

        # 暂停/取消按钮
        self.pause_button = tk.Button(self.root, text="暂停/取消", command=self.pause_serial)
        self.pause_button.grid(row=5, column=1, padx=10, pady=10)

    def list_serial_ports(self):
        # 自动读取电脑可用的串口线接口信息
        return [port.device for port in serial.tools.list_ports.comports()]

    def start_serial(self):
        # 开始串口通信
        port = self.serial_port.get()
        baud = self.baud_rate.get()
        global ser
        ser = serial.Serial(port, baud, timeout=1)
        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self.monitor_serial)
        self.monitor_thread.start()

    def pause_serial(self):
        # 暂停或取消串口通信
        if ser:
            ser.close()

    def monitor_serial(self):
        # 监控串口数据
        while ser.is_open:
            data = ser.readline()
            if data:
                print(data.decode('utf-8').strip())

# 主函数
if __name__ == "__main__":
    root = tk.Tk()
    app = SerialConfigApp(root)
    root.mainloop()