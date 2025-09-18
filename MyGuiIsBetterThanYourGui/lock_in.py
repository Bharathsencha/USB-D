#!/usr/bin/env python3
import tkinter as tk
import platform
import subprocess
import json
import os
import sys


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NullBytes")
        self.geometry("900x600")
        self.configure(bg="black")
        self.resizable(True, True)

        # session data to persist user choices
        self.session_data = {
            "os": platform.system(),
            "device": None,
            "method": None,
            "verification": None
        }

        self.container = tk.Frame(self, bg="black")
        self.container.pack(fill="both", expand=True)

        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.pages = {}
        for Page in (WelcomePage, DevicePage, WipeMethodPage):
            page = Page(parent=self.container, controller=self)
            self.pages[Page] = page
            page.grid(row=0, column=0, sticky="nsew")

        self.show_page(WelcomePage)

    def show_page(self, page_class, **kwargs):
        page = self.pages[page_class]
        if hasattr(page, "on_show"):
            page.on_show(**kwargs)
        page.tkraise()

    def save_session(self, key, value):
        """Update session data and dump to JSON for debugging."""
        self.session_data[key] = value
        print("[SESSION]", json.dumps(self.session_data, indent=2))


class WelcomePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="black")
        self.controller = controller

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        os_name = controller.session_data["os"]
        self.message = f"Welcome to NullBytes\nYou are using {os_name}"

        self.label = tk.Label(
            self,
            text="",
            font=("Consolas", 28, "bold"),
            fg="#00ffcc",
            bg="black",
            justify="center"
        )
        self.label.grid(row=0, column=0, sticky="nsew")

        self.index = 0
        self.typewriter()

    def typewriter(self):
        if self.index < len(self.message):
            self.label.config(text=self.message[:self.index+1])
            self.index += 1
            self.after(80, self.typewriter)
        else:
            self.after(1200, self.fade_out)

    def fade_out(self, step=0):
        if step < 20:
            fade_val = 255 - step*12
            fade_color = f"#{0:02x}{fade_val:02x}{fade_val:02x}"
            self.label.config(fg=fade_color)
            self.after(50, lambda: self.fade_out(step+1))
        else:
            self.controller.show_page(DevicePage)


class DevicePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="black")

        self.controller = controller
        self.selected_device = tk.StringVar(value="")

        # full grid centering
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        wrapper = tk.Frame(self, bg="black")
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.grid_rowconfigure(0, weight=1)
        wrapper.grid_columnconfigure(0, weight=1)

        content = tk.Frame(wrapper, bg="black")
        content.grid(row=0, column=0)

        title = tk.Label(
            content,
            text="Select a Device",
            font=("Consolas", 26, "bold"),
            fg="#ffcc00",
            bg="black"
        )
        title.pack(pady=20)

        self.device_frame = tk.Frame(content, bg="black")
        self.device_frame.pack(pady=10)

        btn_frame = tk.Frame(content, bg="black")
        btn_frame.pack(pady=20)

        refresh_btn = tk.Button(
            btn_frame,
            text="🔄 Refresh",
            font=("Consolas", 14, "bold"),
            fg="black",
            bg="#00ffcc",
            command=self.refresh_devices
        )
        refresh_btn.grid(row=0, column=0, padx=10)

        next_btn = tk.Button(
            btn_frame,
            text="➡ Next",
            font=("Consolas", 14, "bold"),
            fg="black",
            bg="#ffcc00",
            command=self.next_page
        )
        next_btn.grid(row=0, column=1, padx=10)

        self.refresh_devices()

    def refresh_devices(self):
        for widget in self.device_frame.winfo_children():
            widget.destroy()

        devices = []

        try:
            result = subprocess.check_output(
                ["lsblk", "-dpno", "NAME,SIZE,MODEL,TRAN"],
                text=True
            )
            if result.strip():
                for line in result.strip().splitlines():
                    devices.append(("Storage", line.strip()))
        except Exception as e:
            devices.append(("Storage", f"Error: {e}"))

        try:
            adb_result = subprocess.check_output(
                ["adb", "devices"],
                text=True
            )
            lines = adb_result.strip().splitlines()
            if len(lines) > 1:
                for line in lines[1:]:
                    if line.strip():
                        devices.append(("Android", line.strip()))
            else:
                devices.append(("Android", "No Android devices detected."))
        except Exception as e:
            devices.append(("Android", f"Error: {e}"))

        for dtype, info in devices:
            self.create_device_block(dtype, info)

    def create_device_block(self, dtype, info):
        block = tk.Frame(
            self.device_frame,
            bg="#222222",
            bd=2,
            relief="ridge",
            padx=10,
            pady=10
        )
        block.pack(fill="x", padx=40, pady=5)

        rb = tk.Radiobutton(
            block,
            text=f"[{dtype}] {info}",
            variable=self.selected_device,
            value=info,
            font=("Consolas", 14),
            fg="#00ffcc",
            bg="#222222",
            activebackground="#00ffcc",
            activeforeground="black",
            indicatoron=False,
            width=80,
            anchor="w",
            command=lambda b=block: self.highlight_block(b)
        )
        rb.pack(fill="x")

    def highlight_block(self, block):
        for widget in self.device_frame.winfo_children():
            widget.configure(bg="#222222")
            for child in widget.winfo_children():
                child.configure(bg="#222222", fg="#00ffcc")

        block.configure(bg="#00ffcc")
        for child in block.winfo_children():
            child.configure(bg="#00ffcc", fg="black")

    def next_page(self):
        if self.selected_device.get():
            self.controller.save_session("device", self.selected_device.get())
            self.controller.show_page(WipeMethodPage, device=self.selected_device.get())
        else:
            print("No device selected!")


class WipeMethodPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="black")
        self.controller = controller
        self.device_name = ""
        self.method_var = tk.StringVar(value="")
        self.verify_var = tk.StringVar(value="none")

        # grid system for vertical centering
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        wrapper = tk.Frame(self, bg="black")
        wrapper.grid(row=1, column=0, sticky="nsew")

        self.title_label = tk.Label(
            wrapper,
            text="",
            font=("Consolas", 26, "bold"),
            fg="#ffcc00",
            bg="black"
        )
        self.title_label.pack(pady=20)

        self.method_frame = tk.LabelFrame(wrapper, text="Wipe Method", fg="white", bg="black", font=("Consolas", 16, "bold"))
        self.method_frame.pack(fill="x", padx=40, pady=10)

        self.method_desc = tk.Label(
            wrapper,
            text="Select a wipe method to see its description.",
            font=("Consolas", 12),
            fg="white",
            bg="black",
            wraplength=700,
            justify="left"
        )
        self.method_desc.pack(pady=10)

        self.verify_frame = tk.LabelFrame(wrapper, text="Verification", fg="white", bg="black", font=("Consolas", 16, "bold"))
        self.verify_frame.pack(fill="x", padx=40, pady=10)

        btn_frame = tk.Frame(wrapper, bg="black")
        btn_frame.pack(pady=20)

        back_btn = tk.Button(
            btn_frame,
            text="⬅ Back",
            font=("Consolas", 14, "bold"),
            fg="black",
            bg="#ff6666",
            command=lambda: controller.show_page(DevicePage)
        )
        back_btn.grid(row=0, column=0, padx=10)

        next_btn = tk.Button(
            btn_frame,
            text="➡ Next",
            font=("Consolas", 14, "bold"),
            fg="black",
            bg="#00ffcc",
            command=self.next_page
        )
        next_btn.grid(row=0, column=1, padx=10)

    def on_show(self, device):
        self.device_name = device
        self.title_label.config(text=f"{device} - Wipe Method")
        self.populate_methods(device)
        self.populate_verifications()

    def populate_methods(self, device_info):
        for widget in self.method_frame.winfo_children():
            widget.destroy()

        methods = []

        d = device_info.lower()
        if "nvme" in d:
            methods = [
                ("NVMe Sanitize (Purge)", "nvme"),
                ("Zero Fill (Clear)", "zero"),
                ("Random Fill (Clear)", "random"),
                ("Shred + Zero (Clear)", "shred")
            ]
        elif "ata" in d or "sata" in d:
            methods = [
                ("ATA Secure Erase (Purge)", "ata"),
                ("Zero Fill (Clear)", "zero"),
                ("Random Fill (Clear)", "random"),
                ("Shred + Zero (Clear)", "shred")
            ]
        elif "usb" in d or "android" in d:
            methods = [
                ("Quick Wipe", "quick"),
                ("Zero Fill (Clear)", "zero"),
                ("Random Fill (Clear)", "random"),
                ("Shred + Zero (Clear)", "shred")
            ]
        else:
            methods = [
                ("Zero Fill (Clear)", "zero"),
                ("Random Fill (Clear)", "random"),
                ("Shred + Zero (Clear)", "shred")
            ]

        for text, val in methods:
            rb = tk.Radiobutton(
                self.method_frame,
                text=text,
                variable=self.method_var,
                value=val,
                font=("Consolas", 14),
                fg="#00ffcc",
                bg="black",
                selectcolor="black",
                command=lambda v=val: self.update_method_desc(v)
            )
            rb.pack(anchor="w", pady=5)

        if methods:
            self.method_var.set(methods[0][1])
            self.update_method_desc(methods[0][1])

    def update_method_desc(self, method):
        descs = {
            "nvme": "Performs an NVMe Sanitize operation, issuing a built-in firmware purge. NIST category: Purge.",
            "ata": "Issues ATA Secure Erase command to the drive. NIST category: Purge.",
            "zero": "Overwrites all sectors with zeros. Simple clear operation. NIST category: Clear.",
            "random": "Overwrites all sectors with random data. Clear operation with stronger obfuscation. NIST category: Clear.",
            "shred": "Multiple overwrite passes (default 3) with random data followed by zero fill. NIST category: Clear.",
            "quick": "Will instantly erase your data but not NIST compliant. Unsafe and can be recovered."
        }
        self.method_desc.config(text=descs.get(method, ""))

    def populate_verifications(self):
        for widget in self.verify_frame.winfo_children():
            widget.destroy()

        options = [
            ("None", "none"),
            ("Sampled", "sampled"),
            ("Full", "full")
        ]

        for text, val in options:
            rb = tk.Radiobutton(
                self.verify_frame,
                text=text,
                variable=self.verify_var,
                value=val,
                font=("Consolas", 14),
                fg="#00ffcc",
                bg="black",
                selectcolor="black"
            )
            rb.pack(anchor="w", pady=5)

    def next_page(self):
        method = self.method_var.get()
        verify = self.verify_var.get()

        self.controller.save_session("method", method)
        self.controller.save_session("verification", verify)

        # prepare payload
        payload = json.dumps(self.controller.session_data)

        # write to temp.json (could also pass directly as arg)
        temp_file = os.path.join(os.path.dirname(__file__), "session.json")
        with open(temp_file, "w") as f:
            f.write(payload)

        # path to usb_linux.py
        usb_path = os.path.join(os.path.dirname(__file__), "engine", "usb_linux.py")

        print("[INFO] Launching usb_linux.py with session.json")
        try:
            subprocess.Popen([sys.executable, usb_path, temp_file], start_new_session=True)
            self.controller.destroy()
        except Exception as e:
            print(f"[ERROR] Could not launch wipe script: {e}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
