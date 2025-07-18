import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
from typing import List, Optional
import logging
import os
import subprocess
import platform
import time

class Constants:
    WINDOW_TITLE = "Serial PWM Sender"
    SERIAL_BAUDRATE = 115200
    SERIAL_TIMEOUT = 1
    PWM_MIN_VALUE = -25000
    PWM_MAX_VALUE = 25000
    CAN_ID_MIN = 1
    CAN_ID_MAX = 4
    PWM_COUNT = 4
    ENTRY_WIDTH = 20
    COMBO_WIDTH = 20
    LOG_FILE_NAME = "serial_gui.log"

class SerialManager:
    
    def __init__(self):
        self.serial_connection: Optional[serial.Serial] = None
    
    def get_available_ports(self) -> List[str]:
        try:
            ports = serial.tools.list_ports.comports()
            return [port.device for port in ports]
        except Exception as e:
            logging.error(f"Failed to get serial ports: {e}")
            return []
    
    def open_connection(self, port: str) -> bool:
        if not port:
            return False
        
        try:
            self.close_connection()
            self.serial_connection = serial.Serial(
                port, 
                Constants.SERIAL_BAUDRATE, 
                timeout=Constants.SERIAL_TIMEOUT
            )
            return True
        except Exception as e:
            logging.error(f"Failed to open serial connection: {e}")
            return False
    
    def close_connection(self):
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
    
    def send_command(self, command: str) -> bool:
        if not self.serial_connection or not self.serial_connection.is_open:
            return False
        
        try:
            self.serial_connection.write(command.encode())
            return True
        except Exception as e:
            logging.error(f"Failed to send command: {e}")
            return False

class ValidationHelper:
    
    @staticmethod
    def validate_can_id(can_id: str) -> tuple[bool, Optional[int], str]:
        try:
            cid = int(can_id.strip())
            if Constants.CAN_ID_MIN <= cid <= Constants.CAN_ID_MAX:
                return True, cid, ""
            else:
                return False, None, f"CAN ID out of range ({Constants.CAN_ID_MIN}-{Constants.CAN_ID_MAX})"
        except ValueError:
            return False, None, "Invalid CAN ID (must be integer)"
    
    @staticmethod
    def validate_pwm_value(value: str) -> tuple[bool, Optional[int], str]:
        try:
            v = int(value.strip())
            if Constants.PWM_MIN_VALUE <= v <= Constants.PWM_MAX_VALUE:
                return True, v, ""
            else:
                return False, None, f"Value out of range ({Constants.PWM_MIN_VALUE}~{Constants.PWM_MAX_VALUE})"
        except ValueError:
            return False, None, "Invalid value (must be integer)"
    
    @staticmethod
    def validate_pwm_values(values: List[str]) -> tuple[bool, Optional[List[int]], str]:
        pwm_values = []
        for i, value in enumerate(values):
            is_valid, pwm_value, error_msg = ValidationHelper.validate_pwm_value(value)
            if not is_valid:
                return False, None, f"PWM[{i}]: {error_msg}"
            pwm_values.append(pwm_value)
        return True, pwm_values, ""

