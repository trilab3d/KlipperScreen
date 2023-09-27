import logging
import os

import gi
import netifaces

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
from ks_includes.screen_panel import ScreenPanel


def create_panel(*args, **kvargs):
    return NetworkManagerInterfacePanel(*args, **kvargs)

class NetworkManagerInterfacePanel(ScreenPanel):
    def __init__(self, screen, title, **kvargs):
        super().__init__(screen, title)
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.content.add(self.box)
        self.notebook = Gtk.Notebook()
        self.notebook.set_scrollable(True)
        self.box.add(self.notebook)

        self.interface = kvargs['interface']

        self.page_connections = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.page_connections.set_vexpand(True)
        self.page_connections.add(Gtk.Label(f"Connections"))
        self.notebook.append_page(self.page_connections, Gtk.Label("Connections"))

        self.page_general = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.page_general.set_vexpand(True)
        self.page_general.add(Gtk.Label(f"Interface: {self.interface['GENERAL']['DEVICE']}"))
        self.notebook.append_page(self.page_general, Gtk.Label("General"))

        self.page_ipv4 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.page_ipv4.set_vexpand(True)
        self.page_ipv4.add(Gtk.Label("IPv4"))
        self.notebook.append_page(self.page_ipv4, Gtk.Label("IPv4"))

        self.page_ipv6 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.page_ipv6.set_vexpand(True)
        self.page_ipv6.add(Gtk.Label("IPv6"))
        self.notebook.append_page(self.page_ipv6, Gtk.Label("IPv6"))

        btn_save = self._gtk.Button("settings", "Save", "color1")
        btn_save.set_hexpand(False)
        btn_save.set_vexpand(False)
        #btn_save.connect("clicked", self.show_interface_settings, interface)
        btn_discard = self._gtk.Button("settings", "Discard", "color1")
        btn_discard.set_hexpand(False)
        btn_discard.set_vexpand(False)
        # btn_save.connect("clicked", self.show_interface_settings, interface)

        self.button_panel = self._gtk.HomogeneousGrid()
        #self.button_panel
        self.box.add(self.button_panel)
        self.button_panel.attach(btn_discard, 0, 0, 1, 1)
        self.button_panel.attach(btn_save, 1, 0, 1, 1)

    def refetch_interface(self):
        rsp = self._screen.tpcclient.send_request("network-manager/list-interfaces")
        interfaces = rsp["interfaces"]

        for i, interface in enumerate(interfaces):
            if interface['GENERAL']['DEVICE'] == self.interface['GENERAL']['DEVICE']:
                self.interface = interface