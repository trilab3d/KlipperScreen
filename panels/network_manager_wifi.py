import logging
import os

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
from ks_includes.screen_panel import ScreenPanel


def create_panel(*args, **kvargs):
    return NetworkManagerWifiPanel(*args, **kvargs)

class NetworkManagerWifiPanel(ScreenPanel):
    def __init__(self, screen, title, **kvargs):
        super().__init__(screen, title)
        self.interface = kvargs['interface']
        self.do_schedule_refresh = False
        scroll = self._gtk.ScrolledWindow()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.set_vexpand(True)
        self.labels['networklist'] = Gtk.Grid()
        box.pack_start(self.labels['networklist'], False, False, 0)
        scroll.add(box)
        self.content.add(scroll)
        self.load_networks()

    def load_networks(self):
        rsp = self._screen.tpcclient.send_request("/network-manager/list-networks", timeout=20)
        print(rsp)
        networks = rsp["connections"]

        for ch in self.labels['networklist'].get_children():
            self.labels['networklist'].remove(ch)

        for i, net in enumerate(networks):
            network = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            network.get_style_context().add_class("frame-item")
            network.set_hexpand(True)
            network.set_vexpand(False)

            if net["SECURITY"] == "--":
                btn = self._gtk.Button("arrow-right", None, "color1", 0.5)
                btn.set_hexpand(False)
                btn.set_halign(Gtk.Align.END)
                btn.connect("clicked", self.connect_network, net)
            else:
                btn = self._gtk.Button("admin", None, "color1", 0.5)
                btn.set_hexpand(False)
                btn.set_halign(Gtk.Align.END)
                btn.connect("clicked", self.connect_network_password, net)

            if net['BARS'] == "****":
                image = self._gtk.Image("wifi-signal-4", self._gtk.content_width * .1, self._gtk.content_height * .1)
            elif net['BARS'] == "***":
                image = self._gtk.Image("wifi-signal-3", self._gtk.content_width * .1, self._gtk.content_height * .1)
            elif net['BARS'] == "**":
                image = self._gtk.Image("wifi-signal-2", self._gtk.content_width * .1, self._gtk.content_height * .1)
            else:
                image = self._gtk.Image("wifi-signal-1", self._gtk.content_width * .1, self._gtk.content_height * .1)
            network.add(image)

            labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            labels.set_hexpand(True)
            labels.set_valign(Gtk.Align.CENTER)
            labels.set_halign(Gtk.Align.START)

            name = Gtk.Label()
            name.set_markup(f"<big><b>{net['SSID'] if net['SSID'] != '--' else net['BSSID']}</b></big>")
            name.set_halign(Gtk.Align.START)
            labels.add(name)

            network.add(labels)

            network.add(btn)

            self.labels['networklist'].attach(network, 0, i, 1, 1)
        self.content.show_all()

        if self.do_schedule_refresh:
            GLib.timeout_add_seconds(3, self.load_networks)

    def connect_network_password(self, widget, network):
        if network['SSID'] != "--":
            name = network["SSID"]
        else:
            name = network["BSSID"]
        self._screen.show_panel(name, "network_manager_wifi_connect", name, 1, False, network=network,
                                interface=self.interface)

    def connect_network(self, widget, network):
        b = {
                "ifname": self.interface['GENERAL']['DEVICE']
            }
        if network['SSID'] != "--":
            b["ssid"] = network["SSID"]
        b["bssid"] = network["BSSID"]

        self._screen.tpcclient.send_request("/network-manager/connect-wifi", "POST", body=b)
