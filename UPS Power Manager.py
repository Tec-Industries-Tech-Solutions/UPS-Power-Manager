#Import Libaries 
from tkinter import *
from tkinter import ttk
import tkinter as tk
import subprocess
import screeninfo as si 
from screeninfo import Monitor
import json
from tkinter import ttk, filedialog, messagebox

class Device:
    def __init__(self, number, name, port):
        self.number = number
        self.name = name
        self.port = port

    def to_dict(self):
        """Convert a Device instance to a dictionary for JSON storage."""
        return {"number": self.number, "name": self.name, "port": self.port}

    @staticmethod
    def from_dict(data):
        """Convert dictionary data back to a Device instance."""
        return Device(data["number"], data["name"], data["port"])

import json

SAVE_FILE = "device_data.json"  # File for storage

def save_devices():
    """Save device list to a JSON file and force file creation."""
    if not device_objects:
        print("No devices to save.")
        return

    try:
        with open(SAVE_FILE, "w") as file:
            json.dump([device.to_dict() for device in device_objects], file, indent=4)
        print("Device data saved successfully.")
    except Exception as e:
        print(f"Error saving devices: {e}")


def load_devices():
    """Load device list from a JSON file."""
    global device_objects
    try:
        with open(SAVE_FILE, "r") as file:
            data = json.load(file)
            device_objects = [Device.from_dict(device) for device in data]
            update_device_dropdown()  # Refresh UI dropdown
            result_label.config(text=f"{len(device_objects)} devices loaded.")
            print("Device data loaded.")
    except FileNotFoundError:
        print("No saved device data found.")

# Set the window size to to 1440p
root = tk.Tk()
root.geometry("2560x1440")
root.title("UPS Power Manager")

# Creating a Content Frame
mainframe = ttk.Frame(root, padding="3 3 12 12")
mainframe.grid(column=0, row=1, sticky=(N, W, E, S))

# Configure the weights for the root window
root.columnconfigure(0, weight=0)
root.rowconfigure(1, weight=1)

# Configure the weights for the mainframe
for i in range(12):  # Assuming 12 rows
    mainframe.grid_rowconfigure(i, weight=1)
for i in range(4):  # Assuming 4 columns
    mainframe.grid_columnconfigure(i, weight=1)

# Add a label and position it using grid
label = tk.Label(root, text="UPS Power Manager", font=("Garamondx", 70), fg="black", bg="light gray")
label.grid(row=0, column=0, columnspan=1, sticky=(W,E))  # Center the label

devices_count = 0
device_objects = []  # Stores all created devices

# Add a label that says how many devices are connected to the UPS
result_label = tk.Label(mainframe, text=f"{devices_count} devices are connected to the UPS", font=("Garamond", 20), fg="black", bg="light gray")
result_label.grid(column=0, row=0, columnspan=1, sticky=(W, N), padx=0, pady=10)  # Align to the center

# Add a label above the entry widget
entry_label = tk.Label(mainframe, text="Select device count (press select to submit)", font=("Garamond", 20), bg="light gray", fg="black")
entry_label.grid(column=0, row=1, columnspan=1, sticky=(W, N), padx=30, pady=5)  # Center the entry label

# Define a variable to store the selected option
selected_option = tk.StringVar()
selected_option.set("-")  # Set the default value

# Define the options for the drop-down box
options = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20"]
# Create the OptionMenu (drop-down box)
dropdown = tk.OptionMenu(mainframe, selected_option, *options)
dropdown.grid(column=0, row=1, columnspan=1, sticky = (W, E), padx=50, pady=10)  # Place the dropdown in the grid
dropdown.lift()

# Define a variable to store the selected device option
device_selected_option = tk.StringVar()
device_selected_option.set("-")  # Set the default value

# Create the device name dropdown (drop-down box)
device_selection_dropdown = tk.OptionMenu(mainframe, device_selected_option, "-")
device_selection_dropdown.config(bg="light gray", fg="black", activebackground="black", activeforeground="light gray")  # Set colors
device_selection_dropdown.grid(column=4, row=1, columnspan=1, sticky=(W, S), padx=5, pady=10)  # Adjust column and reduce padding

def update_device_dropdown():
    """Recreate the dropdown to reflect updated device names."""
    global device_selection_dropdown

    device_options = [f"{device.number} - {device.name}" for device in device_objects]  # Show number & name
    
    # Remove the old dropdown
    device_selection_dropdown.destroy()

    # Create a new dropdown with updated values
    device_selected_option.set("-")  # Reset selection
    device_selection_dropdown = tk.OptionMenu(mainframe, device_selected_option, *device_options)
    device_selection_dropdown.config(bg="light gray", fg="black", activebackground="black", activeforeground="light gray")
    device_selection_dropdown.grid(column=4, row=1, columnspan=1, sticky=(E, S), padx=5, pady=10)


# Function to update the label with the selected option and update device dropdown options
def show_selection():
    global devices_count, device_objects
    devices_count = int(selected_option.get())
    result_label.config(text=f"{devices_count} devices are connected to the UPS")

    device_objects = []
    for i in range(devices_count):
        device = Device(i + 1, f"Device_{i+1}", f"Port_{i+1}")
        device_objects.append(device)

    update_device_dropdown()  # Refresh dropdown menu
    save_devices()  # ⬅️ Ensure this is at the end!

# Create the Select button for the device count
select_button = ttk.Button(mainframe, text="Select", command=show_selection)
select_button.grid(column=0, row=2, columnspan=1, sticky=(W, E, N), padx=100, pady=0)

