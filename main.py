from os import listdir
from os.path import isfile, isdir, join
from subprocess import check_output, run, CalledProcessError
from sys import stderr
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
from time import sleep

# Globals
WLAN_TURN_OFF_CMD = "sudo rfkill block wifi"
WLAN_TURN_ON_CMD = "sudo rfkill unblock wifi"
WPA_SUPPL_TERM_CMD = "sudo killall wpa_supplicant"
SCAN_CMD = "sudo wpa_cli -i DEV_NAME scan 2> /dev/null"
# SCAN_RESULTS_CMD = "sudo wpa_cli -i DEV_NAME scan_results | sed 1d | cut -f4-"
SCAN_RESULTS_CMD = "sudo wpa_cli -i DEV_NAME scan_results | cut -f4- \
| sed -e 1d -e 's/\\[WPA2-.*\\]/(WPA2)/g' -e 's/\\[ESS\\]//g' -e 's/\t/|/g' -e 's/\\[WPA-.*\\]/(WPA)/g'"
WPA_SUPPL_CMD = "sudo wpa_supplicant -D nl80211 -i DEV_NAME -C /run/wpa_supplicant -B"
NET_DEVICES_DIR = "/sys/class/net"
DEV_TYPE_CMD = "cat /sys/class/net/DEV_NAME/uevent | head -n 1 | cut -d'=' -f2"
RFKILL_DEV_NAME_CMD = "grep wlan /sys/class/rfkill/*/type | head -n 1 | cut -d':' -f1 | grep -o rfkill[0-9]"
WLAN_STATE_CMD = "cat /sys/class/rfkill/RFKILL_DEV_NAME/state"

DEFAULT_PADDING = 10
NO_PADDING = 0
REFRESH_BUTTON_LABEL = "Refresh"
SEARCHING = False

class WifiNetwork():

    def __init__(self, parent_list_box, ssid, protection):

        # Add a box
        box = Gtk.Box()

        # To show the SSID of the network
        ssid_label = Gtk.Label()
        ssid_label.set_text(ssid)
        ssid_label.set_line_wrap(True)
        ssid_label.set_xalign(-1)

        # Add it to the box
        box.pack_start(ssid_label, True, True, DEFAULT_PADDING)

        if protection is not None:
            protection_label = Gtk.Label()
            protection_label.set_text(protection)

            # Add it to the box
            box.pack_end(protection_label, False, False, DEFAULT_PADDING)

        # add the box to the root widget
        list_box_row = Gtk.ListBoxRow()
        list_box_row.add(box)
        parent_list_box.add(list_box_row)

