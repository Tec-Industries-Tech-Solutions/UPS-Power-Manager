#Import Libaries 
# Import required libraries
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import json

class Device:
    def __init__(self, number, name, port, status, logs=None, settings=None):
        self.number = number
        self.name = name
        self.port = port
        self.logs = logs or []
        self.settings = settings or {}
        self.status = status

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

# DeviceWindow class for displaying device information in a new window

# DeviceWindow class for displaying device information in a new window
class DeviceWindow:
    """Window to display and edit settings for a specific device."""
    def __init__(self, root, device: Device):
        self.device = device
        self.window = tk.Toplevel(root)
        self.window.configure(bg="#DCDAD6")
        self.window.title(f"Device {device.number}: {device.name}")
        self.window.geometry("2560x1440")
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        self.build_ui()

    def build_ui(self):
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
        items = ["Time", "Battery Percentage", "Cherry", "Date", "Elderberry"]
        for item in items:
            self.shutdown_condition_listbox.insert(tk.END, item)

        # Threshold Entry
        self.threshold_var = tk.StringVar()
        threshold_label = tk.Label(frame, text="Shutoff Threshold (%)", font=("Garamond", 18), bg="light gray", fg="black")
        threshold_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=10)
        threshold_entry = tk.Entry(frame, textvariable=self.threshold_var)
        threshold_entry.grid(row=3, column=2, columnspan=2, sticky="w", padx=10, pady=10)

        # Save Settings Button
        save_settings_button = tk.Button(
            frame,
            text="Save Settings",
            command=self.save_settings,
            font=("Garamond", 18),
            bg="light gray",
            fg="black",
            activebackground="black",
            activeforeground="light gray"
        )
        save_settings_button.grid(row=4, column=0, columnspan=6, sticky="ew", pady=20)

    def save_settings(self):
        """Save device settings from the UI."""
        try:
            threshold = int(self.threshold_var.get())
            if 0 <= threshold <= 100:
                self.device.settings["shutoff_threshold"] = threshold
                print(f"Shutoff threshold set to {threshold}% for device {self.device.name}")
            else:
                messagebox.showerror("Invalid Value", "Please enter a value between 0 and 100.")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number.")


# Constants
SAVE_FILE = "device_data.json"  # File for storage


def save_devices():
    """Save device list to a JSON file with error handling."""
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
    """Load device list from a JSON file with error handling."""
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
mainframe.grid(column=0, row=1, sticky=(tk.N, tk.W, tk.E, tk.S))

# Configure the weights for the root window
root.columnconfigure(0, weight=0)
root.rowconfigure(1, weight=1)

# Configure the weights for the mainframe
for i in range(12):  # Assuming 12 rows
    mainframe.grid_rowconfigure(i, weight=1)
for i in range(4):  # Assuming 4 columns
    mainframe.grid_columnconfigure(i, weight=1)

# Add a label and position it using grid
label = tk.Label(root, text="UPS Power Manager", font=("Garamond", 70), fg="black", bg="light gray")
label.grid(row=0, column=0, columnspan=1, sticky=(tk.W, tk.E))  # Center the label

devices_count = 0
device_objects = []  # Stores all created devices

# Add a label that says how many devices are connected to the UPS
result_label = tk.Label(mainframe, text=f"{devices_count} devices are connected to the UPS", font=("Garamond", 20), fg="black", bg="light gray")
result_label.grid(column=0, row=0, columnspan=1, sticky=(tk.W, tk.N), padx=0, pady=10)  # Align to the center

# Add a label above the entry widget
entry_label = tk.Label(mainframe, text="Select device count (press select to submit)", font=("Garamond", 20), bg="light gray", fg="black")
entry_label.grid(column=0, row=1, columnspan=1, sticky=(tk.W, tk.N), padx=30, pady=5)  # Center the entry label

# Define a variable to store the selected option
selected_option = tk.StringVar()
selected_option.set("-")  # Set the default value

# Define the options for the drop-down box
options = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20"]
# Create the OptionMenu (drop-down box)
dropdown = tk.OptionMenu(mainframe, selected_option, *options)
dropdown.grid(column=0, row=1, columnspan=1, sticky=(tk.W, tk.E), padx=50, pady=10)  # Place the dropdown in the grid
dropdown.lift()

# Define a variable to store the selected device option
device_selected_option = tk.StringVar()
device_selected_option.set("-")  # Set the default value

