# #!/usr/bin/env python3
# import os
# import subprocess
# import threading
# import tkinter as tk
# from tkinter import ttk, messagebox, filedialog
# from datetime import datetime
#
# # --- Logging ---
# LOG_FILE = "usb_wipe.log"
#
# def log(message, log_widget=None):
#     """Log to file + UI"""
#     timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
#     full_msg = timestamp + message
#     with open(LOG_FILE, "a") as f:
#         f.write(full_msg + "\n")
#     if log_widget:
#         log_widget.insert(tk.END, full_msg + "\n")
#         log_widget.see(tk.END)
#     print(full_msg)
#
#
# # --- Device Utils ---
# def get_usb_devices(log_widget=None):
#     usb_devices = []
#     try:
#         result = subprocess.run(
#             ['lsblk', '-d', '-o', 'NAME,RO,RM,SIZE,TYPE'],
#             capture_output=True, text=True, check=True
#         )
#         for line in result.stdout.splitlines()[1:]:
#             parts = line.split()
#             if len(parts) >= 5 and parts[4] == 'disk' and parts[2] == '1':
#                 usb_devices.append('/dev/' + parts[0])
#     except Exception as e:
#         log(f"Error finding USB devices: {e}", log_widget)
#     return usb_devices
#
#
# def unmount_device(device, log_widget=None):
#     try:
#         log(f"Unmounting partitions on {device}...", log_widget)
#         for part in os.listdir('/dev'):
#             if part.startswith(device.split('/')[-1]) and part != device.split('/')[-1]:
#                 try:
#                     subprocess.run(['umount', '-f', '/dev/' + part], check=True, timeout=10)
#                     log(f"Unmounted /dev/{part}", log_widget)
#                 except Exception as e:
#                     log(f"Could not unmount /dev/{part}: {e}", log_widget)
#         return True
#     except Exception as e:
#         log(f"Error unmounting device {device}: {e}", log_widget)
#         return False
#
#
# # --- GUI App ---
# class USBWipeApp(tk.Tk):
#     def __init__(self, session_data=None):
#         super().__init__()
#         self.title("USB Wiper")
#         self.geometry("900x600")
#
#         # session data (method, user, etc.)
#         self.controller = self
#         self.session_data = session_data if session_data else {"method": "zero"}
#
#         self.cancel_event = threading.Event()
#
#         # --- UI Layout ---
#         tk.Label(self, text="Select USB Device:", font=("Arial", 12, "bold")).pack(pady=5)
#
#         self.device_list = ttk.Combobox(self, state="readonly", width=60)
#         self.device_list.pack(pady=5)
#
#         controls = tk.Frame(self)
#         controls.pack(pady=5)
#
#         ttk.Button(controls, text="Refresh Devices", command=self.refresh_devices).grid(row=0, column=0, padx=5)
#         ttk.Button(controls, text="Start Wipe", command=self.start_wipe).grid(row=0, column=1, padx=5)
#         ttk.Button(controls, text="Cancel", command=self.cancel_wipe).grid(row=0, column=2, padx=5)
#         ttk.Button(controls, text="Generate Certificate", command=self.generate_certificate).grid(row=0, column=3, padx=5)
#         ttk.Button(controls, text="Exit", command=self.quit).grid(row=0, column=4, padx=5)
#
#         tk.Label(self, text="Logs:", font=("Arial", 12, "bold")).pack(pady=5)
#         self.log_box = tk.Text(self, wrap="word", height=20)
#         self.log_box.pack(expand=True, fill="both", padx=10, pady=10)
#
#         self.refresh_devices()
#
#     # --- Functions ---
#     def refresh_devices(self):
#         devices = get_usb_devices(self.log_box)
#         if devices:
#             self.device_list['values'] = devices
#             self.device_list.current(0)
#         else:
#             self.device_list['values'] = []
#             log("No USB devices found", self.log_box)
#
#     def start_wipe(self):
#         device = self.device_list.get()
#         if not device:
#             messagebox.showwarning("No Device", "Please select a USB device first")
#             return
#         self.cancel_event.clear()
#         threading.Thread(target=self._wipe_thread, args=(device,), daemon=True).start()
#
#     def _wipe_thread(self, device):
#         method = self.session_data.get("method", "zero")
#         log(f"Selected method: {method}", self.log_box)
#
#         if not unmount_device(device, self.log_box):
#             log("Warning: could not unmount partitions.", self.log_box)
#
#         # pick command based on method
#         if method == "random":
#             cmd = ["sudo", "dd", "if=/dev/urandom", f"of={device}", "bs=1M", "status=progress"]
#         else:
#             cmd = ["sudo", "dd", "if=/dev/zero", f"of={device}", "bs=1M", "status=progress"]
#
#         log(f"Running: {' '.join(cmd)}", self.log_box)
#
#         try:
#             process = subprocess.Popen(
#                 cmd,
#                 stdout=subprocess.PIPE,
#                 stderr=subprocess.STDOUT,
#                 text=True,
#                 bufsize=1
#             )
#
#             for line in iter(process.stdout.readline, ''):
#                 if self.cancel_event.is_set():
#                     process.terminate()
#                     log("Wipe cancelled by user.", self.log_box)
#                     return
#                 if line.strip():
#                     log(line.strip(), self.log_box)
#
#             process.wait()
#
#             if process.returncode == 0:
#                 log("Wipe completed successfully!", self.log_box)
#                 messagebox.showinfo("Done", f"Successfully wiped {device}")
#             else:
#                 log(f"dd exited with code {process.returncode}", self.log_box)
#                 messagebox.showerror("Error", f"Failed to wipe {device}")
#
#         except FileNotFoundError:
#             log("Error: 'dd' command not found. Install coreutils.", self.log_box)
#             messagebox.showerror("Error", "The 'dd' tool is missing on this system.")
#         except PermissionError:
#             log("Error: insufficient permissions to access device.", self.log_box)
#             messagebox.showerror("Error", "Run this tool with sudo/admin rights.")
#         except Exception as e:
#             log(f"Error: {e}", self.log_box)
#             messagebox.showerror("Error", str(e))
#
#     def cancel_wipe(self):
#         self.cancel_event.set()
#         log("Cancellation requested...", self.log_box)
#
#     def generate_certificate(self):
#         cert_path = filedialog.asksaveasfilename(defaultextension=".txt", title="Save Certificate As")
#         if cert_path:
#             with open(cert_path, "w") as f:
#                 f.write("USB Wipe Certificate\n")
#                 f.write(f"Method: {self.session_data.get('method')}\n")
#                 f.write(f"Generated on: {datetime.now()}\n")
#             log(f"Certificate saved at {cert_path}", self.log_box)
#             messagebox.showinfo("Certificate", f"Certificate saved at {cert_path}")
#
#
# # --- Run App ---
# if __name__ == "__main__":
#     session = {"method": "zero"}  # injected session data
#     app = USBWipeApp(session)
#     app.mainloop()

