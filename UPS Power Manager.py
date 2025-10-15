# Constants
UPS_NAME = "ups"
VERSION = "1.0.3"
LAST_UPDATE = "2025-10-03"

#Import Libaries 
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import json
from typing import Optional

class Device:
    def __init__(self, number, name, port, status, logs=None, settings=None):
        self.number = number
        self.name = name
        self.port = port
        self.logs = logs or []
        self.settings = settings or {}
        self.status = status
        # Conditions for shutdown (list of dicts, e.g., {"type": "battery", "threshold": 20})
        self.conditions = self.settings.get("conditions", [])

    def to_dict(self):
        """Convert a Device instance to a dictionary for JSON storage."""
        return {
            "number": self.number,
            "name": self.name,
            "port": self.port,
            "status": self.status,
            "logs": self.logs,
            "settings": self.settings,
        }

    @staticmethod
    def from_dict(data):
        """Convert dictionary data back to a Device instance."""
        return Device(
            number=data["number"],
            name=data["name"],
            port=data["port"],
            status=data.get("status", "Disconnected"),
            logs=data.get("logs", []),
            settings=data.get("settings", {}),
        )

    def should_shutdown(self, battery_level: int, runtime_left: Optional[int] = None, load_percent: Optional[int] = None) -> bool:
        """
        Determine whether this device should shut down based on its defined conditions.
        Args:
            battery_level: Current UPS battery percentage.
            runtime_left: Estimated UPS runtime in minutes (optional).
            load_percent: Current UPS load percentage (optional).
        Returns:
            bool: True if shutdown conditions are met, otherwise False.
        """
        for condition in self.conditions:
            ctype = condition.get("type")
            threshold = condition.get("threshold")

            if ctype == "battery" and battery_level <= threshold:
                return True
            elif ctype == "runtime" and runtime_left is not None and runtime_left <= threshold:
                return True
            elif ctype == "load" and load_percent is not None and load_percent >= threshold:
                return True
        return False


# Helper function for dropdowns
def create_option_menu(parent: tk.Widget, variable: tk.StringVar, options, column: int, row: int, columnspan: int = 1):
    """
    Create a styled OptionMenu and place it in the grid.
    """
    menu = tk.OptionMenu(parent, variable, *options)
    menu.config(bg="light gray", fg="black", activebackground="black", activeforeground="light gray")
    menu.grid(column=column, row=row, columnspan=columnspan, sticky='we', padx=5, pady=10)
    return menu


