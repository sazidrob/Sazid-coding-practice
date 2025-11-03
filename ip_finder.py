# ip_finder.py
# Works with Python 3.7+

import json
import urllib.request
import urllib.parse
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
import sys
import webbrowser

API_BASE = "http://ip-api.com/json/"

def query_ip(ip: str):
    """Query ip-api and return a dict (or raise an exception)."""
    url = API_BASE + urllib.parse.quote(ip.strip())
    req = urllib.request.Request(url, headers={"User-Agent": "ip-finder-tk/1.0"})
    with urllib.request.urlopen(req, timeout=8) as resp:
        raw = resp.read().decode("utf-8")
    data = json.loads(raw)
    return data

class IPFinderApp:
    def __init__(self, root):
        self.root = root
        root.title("SAR's IP Finder")
        root.geometry("640x420")
        root.resizable(False, False)

        frm = ttk.Frame(root, padding=12)
        frm.pack(fill="both", expand=True)

        # Input row
        row = ttk.Frame(frm)
        row.pack(fill="x", pady=(0,8))

        ttk.Label(row, text="IP (leave blank for your IP):").pack(side="left")
        self.ip_var = tk.StringVar()
        self.entry = ttk.Entry(row, textvariable=self.ip_var, width=28)
        self.entry.pack(side="left", padx=(8,6))
        self.entry.bind("<Return>", lambda e: self.lookup())

        self.btn_lookup = ttk.Button(row, text="Lookup", command=self.lookup)
        self.btn_lookup.pack(side="left", padx=4)
        self.btn_myip = ttk.Button(row, text="My IP", command=self.fill_my_ip)
        self.btn_myip.pack(side="left", padx=4)
        self.btn_clear = ttk.Button(row, text="Clear", command=self.clear)
        self.btn_clear.pack(side="left", padx=4)

        # Result box
        self.out = ScrolledText(frm, height=18, wrap="word", state="disabled", font=("Consolas", 10))
        self.out.pack(fill="both", expand=True)

        # Bottom row
        bottom = ttk.Frame(frm)
        bottom.pack(fill="x", pady=(8,0))
        self.copy_btn = ttk.Button(bottom, text="Copy JSON", command=self.copy_json)
        self.copy_btn.pack(side="left")
        self.open_btn = ttk.Button(bottom, text="Open ip-api.com docs", command=lambda: webbrowser.open("http://ip-api.com/docs/"))
        self.open_btn.pack(side="left", padx=6)

        # status
        self.status = ttk.Label(bottom, text="Ready")
        self.status.pack(side="right")

        self.last_json = None

    def set_status(self, text):
        self.status.config(text=text)
        self.status.update_idletasks()

    def append_text(self, text):
        self.out.configure(state="normal")
        self.out.delete("1.0", "end")
        self.out.insert("1.0", text)
        self.out.configure(state="disabled")

    def clear(self):
        self.ip_var.set("")
        self.append_text("")
        self.last_json = None
        self.set_status("Cleared")

    def fill_my_ip(self):
        self.ip_var.set("")
        self.lookup()

    def copy_json(self):
        if not self.last_json:
            messagebox.showinfo("Nothing to copy", "Do a lookup first.")
            return
        try:
            json_text = json.dumps(self.last_json, indent=2)
            self.root.clipboard_clear()
            self.root.clipboard_append(json_text)
            self.set_status("JSON copied to clipboard")
        except Exception as e:
            messagebox.showerror("Copy failed", str(e))

    def lookup(self):
        ip = self.ip_var.get().strip()
        # UI lock
        self.btn_lookup.config(state="disabled")
        self.btn_myip.config(state="disabled")
        self.copy_btn.config(state="disabled")
        self.set_status("Querying...")
        self.append_text("Querying ip-api.com...\n")

        def worker():
            try:
                data = query_ip(ip)
            except Exception as e:
        
                self.root.after(0, self.on_error, str(e))
                return
            self.root.after(0, self.on_success, data)

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def on_error(self, err):
        self.append_text(f"Error: {err}")
        self.set_status("Error")
        self.btn_lookup.config(state="normal")
        self.btn_myip.config(state="normal")
        self.copy_btn.config(state="normal")

    def on_success(self, data):
        self.last_json = data
        # ip-api returns {"status":"success" or "fail", ...}
        if data.get("status") != "success":
            msg = data.get("message", "lookup failed")
            self.append_text(f"Lookup failed: {msg}\n\nRaw response:\n{json.dumps(data, indent=2)}")
            self.set_status("Failed")
        else:
            pretty = self.format_result(data)
            self.append_text(pretty)
            self.set_status("Done")
        self.btn_lookup.config(state="normal")
        self.btn_myip.config(state="normal")
        self.copy_btn.config(state="normal")

    def format_result(self, d):
    
        fields = [
            ("query", "IP"),
            ("country", "Country"),
            ("countryCode", "Country Code"),
            ("regionName", "Region"),
            ("region", "Region Code"),
            ("city", "City"),
            ("zip", "ZIP"),
            ("lat", "Latitude"),
            ("lon", "Longitude"),
            ("timezone", "Timezone"),
            ("isp", "ISP"),
            ("org", "Org"),
            ("as", "AS"),
        ]
        lines = []
        lines.append("IP Lookup Result (ip-api.com)\n" + "="*30)
        for key, label in fields:
            val = d.get(key, "")
            lines.append(f"{label:13}: {val}")
        lines.append("")
        lines.append("Full JSON:")
        lines.append(json.dumps(d, indent=2))
        return "\n".join(lines)


def main():
    root = tk.Tk()
    app = IPFinderApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