#!/usr/bin/env python3
import os
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import sys

LOG_FILE = "usb_wipe.log"

# -------------------
# Logging
# -------------------
def log(message, log_widget=None):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
    full_msg = timestamp + message
    with open(LOG_FILE, "a") as f:
        f.write(full_msg + "\n")
    if log_widget:
        log_widget.insert(tk.END, full_msg + "\n")
        log_widget.see(tk.END)
    print(full_msg)

# -------------------
# Root Check
# -------------------
def is_root():
    return os.geteuid() == 0

# -------------------
# USB Device Utilities
# -------------------
def get_usb_devices(log_widget=None):
    usb_devices = []
    try:
        result = subprocess.run(
            ['lsblk', '-d', '-o', 'NAME,RO,RM,SIZE,TYPE'],
            capture_output=True, text=True, check=True
        )
        for line in result.stdout.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 5 and parts[4] == 'disk' and parts[2] == '1':
                usb_devices.append('/dev/' + parts[0])
    except Exception as e:
        log(f"Error finding USB devices: {e}", log_widget)
    return usb_devices

def unmount_device(device, log_widget=None):
    try:
        log(f"Unmounting partitions on {device}...", log_widget)
        for part in os.listdir('/dev'):
            if part.startswith(device.split('/')[-1]) and part != device.split('/')[-1]:
                part_path = '/dev/' + part
                try:
                    subprocess.run(['umount', '-f', part_path], check=True, timeout=10)
                    log(f"Unmounted {part_path}", log_widget)
                except subprocess.TimeoutExpired:
                    log(f"Force unmounting {part_path}", log_widget)
                    subprocess.run(['umount', '-l', part_path], check=True)
                except Exception as e:
                    log(f"Could not unmount {part_path}: {e}", log_widget)
        return True
    except Exception as e:
        log(f"Error unmounting {device}: {e}", log_widget)
        return False

# -------------------
# Wipe Methods
# -------------------
def quick_wipe(device, log_widget=None):
    """Quick wipe: remove filesystem and recreate partition"""
    try:
        log(f"Starting QUICK wipe for {device}", log_widget)
        unmount_device(device, log_widget)
        subprocess.run(['wipefs', '-a', device], check=True, timeout=30)
        subprocess.run(['dd', 'if=/dev/zero', f'of={device}', 'bs=1M', 'count=10'], check=True, timeout=30)
        size = int(subprocess.check_output(['blockdev', '--getsize64', device]))
        if size > 1048576:
            seek = (size - 1048576) // 1048576
            subprocess.run(['dd', 'if=/dev/zero', f'of={device}', 'bs=1M', f'seek={seek}', 'count=1'], check=True, timeout=30)
        subprocess.run(['parted', '-s', device, 'mklabel', 'msdos'], check=True, timeout=10)
        subprocess.run(['parted', '-s', device, 'mkpart', 'primary', 'fat32', '0%', '100%'], check=True, timeout=10)
        log(f"Quick wipe completed for {device}", log_widget)
        return True
    except Exception as e:
        log(f"Quick wipe error: {e}", log_widget)
        return False