# DeviceWindow class for displaying device information in a new window
class DeviceWindow:
    """Window to display and edit settings for a specific device."""
    def __init__(self, root, device: Device):
        self.device = device
        self.selected_condition = "None"
        self.selected_threshold = "N/A"
        self.window = tk.Toplevel(root)
        self.window.configure(bg="#DCDAD6")
        self.window.title(f"Device {device.number}: {device.name}")
        self.window.geometry("2560x1440")
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        self.build_gui()

    def build_gui(self):
        """Build the device settings UI."""
        frame = tk.Frame(self.window, bg="#DCDAD6", padx=20, pady=20)
        frame.grid(row=0, column=0, sticky="nsew")

        # Configure the weights for the frame
        for i in range(12):  # Assuming 12 rows
            frame.grid_rowconfigure(i, weight=1)
        for i in range(6):  # Assuming 6 columns
            frame.grid_columnconfigure(i, weight=1)

        # Device Information Section
        tk.Label(frame, text="Device Information", font=("Garamond", 30), bg="light gray", fg="black").grid(row=0, column=0, columnspan=2, sticky="w", pady=10)
        tk.Label(frame, text=f"Name: {self.device.name}", font=("Garamond", 20), bg="light gray", fg="black").grid(row=1, column=0, columnspan=2, sticky="w", pady=10)
        tk.Label(frame, text=f"Port: {self.device.port}", font=("Garamond", 20), bg="light gray", fg="black").grid(row=2, column=0, columnspan=2, sticky="w", pady=10)

        # Settings Section
        tk.Label(frame, text="Settings", font=("Garamond", 30), bg="light gray", fg="black").grid(row=0, column=4, columnspan=2, sticky="w", pady=10)
        tk.Label(frame, text="Select condition for shutdown", font=("Garamond", 20), bg="light gray", fg="black").grid(row=1, column=4, columnspan=2, sticky="w", pady=10)
        
        # Listbox for shutdown condition
        self.shutdown_condition_listbox = tk.Listbox(frame)
        self.shutdown_condition_listbox.grid(row=2, column=4, columnspan=2, sticky="nsew", padx=10, pady=10)  # Consistent sticky
        items = ["UPS Time left", "Battery Percentage", "Elapsed time on battery", "UPS load", "Protection offline"]
        for item in items:
            self.shutdown_condition_listbox.insert(tk.END, item)

        # Threshold Entry
        self.threshold_var = tk.StringVar()
        threshold_label = tk.Label(frame, text="Shutoff Threshold", font=("Garamond", 18), bg="light gray", fg="black")
        threshold_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=10)
        threshold_entry = tk.Entry(frame, textvariable=self.threshold_var)
        threshold_entry.grid(row=3, column=2, columnspan=2, sticky="w", padx=10, pady=10)
        
        

        # Determine current condition type before threshold display
        if self.device.conditions:
            last_condition = self.device.conditions[-1]
            condition_type = last_condition.get("type", "")
        else:
            condition_type = ""

        # Threshold info display using instance variables for later update
        self.threshold_condition_label = tk.Label(frame, text=f'Threshhold condition: {self.selected_condition}', bg="light gray", fg="black")
        self.threshold_condition_label.grid(row=4, column=0, columnspan=1, sticky="w")
        if "runtime" in condition_type:
            self.threshold_value_label = tk.Label(frame, text=f'Threshhold value: {self.selected_threshold} min', bg="light gray", fg="black")
        elif "battery" in condition_type:
            self.threshold_value_label = tk.Label(frame, text=f'Threshhold value: {self.selected_threshold}%', bg="light gray", fg="black")
        elif "elapsed_time" in condition_type:
            self.threshold_value_label = tk.Label(frame, text=f'Threshhold value: {self.selected_threshold} min', bg="light gray", fg="black")
        elif "load" in condition_type:
            self.threshold_value_label = tk.Label(frame, text=f'Threshhold value: {self.selected_threshold}%', bg="light gray", fg="black")
        else:
            self.threshold_value_label = tk.Label(frame, text=f'Threshhold value: {self.selected_threshold} min', bg="light gray", fg="black")

        self.threshold_value_label.grid(row=5, column=0, columnspan=1, sticky="w")


        # Save Settings Button
        save_settings_button = tk.Button(frame, text="Save Settings", command=self.save_settings, font=("Garamond", 18), bg="light gray", fg="black", activebackground="black", activeforeground="light gray")
        save_settings_button.grid(row=6, column=0, columnspan=6, sticky="ew", pady=20)

    def save_settings(self):
        """
        Save device settings from the UI.

        This method sets two new instance variables:
        - self.selected_threshold: holds the numeric threshold entered by the user.
        - self.selected_condition: holds the string name of the condition selected from the listbox.
        You can access these variables later to retrieve the user's last selections.
        """
        try:
            # Get the threshold value
            threshold = int(self.threshold_var.get())
            self.selected_threshold = threshold  # Store threshold in an instance variable

            # Get selected condition from listbox
            selected_condition = self.shutdown_condition_listbox.get(tk.ACTIVE)
            self.selected_condition = selected_condition  # Store selected condition in an instance variable

            # Map user-friendly names to internal condition types
            condition_type_map = {
                "Battery Percentage": "battery",
                "UPS Time left": "runtime",
                "UPS load": "load",
                "Elapsed time on battery": "elapsed_time",
                "Protection offline": "protection"
            }

            condition_type = condition_type_map.get(selected_condition)

            if condition_type:
                # Create and store the condition
                condition = {"type": condition_type, "threshold": threshold}
                self.device.conditions.append(condition)
                self.device.settings["conditions"] = self.device.conditions

                # Also store the raw threshold in settings for reference
                self.device.settings["shutoff_threshold"] = threshold

                print(f"Saved shutdown condition for {self.device.name}: {condition}")
                messagebox.showinfo("Settings Saved", f"Condition '{selected_condition}' with threshold {threshold} saved.")
                # Update displayed threshold info
                self.threshold_condition_label.config(text=f"Threshhold condition: {self.selected_condition}")
                self.threshold_value_label.config(text=f"Threshhold value: {self.selected_threshold}")
            else:
                messagebox.showerror("Invalid Condition", "Please select a valid shutdown condition.")

        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number.")


