from threading import Thread
from time import sleep
from os import getenv
from subprocess import check_output, run, CalledProcessError
import gi
gi.require_version("Gtk", '3.0')
from gi.repository import Gtk

# Globals
# WPA_SUPPL_TERM_CMD = "sudo killall wpa_supplicant"
DEFAULT_CONF_FILE = "/.local/gigswifi-wpa_supplicant.conf"  # with $HOME prefixed to it
SCAN_CMD = "wpa_cli -i DEV_NAME scan 2> /dev/null"
SCAN_RESULTS_CMD = "wpa_cli -i DEV_NAME scan_results | cut -f4- \
| sed -e 1d -e 's/\\[WPA2-.*\\]/(WPA2)/g' -e 's/\\[ESS\\]//g' -e 's/\t/|/g' -e 's/\\[WPA-.*\\]/(WPA)/g'"
WPA_SUPPL_CMD = "sudo wpa_supplicant -D nl80211 -i DEV_NAME -c " + getenv('HOME') + DEFAULT_CONF_FILE + " -B"
LIST_NETWORKS_CMD = "wpa_cli -i DEV_NAME list_networks | sed -e 1d | cut -f2"
CONNECT_CMD = "wpa_cli -i DEV_NAME enable_network "
DISCONNECT_CMD = "wpa_cli -i DEV_NAME disable_network "
GET_CURRENT_NETWORK_CMD = "wpa_cli -i DEV_NAME list_networks | grep CURRENT | cut -f1"

NETWORK_LIST_PADDING = 10
SEARCH_DURATION = 5 # in seconds

networks = {}   # to store saved networks
connected_network = None  # stores ssid key of currently active network, None if none

class Network():

    def __init__(self, parent_list_box, ssid, protection, interface):

        self.ssid = ssid
        self.interface = interface

        # Add a box
        self.box = Gtk.Box()

        # To show the SSID of the network
        self.ssid_label = Gtk.Label()
        self.ssid_label.set_text(self.ssid)
        self.ssid_label.set_line_wrap(True)
        self.ssid_label.set_xalign(-1)

        # Add it to the box
        self.box.pack_start(self.ssid_label, True, True, NETWORK_LIST_PADDING)

        if protection is not None:
            self.protection_label = Gtk.Label()
            self.protection_label.set_text(protection)

            # Add it to the box
            self.box.pack_end(self.protection_label, False, False, NETWORK_LIST_PADDING)

        # add the box to the root widget
        self.list_box_row = Gtk.ListBoxRow()
        self.list_box_row.connect('activate', self.connect_to_the_network)
        self.list_box_row.add(self.box)
        parent_list_box.add(self.list_box_row)

    def connect_to_the_network(self, list_box_row):
        # Check if it's already saved
        for network in networks:
            if self.ssid == networks[network]:
                # Connect to self.ssid

                # Check if device is already connected to a network
                # and it is not the one user just selected. If it's not,
                # disconnect from the already connected network
                if connected_network is not None and connected_network is not network:
                    run(DISCONNECT_CMD.replace("DEV_NAME", self.interface, 1) + connected_network, shell = True)

                # now connect
                run(CONNECT_CMD.replace("DEV_NAME", self.interface, 1) + network, shell = True)
                return  # return, now that it is connected!

        # Current network is not saved

# Thread to refresh networks list
class RefreshNetworkThread(Thread):
    def __init__(self, interface, list_box, refresh_button):
        Thread.__init__(self)

        self.interface = interface
        self.list_box = list_box
        self.refresh_button = refresh_button

        self.refresh_button.set_visible(False)  # hide it when searching for networks

        # to populate networks[] with all the already saved networks
        get_saved_networks(self.interface)

        # to save currently active network into connected_network
        get_current_network(self.interface)

    def run(self):
        # Check if wpa_supplicant is running
        if not wpa_suppl_is_running(self.interface):
            start_wpa_supplicant(self.interface)    # started wpa_supplicant
            scan_for_networks(self.interface)   # issued the scan command via wpa_cli

        # Find networks and update the list
        sleep(SEARCH_DURATION)  # to wait for networks to appear
        self.networks = get_available_networks(self.interface)
        self.add_networks_to_listbox()

    def add_networks_to_listbox(self):
        for self.network in self.networks:
            # Check the protection
            if self.network.find('(WPA2)') != -1:
                self.protection = 'WPA2'
            elif self.network.find('(WPA)') != -1:
                self.protection = 'WPA'
            else:
                self.protection = 'none'
            # Now add the entry
            Network(self.list_box, self.network.split('|')[1], self.protection, self.interface)

            # Refresh the window
            self.list_box.show_all()

            # Now reveal the refresh button
            self.refresh_button.set_visible(True)

# Kill wpa_supplicant if it's already running and (re)start it
def start_wpa_supplicant(interface):
    # run(WPA_SUPPL_TERM_CMD, shell=True)
    # sleep(0.3)  # to make sure wpa_supplicant is no longer running
    run(WPA_SUPPL_CMD.replace("DEV_NAME", interface, 1), shell=True)

def scan_for_networks(interface):
    run(SCAN_CMD.replace("DEV_NAME", interface, 1), shell=True)

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
    return check_output(SCAN_RESULTS_CMD.replace("DEV_NAME", interface, 1), shell=True).decode().splitlines()

# List the networks saved in the config
def get_saved_networks(interface):
    global networks
    network_list = check_output(LIST_NETWORKS_CMD.replace("DEV_NAME", interface, 1), shell = True).decode().splitlines()

    index = 0
    for network in network_list:
        networks[str(index)] = network
        index += 1

def get_current_network(interface):
    global connected_network
    connected_network = check_output(GET_CURRENT_NETWORK_CMD.replace("DEV_NAME", interface, 1), shell = True).decode().strip()

    if connected_network == '':
        connected_network = None