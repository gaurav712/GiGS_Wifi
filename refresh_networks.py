from threading import Thread
from time import sleep
from subprocess import check_output, run, CalledProcessError
import gi
gi.require_version("Gtk", '3.0')
from gi.repository import Gtk

# Globals
# WPA_SUPPL_TERM_CMD = "sudo killall wpa_supplicant"
SCAN_CMD = "wpa_cli -i DEV_NAME scan 2> /dev/null"
SCAN_RESULTS_CMD = "wpa_cli -i DEV_NAME scan_results | cut -f4- \
| sed -e 1d -e 's/\\[WPA2-.*\\]/(WPA2)/g' -e 's/\\[ESS\\]//g' -e 's/\t/|/g' -e 's/\\[WPA-.*\\]/(WPA)/g'"
WPA_SUPPL_CMD = "sudo wpa_supplicant -D nl80211 -i DEV_NAME -C \"DIR=/var/run/wpa_supplicant GROUP=wheel\" -B"

NETWORK_LIST_PADDING = 10
SEARCH_DURATION = 5 # in seconds

class Network():

    def __init__(self, parent_list_box, ssid, protection):

        # Add a box
        self.box = Gtk.Box()

        # To show the SSID of the network
        self.ssid_label = Gtk.Label()
        self.ssid_label.set_text(ssid)
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
        # Just a basic structure for now
        print(self.ssid_label.get_label())

# Thread to refresh networks list
class RefreshNetworkThread(Thread):
    def __init__(self, interface, list_box):
        Thread.__init__(self)

        self.interface = interface
        self.list_box = list_box

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
            Network(self.list_box, self.network.split('|')[1], self.protection)

            # Refresh the window
            self.list_box.show_all()

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
    return check_output(SCAN_RESULTS_CMD.replace("DEV_NAME", interface, 1), shell=True).decode().strip().splitlines()