# Constants
SAVE_FILE = "device_data.json"  # File for storage


def save_devices():
    """Save device list to a JSON file with error handling.

    Returns:
        None
    """
    if not device_objects:
        print("No devices to save.")
        return
    try:
        tmp_file = SAVE_FILE + ".tmp"
        with open(tmp_file, "w") as file:
            json.dump([device.to_dict() for device in device_objects], file, indent=4)
        os.replace(tmp_file, SAVE_FILE)
        print("Device data saved successfully.")
    except Exception as e:
        print(f"Error saving devices: {e}")


def load_devices():
    """Load device list from a JSON file with error handling.

    Returns:
        None
    """
    global device_objects
    try:
        with open(SAVE_FILE, "r") as file:
            data = json.load(file)
            device_objects = [Device.from_dict(device) for device in data]
        if device_objects:
            update_device_dropdown()  # Refresh UI dropdown
        result_label.config(text=f"{len(device_objects)} devices loaded.")
        print("Device data loaded.")
    except FileNotFoundError:
        print("No saved device data found.")
    except Exception as e:
        print(f"Error loading devices: {e}")

# Set the window size to to 1440p
root = tk.Tk()
root.geometry("2560x1440")
root.title("UPS Power Manager")

# Creating a Content Frame
mainframe = ttk.Frame(root, padding="3 3 12 12")
mainframe.grid(column=0, row=1, sticky='nwes')

# Configure the weights for the root window
root.columnconfigure(0, weight=0)
root.rowconfigure(1, weight=1)

# Configure the weights for the mainframe
for i in range(12):  # Assuming 12 rows
    mainframe.grid_rowconfigure(i, weight=1)
for i in range(4):  # Assuming 4 columns
    mainframe.grid_columnconfigure(i, weight=1)
# Ensure column 5 does not stretch
mainframe.grid_columnconfigure(5, weight=0)
mainframe.grid_columnconfigure(4, weight=0)

# Add a label and position it using grid
label = tk.Label(root, text="UPS Power Manager", font=("Garamond", 70), fg="black", bg="light gray")
label.grid(row=0, column=0, columnspan=1, sticky='we')  # Center the label

devices_count = 0
device_objects = []  # Stores all created devices

# Add a label that says how many devices are connected to the UPS
result_label = tk.Label(mainframe, text=f"{devices_count} devices are connected to the UPS", font=("Garamond", 20), fg="black", bg="light gray")
result_label.grid(column=0, row=0, columnspan=1, sticky='wn', padx=0, pady=10)  # Align to the center

# Add a label above the entry widget
entry_label = tk.Label(mainframe, text="Select device count (press select to submit)", font=("Garamond", 20), bg="light gray", fg="black")
entry_label.grid(column=0, row=1, columnspan=1, sticky='wn', padx=30, pady=5)  # Center the entry label

# Define a variable to store the selected option
selected_option = tk.StringVar()
selected_option.set("-")  # Set the default value

# Define the options for the drop-down box
options = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20"]
# Create the OptionMenu (drop-down box) using helper
dropdown = create_option_menu(mainframe, selected_option, options, column=0, row=1, columnspan=1)
dropdown.lift()

# Define a variable to store the selected device option
device_selected_option = tk.StringVar()
device_selected_option.set("-")  # Set the default value

# Define a variable to store the device window option
device_window_option = tk.StringVar()
device_window_option.set("-") #Set the default value

# Create the device name dropdown (drop-down box) using helper
device_selection_dropdown = create_option_menu(mainframe, device_selected_option, ["-"], column=5, row=1, columnspan=1)
device_window_dropdown = create_option_menu(mainframe, device_window_option, ["-"], column=5, row=5)
device_window_dropdown.config(width=12)
device_window_dropdown.grid(sticky='e', padx=5, pady=10)


