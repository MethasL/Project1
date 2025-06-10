import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import serial
import csv
import os

SERIAL_PORT = 'ttyACM0'
BAUD_RATE = 9600
TIMEOUT = 1
MACHINE_RUNTIME = 10  # seconds
CSV_FILE = 'rfid_log.csv'

def calculate_bcc(data_bytes):
    bcc = 0
    for b in data_bytes:
        bcc ^= b
    return bcc

def build_command(command_bytes):
    length = len(command_bytes)
    full_command = [0x01, length] + command_bytes
    bcc = calculate_bcc(full_command[1:])
    full_command.append(bcc)
    return bytes(full_command)

def parse_response(data):
    if len(data) < 4:
        return None
    payload = data[2:-1]
    bcc = data[-1]
    if calculate_bcc(data[1:-1]) != bcc:
        return None
    try:
        ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in payload)
        reversed_ascii = ascii_str[::-1]
        return reversed_ascii
    except Exception:
        return None

class RFIDApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RFID Tag Monitor")

        self.uid = tk.StringVar()
        self.machine_running = False
        self.machine_end_time = 0
        self.confirmed_uid = None

        self.setup_gui()
        self.load_existing_data()
        self.start_serial_thread()

    def setup_gui(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        tk.Label(frame, text="Enter User ID:").grid(row=0, column=0, padx=5)
        self.uid_entry = tk.Entry(frame, textvariable=self.uid)
        self.uid_entry.grid(row=0, column=1, padx=5)
        self.confirm_button = tk.Button(frame, text="Confirm UID", command=self.confirm_uid)
        self.confirm_button.grid(row=0, column=2, padx=5)

        self.status_label = tk.Label(self.root, text="Status: Idle", fg="blue")
        self.status_label.pack()

        self.tree = ttk.Treeview(self.root, columns=("Tag ID", "Timestamp", "User ID"), show="headings")
        self.tree.heading("Tag ID", text="Tag ID")
        self.tree.heading("Timestamp", text="Timestamp")
        self.tree.heading("User ID", text="User ID")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def load_existing_data(self):
        if os.path.exists(CSV_FILE):
            with open(CSV_FILE, mode='r', newline='') as file:
                reader = csv.reader(file)
                next(reader, None)  # Skip header
                for row in reader:
                    if len(row) == 3:
                        self.tree.insert("", "end", values=(row[0], row[1], row[2]))

    def confirm_uid(self):
        uid = self.uid.get().strip()
        if uid:
            self.confirmed_uid = uid
            self.uid_entry.config(state='disabled')
            self.confirm_button.config(state='disabled')
            self.status_label.config(text="Status: Ready to scan tag", fg="green")
        else:
            messagebox.showwarning("Input Error", "Please enter a valid User ID.")

    def start_serial_thread(self):
        threading.Thread(target=self.serial_loop, daemon=True).start()

    def serial_loop(self):
        try:
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT) as ser:
                command = build_command([0x08, 0xC8])
                while True:
                    if self.confirmed_uid and not self.machine_running:
                        ser.write(command)
                        time.sleep(0.1)
                        if ser.in_waiting:
                            data = ser.read(ser.in_waiting)
                            tag = parse_response(data)
                            if tag and tag != ".":
                                self.prompt_and_start(tag)
                    elif self.machine_running:
                        if time.time() >= self.machine_end_time:
                            self.machine_running = False
                            self.status_label.config(text="Status: Idle", fg="blue")
                            self.uid.set("")
                            self.uid_entry.config(state='normal')
                            self.confirm_button.config(state='normal')
                            self.confirmed_uid = None
                    time.sleep(0.4)
        except serial.SerialException as e:
            print(f"Serial error: {e}")

    def prompt_and_start(self, tag):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        response = messagebox.askyesno("Confirm", f"Start machine with:\nUser ID: {self.confirmed_uid}\nTag ID: {tag}?")
        if response:
            self.machine_running = True
            self.machine_end_time = time.time() + MACHINE_RUNTIME
            self.status_label.config(text="Status: Running", fg="red")
            self.tree.insert("", "end", values=(tag, timestamp, self.confirmed_uid))
            with open(CSV_FILE, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([tag, timestamp, self.confirmed_uid])

if __name__ == "__main__":
    root = tk.Tk()
    app = RFIDApp(root)
    root.mainloop()

