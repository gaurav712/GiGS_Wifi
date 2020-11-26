#!/usr/bin/python3

from os import listdir
from os.path import isfile, isdir, join
from subprocess import check_output, run
from sys import stderr
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from threading import Thread
from time import sleep

from refresh_networks import RefreshNetworkThread, Network

# Globals
WLAN_TURN_OFF_CMD = "sudo rfkill block wifi"
WLAN_TURN_ON_CMD = "sudo rfkill unblock wifi"
NET_DEVICES_DIR = "/sys/class/net"
DEV_TYPE_CMD = "cat /sys/class/net/DEV_NAME/uevent | head -n 1 | cut -d'=' -f2"
RFKILL_DEV_NAME_CMD = "grep wlan /sys/class/rfkill/*/type | head -n 1 | cut -d':' -f1 | grep -o rfkill[0-9]"
WLAN_STATE_CMD = "cat /sys/class/rfkill/RFKILL_DEV_NAME/state"

DEFAULT_PADDING = 10
NO_PADDING = 0
REFRESH_BUTTON_LABEL = "Refresh"
SEARCHING = False

class MainWindow(Gtk.Window):

    def __init__(self, interface):

        self.interface = interface

        Gtk.Window.__init__(self, title = "Available Networks")
        self.connect("destroy", self.close_root_window)

        self.set_size_request(360, 360)
        self.set_position(Gtk.WindowPosition.CENTER)    # place it in center
        self.set_decorated(False)   # No decorations

        # This box is used as the root layout
        self.vertical_box = Gtk.Box()
        self.add(self.vertical_box)  # add the box to the window
        self.vertical_box.set_orientation(Gtk.Orientation.VERTICAL)

        # This box contains the wifi power state related stuff
        self.wifi_state_section_box = Gtk.Box()
        self.vertical_box.pack_start(self.wifi_state_section_box, False, False, DEFAULT_PADDING)    # add the box to the vertical_box

        # Add a relevant Label
        self.wifi_label = Gtk.Label()
        self.wifi_state_section_box.pack_start(self.wifi_label, False, False, DEFAULT_PADDING)    # add it to wifi_state_section_box
        self.wifi_label.set_text("WiFi")

        # Add a toggle switch
        self.wifi_state_switch = Gtk.Switch()
        self.wifi_state_section_box.pack_end(self.wifi_state_switch, False, False, DEFAULT_PADDING) # add to wifi_state_section_box
        self.wifi_state_switch.connect("notify::active", self.toggle_wifi_switch)

        # Spawn a thread to toggle switch automatically (in case if wifi state is toggled externally)
        self.refresh_toggle_switch_thread = RefreshToggleSwitchState(self.wifi_state_switch)
        self.refresh_toggle_switch_thread.start()

        # Add a refresh button(to refresh available networks' list)
        self.refresh_button = Gtk.Button()
        self.refresh_button.connect('clicked', self.refresh_button_clicked) # attatch to a function
        self.wifi_state_section_box.pack_end(self.refresh_button, False, False, DEFAULT_PADDING)  # add it to wifi_state_section_box
        self.refresh_button.set_label(REFRESH_BUTTON_LABEL)

        self.network_list_section = Gtk.ScrolledWindow()
        self.vertical_box.pack_start(self.network_list_section, True, True, NO_PADDING)    # add it to the vertical_box

        # To list the networks
        self.network_list = Gtk.ListBox()
        self.network_list_section.add(self.network_list)  # add it to the ScrolledWindow

    # Toggle wifi on/off
    def toggle_wifi_switch(self, switch, gparam):
        if switch.get_active():
            run(WLAN_TURN_ON_CMD, shell=True)
            print('turned on')
            self.refresh_network_list()
        else:
            run(WLAN_TURN_OFF_CMD, shell=True)
            self.clear_listbox()

    def refresh_network_list(self):
        if check_wlan_state():  # Make sure wifi is enabled
            # Search for networks and add to the list (if available)
            refreshNetworkThread = RefreshNetworkThread(self.interface, self.network_list)
            refreshNetworkThread.start()

    def refresh_button_clicked(self, button):
        # Clear listbox
        self.clear_listbox()

        # Reload the networks
        self.refresh_network_list()

    def clear_listbox(self):
        # Remove all the existing rows from the listbox
        for row in self.network_list:
            self.network_list.remove(row)

    def close_root_window(self, signal):
        self.refresh_toggle_switch_thread.terminate()
        Gtk.main_quit()

# Thread to refresh the toggle switch
class RefreshToggleSwitchState(Thread):

    def __init__(self, wifi_state_switch):
        Thread.__init__(self)

        self.should_terminate = False
        self.wifi_state_switch = wifi_state_switch

    def run(self):
        while(not self.should_terminate):
            if check_wlan_state() and not self.wifi_state_switch.get_active():
                self.wifi_state_switch.set_active(True)
            elif not check_wlan_state() and self.wifi_state_switch.get_active():
                self.wifi_state_switch.set_active(False)

            sleep(0.5)

    def terminate(self):
        self.should_terminate = True

# Get wifi interface
def get_wifi_interface():
    directories = [f for f in listdir(NET_DEVICES_DIR) if isdir(join(NET_DEVICES_DIR, f))]
    for directory in directories:
        if check_output(DEV_TYPE_CMD.replace("DEV_NAME", directory, 1), shell=True).decode().strip() == "wlan":
            return directory

    print("Can't find the wifi interface!", file = stderr)

# Check wifi state
def check_wlan_state():

    # Get rfkill device name
    rfkill_dev_name = check_output(RFKILL_DEV_NAME_CMD, shell=True).decode().strip()

    # Check if wifi is on or off
    if check_output(WLAN_STATE_CMD.replace("RFKILL_DEV_NAME", rfkill_dev_name, 1), shell=True).decode().strip() == "1":
        return True
    return False

############# MAIN ##############

interface = get_wifi_interface()

# Draw and show the network selection window
mainWindow = MainWindow(interface)
mainWindow.show_all()
Gtk.main()
