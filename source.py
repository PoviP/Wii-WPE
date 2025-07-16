import time
import os
import subprocess
import re
import shlex
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import json
import sys
from PIL import Image, ImageTk
import pystray
import winshell

# --- Configuration ---
POLL_INTERVAL = 0.5
DEBOUNCE_INTERVAL = 1
first_run = True 
last_executed_time = 0 
monitoring_thread_running = False

class LogMonitorGUI:
    def __init__(self, master):
        global first_run, monitoring_thread_running
        self.master = master
        master.title("wiiWPE Configuration")

        # Set minimum window size
        master.minsize(800, 400)

        # --- Variables ---
        self.log_file_path = tk.StringVar(value="C:\\Program Files (x86)\\Steam\\steamapps\\common\\wallpaper_engine\\log.txt")
        self.app_commands = {f"app{i}": tk.StringVar() for i in range(1, 16)}
        self.is_function = {f"app{i}": tk.BooleanVar() for i in range(1, 16)}
        self.autostart_enabled = tk.BooleanVar() 
        self.monitoring_active = tk.BooleanVar(value=False) 
        self.icon = None

        # --- Log File Path ---
        tk.Label(master, text="Log File Path:").grid(row=0, column=0, sticky="w")
        tk.Entry(master, textvariable=self.log_file_path, width=60).grid(row=0, column=1, sticky="we")
        tk.Button(master, text="Browse", command=self.browse_log_file).grid(row=0, column=2, sticky="e")

        # --- App Configuration ---
        for i in range(1, 16):
            tk.Label(master, text=f"App {i}:").grid(row=i, column=0, sticky="w")
            tk.Entry(master, textvariable=self.app_commands[f"app{i}"], width=60).grid(row=i, column=1, sticky="we")
            tk.Checkbutton(master, text="Function", variable=self.is_function[f"app{i}"] ).grid(row=i, column=2, sticky="e")

        # --- Autostart Checkbox ---
        tk.Checkbutton(master, text="Autostart on Login", variable=self.autostart_enabled, command=self.update_autostart).grid(row=17, column=0, columnspan=3)

        # --- Buttons ---
        tk.Button(master, text="Save Configuration", command=self.save_configuration).grid(row=18, column=0, columnspan=3)
        self.exit_button = tk.Button(master, text="Exit", command=self.confirm_quit)
        self.exit_button.grid(row=19, column=0, columnspan=3)

        # --- Terminal Output ---
        tk.Label(master, text="Output:").grid(row=20, column=0, sticky="w")
        self.terminal = tk.Text(master, height=10, width=70, state="disabled")
        self.terminal.grid(row=21, column=0, columnspan=3, sticky="we")

        sys.stdout = TextRedirector(self.terminal, "stdout")
        sys.stderr = TextRedirector(self.terminal, "stderr")

        # Load initial configuration
        self.load_configuration()

        if "--minimized" in sys.argv:
            self.master.withdraw() 
        else:
            self.master.deiconify() 
        self.monitoring_active = True
        if not monitoring_thread_running:
            self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            monitoring_thread_running = True

    def browse_log_file(self):
        filename = filedialog.askopenfilename(initialdir=os.path.dirname(self.log_file_path.get()), title="Select Log File", filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
        if filename:
            self.log_file_path.set(filename)

    def save_configuration(self):
        """Saves the configuration to a file."""
        config = {
            "log_file_path": self.log_file_path.get(),
            "app_commands": {app: self.app_commands[app].get() for app in self.app_commands},
            "is_function": {app: self.is_function[app].get() for app in self.is_function},
            "autostart_enabled": self.autostart_enabled.get(),
        }
        try:
            import json
            with open("config.json", "w") as f:
                json.dump(config, f, indent=4)
            messagebox.showinfo("Success", "Configuration saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving configuration: {e}")


    def load_configuration(self):
        """Loads the configuration from a file."""
        try:
            import json
            with open("config.json", "r") as f:
                config = json.load(f)
            self.log_file_path.set(config.get("log_file_path", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\wallpaper_engine\\log.txt"))
            for app in self.app_commands:
                self.app_commands[app].set(config.get("app_commands", {}).get(app, ""))
                self.is_function[app].set(config.get("is_function", {}).get(app, False))
            self.autostart_enabled.set(config.get("autostart_enabled", False))
            self.update_autostart()

        except FileNotFoundError:
            pass
        except Exception as e:
            messagebox.showerror("Error", f"Error loading configuration: {e}")

    def update_autostart(self):
        """Enables or disables autostart by creating/deleting a shortcut in the Startup folder."""
        app_name = "wiiWPE"
        startup_folder = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", "Programs", "Startup")

        shortcut_path = os.path.join(startup_folder, f"{app_name}.lnk")

        if self.autostart_enabled.get():
            # Create a shortcut to the executable
            try:
                import winshell
                with winshell.shortcut(shortcut_path) as shortcut:
                    shortcut.path = sys.executable
                    shortcut.description = "Starts wiiWPE on login."
                    shortcut.working_directory = os.path.dirname(sys.executable)
                    shortcut.arguments = "--minimized"
            except Exception as e:
                messagebox.showerror("Error", f"Error creating shortcut: {e}")
        else:
            # Delete the shortcut
            try:
                os.remove(shortcut_path)
            except FileNotFoundError:
                pass  # Shortcut doesn't exist, nothing to delete
            except Exception as e:
                messagebox.showerror("Error", f"Error deleting shortcut: {e}")

    def init_system_tray(self):
        """Initialize the system tray icon and menu."""
        image = Image.open("icon.png")
        menu = (
            pystray.MenuItem("Show", self.show_window),
            pystray.MenuItem("Quit", self.quit_app),
        )
        self.icon = pystray.Icon("wiiWPE", image, "wiiWPE", menu)

        threading.Thread(target=self.icon.run, daemon=True).start()

    def show_window(self, icon=None, item=None):
        """Show the main window and stop hiding it."""
        self.master.after(0, self.master.deiconify)
        if self.icon:
            self.icon.stop()
            self.icon = None

    def hide_window(self):
        """Hide the main window and show icon in system tray."""
        self.master.withdraw()
        if self.icon is None:
            self.init_system_tray()

    def quit_app(self, icon=None, item=None):
        """Quit the application."""
        global monitoring_thread_running
        if self.is_config_saved():
            if self.icon:
                self.icon.stop()
            self.master.destroy()
            monitoring_thread_running = False
            os._exit(0)
        else:
            response = messagebox.askyesnocancel("Confirm Exit", "Configuration not saved. Exit anyway?")
            if response == True:
                if self.icon:
                    self.icon.stop()
                self.master.destroy()
                monitoring_thread_running = False
                os._exit(0)

    def confirm_quit(self):
        """A wrapper for the quit_app function to get exit prompt."""
        return self.quit_app(None, None)

    def start_monitoring(self):
        """Starts the log monitoring process."""
        return

    def stop_monitoring(self):
        """Stops the log monitoring process."""
        self.monitoring_active = False

    def monitoring_loop(self):
        """The main monitoring loop."""
        while self.monitoring_active:
            self.read_log_and_execute()
            time.sleep(POLL_INTERVAL)

    def read_log_and_execute(self):
        """Reads the log file for new entries and executes commands based on app names."""
        global first_run
        log_file = self.log_file_path.get()
        global last_known_position, last_executed_time
        command_mappings = {app: self.app_commands[app].get() for app in self.app_commands}
        processed_lines = set()

        try:
            with open(log_file, 'r', encoding='utf-8') as log_file:

                # On the first run, read to the end to skip existing entries.
                if first_run:
                    log_file.seek(0, os.SEEK_END)
                    last_known_position = log_file.tell()
                    first_run = False

                else:
                    log_file.seek(last_known_position)  # Start from the last read position
                for line in log_file:
                    if line in processed_lines:
                        continue #Skip if already processed

                    match = re.search(r"Log: (app\d+)", line)

                    if match:
                        app_name = match.group(1)  # Extract the app name from the matched group

                        # Debounce logic
                        current_time = time.time()
                        if current_time - last_executed_time > DEBOUNCE_INTERVAL:
                            print(f"Detected app: {app_name}")
                            self.execute_command(app_name, command_mappings)
                            last_executed_time = current_time
                            processed_lines.add(line)
                        else:
                            print(f"Debounced app: {app_name}")
                            processed_lines.add(line)


                last_known_position = log_file.tell()

        except FileNotFoundError:
            print(f"Error: Log file not found at {log_file}")
        except Exception as e:
            print(f"Error reading log file: {e}")

    def execute_command(self, app_name, command_mappings):
        """Executes the command associated with the given app name."""
        if app_name in command_mappings:
            command = command_mappings[app_name]

            # Check if the command needs the shell (e.g., 'start' or steam://)
            if self.is_function[app_name].get():
                try:
                    subprocess.Popen(command, shell=True)  # Execute the command _with_ shell=True
                    print(f"Executed (with shell): {command}")
                except Exception as e:
                    print(f"Error executing (with shell) {command}: {e}")
            else:
                try:
                    # Use shlex.split to handle spaces and arguments correctly
                    command_list = shlex.split(command, posix=False)
                    subprocess.Popen(command_list)
                    print(f"Executed: {command}")
                except Exception as e:
                    print(f"Error executing {command}: {e}")
        else:
            print(f"No command defined for app: {app_name}")

    def is_config_saved(self):
        """Check to see if config is saved"""
        config = {
            "log_file_path": self.log_file_path.get(),
            "app_commands": {app: self.app_commands[app].get() for app in self.app_commands},
            "is_function": {app: self.is_function[app].get() for app in self.is_function},
            "autostart_enabled": self.autostart_enabled.get(),
        }
        try:
            import json
            with open("config.json", "r") as f:
                current_config = json.load(f)
        except:
            return False
        return config == current_config

class TextRedirector:
    """A class for redirecting stdout and stderr to a Tkinter Text widget."""
    def __init__(self, widget, tag):
        self.widget = widget
        self.tag = tag

    def write(self, str):
        self.widget.configure(state="normal")
        self.widget.insert("end", str, (self.tag,))
        self.widget.configure(state="disabled")
        self.widget.see("end")

    def flush(self):
        pass

# --- Main ---
if __name__ == "__main__":
    root = tk.Tk()
    gui = LogMonitorGUI(root)

    # Initialize system tray icon only once
    gui.init_system_tray()

    # Override the close event
    root.protocol("WM_DELETE_WINDOW", gui.hide_window)

    root.mainloop()