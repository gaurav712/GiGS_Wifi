import gi
gi.require_version("Gtk", '3.0')
from gi.repository import Gtk
from subprocess import run

CANCEL_ADDING_NETWORK_CMD = "wpa_cli -i DEV_NAME remove_network NETWORK_NUM"

PADDING = 20

class PasswordEntry(Gtk.Window):

    def __init__(self, interface, ssid, add_psk, disconnect, get_connected, network_num, save_config):
        Gtk.Window.__init__(self, title = 'Enter password for ' + ssid)
        self.connect('destroy', self.close_window)

        self.set_position(Gtk.WindowPosition.CENTER)    # place it in center

        # Initialize necessary values
        self.interface = interface
        self.disconnect = disconnect
        self.add_psk = add_psk
        self.get_connected = get_connected
        self.network_num = network_num
        self.save_config = save_config

        # Box for entry and buttons
        self.parent_box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)

        # Password entry field
        self.entry_box = Gtk.Entry()
        self.entry_box.set_visibility(False)    # to make the text invisible
        self.entry_box.connect('activate', self.submit_password)    # submit when Return key is pressed
        self.parent_box.pack_start(self.entry_box, False, False, PADDING)

        # Box to pack buttons
        self.button_box = Gtk.Box()

        # Buttons for OK and Cancel
        self.submit_button = Gtk.Button(label = 'OK')
        self.submit_button.connect('clicked', self.submit_password)

        self.cancel_button = Gtk.Button(label = 'Cancel')
        self.cancel_button.connect('clicked', self.cancel_entry)

        # Add them to the button_box
        self.button_box.pack_start(self.submit_button, False, False, PADDING)
        self.button_box.pack_end(self.cancel_button, False, False, PADDING)

        # Add button_box to the parent_box
        self.parent_box.pack_start(self.button_box, False, False, PADDING)

        # Add it to the window
        self.add(self.parent_box)

    def submit_password(self, submit):
        self.password = self.entry_box.get_text()
        if self.password is None:
            print('No password entered')
        else:
            if self.disconnect is not None:
                self.disconnect()
            self.add_psk(self.password, self.network_num)
            self.get_connected(self.network_num)
            self.save_config()
            self.close_window()

    def cancel_entry(self, cancel_button):
        print('Cancelled password entry!')
        self.close_window()

    def close_window(self, signal = None):
        # Remove the dummy network that was added
        run(CANCEL_ADDING_NETWORK_CMD.replace("DEV_NAME", self.interface, 1).replace("NETWORK_NUM", self.network_num, 1), shell = True)
        self.destroy()  # now exit