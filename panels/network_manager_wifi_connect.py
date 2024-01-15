import logging
import os
import time

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
from ks_includes.screen_panel import ScreenPanel


def create_panel(*args, **kvargs):
    return NetworkManagerWifiConnectPanel(*args, **kvargs)

class NetworkManagerWifiConnectPanel(ScreenPanel):
    def __init__(self, screen, title, **kvargs):
        super().__init__(screen, title)
        self.network = kvargs['network']
        self.interface = kvargs['interface']
        self.password = ""
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content.add(self.box)
        self.build_panel()

    def build_panel(self):
        password_grid = self._gtk.HomogeneousGrid()
        password_grid.set_hexpand(True)
        password_label = Gtk.Label(label="Password:")
        password_label.set_halign(Gtk.Align.END)
        password_entry = Gtk.Entry()
        password_entry.connect("changed", self.change_password)
        password_entry.set_visibility(True)
        password_entry.connect("button-press-event", self._screen.show_keyboard)
        password_entry.set_hexpand(True)
        password_entry.set_vexpand(False)
        password_grid.attach(password_label, 0, 0, 2, 1)
        password_grid.attach(password_entry, 2, 0, 3, 1)
        self.box.add(password_grid)

        btn_connect = self._gtk.Button("arrow-right", "Connect", "color1")
        btn_connect.set_hexpand(True)
        btn_connect.set_vexpand(False)
        btn_connect.connect("clicked", self.connect_network)
        self.box.add(btn_connect)

    def change_password(self, widget):
        self.password = widget.get_text()

    def connect_network(self, widget):
        b = {
                "ifname": self.interface['GENERAL']['DEVICE'],
                "password": self.password
            }
        if self.network['SSID'] != "--":
            b["ssid"] = self.network["SSID"]
            name = self.network["SSID"]
        else:
            name = self.network["BSSID"]
            b["bssid"] = self.network["BSSID"]

        logging.info(self.password)

        res = self._screen.tpcclient.send_request("/network-manager/connect-wifi", "POST", body=b)
        while True:
            time.sleep(1)
            res = self._screen.tpcclient.send_request("/network-manager/connect-wifi-result")
            if ("stderr" in res and len(res["stderr"]) > 0) or ("stdout" in res and len(res["stdout"]) > 0):
                break
        logging.info(res)
        if len(res["stderr"]):
            self._screen.show_popup_message("Connection Failed", 3)
        else:
            self._screen.remove_keyboard()
            self._screen._menu_go_back()
            self._screen._menu_go_back()
            self._screen.show_popup_message(f"Connected to {name}", 1)