# Define a variable to store the device window option
device_window_option = tk.StringVar()
device_window_option.set("-") #Set the default value

# Create the device name dropdown (drop-down box)
device_selection_dropdown = tk.OptionMenu(mainframe, device_selected_option, "-")
device_selection_dropdown.config(bg="light gray", fg="black", activebackground="black", activeforeground="light gray")  # Set colors
device_selection_dropdown.grid(column=4, row=1, columnspan=1, sticky=(tk.W, tk.E), padx=5, pady=10)  # Adjust column and reduce padding

# Create the device window dropdown (drop-down box)
device_window_dropdown = tk.OptionMenu(mainframe, device_window_option, "-")
device_window_dropdown.config(bg="light gray", fg="black", activebackground="black", activeforeground="light gray")  # Set colors
device_window_dropdown.grid(column=5, row=5, columnspan=1, sticky=(tk.E), padx=5, pady=10)  # Adjust column and reduce padding


def update_device_dropdown():
    """Recreate the dropdowns to reflect updated device names."""
    global device_selection_dropdown
    global device_window_dropdown

    device_options = [f"{device.number} - {device.name}" for device in device_objects]  # Show number & name

    # Remove the old dropdowns
    device_selection_dropdown.destroy()
    device_window_dropdown.destroy()

    # Create a new dropdown with updated values (selection)
    device_selected_option.set("-")  # Reset selection
    device_selection_dropdown = tk.OptionMenu(mainframe, device_selected_option, *device_options)
    device_selection_dropdown.config(bg="light gray", fg="black", activebackground="black", activeforeground="light gray")
    device_selection_dropdown.grid(column=4, row=1, columnspan=1, sticky=(tk.W, tk.E), padx=5, pady=10)

    # Create a new dropdown with updated values (window)
    device_window_option.set("-")  # Reset selection
    device_window_dropdown = tk.OptionMenu(mainframe, device_window_option, *device_options)
    device_window_dropdown.config(bg="light gray", fg="black", activebackground="black", activeforeground="light gray")
    device_window_dropdown.grid(column=5, row=5, columnspan=1, sticky=(tk.W, tk.E), padx=5, pady=10)


# Function to update the label with the selected option and update device dropdown options
def show_selection():
    """Handle device count selection, update device list and dropdowns."""
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
        update_device_dropdown()  # Refresh dropdown menu
    save_devices()  # ⬅️ Ensure this is at the end!

# Create the Select button for the device count
select_button = ttk.Button(mainframe, text="Select", command=show_selection)
select_button.grid(column=0, row=2, columnspan=1, sticky=(tk.W, tk.E, tk.N), padx=100, pady=0)

# Name of device
device_name_entry = tk.Entry(mainframe, width=45, bg="gray", fg="black")
device_name_entry.grid(column=5, row=1, columnspan=1, sticky=(tk.W, tk.E), padx=5, pady=10)  # Adjust padding to align with label

device_names = []

# Define a list to store the device names
device_name_list = []


# Get device name and update the dropdown option
def get_device_name():
    """Update the selected device's name and refresh dropdown."""
    device_name_entry_value = device_name_entry.get()
    if device_selected_option.get() == "-":
        return
    try:
        selected_index = int(device_selected_option.get().split(" - ")[0]) - 1  # Get device number
        if 0 <= selected_index < len(device_objects):
            device_objects[selected_index].name = device_name_entry_value  # Update name in object
            update_device_dropdown()  # Refresh dropdown with updated names
            device_name_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "Selected device index out of range.")
    except Exception as e:
        messagebox.showerror("Error", f"Could not update device name: {e}")


# Create the Select button for the device selection
device_select_button = ttk.Button(mainframe, text="Select", command=get_device_name)
device_select_button.grid(column=5, row=2, columnspan=1, sticky=(tk.W, tk.E, tk.N), padx=100, pady=10)

# Battery level (global)
battery_level = 0

# Function to fetch the battery level using the upsc command
def fetch_battery_level(ups_name=None):
    """Fetch UPS data using the upsc command locally."""
    if not ups_name:
        ups_name = "ups"
        # Try to use device name if available
        if device_objects:
            ups_name = device_objects[0].name
    command = ["upsc", ups_name]
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            ups_data = {}
            for line in result.stdout.strip().split("\n"):
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                ups_data[key.strip()] = value.strip()
            return int(ups_data.get("battery.charge", 0))
        else:
            print(f"Error fetching UPS data for {ups_name}: {result.stderr}")
            return 0
    except Exception as e:
        print(f"Error: {e}")
        return 0

