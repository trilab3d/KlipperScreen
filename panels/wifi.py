import logging

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

from ks_includes.screen_panel import ScreenPanel


def create_panel(*args):
    return WifiPanel(*args)


class WifiPanel(ScreenPanel):
    def __init__(self, screen, title):
        super().__init__(screen, title)

        self.modes = ['AP', 'STA', 'AUTO', 'OFF']
        self.mode = self.modes[0]
        self.mode_buttons = {}

        self.wifi_ap_ssid = ""
        self.wifi_ap_pass = ""
        self.wifi_sta_ssid = ""
        self.wifi_sta_pass = ""

        self.scroll = self._gtk.ScrolledWindow()
        self.content.add(self.scroll)
        self.scroll_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.form_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.network_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.scroll.add(self.scroll_box)
        self.scroll_box.add(self.form_box)
        self.scroll_box.add(self.network_box)

        self.sta_ssid_entry = None
        self.sta_pass_entry = None
        self.ap_ssid_entry = None
        self.ap_pass_entry = None

        self.btn_refresh = None

        self.has_changes = False

        self.fetch_settings()
        self.refresh()
        GLib.timeout_add_seconds(1, self.fetch_networks)

    def fetch_settings(self):
        rsp = self._screen.tpcclient.send_request("settings")
        network_data = rsp["network_data"]
        self.mode = network_data["wifi_mode"]
        self.wifi_ap_ssid = network_data["wifi_ap_ssid"]
        self.wifi_ap_pass = network_data["wifi_ap_pass"]
        self.wifi_sta_ssid = network_data["wifi_sta_ssid"]
        self.wifi_sta_pass = network_data["wifi_sta_pass"]

    def fetch_networks(self):
        rsp = self._screen.tpcclient.send_request("network/wifi/list")
        networks = rsp["networks"]

        def key_func(e):
            v = float(e['signal'].split(' ')[0])
            return v

        networks.sort(key=key_func, reverse=True)

        for child in self.network_box.get_children():
            self.network_box.remove(child)

        for network in networks:
            logging.info(f"Adding network {network}")
            network_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            network_box.get_style_context().add_class("frame-item")
            network_box.set_hexpand(True)
            network_box.set_vexpand(False)

            sig_num = float(network['signal'].split(' ')[0])
            logging.info(f"signal numeric: {sig_num}")

            if sig_num > -40:
                img = self._gtk.Image("wifi-signal-4", self._gtk.content_width * .1, self._gtk.content_height * .1)
            elif sig_num > -65:
                img = self._gtk.Image("wifi-signal-3", self._gtk.content_width * .1, self._gtk.content_height * .1)
            elif sig_num > -80:
                img = self._gtk.Image("wifi-signal-2", self._gtk.content_width * .1, self._gtk.content_height * .1)
            else:
                img = self._gtk.Image("wifi-signal-1", self._gtk.content_width * .1, self._gtk.content_height * .1)

            network_box.add(img)

            labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            labels.set_hexpand(True)
            labels.set_valign(Gtk.Align.CENTER)
            labels.set_halign(Gtk.Align.START)
            network_box.add(labels)

            name = Gtk.Label()
            name.set_markup(f"<big><b>{network['ssid']}</b></big>")
            name.set_halign(Gtk.Align.START)
            labels.add(name)

            signal = Gtk.Label()
            signal.set_markup(f"<b>signal:</b> {network['signal']}")
            signal.set_halign(Gtk.Align.START)
            labels.add(signal)

            bssid = Gtk.Label()
            bssid.set_markup(f"<b>bssid:</b> {network['bssid']}")
            bssid.set_halign(Gtk.Align.START)
            labels.add(bssid)

            #empty_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

            btn = self._gtk.Button("arrow-up", None, "color1")
            btn.connect("clicked", self.select_wifi, network['ssid'])
            btn.set_hexpand(False)
            btn.set_halign(Gtk.Align.END)
            network_box.add(btn)

            self.network_box.add(network_box)

        if self.btn_refresh:
            self.btn_refresh.set_sensitive(True)
        self.content.show_all()

    def refresh(self):

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.set_vexpand(False)

        for child in self.form_box.get_children():
            self.form_box.remove(child)
        self.form_box.add(box)

        grid = Gtk.Grid()
        grid.set_vexpand(False)
        box.pack_start(grid, False, False, 0)

        lbl1 = Gtk.Label()
        lbl1.set_markup(f"<big><b>Mode</b></big>")
        lbl1.set_halign(Gtk.Align.END)
        distgrid = Gtk.Grid()
        distgrid.set_vexpand(False)
        distgrid.set_hexpand(False)
        for j, i in enumerate(self.modes):
            # logging.info(f"creating button #{j}: {i}")
            self.mode_buttons[i] = self._gtk.Button(label=i)
            self.mode_buttons[i].set_direction(Gtk.TextDirection.LTR)
            self.mode_buttons[i].connect("clicked", self.change_mode, i)
            ctx = self.mode_buttons[i].get_style_context()
            if (self._screen.lang_ltr and j == 0) or (not self._screen.lang_ltr and j == len(self.modes) - 1):
                ctx.add_class("distbutton_top")
            elif (not self._screen.lang_ltr and j == 0) or (self._screen.lang_ltr and j == len(self.modes) - 1):
                ctx.add_class("distbutton_bottom")
            else:
                ctx.add_class("distbutton")
            if i == self.mode:
                ctx.add_class("distbutton_active")
            distgrid.attach(self.mode_buttons[i], j, 0, 1, 1)
        grid.attach(lbl1, 0, 0, 1, 1)
        grid.attach(distgrid, 1, 0, 1, 1)

        if self.mode == 'STA' or self.mode == 'AUTO':
            lbl2 = Gtk.Label()
            lbl2.set_markup(f"<big><b>SSID</b></big>")
            lbl2.set_halign(Gtk.Align.END)
            self.sta_ssid_entry = Gtk.Entry()
            self.sta_ssid_entry.set_text(self.wifi_sta_ssid)
            self.sta_ssid_entry.set_hexpand(True)
            self.sta_ssid_entry.set_vexpand(False)
            self.sta_ssid_entry.connect("button-press-event", self._screen.show_keyboard)
            self.sta_ssid_entry.connect("focus-in-event", self._screen.show_keyboard)
            self.sta_ssid_entry.connect("changed", self.data_changed)
            self.sta_ssid_entry.set_visibility(True)
            grid.attach(lbl2, 0, 1, 1, 1)
            grid.attach(self.sta_ssid_entry, 1, 1, 1, 1)

            lbl3 = Gtk.Label()
            lbl3.set_markup(f"<big><b>Password</b></big>")
            lbl3.set_halign(Gtk.Align.END)
            sta_pass_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            self.sta_pass_entry = Gtk.Entry()
            self.sta_pass_entry.set_text(self.wifi_sta_pass)
            self.sta_pass_entry.set_hexpand(True)
            self.sta_pass_entry.set_vexpand(False)
            self.sta_pass_entry.connect("button-press-event", self._screen.show_keyboard)
            self.sta_pass_entry.connect("focus-in-event", self._screen.show_keyboard)
            self.sta_pass_entry.connect("changed", self.data_changed)
            self.sta_pass_entry.set_visibility(False)
            sta_pass_btn = self._gtk.Button("stop", None, "color1", 0.33)  # put some eye icon here
            sta_pass_btn.connect("clicked", self.toggle_pass_visibility, self.sta_pass_entry)
            sta_pass_btn.set_hexpand(False)
            sta_pass_box.add(self.sta_pass_entry)
            sta_pass_box.add(sta_pass_btn)
            grid.attach(lbl3, 0, 2, 1, 1)
            grid.attach(sta_pass_box, 1, 2, 1, 1)

        if self.mode == 'AP' or self.mode == 'AUTO':
            lbl4 = Gtk.Label()
            lbl4.set_markup(f"<big><b>AP SSID</b></big>")
            lbl4.set_halign(Gtk.Align.END)
            self.ap_ssid_entry = Gtk.Entry()
            self.ap_ssid_entry.set_text(self.wifi_ap_ssid)
            self.ap_ssid_entry.set_hexpand(True)
            self.ap_ssid_entry.set_vexpand(False)
            self.ap_ssid_entry.connect("button-press-event", self._screen.show_keyboard)
            self.ap_ssid_entry.connect("focus-in-event", self._screen.show_keyboard)
            self.ap_ssid_entry.connect("changed", self.data_changed)
            self.ap_ssid_entry.set_visibility(True)
            grid.attach(lbl4, 0, 3, 1, 1)
            grid.attach(self.ap_ssid_entry, 1, 3, 1, 1)

            lbl5 = Gtk.Label()
            lbl5.set_markup(f"<big><b>AP Password</b></big>")
            lbl5.set_halign(Gtk.Align.END)
            ap_pass_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            self.ap_pass_entry = Gtk.Entry()
            self.ap_pass_entry.set_text(self.wifi_ap_pass)
            self.ap_pass_entry.set_hexpand(True)
            self.ap_pass_entry.set_vexpand(False)
            self.ap_pass_entry.connect("button-press-event", self._screen.show_keyboard)
            self.ap_pass_entry.connect("focus-in-event", self._screen.show_keyboard)
            self.ap_pass_entry.connect("changed", self.data_changed)
            self.ap_pass_entry.set_visibility(False)
            ap_pass_btn = self._gtk.Button("stop", None, "color1", 0.33)  # put some eye icon here
            ap_pass_btn.connect("clicked", self.toggle_pass_visibility, self.ap_pass_entry)
            ap_pass_btn.set_hexpand(False)
            ap_pass_box.add(self.ap_pass_entry)
            ap_pass_box.add(ap_pass_btn)
            grid.attach(lbl5, 0, 4, 1, 1)
            grid.attach(ap_pass_box, 1, 4, 1, 1)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        btn_cancel = self._gtk.Button("cancel", "Cancel", "color1")
        btn_save = self._gtk.Button("complete", "Save", "color1")
        self.btn_refresh = self._gtk.Button("refresh", "Refresh", "color1")
        btn_save.connect("clicked", self.save)
        btn_cancel.connect("clicked", self.cancel)
        self.btn_refresh.connect("clicked", self.wifi_refresh)
        btn_save.set_sensitive(self.has_changes)
        btn_cancel.set_sensitive(self.has_changes)
        btn_box.add(btn_cancel)
        btn_box.add(btn_save)
        btn_box.add(self.btn_refresh)

        grid.attach(btn_box, 1, 5, 1, 1)
        self.content.show_all()

    def change_mode(self, widget, mode, refresh=True):
        if self.mode == mode:
            return
        self.has_changes = True
        logging.info(f"### Wifi mode {mode}")
        self.mode_buttons[f"{self.mode}"].get_style_context().remove_class("distbutton_active")
        self.mode_buttons[f"{mode}"].get_style_context().add_class("distbutton_active")
        self.mode = mode
        if refresh:
            self.refresh()

    def select_wifi(self, widget, wifi):
        if self.mode == 'AP':
            self.change_mode(None, 'AUTO', False)
        elif self.mode != 'AUTO':
            self.change_mode(None, 'STA', False)

        self.wifi_sta_ssid = wifi
        self.wifi_sta_pass = ""

        position = self.scroll.get_vadjustment()
        position.set_value(0)
        self.scroll.set_vadjustment(position)

        self.refresh()

    def data_changed(self, widget):
        self.has_changes = True

    def toggle_pass_visibility(self, widget, entry):
        entry.set_visibility(not entry.get_visibility())

    def save(self, widget):
        data = {}
        data["network_data"] = {}
        data["network_data"]["wifi_mode"] = str(self.mode)
        if self.mode == 'STA' or self.mode == 'AUTO':
            data["network_data"]["wifi_sta_ssid"] = str(self.sta_ssid_entry.get_text())
            data["network_data"]["wifi_sta_pass"] = str(self.sta_pass_entry.get_text())
        if self.mode == 'AP' or self.mode == 'AUTO':
            data["network_data"]["wifi_ap_ssid"] = str(self.ap_ssid_entry.get_text())
            data["network_data"]["wifi_ap_pass"] = str(self.ap_pass_entry.get_text())
        self._screen.tpcclient.post_request("settings", data)
        self.fetch_settings()
        self.has_changes = False
        self.refresh()

    def cancel(self, widget):
        self.fetch_settings()
        self.has_changes = False
        self.refresh()

    def wifi_refresh(self, widget=None):
        if self.btn_refresh:
            self.btn_refresh.set_sensitive(False)
        GLib.timeout_add_seconds(1, self.fetch_networks)

    def activate(self):
        self.fetch_settings()
        self.refresh()
        self.wifi_refresh()
