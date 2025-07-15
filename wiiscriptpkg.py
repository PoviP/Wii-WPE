import time
import os
import subprocess
import re
import shlex
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import json
import sys  # Import the sys module
import winreg as reg  # Import the winreg module (for Windows registry)
from PIL import Image, ImageTk  # Import PIL for icon support
import pystray  # Import pystray

POLL_INTERVAL = 1  # Moved POLL_INTERVAL to global scope

class LogMonitorGUI:
    def __init__(self, master):
        self.master = master
        master.title("Log Monitor Configuration")

        # --- Variables ---
        self.log_file_path = tk.StringVar(value="C:\\Program Files (x86)\\Steam\\steamapps\\common\\wallpaper_engine\\log.txt")
        self.app_commands = {f"app{i}": tk.StringVar() for i in range(1, 13)}
        self.is_function = {f"app{i}": tk.BooleanVar() for i in range(1, 13)} # Checkboxes if function.
        self.autostart_enabled = tk.BooleanVar()  # Checkbox to control autostart
        self.monitoring_active = tk.BooleanVar(value=False) # Indicate monitor is running or not

        # --- Log File Path ---
        tk.Label(master, text="Log File Path:").grid(row=0, column=0, sticky="w")
        tk.Entry(master, textvariable=self.log_file_path, width=60).grid(row=0, column=1, sticky="we")
        tk.Button(master, text="Browse", command=self.browse_log_file).grid(row=0, column=2, sticky="e")

        # --- App Configuration ---
        for i in range(1, 13):
            tk.Label(master, text=f"App {i} Command:").grid(row=i, column=0, sticky="w")
            tk.Entry(master, textvariable=self.app_commands[f"app{i}"], width=60).grid(row=i, column=1, sticky="we")
            tk.Checkbutton(master, text="Is Function?", variable=self.is_function[f"app{i}"] ).grid(row=i, column=2, sticky="e")  #Function Checkbox


        # --- Autostart Checkbox ---
        tk.Checkbutton(master, text="Autostart on Login", variable=self.autostart_enabled, command=self.update_autostart).grid(row=13, column=0, columnspan=3)

        # --- Terminal Output ---
        tk.Label(master, text="Output Terminal:").grid(row=16, column=0, sticky="w")
        self.terminal = tk.Text(master, height=10, width=70, state="disabled") # Create the terminal widget
        self.terminal.grid(row=17, column=0, columnspan=3, sticky="we")

        # --- Redirect stdout and stderr to the terminal ---
        sys.stdout = TextRedirector(self.terminal, "stdout") #Redirect terminal
        sys.stderr = TextRedirector(self.terminal, "stderr") #Redirect terminal


        # --- Buttons ---
        tk.Button(master, text="Save Configuration", command=self.save_configuration).grid(row=14, column=0, columnspan=3) #Modified buttons
        self.start_button = tk.Button(master, text="Start Monitoring", command=self.start_monitoring)
        self.start_button.grid(row=15, column=0, columnspan=3) #Modified Buttons


        # Load initial configuration
        self.load_configuration()

        # Initialize system tray icon and menu
        self.init_system_tray()

        # Hide the window on initialization
        self.master.withdraw()

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
          self.autostart_enabled.set(config.get("autostart_enabled", False))  # Load autostart setting
          self.update_autostart()

      except FileNotFoundError:
          pass  # Use default values if config file doesn't exist
      except Exception as e:
          messagebox.showerror("Error", f"Error loading configuration: {e}")

    def update_autostart(self):
        """Enables or disables autostart by creating/deleting a registry entry."""
        app_name = "LogMonitor"  # A name for your application in the registry
        app_path = sys.executable  # Path to the executable
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

        try:
            key = reg.OpenKey(reg.HKEY_CURRENT_USER, key_path, 0, reg.KEY_ALL_ACCESS)
            if self.autostart_enabled.get():
                reg.SetValueEx(key, app_name, 0, reg.REG_SZ, app_path)
            else:
                try:
                    reg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass  # Entry doesn't exist, nothing to delete
            reg.CloseKey(key)
        except Exception as e:
            messagebox.showerror("Error", f"Error updating autostart: {e}")

    def init_system_tray(self):
        """Initialize the system tray icon and menu."""
        image = Image.open("icon.png")  # Replace "icon.png" with the path to your icon file
        menu = (
            pystray.MenuItem("Show", self.show_window),
            pystray.MenuItem("Hide", self.hide_window),
            pystray.MenuItem("Quit", self.quit_app)
        )
        self.icon = pystray.Icon("Log Monitor", image, "Log Monitor", menu)

        # Start the icon in a separate thread to avoid blocking the GUI
        threading.Thread(target=self.icon.run, daemon=True).start()

    def show_window(self, icon, item):
        """Show the main window and stop hiding it."""
        self.master.after(0, self.master.deiconify)
        self.icon.update_menu() # Update menu if needed

    def hide_window(self, icon, item):
        """Hide the main window."""
        self.master.withdraw()
        self.icon.update_menu() # Update Menu if needed

    def quit_app(self, icon, item):
        """Quit the application."""
        self.icon.stop()
        self.master.destroy() # Properly close the Tkinter window

    def start_monitoring(self):
        """Starts the log monitoring process."""
        log_file = self.log_file_path.get()
        command_mappings = {app: self.app_commands[app].get() for app in self.app_commands}
        self.monitoring_active.set(True)
        self.start_button.config(text="Stop Monitoring", command=self.stop_monitoring) #Change buttons
        # --- Start Monitoring Logic ---
        global last_known_position, first_run  #Access Global Variables
        last_known_position = 0
        first_run = True

        def execute_command(app_name):
            """Executes the command associated with the given app name."""

            if app_name in command_mappings:
                command = command_mappings[app_name]
                if self.is_function[app_name].get():
                    try:
                        subprocess.Popen(command, shell=True)  # Execute the command *with* shell=True
                        print(f"Executed (with shell): {command}")
                    except Exception as e:
                        print(f"Error executing (with shell) {command}: {e}")
                else:
                    try:
                        # Use shlex.split to handle spaces and arguments correctly
                        command_list = shlex.split(command)
                        subprocess.Popen(command_list)  # Execute the command *without* shell=True
                        print(f"Executed: {command}")
                    except Exception as e:
                        print(f"Error executing {command}: {e}")
            else:
                print(f"No command defined for app: {app_name}")


        def read_log_and_execute(log_file_path):
            """Reads the log file for new entries and executes commands based on app names."""
            global last_known_position, first_run

            try:
                with open(log_file_path, 'r', encoding='utf-8') as log_file:

                    # On the first run, read to the end to skip existing entries.
                    if first_run:
                        log_file.seek(0, os.SEEK_END) # Seek to the end of the file
                        last_known_position = log_file.tell() #Update last_known_position
                        first_run = False # Turn the flag off

                    else: # Subsequent Runs
                        log_file.seek(last_known_position)  # Start from the last read position
                    for line in log_file:
                        match = re.search(r"Log: (app\d+)", line)

                        if match:
                            app_name = match.group(1)  # Extract the app name from the matched group
                            print(f"Detected app: {app_name}")
                            execute_command(app_name)

                    last_known_position = log_file.tell()  # Update the last read position

            except FileNotFoundError:
                print(f"Error: Log file not found at {log_file_path}")
            except Exception as e:
                print(f"Error reading log file: {e}")

        # --- Start the monitoring loop in a separate thread ---
        self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        messagebox.showinfo("Monitoring", "Log monitoring started in the background.")

    def stop_monitoring(self):
        """Stops the log monitoring process."""
        self.monitoring_active.set(False)
        self.start_button.config(text="Start Monitoring", command=self.start_monitoring) # Change buttons

    def monitoring_loop(self):
        """The main monitoring loop."""
        log_file = self.log_file_path.get()
        global last_known_position, first_run #Access Global Variables
        while self.monitoring_active.get():
            self.read_log_and_execute(log_file)
            time.sleep(POLL_INTERVAL)

        print("Monitoring stopped.") #Show message

    def read_log_and_execute(self, log_file_path):
        """Reads the log file for new entries and executes commands based on app names."""
        global last_known_position, first_run

        command_mappings = {app: self.app_commands[app].get() for app in self.app_commands}

        try:
            with open(log_file_path, 'r', encoding='utf-8') as log_file:

                # On the first run, read to the end to skip existing entries.
                if first_run:
                    log_file.seek(0, os.SEEK_END) # Seek to the end of the file
                    last_known_position = log_file.tell() #Update last_known_position
                    first_run = False # Turn the flag off

                else: # Subsequent Runs
                    log_file.seek(last_known_position)  # Start from the last read position
                for line in log_file:
                    match = re.search(r"Log: (app\d+)", line)

                    if match:
                        app_name = match.group(1)  # Extract the app name from the matched group
                        print(f"Detected app: {app_name}")
                        self.execute_command(app_name, command_mappings) #Pass the command mapping

                last_known_position = log_file.tell()  # Update the last read position

        except FileNotFoundError:
            print(f"Error: Log file not found at {log_file_path}")
        except Exception as e:
            print(f"Error reading log file: {e}")

    def execute_command(self, app_name, command_mappings):
        """Executes the command associated with the given app name."""
        if app_name in command_mappings:
            command = command_mappings[app_name]
            if self.is_function[app_name].get():
                try:
                    subprocess.Popen(command, shell=True)  # Execute the command *with* shell=True
                    print(f"Executed (with shell): {command}")
                except Exception as e:
                    print(f"Error executing (with shell) {command}: {e}")
            else:
                try:
                    # Use shlex.split to handle spaces and arguments correctly
                    command_list = shlex.split(command)
                    subprocess.Popen(command_list)  # Execute the command *without* shell=True
                    print(f"Executed: {command}")
                except Exception as e:
                    print(f"Error executing {command}: {e}")
        else:
            print(f"No command defined for app: {app_name}")

class TextRedirector:
    """A class for redirecting stdout and stderr to a Tkinter Text widget."""
    def __init__(self, widget, tag):
        self.widget = widget
        self.tag = tag

    def write(self, str):
        self.widget.configure(state="normal")
        self.widget.insert("end", str, (self.tag,))
        self.widget.configure(state="disabled")
        self.widget.see("end")  # Autoscroll to the end

    def flush(self):
        pass

# --- Main ---
if __name__ == "__main__":
    root = tk.Tk()
    gui = LogMonitorGUI(root)
    root.mainloop()