# Function to update the progress bar and schedule the next update
def update_progress():
    """Update the battery level progress bar and label."""
    global battery_level
    battery_level = fetch_battery_level()  # Get the current battery level
    progress_bar["value"] = battery_level  # Update progress bar
    percentage_label.config(text=f"{battery_level}%")  # Update label
    # Schedule the function to run again after 5000 milliseconds (5 seconds)
    root.after(5000, update_progress)

# Create a style for the frame
style = ttk.Style()
style.theme_use("clam")  # Use a theme that supports custom styles
style.configure("BatteryFrame.TFrame")  # Set the background color to light blue

# Create a frame for the battery information with the custom style and 3D effect
battery_frame = ttk.Frame(mainframe, padding="10 10 10 10", borderwidth=5, relief="raised", style="BatteryFrame.TFrame")
battery_frame.grid(column=3, row=2, rowspan=1, columnspan=2, sticky=(tk.N, tk.W, tk.E, tk.S), padx=10, pady=10)

fetch_battery_level()

# Create a label to display the battery percentage
percentage_label = tk.Label(battery_frame, text=f"{battery_level}%", font=("Garamond", 20), bg="light gray", fg="black")
percentage_label.grid(column=0, row=2, columnspan=2, sticky=(tk.W, tk.E, tk.N), padx=5, pady=10)

# Create a progress bar
progress_bar = ttk.Progressbar(battery_frame, orient="horizontal", length=750, mode="determinate", maximum=100)
progress_bar.grid(column=0, row=3, columnspan=2, sticky=(tk.W, tk.E, tk.N), padx=10, pady=0)

# Create battery level label
battery_level_label = tk.Label(battery_frame, text="Battery Level", font=("Garamond", 20), bg = "light gray", fg = "black")
battery_level_label.grid(column=0, row=1, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=10)

# Add a style for the progress bar to make it taller
style.configure("TProgressbar", thickness=30)  # Adjust the thickness value as needed

# Apply the style to the progress bar
progress_bar.configure(style="TProgressbar")

#Label devices
device_label = tk.Label(mainframe, text="Enter the name for each device connected", font=("Garamond", 20), bg="light gray", fg="black")
device_label.grid(column=5, row=1, columnspan=1, sticky=(tk.N, tk.W), padx=20, pady=10)

#Create Save Devices button
save_button = ttk.Button(mainframe, text="Save Devices", command=save_devices)
save_button.grid(column=5, row=3, columnspan=1, sticky=(tk.W, tk.E), padx=100, pady=10)


# Bring the battery_frame to the front
battery_frame.lift()

# Bring the device_label to the front
device_label.lift()

# Start the update loop
update_progress()

load_devices()  # ⬅️ Load stored devices before starting the UI

#Create a button to load devices
load_button = ttk.Button(mainframe, text="Load Devices", command=load_devices)
load_button.grid(column=5, row=4, columnspan=1, sticky=(tk.W, tk.E), padx=100, pady=10)


# Function to open the device window
def open_device_window():
    """Open a settings window for the selected device."""
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
def remove_device():
    """Remove the selected device from the device list and update dropdowns."""
    if device_selected_option.get() == "-":
        return
    try:
        selected_index = int(device_selected_option.get().split(" - ")[0]) - 1
        if 0 <= selected_index < len(device_objects):
            del device_objects[selected_index]
            update_device_dropdown()
            save_devices()
            result_label.config(text=f"{len(device_objects)} devices are connected to the UPS")
        else:
            messagebox.showerror("Error", "Selected device index out of range.")
    except Exception as e:
        messagebox.showerror("Error", f"Could not remove device: {e}")

# Create button to open device window
device_window_button = ttk.Button(mainframe, text="Device Window", command=open_device_window)
device_window_button.grid(column=5, row=5, columnspan=1, sticky=(tk.W, tk.E), padx=100, pady=10)


remove_device_button = ttk.Button(mainframe, text="Remove Device", command=remove_device)
remove_device_button.grid(column=4, row=2, columnspan=1, sticky=(tk.W, tk.E), padx=5, pady=10)

# Run the Tkinter event loop
root.mainloop()