class LogManager:
    
    def __init__(self):
        self.log_file_path = Constants.LOG_FILE_NAME
        self.log_enabled = tk.BooleanVar(value=True)
        self.file_handler = None
        self.setup_logging()
    
    def ensure_log_file_handler(self):
        if self.log_enabled.get() and (self.file_handler is None or not os.path.exists(self.log_file_path)):
            self.add_file_handler()
    
    def setup_logging(self):
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        
        if self.log_enabled.get():
            self.add_file_handler()
    
    def add_file_handler(self):
        try:
            if self.file_handler:
                logging.getLogger().removeHandler(self.file_handler)
                self.file_handler.close()
            
            self.file_handler = logging.FileHandler(self.log_file_path)
            self.file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            )
            logging.getLogger().addHandler(self.file_handler)
        except Exception as e:
            print(f"Failed to create log file: {e}")
    
    def remove_file_handler(self):
        if self.file_handler:
            try:
                logging.getLogger().removeHandler(self.file_handler)
                self.file_handler.close()
                self.file_handler = None
            except Exception as e:
                print(f"Failed to remove file handler: {e}")
    
    def toggle_log_file(self):
        if self.log_enabled.get():
            self.add_file_handler()
            logging.info("Log file enabled")
        else:
            self.remove_file_handler()
            logging.info("Log file disabled")
    
    def open_log_file(self) -> bool:
        if not os.path.exists(self.log_file_path):
            messagebox.showwarning("Warning", "Log file does not exist.")
            return False
        
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(self.log_file_path)
            elif system == "Darwin":
                subprocess.run(["open", self.log_file_path])
            else:
                subprocess.run(["xdg-open", self.log_file_path])
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open log file: {e}")
            return False
    
    def clear_log_file(self) -> bool:
        self.ensure_log_file_handler()  # ファイルハンドラがなければ追加
        if not os.path.exists(self.log_file_path):
            # ファイルがなければ新規作成
            try:
                with open(self.log_file_path, 'w') as f:
                    f.write('')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create log file: {e}")
                return False
        try:
            self.remove_file_handler()
            with open(self.log_file_path, 'w') as f:
                f.write('')
            if self.log_enabled.get():
                self.add_file_handler()
            logging.info("Log file cleared")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear log file: {e}")
            if self.log_enabled.get():
                self.add_file_handler()
            return False
    
    def delete_log_file(self) -> bool:
        if not os.path.exists(self.log_file_path):
            messagebox.showwarning("Warning", "Log file does not exist.")
            return False
        
        try:
            self.remove_file_handler()
            logging.shutdown()  # 追加: 全てのハンドラを閉じる
            time.sleep(0.1)
            try:
                with open(self.log_file_path, 'r') as f:
                    pass
            except PermissionError:
                messagebox.showerror("Error", "Log file is being used by another process. Please close any applications that might be using the log file.")
                if self.log_enabled.get():
                    self.add_file_handler()
                return False

            os.remove(self.log_file_path)
            return True
        except PermissionError as e:
            messagebox.showerror("Error", f"Permission denied: {e}\nThe log file might be open in another application.")
            if self.log_enabled.get():
                self.add_file_handler()
            return False
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete log file: {e}")
            if self.log_enabled.get():
                self.add_file_handler()
            return False
    
    def get_log_file_size(self) -> str:
        if os.path.exists(self.log_file_path):
            size = os.path.getsize(self.log_file_path)
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        return "N/A"

