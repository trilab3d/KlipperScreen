import logging
import os

import gi
import json

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
from ks_includes.screen_panel import ScreenPanel


def create_panel(*args, **kvargs):
    return NetworkManagerInterfacePanel(*args, **kvargs)

class NetworkManagerInterfacePanel(ScreenPanel):
    def __init__(self, screen, title, **kvargs):
        super().__init__(screen, title)
        self.interface = kvargs['interface']
        self.wireless = self.interface['GENERAL']['TYPE'] == "wifi"
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.content.add(self.box)
        self.labels['connection-list'] = Gtk.Grid()
        self.labels['top-bar'] = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.labels['top-bar'].set_vexpand(False)
        self.labels['top-bar'].set_hexpand(True)
        if self.wireless:
            wifi_connect_button = self._gtk.Button("wifi", "Connect Wifi", "blocking", 0.5)
            wifi_connect_button.set_hexpand(False)
            wifi_connect_button.set_halign(Gtk.Align.END)
            wifi_connect_button.connect("clicked", self.wifi_connect)
            self.labels['top-bar'].add(wifi_connect_button)
        conn_add_button = self._gtk.Button("increase", "Add Profile", "blocking", 0.5)
        conn_add_button.set_hexpand(False)
        conn_add_button.set_halign(Gtk.Align.END)
        conn_add_button.connect("clicked", self.add_connection)
        self.labels['top-bar'].add(conn_add_button)
        self.box.pack_start(self.labels['top-bar'], False, False, 0)
        self.box.pack_start(self.labels['connection-list'], False, False, 0)
        print(json.dumps(self.interface, indent=2))
        self.load_connections()

    def load_connections(self):
        rsp = self._screen.tpcclient.send_request("network-manager/list-connections")
        connections = rsp["connections"]

        interface_connections = []

        for conn in connections:
            id = conn["UUID"]
            found = False
            if "AVAILABLE-CONNECTIONS" in self.interface["CONNECTIONS"]:
                for ifc_conn in self.interface["CONNECTIONS"]["AVAILABLE-CONNECTIONS"]:
                    conn_id = ifc_conn.split("|")[0].strip()
                    if conn_id == id:
                        found = True
                        break
            if not found:
                conn_full = self._screen.tpcclient.send_request(f"network-manager/show-connection/{id}")
                if conn_full["connection"]["interface-name"] != self.interface["GENERAL"]["DEVICE"]:
                    continue
            interface_connections.append({
                "id": id,
                "name": conn["NAME"],
                "active": conn["ACTIVE"] == "yes"
            })

        for ch in self.labels['connection-list'].get_children():
            self.labels['connection-list'].remove(ch)

        for i, connection in enumerate(interface_connections):

            conn = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
            conn.get_style_context().add_class("frame-item")
            conn.set_hexpand(True)
            conn.set_vexpand(False)

            labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            labels.set_hexpand(True)
            labels.set_valign(Gtk.Align.CENTER)
            labels.set_halign(Gtk.Align.START)

            name = Gtk.Label()
            name.set_markup(f"<big><b>{connection['name']}{' (Active)' if connection['active'] else ''}</b></big>")
            name.set_halign(Gtk.Align.START)
            labels.add(name)

            conn.add(labels)

            remove = self._gtk.Button("delete", None, "color1", 0.5)
            remove.set_hexpand(False)
            remove.set_halign(Gtk.Align.END)
            remove.connect("clicked", self.remove_connection, connection)

            edit = self._gtk.Button("settings", None, "color1", 0.5)
            edit.set_hexpand(False)
            edit.set_halign(Gtk.Align.END)
            edit.connect("clicked", self.edit_connection, connection)

            conn.add(remove)
            conn.add(edit)

            if connection['active']:
                down = self._gtk.Button("cancel", None, "color1", 0.5)
                down.set_hexpand(False)
                down.set_halign(Gtk.Align.END)
                down.connect("clicked", self.down_connection, connection)
                conn.add(down)
            else:
                up = self._gtk.Button("arrow-right", None, "color1", 0.5)
                up.set_hexpand(False)
                up.set_halign(Gtk.Align.END)
                up.connect("clicked", self.up_connection, connection)
                conn.add(up)

            self.labels['connection-list'].attach(conn, 0, i, 1, 1)
        self.content.show_all()

    def wifi_connect(self, widget):
        self._screen.show_panel("Wifi Connect", "network_manager_wifi", "Wifi Connect", 1, False,
                                interface=self.interface)

    def add_connection(self, widget):
        conn_type = "wifi" if self.wireless else "ethernet"
        conn_name = "New-Profile"
        if self.wireless:
            new_conn = {
                "connection.interface-name": self.interface['GENERAL']['DEVICE'],
                "802-11-wireless.band": "bg",
                "802-11-wireless.channel": "3",
                "802-11-wireless-security.key-mgmt": "wpa-psk",
                "802-11-wireless-security.psk": "12345678",
                "ssid": "Printer",  # change me
                "ipv4.method": "manual",
                "ipv4.addresses": "10.0.0.5/8",
                "ipv6.addr-gen-mode": "0",
                "autoconnect": "yes",
                "connection.autoconnect-priority": "0"
            }
        else:
            new_conn = {
                "connection.interface-name": self.interface['GENERAL']['DEVICE'],
                "autoconnect": "yes",
                "connection.autoconnect-priority": "0",
                "connection.autoconnect-retries": "3",
                "ipv4.method": "auto",
                "ipv4.dhcp-timeout": "10",
                "ipv4.may-fail": "false",
                "ipv6.addr-gen-mode": "0"
            }
        self._screen.tpcclient.send_request(f"network-manager/add-connection/{conn_type}/{conn_name}", "POST",
                                            body=new_conn)
        self.load_connections()

    def remove_connection(self, widget, connection):
        self._screen.tpcclient.send_request(f"network-manager/delete-connection/{connection['id']}", "POST")
        self.load_connections()

    def edit_connection(self, widget, connection):
        name = connection["name"]
        self._screen.show_panel(f"network_manager_connection_{name}", "network_manager_connection", name, 1, False, connection=connection,
                                wireless=self.wireless)

    def up_connection(self, widget, connection):
        self._screen.tpcclient.send_request(f"network-manager/up-down-connection/{connection['id']}/up", "POST")
        widget.set_image(self._gtk.Image("retract"))
        self.load_connections()

    def down_connection(self, widget, connection):
        self._screen.tpcclient.send_request(f"network-manager/up-down-connection/{connection['id']}/down", "POST")
        widget.set_image(self._gtk.Image("retract"))
        self.load_connections()

    def refetch_interface(self):
        rsp = self._screen.tpcclient.send_request("network-manager/list-interfaces")
        interfaces = rsp["interfaces"]

        for i, interface in enumerate(interfaces):
            if interface['GENERAL']['DEVICE'] == self.interface['GENERAL']['DEVICE']:
                self.interface = interface

    def activate(self):
        self.load_connections()