def erase_device(device, method, cancel_event, log_widget=None):
    """Full wipe using zero, random, or shred"""
    try:
        unmount_device(device, log_widget)
        if method == "zero":
            cmd = ["dd", "if=/dev/zero", f"of={device}", "bs=1M", "status=progress"]
        elif method == "random":
            cmd = ["dd", "if=/dev/urandom", f"of={device}", "bs=1M", "status=progress"]
        elif method == "shred":
            cmd = ["shred", "-v", "-n", "1", device]
        else:
            log(f"Unknown method {method}, defaulting to zero", log_widget)
            cmd = ["dd", "if=/dev/zero", f"of={device}", "bs=1M", "status=progress"]

        log(f"Running: {' '.join(cmd)}", log_widget)
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in iter(process.stdout.readline, ""):
            if cancel_event.is_set():
                process.terminate()
                log("Wipe cancelled by user", log_widget)
                return
            if line.strip():
                log(line.strip(), log_widget)
        process.wait()
        if process.returncode == 0:
            log(f"{method.upper()} wipe completed successfully for {device}", log_widget)
        else:
            log(f"{method.upper()} wipe failed with code {process.returncode}", log_widget)
    except Exception as e:
        log(f"Error wiping device {device}: {e}", log_widget)

# -------------------
# GUI App
# -------------------
class USBWipeApp(tk.Tk):
    def __init__(self, session_data=None):
        super().__init__()
        self.title("USB Wiper")
        self.geometry("900x600")
        self.session_data = session_data if session_data else {"method": "zero"}
        self.cancel_event = threading.Event()

        # UI
        tk.Label(self, text="USB Devices Found:", font=("Arial", 12, "bold")).pack(pady=5)
        self.device_list = ttk.Combobox(self, state="readonly", width=60)
        self.device_list.pack(pady=5)
        controls = tk.Frame(self)
        controls.pack(pady=5)
        ttk.Button(controls, text="Refresh Devices", command=self.refresh_devices).grid(row=0, column=0, padx=5)
        ttk.Button(controls, text="Start Wipe", command=self.start_wipe).grid(row=0, column=1, padx=5)
        ttk.Button(controls, text="Cancel", command=self.cancel_wipe).grid(row=0, column=2, padx=5)
        ttk.Button(controls, text="Generate Certificate", command=self.generate_certificate).grid(row=0, column=3, padx=5)
        ttk.Button(controls, text="Exit", command=self.quit).grid(row=0, column=4, padx=5)
        tk.Label(self, text="Logs:", font=("Arial", 12, "bold")).pack(pady=5)
        self.log_box = tk.Text(self, wrap="word", height=20)
        self.log_box.pack(expand=True, fill="both", padx=10, pady=10)

        if not is_root():
            messagebox.showwarning("Root Required", "Run this program as root to allow device wiping!")

        self.refresh_devices()

    def refresh_devices(self):
        devices = get_usb_devices(self.log_box)
        if devices:
            self.device_list['values'] = devices
            self.device_list.current(0)
            log(f"Found devices: {devices}", self.log_box)
        else:
            self.device_list['values'] = []
            log("No USB devices found", self.log_box)

    def start_wipe(self):
        device = self.device_list.get()
        method = self.session_data.get("method", "zero")
        if not device:
            messagebox.showwarning("No Device", "Select a USB device")
            return
        self.cancel_event.clear()
        threading.Thread(target=self._wipe_thread, args=(device, method), daemon=True).start()

    def _wipe_thread(self, device, method):
        log(f"Starting wipe for {device} with method {method}", self.log_box)
        if method == "quick":
            success = quick_wipe(device, self.log_box)
            if success:
                messagebox.showinfo("Done", f"Quick wipe completed for {device}")
            else:
                messagebox.showerror("Error", f"Quick wipe failed for {device}")
        else:
            erase_device(device, method, self.cancel_event, self.log_box)
            messagebox.showinfo("Done", f"{method.upper()} wipe finished for {device}")

    def cancel_wipe(self):
        self.cancel_event.set()
        log("Cancellation requested", self.log_box)

    def generate_certificate(self):
        cert_path = filedialog.asksaveasfilename(defaultextension=".txt", title="Save Certificate As")
        if cert_path:
            with open(cert_path, "w") as f:
                f.write("USB Wipe Certificate\n")
                f.write(f"Method: {self.session_data.get('method')}\n")
                f.write(f"Generated on: {datetime.now()}\n")
            log(f"Certificate saved at {cert_path}", self.log_box)
            messagebox.showinfo("Certificate", f"Certificate saved at {cert_path}")

# -------------------
# Run App
# -------------------
if __name__ == "__main__":
    session = {"method": "zero"}  # Change to "random", "shred", or "quick" as needed
    app = USBWipeApp(session)
    app.mainloop()
