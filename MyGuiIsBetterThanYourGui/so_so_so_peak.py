import tkinter as tk
from tkinter import ttk
import subprocess, platform, threading

# -------- Device Detection Helpers --------
def detect_devices():
    devices = []
    try:
        output = subprocess.check_output(
            ["lsblk", "-dpno", "NAME,MODEL,TRAN"],
            text=True
        ).strip().split("\n")
        for line in output:
            parts = line.split()
            if not parts:
                continue
            name = parts[0]
            model = " ".join(parts[1:-1]) if len(parts) > 2 else "Unknown"
            tran = parts[-1] if len(parts) > 1 else "Unknown"
            devices.append((name, model, tran))
    except Exception as e:
        devices.append(("Error", str(e), ""))
    return devices

def detect_android():
    try:
        output = subprocess.check_output(
            ["adb", "devices"],
            text=True
        ).strip().split("\n")[1:]
        devices = [line.split()[0] for line in output if "device" in line]
        return devices
    except:
        return []

# -------- Main App --------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NullBytes")
        self.geometry("900x600")
        self.configure(bg="black")
        self.resizable(True, True)

        self.container = tk.Frame(self, bg="black")
        self.container.pack(fill="both", expand=True)

        self.pages = {}
        for Page in (DevicePage, LogPage):
            page = Page(self.container, self)
            self.pages[Page] = page
            page.grid(row=0, column=0, sticky="nsew")

        self.show_page(DevicePage)

    def show_page(self, page_class, **kwargs):
        page = self.pages[page_class]
        if hasattr(page, "on_show"):
            page.on_show(**kwargs)
        page.tkraise()


# -------- Device Selection Page --------
class DevicePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="black")
        self.controller = controller

        self.devices_frame = tk.Frame(self, bg="black")
        self.devices_frame.grid(row=0, column=0, sticky="nsew")

        self.selection = tk.StringVar()
        self.method = tk.StringVar()

        # Buttons at bottom
        bottom = tk.Frame(self, bg="black")
        bottom.grid(row=1, column=0, pady=20)
        ttk.Button(bottom, text="Refresh", command=self.refresh).pack(side="left", padx=10)
        ttk.Button(bottom, text="Next", command=self.next_page).pack(side="left", padx=10)

        # center vertically
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)

        self.refresh()

    def refresh(self):
        for widget in self.devices_frame.winfo_children():
            widget.destroy()

        devices = detect_devices()
        androids = detect_android()
        if androids:
            for d in androids:
                devices.append((d, "Android Device", "adb"))

        for dev, model, tran in devices:
            frame = tk.Frame(self.devices_frame, bg="#222", bd=2, relief="ridge")
            frame.pack(fill="x", pady=10, padx=200)

            rb = tk.Radiobutton(
                frame,
                text=f"{dev} ({model}) [{tran}]",
                variable=self.selection,
                value=dev,
                font=("Consolas", 14),
                fg="white",
                bg="#222",
                selectcolor="#444",
                indicatoron=0,
                width=50,
                pady=10
            )
            rb.pack()

            # method options based on device type
            if "nvme" in dev:
                tk.Radiobutton(frame, text="NVMe Sanitize", variable=self.method,
                               value="nvme_sanitize", bg="#222", fg="#00ffcc",
                               selectcolor="#444").pack(anchor="w", padx=20)
            elif tran.lower() in ["sata", "ata"]:
                tk.Radiobutton(frame, text="ATA Secure Erase", variable=self.method,
                               value="ata_secure", bg="#222", fg="#00ffcc",
                               selectcolor="#444").pack(anchor="w", padx=20)
            elif tran.lower() == "usb":
                for m in ["dd_zero", "dd_random", "dd_nist", "quick_wipe"]:
                    label = {
                        "dd_zero": "DD Fill with Zeros",
                        "dd_random": "DD Fill with Random",
                        "dd_nist": "DD (NIST 3-pass)",
                        "quick_wipe": "Quick Disk Wipe"
                    }[m]
                    tk.Radiobutton(frame, text=label, variable=self.method,
                                   value=m, bg="#222", fg="#00ffcc",
                                   selectcolor="#444").pack(anchor="w", padx=20)

    def next_page(self):
        if not self.selection.get() or not self.method.get():
            return
        self.controller.show_page(LogPage,
                                  device=self.selection.get(),
                                  method=self.method.get())


# -------- Log Page --------
class LogPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="black")
        self.controller = controller

        # Left info panel
        self.info = tk.Label(self, text="", font=("Consolas", 14),
                             fg="#00ffcc", bg="black", justify="left")
        self.info.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        # Right log panel
        self.log = tk.Text(self, bg="#111", fg="white", font=("Consolas", 12))
        self.log.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        # Loader at bottom
        self.loader = tk.Label(self, text="Loading...", font=("Consolas", 14),
                               fg="#ffcc00", bg="black")
        self.loader.grid(row=1, column=0, columnspan=2, pady=10)

        # configure layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)

    def on_show(self, device, method):
        self.info.config(text=f"Selected Device:\n{device}\n\nMethod:\n{method}")
        self.log.delete("1.0", tk.END)
        self.run_task(device, method)

    def run_task(self, device, method):
        # Example: run a script and capture logs
        def task():
            # Replace with your actual script
            process = subprocess.Popen(
                ["echo", f"Simulating wipe on {device} with {method}..."],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            for line in process.stdout:
                self.log.insert(tk.END, line)
                self.log.see(tk.END)
        threading.Thread(target=task, daemon=True).start()


if __name__ == "__main__":
    app = App()
    app.mainloop()
