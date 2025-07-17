import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports

class SerialSenderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Serial PWM Sender")
        self.serial_port = None
        self.ser = None

        #シリアルポートの選択画面
        self.port_label = ttk.Label(root, text="Serial Port:")
        self.port_label.grid(row=0, column=0, padx=5, pady=5)
        self.port_combo = ttk.Combobox(root, values=self.get_serial_ports(), width=20)
        self.port_combo.grid(row=0, column=1, padx=5, pady=5)
        self.refresh_btn = ttk.Button(root, text="Refresh", command=self.refresh_ports)
        self.refresh_btn.grid(row=0, column=2, padx=5, pady=5)

        # 数値入力
        self.value_label = ttk.Label(root, text="Value (-25000~25000):")
        self.value_label.grid(row=1, column=0, padx=5, pady=5)
        self.value_entry = ttk.Entry(root, width=20)
        self.value_entry.grid(row=1, column=1, padx=5, pady=5)
        self.send_value_btn = ttk.Button(root, text="Send Value", command=self.send_value)
        self.send_value_btn.grid(row=1, column=2, padx=5, pady=5)

        # ON/OFFボタン
        self.i_btn = ttk.Button(root, text="Start (i)", command=lambda: self.send_cmd('i'))
        self.i_btn.grid(row=2, column=0, padx=5, pady=5)
        self.o_btn = ttk.Button(root, text="Stop (o)", command=lambda: self.send_cmd('o'))
        self.o_btn.grid(row=2, column=1, padx=5, pady=5)

        # 結果表示
        self.status = tk.StringVar()
        self.status_label = ttk.Label(root, textvariable=self.status, foreground="blue")
        self.status_label.grid(row=3, column=0, columnspan=3, padx=5, pady=10)

    def get_serial_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def refresh_ports(self):
        self.port_combo['values'] = self.get_serial_ports()

    def open_serial(self):
        port = self.port_combo.get()
        if not port:
            self.status.set("Select a serial port.")
            return False
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.ser = serial.Serial(port, 115200, timeout=1)
            return True
        except Exception as e:
            self.status.set(f"Serial open error: {e}")
            return False

    def send_value(self):
        value = self.value_entry.get().strip()
        try:
            v = int(value)
            if -25000 <= v <= 25000:
                if self.open_serial():
                    self.ser.write(f"{v}\n".encode())
                    self.status.set(f"Sent value: {v}")
                    self.ser.close()
            else:
                self.status.set("Value out of range (-25000~25000)")
        except ValueError:
            self.status.set("Invalid value (must be integer)")

    def send_cmd(self, cmd):
        if self.open_serial():
            self.ser.write(cmd.encode())
            self.status.set(f"Sent command: {cmd}")
            self.ser.close()

def main():
    root = tk.Tk()
    app = SerialSenderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