#Name of device
device_name_entry = tk.Entry(mainframe, width=45, bg="gray", fg="black")
device_name_entry.grid(column=5, row=1, columnspan=1, sticky=(W, S), padx=5, pady=10)  # Adjust padding to align with dropdown

device_names = []

# Define a list to store the device names
device_name_list = []

# Get device name and update the dropdown option
def get_device_name():
    """Update the selected device's name and refresh dropdown."""
    device_name_entry_value = device_name_entry.get()
    if device_selected_option.get() == "-":
        return

    selected_index = int(device_selected_option.get().split(" - ")[0]) - 1  # Get device number
    device_objects[selected_index].name = device_name_entry_value  # Update name in object

    update_device_dropdown()  # Refresh dropdown with updated names
    device_name_entry.delete(0, tk.END)


# Create the Select button for the device selection
device_select_button = ttk.Button(mainframe, text="Select", command=get_device_name)
device_select_button.grid(column=5, row=2, columnspan=1, sticky=(W, E, N), padx=100, pady=10)

battery_level = 0

# Function to fetch the battery level using the upsc command
def fetch_battery_level(ups_name="ups"):
    """Fetch UPS data using the upsc command locally."""
    command = ["upsc", ups_name]
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            ups_data = {}
            for line in result.stdout.strip().split("\n"):
                key, value = line.split(":", 1)
                ups_data[key.strip()] = value.strip()
            battery_level = int(ups_data.get("battery.charge", 0))
            return battery_level
        else:
            print(f"Error fetching UPS data for {ups_name}: {result.stderr}")
            return 0
    except Exception as e:
        print(f"Error: {e}")
        return 0

# Function to update the progress bar and schedule the next update
def update_progress():
    print("Updating progress...")  # Debug print
    battery_level = fetch_battery_level()  # Get the current battery level
    print(f"Updating progress bar with battery level: {battery_level}%")  # Debug print
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
battery_frame.grid(column=3, row=2, rowspan=1, columnspan=2, sticky=(N, W, E, S), padx=10, pady=10)

fetch_battery_level()

# Create a label to display the battery percentage
percentage_label = tk.Label(battery_frame, text=f"{battery_level}%", font=("Garamond", 20), bg="light gray", fg="black")
percentage_label.grid(column=0, row=2, columnspan=2, sticky=(W, E, N), padx=5, pady=10)

# Create a progress bar
progress_bar = ttk.Progressbar(battery_frame, orient="horizontal", length=750, mode="determinate", maximum=100)
progress_bar.grid(column=0, row=3, columnspan=2, sticky=(W, E, N), padx=10, pady=0)

# Create battery level label
battery_level_label = tk.Label(battery_frame, text="Battery Level", font=("Garamond", 20), bg = "light gray", fg = "black")
battery_level_label.grid(column=0, row=1, columnspan=2, sticky=(W, E), padx=5, pady=10)

# Add a style for the progress bar to make it taller
style.configure("TProgressbar", thickness=500)  # Adjust the thickness value as needed

# Apply the style to the progress bar
progress_bar.configure(style="TProgressbar")

#Label devices
device_label = tk.Label(mainframe, text="Enter the name for each device connected", font=("Garamond", 20), bg="light gray", fg="black")
device_label.grid(column = 5, row=1, columnspan=1, sticky=(N, W), padx =20, pady= 10)

#Create Save Devices button
save_button = ttk.Button(mainframe, text="Save Devices", command=save_devices)
save_button.grid(column=5, row=3, columnspan=1, sticky=(W, E), padx=100, pady=10)


# Bring the battery_frame to the front
battery_frame.lift()

# Bring the device_label to the front
device_label.lift()

# Start the update loop
update_progress()

load_devices()  # ⬅️ Load stored devices before starting the UI

#Create a button to load devices
load_button = ttk.Button(mainframe, text="Load Devices", command=load_devices)
load_button.grid(column=5, row=4, columnspan=1, sticky=(W, E), padx=100, pady=10)

#Create Device Tab class
class DeviceTab:
    """Base class for a notebook tab."""
    def __init__(self, notebook, title):
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text=title)
        self.setup_ui()

    def setup_ui(self):
        """Override this method in child classes to set up specific UI."""
        pass

class TabOne(DeviceTab):
    """First tab with device information."""
    def __init__(self, notebook):
        super().__init__(notebook, "Device Info")

    def setup_ui(self):
        label = tk.Label(self.frame, text="Device Information", font=("Garamond", 20))
        label.pack(pady=10)

class TabTwo(DeviceTab):
    """Second tab with additional functionality."""
    def __init__(self, notebook):
        super().__init__(notebook, "Settings")

    def setup_ui(self):
        label = tk.Label(self.frame, text="Settings Tab", font=("Garamond", 20))
        label.pack(pady=10)


# Function to open the device window
def open_device_window():
    """Open a new window to display device information."""
    device_window = tk.Tk()
    device_window.geometry("2560x1440")
    device_window.title("Device")

#Create a list of devices
choices = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20"]
choicesvar = StringVar(value=choices)
l = Listbox(root, listvariable=choicesvar)
l.grid(column=5, row=5, columnspan=1, sticky=(W, E), padx=100, pady=10)

# Create button to open device window
device_window_button = ttk.Button(mainframe, text="Device Window", command=open_device_window)
device_window_button.grid(column=5, row=5, columnspan=1, sticky=(W, E), padx=100, pady=10)

# Run the Tkinter event loop
root.mainloop()






