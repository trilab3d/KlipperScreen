import logging
import os

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
from ks_includes.screen_panel import ScreenPanel


HIDDEN_TYPES = ["loopback", "wifi-p2p"]

def create_panel(*args):
    return NetworkManagerPanel(*args)

class NetworkManagerPanel(ScreenPanel):
    def __init__(self, screen, title):
        super().__init__(screen, title)
        self.do_schedule_refresh = True
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.set_vexpand(True)
        self.labels['top-bar'] = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.labels['top-bar'].set_vexpand(False)
        self.labels['top-bar'].set_hexpand(True)
        self.labels['networklist'] = Gtk.Grid()
        # change_hostname_button = self._gtk.Button("settings", "Printer Name", "color1", 0.5)
        # change_hostname_button.set_hexpand(False)
        # change_hostname_button.set_halign(Gtk.Align.END)
        # change_hostname_button.connect("clicked", self.show_change_hostname)
        # self.labels['top-bar'].add(change_hostname_button)
        box.pack_start(self.labels['top-bar'], False, False, 0)
        box.pack_start(self.labels['networklist'], False, False, 0)
        self.content.add(box)
        self.load_interfaces()

    def load_interfaces(self):
        rsp = self._screen.tpcclient.send_request("network-manager/list-interfaces")
        interfaces = rsp["interfaces"]

        #n = self.labels['networklist'].get_child_at(0, i)
        #if n:
        #    self.labels['networklist'].remove(n)

        for ch in self.labels['networklist'].get_children():
            self.labels['networklist'].remove(ch)

        for i, interface in enumerate(interfaces):

            if 'GENERAL' not in interface:
                continue
            if interface['GENERAL']['TYPE'] in HIDDEN_TYPES:
                continue

            network = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            network.get_style_context().add_class("frame-item")
            network.set_hexpand(True)
            network.set_vexpand(False)

            btn = self._gtk.Button("settings", None, "color1")
            btn.set_hexpand(False)
            btn.set_halign(Gtk.Align.END)
            btn.connect("clicked", self.show_interface_settings, interface)

            if interface['GENERAL']['TYPE'] == "wifi":
                image = self._gtk.Image("wifi", self._gtk.content_width * .1, self._gtk.content_height * .1)
            else:
                image = self._gtk.Image("wired", self._gtk.content_width * .1, self._gtk.content_height * .1)
            network.add(image)

            labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            labels.set_hexpand(True)
            labels.set_valign(Gtk.Align.CENTER)
            labels.set_halign(Gtk.Align.START)

            name = Gtk.Label()
            name.set_markup(f"<big><b>{interface['GENERAL']['TYPE']}</b></big>")
            name.set_halign(Gtk.Align.START)
            labels.add(name)

            ifc = Gtk.Label()
            ifc.set_markup(f"<big><b>Interface:</b> {interface['GENERAL']['DEVICE']}</big>")
            ifc.set_halign(Gtk.Align.START)
            labels.add(ifc)

            if interface['GENERAL']['TYPE'] == "wifi":
                ssid = Gtk.Label()
                ssid.set_markup(f"<big><b>SSID:</b> {interface['GENERAL']['CONNECTION']}</big>")
                ssid.set_halign(Gtk.Align.START)
                labels.add(ssid)

            for addr in interface['IP4']['ADDRESS'] if 'IP4' in interface and "ADDRESS" in interface['IP4'] else []:
                ip = Gtk.Label()
                ip.set_markup(f"<big><b>IPv4:</b> {addr}</big>")
                ip.set_halign(Gtk.Align.START)
                labels.add(ip)
            for addr in interface['IP6']['ADDRESS'] if 'IP6' in interface and "ADDRESS" in interface['IP6'] else []:
                ip = Gtk.Label()
                ip.set_line_wrap(True)
                ip.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
                ip.set_xalign(0.0)
                ip.set_justify(Gtk.Justification.LEFT)
                ip.set_markup(f"<big><b>IPv6:</b> {addr}</big>")
                ip.set_halign(Gtk.Align.START)
                labels.add(ip)

            mac = Gtk.Label()
            mac.set_markup(f"<big><b>MAC:</b> {interface['GENERAL']['HWADDR']}</big>")
            mac.set_halign(Gtk.Align.START)
            labels.add(mac)

            network.add(labels)

            network.add(btn)

            self.labels['networklist'].attach(network, 0, i, 1, 1)
        self.content.show_all()

        if self.do_schedule_refresh:
            GLib.timeout_add_seconds(3, self.load_interfaces)

    def show_interface_settings(self, widget, interface):
        name = interface['GENERAL']['DEVICE']
        self._screen.show_panel(f"network_manager_interface_{name}", "network_manager_interface", name, 1, False, interface=interface)

    def show_change_hostname(self, widget):
        self._screen.show_panel(f"hostname", "hostname", "Hostname", 1, False)

    def activate(self):
        self.do_schedule_refresh = True
        self.load_interfaces()

    def deactivate(self):
       self.do_schedule_refresh = False