def update_device_dropdown() -> None:
    """
    Recreate the dropdowns to reflect updated device names.
    """
    global device_selection_dropdown
    global device_window_dropdown
    device_options = [f"{device.number} - {device.name}" for device in device_objects]
    # Remove the old dropdowns
    device_selection_dropdown.destroy()
    device_window_dropdown.destroy()
    # Create a new dropdown with updated values using helper
    device_selected_option.set("-")
    device_selection_dropdown = create_option_menu(mainframe, device_selected_option, device_options, column=4, row=1, columnspan=1)
    device_selection_dropdown.grid(sticky='w', padx=5, pady=10)
    device_window_option.set("-")
    device_window_dropdown = create_option_menu(mainframe, device_window_option, device_options, column=4, row=5)
    device_window_dropdown.config(width=12)
    device_window_dropdown.grid(sticky='w', padx=5, pady=10)


# UI refresh helper
def refresh_ui() -> None:
    """
    Refresh device dropdowns, progress bar, and device count label.
    """
    update_device_dropdown()
    update_progress()
    result_label.config(text=f"{len(device_objects)} devices are connected to the UPS")


# Function to update the label with the selected option and update device dropdown options
def show_selection() -> None:
    """
    Handle device count selection, update device list and dropdowns.
    """
    global devices_count, device_objects
    try:
        devices_count = int(selected_option.get())
    except Exception as e:
        messagebox.showerror("Invalid Selection", "Please select a valid device count.")
        return
    result_label.config(text=f"{devices_count} devices are connected to the UPS")
    device_objects = []
    for i in range(devices_count):
        device = Device(i + 1, f"Device_{i+1}", f"Port_{i+1}", status="Disconnected")
        device_objects.append(device)
        print("Creating device:", i+1)
    if device_objects:
        update_device_dropdown()
    save_devices()

# Create the Select button for the device count
select_button = ttk.Button(mainframe, text="Select", command=show_selection)
select_button.grid(column=0, row=2, columnspan=1, sticky='wen', padx=100, pady=0)

# Name of device
device_name_entry = tk.Entry(mainframe, width=45, bg="gray", fg="black")
device_name_entry.grid(column=5, row=1, columnspan=1, sticky='we', padx=5, pady=10)  # Adjust padding to align with label

device_names = []

# Define a list to store the device names
device_name_list = []


# Get device name and update the dropdown option
def get_device_name() -> None:
    """
    Update the selected device's name and refresh dropdown.
    """
    device_name_entry_value = device_name_entry.get()
    if device_selected_option.get() == "-":
        return
    try:
        selected_index = int(device_selected_option.get().split(" - ")[0]) - 1
        if 0 <= selected_index < len(device_objects):
            device_objects[selected_index].name = device_name_entry_value
            update_device_dropdown()
            device_name_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "Selected device index out of range.")
    except Exception as e:
        messagebox.showerror("Error", f"Could not update device name: {e}")


# Create the Select button for the device selection
device_select_button = ttk.Button(mainframe, text="Select", command=get_device_name)
device_select_button.grid(column=5, row=2, columnspan=1, sticky='wen', padx=100, pady=10)

# Battery level (global)
battery_level = 0

