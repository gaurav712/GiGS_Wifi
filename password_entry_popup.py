import gi
gi.require_version("Gtk", '3.0')
from gi.repository import Gtk

PADDING = 20

class PasswordEntry(Gtk.Window):

    password = None

    def __init__(self, ssid):
        Gtk.Window.__init__(self, title = 'Enter password for ' + ssid)
        self.connect('destroy', self.close_window)

        self.set_position(Gtk.WindowPosition.CENTER)    # place it in center

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
        self.close_window()

    def cancel_entry(self, cancel_button):
        print('Cancelled password entry!')
        self.close_window()

    def close_window(self, signal = None):
        self.destroy()