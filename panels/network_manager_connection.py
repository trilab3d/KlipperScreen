import logging
import os

import gi
import netifaces

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
from ks_includes.screen_panel import ScreenPanel


def create_panel(*args, **kvargs):
    return NetworkManagerConnectionPanel(*args, **kvargs)

class NetworkManagerConnectionPanel(ScreenPanel):
    def __init__(self, screen, title, **kvargs):
        super().__init__(screen, title)

        self.connection = kvargs['connection']

        self.box = Gtk.Box()
        self.content.add(self.box)


    def refetch_connection(self):
        rsp = self._screen.tpcclient.send_request("network-manager/list-interfaces")
        interfaces = rsp["interfaces"]

        for i, interface in enumerate(interfaces):
            if interface['GENERAL']['DEVICE'] == self.interface['GENERAL']['DEVICE']:
                self.interface = interface