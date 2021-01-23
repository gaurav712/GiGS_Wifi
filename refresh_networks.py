from threading import Thread
from time import sleep
from os import getenv
from subprocess import check_output, run, CalledProcessError
import gi
gi.require_version("Gtk", '3.0')
from gi.repository import Gtk

from password_entry_popup import PasswordEntry

# Globals
# WPA_SUPPL_TERM_CMD = "sudo killall wpa_supplicant"
DEFAULT_CONF_FILE = "/.local/gigswifi-wpa_supplicant.conf"  # with $HOME prefixed to it
SCAN_CMD = "wpa_cli -i DEV_NAME scan 2> /dev/null"
SCAN_RESULTS_CMD = "wpa_cli -i DEV_NAME scan_results | cut -f4- \
| sed -e 1d -e 's/\\[WPA2-.*\\]/(WPA2)/g' -e 's/\\[ESS\\]//g' -e 's/\t/|/g' -e 's/\\[WPA-.*\\]/(WPA)/g'"
WPA_SUPPL_CMD = "sudo wpa_supplicant -D nl80211 -i DEV_NAME -c " + getenv('HOME') + DEFAULT_CONF_FILE + " -B"
LIST_NETWORKS_CMD = "wpa_cli -i DEV_NAME list_networks | sed -e 1d | cut -f2"
CONNECT_CMD = "wpa_cli -i DEV_NAME enable_network "
DISABLE_CMD = "wpa_cli -i DEV_NAME disable_network "
GET_CURRENT_NETWORK_CMD = "wpa_cli -i DEV_NAME list_networks | grep CURRENT | cut -f2"

ADD_NETWORK_CMD = "wpa_cli -i DEV_NAME add_network"
SET_SSID_CMD = "wpa_cli -i DEV_NAME set_network NETWORK_NUM ssid \'\"SSID\"\'"
SET_PSK_CMD = "wpa_cli -i DEV_NAME set_network NETWORK_NUM psk \'\"PSK\"\'"
SET_NO_KEY_CMD = "wpa_cli -i DEV_NAME set_network NETWORK_NUM key_mgmt NONE"
SAVE_CONFIG_CMD = "wpa_cli -i DEV_NAME save_config"

LIST_DISABLED_NETWORKS_CMD = "wpa_cli -i DEV_NAME list_networks | grep DISABLED | cut -f1"

NETWORK_LIST_PADDING = 10
SEARCH_DURATION = 5 # in seconds

networks = {}   # to store saved networks
connected_network = None  # stores ssid key of currently active network, None if none

class Network():

    def __init__(self, parent_list_box, ssid, protection, interface):

        self.ssid = ssid
        self.protection = protection
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
            self.protection_label.set_text(self.protection)

            # Add it to the box
            self.box.pack_end(self.protection_label, False, False, NETWORK_LIST_PADDING)

        # add the box to the root widget
        self.list_box_row = Gtk.ListBoxRow()
        self.list_box_row.connect('activate', self.connect_to_the_network)
        self.list_box_row.add(self.box)
        parent_list_box.add(self.list_box_row)

    def connect_to_the_network(self, list_box_row):
        # Connect to self.ssid

        # Disable other networks
        for network in networks:
            if self.ssid is not networks[network]:
                self.disable(network)

        # Get self.ssid's index in networks
        for network in networks:
            if networks[network] == self.ssid:
                network_num = network
                break

        # Check if it's already saved
        if self.ssid in networks.values():
            # Current network is saved
            self.get_connected(network_num)
        else:
            # Current network is not saved
            self.add_network(network)

    def add_network(self, network):

        # issue the add_network command
        network_number = str(check_output(ADD_NETWORK_CMD.replace("DEV_NAME", self.interface, 1), shell = True).decode().strip())

        # set the ssid
        run(SET_SSID_CMD.replace("DEV_NAME", self.interface, 1).replace("NETWORK_NUM", network_number, 1).replace("SSID", self.ssid, 1), shell = True)

        # set the password
        # Check if network has any protection
        if self.protection == 'none':   # no protection
            run(SET_NO_KEY_CMD.replace("DEV_NAME", self.interface, 1).replace("NETWORK_NUM", network_number, 1), shell = True)
            self.get_connected(network_number)
            self.save_config()  # Save it to the config
        else:   # it is protected

            # Get the password

            # If the network is not saved
            if network not in networks.values():
                passwordWindow = PasswordEntry(self.interface, self.ssid, self.add_psk, self.get_connected, network_number, self.save_config, self.update_connnected_network)
                passwordWindow.show_all()

    def add_psk(self, password, network_num):
        run(SET_PSK_CMD.replace("DEV_NAME", self.interface, 1).replace("NETWORK_NUM", network_num, 1).replace("PSK", password, 1), shell = True)

    def disable(self, network):
        run(DISABLE_CMD.replace("DEV_NAME", self.interface, 1) + network, shell = True)

    def get_connected(self, network_num):
        run(CONNECT_CMD.replace("DEV_NAME", self.interface, 1) + network_num, shell = True)

    def save_config(self):

        #TODO
        # enable all the networks before saving to config
        # so that none of them is blacklisted(kind of)

        disabled_networks = check_output(LIST_DISABLED_NETWORKS_CMD.replace("DEV_NAME", self.interface, 1), shell = True).decode().splitlines()

        # now enable all the networks
        for disabled_network in disabled_networks:
            run(CONNECT_CMD.replace("DEV_NAME", self.interface, 1) + disabled_network, shell = True)

        # save to config
        run(SAVE_CONFIG_CMD.replace("DEV_NAME", self.interface, 1), shell = True)

        # now disable the networks that were previously disabled
        for disabled_network in disabled_networks:
            run(DISABLE_CMD.replace("DEV_NAME", self.interface, 1) + disabled_network, shell = True)

    def update_connnected_network(self):
        # Update connected_network
        get_current_network(self.interface)

        # Update networks as well
        get_saved_networks(self.interface)

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