class SerialSenderGUI:    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(Constants.WINDOW_TITLE)
        
        self.serial_manager = SerialManager()
        self.log_manager = LogManager()
        self.status_var = tk.StringVar()
        
        self._init_gui_components()
        self._setup_layout()
    
    def _init_gui_components(self):
        self.port_label = ttk.Label(self.root, text="Serial Port:")
        self.port_combo = ttk.Combobox(
            self.root, 
            values=self.serial_manager.get_available_ports(), 
            width=Constants.COMBO_WIDTH
        )
        self.refresh_btn = ttk.Button(self.root, text="Refresh", command=self._refresh_ports)
        
        self.canid_label = ttk.Label(self.root, text=f"CAN ID ({Constants.CAN_ID_MIN}-{Constants.CAN_ID_MAX}):")
        self.canid_entry = ttk.Entry(self.root, width=Constants.ENTRY_WIDTH)
        self.canid_entry.insert(0, str(Constants.CAN_ID_MIN))
        self.set_canid_btn = ttk.Button(self.root, text="Set CAN ID", command=self._set_canid)
        
        self.pwm_frame = ttk.LabelFrame(self.root, text="Individual PWM Values", padding="5")
        self.pwm_entries = []
        self.pwm_labels = []
        
        for i in range(Constants.PWM_COUNT):
            label = ttk.Label(self.pwm_frame, text=f"PWM[{i}]:")
            self.pwm_labels.append(label)
            
            entry = ttk.Entry(self.pwm_frame, width=15)
            entry.insert(0, "0")
            self.pwm_entries.append(entry)
        
        self.send_all_pwm_btn = ttk.Button(
            self.pwm_frame, 
            text="Send All PWM Values", 
            command=self._send_all_pwm
        )
        
        self.value_label = ttk.Label(
            self.root, 
            text=f"Set All PWM ({Constants.PWM_MIN_VALUE}~{Constants.PWM_MAX_VALUE}):"
        )
        self.value_entry = ttk.Entry(self.root, width=Constants.ENTRY_WIDTH)
        self.send_value_btn = ttk.Button(self.root, text="Send All", command=self._send_value)
        
        self.control_frame = ttk.LabelFrame(self.root, text="Control", padding="5")
        self.i_btn = ttk.Button(self.control_frame, text="Start (i)", command=lambda: self._send_cmd('i'))
        self.o_btn = ttk.Button(self.control_frame, text="Stop (o)", command=lambda: self._send_cmd('o'))
        
        self.log_frame = ttk.LabelFrame(self.root, text="Log Management", padding="5")
        
        self.log_checkbox = ttk.Checkbutton(
            self.log_frame, 
            text="Create Log File", 
            variable=self.log_manager.log_enabled,
            command=self.log_manager.toggle_log_file
        )
        
        self.log_size_label = ttk.Label(self.log_frame, text="Size: N/A")
        
        self.open_log_btn = ttk.Button(
            self.log_frame, 
            text="Open Log File", 
            command=self._open_log_file
        )
        self.clear_log_btn = ttk.Button(
            self.log_frame, 
            text="Clear Log File", 
            command=self._clear_log_file
        )
        
        self.status_label = ttk.Label(self.root, textvariable=self.status_var, foreground="blue")
    
    def _setup_layout(self):
        self.port_label.grid(row=0, column=0, padx=5, pady=5)
        self.port_combo.grid(row=0, column=1, padx=5, pady=5)
        self.refresh_btn.grid(row=0, column=2, padx=5, pady=5)
        
        self.canid_label.grid(row=1, column=0, padx=5, pady=5)
        self.canid_entry.grid(row=1, column=1, padx=5, pady=5)
        self.set_canid_btn.grid(row=1, column=2, padx=5, pady=5)
        
        self.pwm_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        
        for i in range(Constants.PWM_COUNT):
            self.pwm_labels[i].grid(row=i//2, column=(i%2)*2, padx=5, pady=2)
            self.pwm_entries[i].grid(row=i//2, column=(i%2)*2+1, padx=5, pady=2)
        
        self.send_all_pwm_btn.grid(row=2, column=0, columnspan=4, padx=5, pady=5)
        
        self.value_label.grid(row=3, column=0, padx=5, pady=5)
        self.value_entry.grid(row=3, column=1, padx=5, pady=5)
        self.send_value_btn.grid(row=3, column=2, padx=5, pady=5)
        
        self.log_frame.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        
        self.log_checkbox.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.log_size_label.grid(row=0, column=1, padx=5, pady=2)
        
        self.open_log_btn.grid(row=1, column=0, padx=5, pady=2)
        self.clear_log_btn.grid(row=1, column=1, padx=5, pady=2)
        
        self.control_frame.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        self.i_btn.grid(row=0, column=0, padx=5, pady=5)
        self.o_btn.grid(row=0, column=1, padx=5, pady=5)
        
        self.status_label.grid(row=6, column=0, columnspan=3, padx=5, pady=10)
        
        self._refresh_log_size()
    
    def _refresh_ports(self):
        self.port_combo['values'] = self.serial_manager.get_available_ports()
        self._update_status("Port list refreshed")
    
    def _set_canid(self):
        canid = self.canid_entry.get()
        is_valid, cid, error_msg = ValidationHelper.validate_can_id(canid)
        
        if not is_valid:
            self._show_error(error_msg)
            return
        
        if self._execute_serial_operation(f"c{cid}"):
            self._update_status(f"Set CAN ID: {cid}")
    
    def _send_all_pwm(self):
        pwm_values = [entry.get() for entry in self.pwm_entries]
        is_valid, values, error_msg = ValidationHelper.validate_pwm_values(pwm_values)
        
        if not is_valid:
            self._show_error(error_msg)
            return
        
        pwm_cmd = f"p0:{values[0]},p1:{values[1]},p2:{values[2]},p3:{values[3]}"
        
        if self._execute_serial_operation(pwm_cmd):
            self._update_status(f"Sent PWM values: {values}")
    
    def _send_value(self):
        value = self.value_entry.get()
        is_valid, v, error_msg = ValidationHelper.validate_pwm_value(value)
        
        if not is_valid:
            self._show_error(error_msg)
            return
        
        if self._execute_serial_operation(f"{v}"):
            self._update_status(f"Sent value: {v}")
    
    def _send_cmd(self, cmd: str):
        if self._execute_serial_operation(cmd):
            self._update_status(f"Sent command: {cmd}")
    
    def _execute_serial_operation(self, command: str) -> bool:
        port = self.port_combo.get()
        if not port:
            self._show_error("Select a serial port.")
            return False
        
        if not self.serial_manager.open_connection(port):
            self._show_error("Failed to open serial connection.")
            return False
        
        try:
            success = self.serial_manager.send_command(command)
            if not success:
                self._show_error("Failed to send command.")
                return False
            return True
        finally:
            self.serial_manager.close_connection()
    
    def _update_status(self, message: str):
        self.log_manager.ensure_log_file_handler()
        self.status_var.set(message)
        logging.info(message)
    
    def _show_error(self, message: str):
        self.log_manager.ensure_log_file_handler()
        self.status_var.set(f"Error: {message}")
        logging.error(message)
        messagebox.showerror("Error", message)

    def _open_log_file(self):
        if self.log_manager.open_log_file():
            self._update_status("Log file opened")
    
    def _clear_log_file(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to clear the log file?"):
            if self.log_manager.clear_log_file():
                self._update_status("Log file cleared")
                self._refresh_log_size()
    
    def _refresh_log_size(self):
        size = self.log_manager.get_log_file_size()
        self.log_size_label.config(text=f"Size: {size}")

def main():
    root = tk.Tk()
    app = SerialSenderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