class NetworkList(Gtk.Window):

    def __init__(self, interface):

        Gtk.Window.__init__(self, title = "Available Networks")
        self.connect("destroy", Gtk.main_quit)

        self.set_size_request(360, 360)
        self.set_position(Gtk.WindowPosition.CENTER)    # place it in center
        self.set_decorated(False)   # No decorations

        # This box is used as the root layout
        vertical_box = Gtk.Box()
        self.add(vertical_box)  # add the box to the window
        vertical_box.set_orientation(Gtk.Orientation.VERTICAL)

        # This box contains the wifi power state related stuff
        wifi_state_section_box = Gtk.Box()
        vertical_box.pack_start(wifi_state_section_box, False, False, DEFAULT_PADDING)    # add the box to the vertical_box

        # Add a relevant Label
        wifi_label = Gtk.Label()
        wifi_state_section_box.pack_start(wifi_label, False, False, DEFAULT_PADDING)    # add it to wifi_state_section_box
        wifi_label.set_text("WiFi")

        # Add a toggle switch
        wifi_state_switch = Gtk.Switch()
        wifi_state_section_box.pack_end(wifi_state_switch, False, False, DEFAULT_PADDING) # add to wifi_state_section_box
        wifi_state_switch.connect("notify::active", self.toggle_wifi_switch)

        # Set switch's initial state
        self.refresh_state(wifi_state_switch)

        # toggle switch automatically every two seconds (in case if wifi state is toggled externally)
        GLib.timeout_add(2000, self.refresh_state, wifi_state_switch)

        # Add a refresh button(to refresh available networks' list)
        refresh_button = Gtk.Button()
        wifi_state_section_box.pack_end(refresh_button, False, False, DEFAULT_PADDING)  # add it to wifi_state_section_box
        refresh_button.set_label(REFRESH_BUTTON_LABEL)

        network_list_section = Gtk.ScrolledWindow()
        vertical_box.pack_start(network_list_section, True, True, NO_PADDING)    # add it to the vertical_box

        # To list the networks
        network_list = Gtk.ListBox()
        network_list_section.add(network_list)  # add it to the ScrolledWindow

        # Scan on startup
        self.refresh_network_list(network_list)

        # List the available networks
        # GLib.timeout_add(100, self.refresh_network_list, network_list)
        # GLib.timeout_add(5000, self.refresh_window)

    # Toggle wifi on/off
    def toggle_wifi_switch(self, switch, gparam):
        if switch.get_active():
            run(WLAN_TURN_ON_CMD, shell=True)
        else:
            run(WLAN_TURN_OFF_CMD, shell=True)
    
    def refresh_state(self, wifi_state_switch):

        # Set the switch according to current wlan state
        if check_wlan_state():
            wifi_state_switch.set_active(True)
        else:
            wifi_state_switch.set_active(False)

        return True
    
    def refresh_network_list(self, network_list):
        if not check_wlan_state():
            return True
        else:
            # Check if wpa_supplicant is running
            if not wpa_suppl_is_running(interface):
                start_wpa_supplicant(interface)
                scan_for_networks(interface)    # Since wpa_supplicant wasn't already running

            # scan_for_networks(interface)

            # Get all the available networks
            sleep(5)
            networks = get_available_networks(interface)
            
            # Arrange networks to add in the window
            for network in networks:
                # Check the protection
                if network.find('(WPA2)') != -1:
                    protection = 'WPA2'
                elif network.find('(WPA2)') != -1:
                    protection = 'WPA'
                else:
                    protection = 'none'
                # Now add the entry
                WifiNetwork(network_list, network.split('|')[1], protection)
                print(network)

            return True
    
    # Refresh the Gtk window
    # def refresh_window(self):
    #     self.queue_draw()
    #     self.show_all()

# Print to stderr
def print_error(error_str):
    print(error_str, file=stderr)

# Get wifi interface
def get_wifi_interface():
    directories = [f for f in listdir(NET_DEVICES_DIR) if isdir(join(NET_DEVICES_DIR, f))]
    for directory in directories:
        if check_output(DEV_TYPE_CMD.replace("DEV_NAME", directory, 1), shell=True).decode().strip() == "wlan":
            return directory
    
    print_error("Can't find the wifi interface!")

# Check wifi state
def check_wlan_state():

    # Get rfkill device name
    rfkill_dev_name = check_output(RFKILL_DEV_NAME_CMD, shell=True).decode().strip()

    # Check if wifi is on or off
    if check_output(WLAN_STATE_CMD.replace("RFKILL_DEV_NAME", rfkill_dev_name, 1), shell=True).decode().strip() == "1":
        return True
    return False

# Kill wpa_supplicant if it's already running and (re)start it
def start_wpa_supplicant(interface):
    run(WPA_SUPPL_TERM_CMD, shell=True)
    sleep(0.3)  # to make sure wpa_supplicant is no longer running
    run(WPA_SUPPL_CMD.replace("DEV_NAME", interface, 1), shell=True)

def scan_for_networks(interface):
    run(SCAN_CMD.replace("DEV_NAME", interface, 1), shell=True)
    # # Check if wpa_supplicant is running
    # if not wpa_suppl_is_running(interface):
    #     start_wpa_supplicant(interface)
    #     # scan_for_networks(interface)    # Since wpa_supplicant wasn't already running
    #     run(SCAN_CMD.replace("DEV_NAME", interface, 1), shell=True)

# Check if wpa_supplicant is running
def wpa_suppl_is_running(interface):
    try:
        check_output(SCAN_CMD.replace("DEV_NAME", interface, 1), shell=True)
        return True
    except CalledProcessError:
        return False

# Scan for available wifi networks
def get_available_networks(interface):
    # Scan for networks
    return check_output(SCAN_RESULTS_CMD.replace("DEV_NAME", interface, 1), shell=True).decode().strip().split()


############# MAIN ##############

interface = get_wifi_interface()

# print(get_available_networks(interface))
# if wpa_suppl_is_running(interface):
#     sleep(5)
#     print(get_available_networks(interface))
# else:
#     print('its not running')

# Draw and show the network selection window
network_list_window = NetworkList(interface)
network_list_window.show_all()
Gtk.main()