# Function to fetch the battery level using the upsc command
def fetch_battery_level(ups_name: str = UPS_NAME) -> int:
    """
    Fetch UPS battery charge level using the upsc command.
    Args:
        ups_name: Optional; UPS name string.
    Returns:
        int: Battery charge percentage, or 0 on error.
    """
    if not ups_name:
        ups_name = UPS_NAME
        if device_objects:
            ups_name = device_objects[0].name
    try:
        result = subprocess.run(["upsc", ups_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            print(f"Error fetching UPS data for {ups_name}: {result.stderr}")
            return 0
        ups_data = dict(line.split(":", 1) for line in result.stdout.strip().split("\n") if ":" in line)
        return int(ups_data.get("battery.charge", "0"))
    except Exception as e:
        print(f"Error: {e}")
        return 0

# Function to update the progress bar and schedule the next update
def update_progress() -> None:
    """
    Update the battery level progress bar and label.
    """
    global battery_level
    battery_level = fetch_battery_level()
    progress_bar["value"] = battery_level
    percentage_label.config(text=f"{battery_level}%")
    root.after(5000, update_progress)

# Create a style for the frame
style = ttk.Style()
style.theme_use("clam")  # Use a theme that supports custom styles
style.configure("BatteryFrame.TFrame")  # Set the background color to light blue

# Create a frame for the battery information with the custom style and 3D effect
battery_frame = ttk.Frame(mainframe, padding="10 10 10 10", borderwidth=5, relief="raised", style="BatteryFrame.TFrame")
battery_frame.grid(column=3, row=2, rowspan=1, columnspan=2, sticky='nwes', padx=10, pady=10)

fetch_battery_level()

# Create a label to display the battery percentage
percentage_label = tk.Label(battery_frame, text=f"{battery_level}%", font=("Garamond", 20), bg="light gray", fg="black")
percentage_label.grid(column=0, row=2, columnspan=2, sticky='wen', padx=5, pady=10)

# Create a progress bar
progress_bar = ttk.Progressbar(battery_frame, orient="horizontal", length=750, mode="determinate", maximum=100)
progress_bar.grid(column=0, row=3, columnspan=2, sticky='wen', padx=10, pady=0)

# Create battery level label
battery_level_label = tk.Label(battery_frame, text="Battery Level", font=("Garamond", 20), bg = "light gray", fg = "black")
battery_level_label.grid(column=0, row=1, columnspan=2, sticky='we', padx=5, pady=10)

# Add a style for the progress bar to make it taller
style.configure("TProgressbar", thickness=30)  # Adjust the thickness value as needed

# Apply the style to the progress bar
progress_bar.configure(style="TProgressbar")

#Label devices
device_label = tk.Label(mainframe, text="Enter the name for each device connected", font=("Garamond", 20), bg="light gray", fg="black")
device_label.grid(column=5, row=0, columnspan=1, sticky='sw', padx=20, pady=10)

#Create Save Devices button
save_button = ttk.Button(mainframe, text="Save Devices", command=save_devices)
save_button.grid(column=5, row=3, columnspan=1, sticky='we', padx=100, pady=10)


# Bring the battery_frame to the front
battery_frame.lift()

# Bring the device_label to the front
device_label.lift()

# Start the update loop
update_progress()

load_devices()  # ⬅️ Load stored devices before starting the UI

#Create a button to load devices
load_button = ttk.Button(mainframe, text="Load Devices", command=load_devices)
load_button.grid(column=5, row=4, columnspan=1, sticky='we', padx=100, pady=10)


# Function to open the device window
def open_device_window() -> None:
    """
    Open a settings window for the selected device.
    """
    if device_window_option.get() == "-":
        return
    try:
        selected_index = int(device_window_option.get().split(" - ")[0]) - 1
        if 0 <= selected_index < len(device_objects):
            selected_device = device_objects[selected_index]
            DeviceWindow(root, selected_device)
        else:
            messagebox.showerror("Error", "Selected device index out of range.")
    except Exception as e:
        messagebox.showerror("Error", f"Could not open device window: {e}")


# Function to remove a device and update dropdowns accordingly
def remove_device() -> None:
    """
    Remove the selected device from the device list and update dropdowns.
    """
    if device_selected_option.get() == "-":
        return
    if not messagebox.askyesno("Confirm Delete", "Are you sure you want to remove this device?"):
        return
    try:
        global device_objects
        selected_index = int(device_selected_option.get().split(" - ")[0]) - 1
        if 0 <= selected_index < len(device_objects):
            del device_objects[selected_index]
            refresh_ui()
            save_devices()
    except Exception as e:
        messagebox.showerror("Error", f"Could not remove device: {e}")

# Create button to open device window
device_window_button = ttk.Button(mainframe, text="Device Window", command=open_device_window)
device_window_button.grid(column=5, row=5, columnspan=2, padx=0, pady=10)
device_window_button.config(width=24)

# Run the Tkinter event loop with exception handling
try:
    root.mainloop()
except Exception as e:
    print(f"UI error: {e}")






