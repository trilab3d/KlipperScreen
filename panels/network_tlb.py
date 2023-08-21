import logging
import os

import gi
import netifaces

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
from ks_includes.screen_panel import ScreenPanel


def create_panel(*args):
    return NetworkTlbPanel(*args)

class NetworkTlbPanel(ScreenPanel):
    initialized = False

    def __init__(self, screen, title):
        super().__init__(screen, title)

        self.labels['networks'] = {}

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.set_vexpand(True)

        self.labels['networklist'] = Gtk.Grid()
        self.load_interfaces()
        box.pack_start(self.labels['networklist'], False, False, 0)

        entry = Gtk.Entry()
        entry.set_hexpand(True)
        entry.set_vexpand(False)
        entry.connect("button-press-event", self._screen.show_keyboard)
        entry.connect("focus-in-event", self._screen.show_keyboard)
        entry.grab_focus_without_selecting()
        entry.set_visibility(False)

        box.pack_start(entry, False, False, 0)

        self.content.add(box)
        self.labels['main_box'] = box
        self.initialized = True

    def load_interfaces(self):
        rsp = self._screen.tpcclient.send_request("network")
        interfaces = rsp["interfaces"]

        for i, interface in enumerate(interfaces):
            network = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            network.get_style_context().add_class("frame-item")
            network.set_hexpand(True)
            network.set_vexpand(False)

            btn = self._gtk.Button("settings", None, "color1")

            if interface['type'] == "WiFi":
                image = self._gtk.Image("wifi", self._gtk.content_width * .1, self._gtk.content_height * .1)
                btn.connect("clicked", self.show_wifi_settings)
            else:
                image = self._gtk.Image("wired", self._gtk.content_width * .1, self._gtk.content_height * .1)
                btn.connect("clicked", self.show_ethernet_settings)
            network.add(image)

            labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            labels.set_vexpand(True)
            labels.set_valign(Gtk.Align.CENTER)
            labels.set_halign(Gtk.Align.START)

            name = Gtk.Label()
            name.set_markup(f"<big><b>{interface['type']}</b></big>")
            name.set_halign(Gtk.Align.START)
            labels.add(name)

            ifc = Gtk.Label()
            ifc.set_markup(f"<big><b>Interface:</b> {interface['interface']}</big>")
            ifc.set_halign(Gtk.Align.START)
            labels.add(ifc)

            if interface['type'] == "WiFi":
                ssid = Gtk.Label()
                ssid.set_markup(f"<big><b>SSID:</b> {interface['wifi']['ssid']}</big>")
                ssid.set_halign(Gtk.Align.START)
                labels.add(ssid)

            ip = Gtk.Label()
            ip.set_markup(f"<big><b>IP:</b> {interface['ip']}</big>")
            ip.set_halign(Gtk.Align.START)
            labels.add(ip)

            mac = Gtk.Label()
            mac.set_markup(f"<big><b>MAC:</b> {interface['mac']}</big>")
            mac.set_halign(Gtk.Align.START)
            labels.add(mac)

            network.add(labels)

            network.add(btn)

            n = self.labels['networklist'].get_child_at(0, i)
            if n:
                self.labels['networklist'].remove(n)
            self.labels['networklist'].attach(network, 0, i, 1, 1)

    def show_wifi_settings(self, widget):
        self._screen.show_panel("wifi", "wifi", "Wifi Settings", 1, False)

    def show_ethernet_settings(self, widget):
        self._screen.show_panel("ethernet", "ethernet", "Ethernet Settings", 1, False)

    def activate(self):
        if self.initialized:
            self.load_interfaces()

    def deactivate(self):
        pass
