# GiGS_Wifi
Graphical frontend to wpa_supplicant

# In Action

![Alt text](in_action.png?raw=true "running under Artix Linux and dwm")

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
2. `wpa_cli`
3. `killall`
4. `rfkill`

# USAGE
 `python main.py`

# NOTES
It's still a work in progress, things you can't do:
* Can't connect to a network.
* Refresh button still needs binding to a function.
* Needs asynchronous implementation to make GUI and backend independent.

# LICENSE
Licensed under MIT License

*Copyright (c) 2020 Gaurav Kumar Yadav*

Have a look at the `LICENSE` for details
