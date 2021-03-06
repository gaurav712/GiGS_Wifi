# GiGS_Wifi
Graphical frontend to wpa_supplicant

# In Action

![Alt text](in_action.png?raw=true "running under Artix Linux and dwm")
`

# Getting it running in your system
* must have python-3.x installed
* must have gobject-introspection-1.0

    name of the package depends on your distribution, e.g.

    Fedora, CentOS, RHEL: gobject-introspection-devel

    Debian, Ubuntu, Mint, Elementary: libgirepository1.0-dev

    ArchLinux: gobject-introspection

* must have PyGObject

    to install: `pip3 install PyGObject`

* must have `wpa_supplicant` installed

* these binaries must be whitelisted in sudoers file (so it doesn't prompt for password):
1. `wpa_supplicant`
4. `rfkill`

# TODO
* Switch to something other than GTK
* Help users add binaries to the sudoers
* Make it able to modify networks in the config
* Better error handling
* Make the UI fluid
* Add to PyPI

# LICENSE
Licensed under MIT License

*Copyright (c) 2020 Gaurav Kumar Yadav*

Have a look at the `LICENSE` for details
