import os
import json
import subprocess
import sys
import webbrowser
import platform
import tkinter as tk
from tkinter import messagebox, scrolledtext

class SwitchBlade:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self):
        """Loads workspace definitions from a JSON file"""
        if not os.path.exists(self.config_path):
            default_config = {
                "aquamind": {
                    "path": "D:/Desktop/projects/aquamind", 
                    "ports": [5173], 
                    "urls": ["http://localhost:5173"],
                    "apps_to_close": ["WhatsApp.Root", "Spotify", "Grammarly.Desktop"]
                },
                "diagnosure": {
                    "path": "D:/Desktop/projects/DiagnoSure-main", 
                    "ports": [5173], 
                    "urls": ["http://localhost:5173"],
                    "apps_to_close": ["WhatsApp", "Spotify", "Grammarly.Desktop"]
                }
            }
            with open(self.config_path,'w') as f:
                json.dump(default_config, f, indent=4)
            return default_config
        
        with open(self.config_path,'r') as f:
            return json.load(f)

    def log(self, message, text_widget=None):
        """Prints to console and updates GUI log if available"""
        print(message)
        if text_widget:
            text_widget.insert(tk.END, message +"\n")
            text_widget.see(tk.END)
            text_widget.update_idletasks()

    def close_apps(self, app_list, log_widget=None):
        """terminates distracting applications based on OS"""
        system = platform.system()
        for app in app_list:
            try:
                if system == "Windows":
                    #/T kills the process tree (child processes like WhatsApp sub-tasks)
                    #/F forces the termination
                    subprocess.run(f"taskkill /F /T /IM {app}.exe", shell=True, 
                                   stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                else:
                    subprocess.run(["pkill", "-f", app], stderr=subprocess.DEVNULL)
                self.log(f"Action: Closed {app}", log_widget)
            except Exception:
                pass

    def run_checks(self, name, log_widget=None):
        """the core logic to switch contexts"""
        ws = self.config.get(name)
        if not ws:
            self.log(f"Error: Workspace {name} not found.", log_widget)
            return

        self.log(f"--- Initializing Workspace: {name.upper()} ---", log_widget)

        #1. Cleanup Applications (WhatsApp, Spotify, etc.)
        apps = ws.get('apps_to_close', [])
        if apps:
            self.close_apps(apps, log_widget)

        #2. Version Control Check
        path = os.path.expanduser(ws.get('path', ''))
        if os.path.isdir(path):
            try:
                res = subprocess.run(["git", "status", "--short"], cwd=path, capture_output=True, text=True)
                if res.stdout.strip():
                    self.log("Warning: Uncommitted git changes detected.", log_widget)
            except Exception:
                pass

        #3. Network Port Conflict Resolution
        for port in ws.get('ports', []):
            self.log(f"Checking status of port {port}...", log_widget)
            try:
                if platform.system() == "Windows":
                    #Find process ID(PID) associated with the port
                    cmd = f"netstat -ano | findstr :{port}"
                    out = subprocess.check_output(cmd, shell=True).decode()
                    if out:
                        for line in out.strip().split('\n'):
                            pid = line.strip().split()[-1]
                            #/T ensures child processes (like Vite/Node) are also killed
                            subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, 
                                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        self.log(f"Success: Terminated process tree on port {port}", log_widget)
                else:
                    pid = subprocess.check_output(f"lsof -t -i:{port}", shell=True).decode().strip()
                    subprocess.run(f"kill -9 {pid}", shell=True)
                    self.log(f"Success: Terminated process on port {port}", log_widget)
            except Exception:
                self.log(f"Status: Port {port} is available.", log_widget)

        #4.Environment Launch
        self.log(f"Action: Launching VS Code editor...", log_widget)
        subprocess.run(["code", path], shell=(platform.system() == "Windows"))
        
        for url in ws.get('urls', []):
            self.log(f"Action: Opening URL: {url}", log_widget)
            webbrowser.open(url)

        self.log(f"--- Execution Complete: {name.upper()} is active ---", log_widget)

def launch_gui(app_logic):
    root = tk.Tk()
    root.title("SwitchBlade Context Manager")
    root.geometry("550x450")

    tk.Label(root, text="SwitchBlade: Workflow Automation", font=("Arial", 14, "bold")).pack(pady=15)

    log_area = scrolledtext.ScrolledText(root, height=12, width=60)
    log_area.pack(pady=10)

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=20)

    for ws_name in app_logic.config.keys():
        btn = tk.Button(btn_frame, text=f"Switch to {ws_name.upper()}", width=20, height=2,
                        command=lambda n=ws_name: app_logic.run_checks(n, log_area))
        btn.pack(side=tk.LEFT, padx=10)

    root.mainloop()

if __name__ == "__main__":
    logic = SwitchBlade()
    if len(sys.argv) > 1:
        logic.run_checks(sys.argv[1].lower())
    else:
        launch_gui(logic)