import logging
import os

import gi
import json

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
from ks_includes.screen_panel import ScreenPanel


def create_panel(*args, **kvargs):
    return NetworkManagerConnectionPanel(*args, **kvargs)

class NetworkManagerConnectionPanel(ScreenPanel):
    def __init__(self, screen, title, **kvargs):
        super().__init__(screen, title)

        self.connection = kvargs['connection']
        self.wireless = kvargs['wireless']

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.content.add(self.box)
        self.notebook = Gtk.Notebook()
        self.notebook.set_scrollable(True)
        self.box.add(self.notebook)

        self.page_general = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        page_general_scroll = self._gtk.ScrolledWindow()
        page_general_scroll.add(self.page_general)
        page_general_scroll.set_vexpand(True)
        self.notebook.append_page(page_general_scroll, Gtk.Label("General"))

        self.page_ipv4 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        page_ipv4_scroll = self._gtk.ScrolledWindow()
        page_ipv4_scroll.add(self.page_ipv4)
        page_ipv4_scroll.set_vexpand(True)
        self.notebook.append_page(page_ipv4_scroll, Gtk.Label("IPv4"))

        self.page_ipv6 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        page_ipv6_scroll = self._gtk.ScrolledWindow()
        page_ipv6_scroll.add(self.page_ipv6)
        page_ipv6_scroll.set_vexpand(True)
        self.notebook.append_page(page_ipv6_scroll, Gtk.Label("IPv6"))

        if self.wireless:
            self.page_wireless = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            page_wireless_scroll = self._gtk.ScrolledWindow()
            page_wireless_scroll.add(self.page_wireless)
            page_wireless_scroll.set_vexpand(True)
            self.notebook.append_page(page_wireless_scroll, Gtk.Label("Wireless"))

        btn_save = self._gtk.Button("settings", "Save", "color1")
        btn_save.set_hexpand(False)
        btn_save.set_vexpand(False)
        btn_save.connect("clicked", self.save_changes)
        btn_discard = self._gtk.Button("cancel", "Discard", "color1")
        btn_discard.set_hexpand(False)
        btn_discard.set_vexpand(False)
        btn_discard.connect("clicked", self.revert_changes)

        self.button_panel = self._gtk.HomogeneousGrid()
        # self.button_panel
        self.box.add(self.button_panel)
        self.button_panel.attach(btn_discard, 0, 0, 1, 1)
        self.button_panel.attach(btn_save, 1, 0, 1, 1)

        self.changed_fields = {}

        self.rebuild_pages()

    def rebuild_pages(self):
        self.refetch_connection()
        self.changed_fields = {}

        for ch in self.page_general.get_children():
            self.page_general.remove(ch)

        for ch in self.page_ipv4.get_children():
            self.page_ipv4.remove(ch)

        for ch in self.page_ipv6.get_children():
            self.page_ipv6.remove(ch)

        if self.wireless:
            for ch in self.page_wireless.get_children():
                self.page_wireless.remove(ch)

        entries = []

        # ---- PAGE GENERAL ----

        name_grid = self._gtk.HomogeneousGrid()
        name_grid.set_hexpand(True)
        name_label = Gtk.Label(label="Name:")
        name_label.set_halign(Gtk.Align.END)
        name_entry = Gtk.Entry()
        name_entry.set_text(self.connection_full["connection"]["id"])
        name_entry.connect("changed", self.change_name)
        name_entry.set_visibility(True)
        entries.append(name_entry)
        name_grid.attach(name_label, 0, 0, 2, 1)
        name_grid.attach(name_entry, 2, 0, 2, 1)
        self.page_general.add(name_grid)

        autoconnect_grid = self._gtk.HomogeneousGrid()
        autoconnect_grid.set_hexpand(True)
        autoconnect_label = Gtk.Label(label="Connect Automatically:")
        autoconnect_label.set_halign(Gtk.Align.END)
        autoconnect_switch = Gtk.Switch()
        autoconnect_switch.set_active(self.connection_full["connection"]["autoconnect"] == "yes")
        autoconnect_switch.set_hexpand(False)
        autoconnect_switch.connect("notify::active", self.change_autoconnect)
        autoconnect_grid.attach(autoconnect_label, 0, 0, 2, 1)
        autoconnect_grid.attach(autoconnect_switch, 2, 0, 1, 1)
        blank_box = Gtk.Box()
        blank_box.set_hexpand(False)
        autoconnect_grid.attach(blank_box, 3, 0, 1, 1)
        self.page_general.add(autoconnect_grid)

        cloned_mac_grid = self._gtk.HomogeneousGrid()
        cloned_mac_grid.set_hexpand(True)
        cloned_mac_label = Gtk.Label(label="Cloned MAC:")
        cloned_mac_label.set_halign(Gtk.Align.END)
        cloned_mac_entry = Gtk.Entry()
        if self.wireless:
            cloned_mac_entry.set_text(self.connection_full["wireless"]["cloned-mac-address"]
                                      if self.connection_full["wireless"]["cloned-mac-address"] != "--" else "")
        else:
            cloned_mac_entry.set_text(self.connection_full["ethernet"]["cloned-mac-address"]
                                      if self.connection_full["ethernet"]["cloned-mac-address"] != "--" else "")
        cloned_mac_entry.connect("changed", self.change_cloned_mac)
        cloned_mac_entry.set_visibility(True)
        entries.append(cloned_mac_entry)
        cloned_mac_grid.attach(cloned_mac_label, 0, 0, 2, 1)
        cloned_mac_grid.attach(cloned_mac_entry, 2, 0, 2, 1)
        self.page_general.add(cloned_mac_grid)

        # ---- PAGE IPv4 ----

        ipv4_method_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        ipv4_method_grid = self._gtk.HomogeneousGrid()
        ipv4_method_grid.set_hexpand(True)
        ipv4_method_label = Gtk.Label(label="IPv4 Method:")
        ipv4_method_label.set_halign(Gtk.Align.END)
        ipv4_method_dropdown = Gtk.ComboBoxText()
        ipv4_methods = [("auto", "Auto (DHCP)"), ("manual", "Manual"), ("link-local", "Link-local Only"),
                        ("shared", "Shared"), ("disabled","Disabled")]
        ipv4_method_current = None
        for i, opt in enumerate(ipv4_methods):
            ipv4_method_dropdown.append(opt[0], opt[1])
            if opt[0] == self.connection_full["ipv4"]["method"]:
                ipv4_method_current = opt[0]
                ipv4_method_dropdown.set_active(i)
        ipv4_method_dropdown.connect("changed", self.ipv4_method_change, ipv4_method_box)
        ipv4_method_dropdown.set_entry_text_column(0)
        ipv4_method_grid.attach(ipv4_method_label, 0, 0, 2, 1)
        ipv4_method_grid.attach(ipv4_method_dropdown, 2, 0, 2, 1)
        self.page_ipv4.add(ipv4_method_grid)
        self.build_ipv4_method_box(ipv4_method_current, ipv4_method_box)
        self.page_ipv4.add(ipv4_method_box)

        # ---- PAGE IPv6 ----

        ipv6_method_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        ipv6_method_grid = self._gtk.HomogeneousGrid()
        ipv6_method_grid.set_hexpand(True)
        ipv6_method_label = Gtk.Label(label="IPv6 Method:")
        ipv6_method_label.set_halign(Gtk.Align.END)
        ipv6_method_dropdown = Gtk.ComboBoxText()
        ipv6_methods = [("auto", "Auto (DHCPv6)"), ("manual", "Manual"), ("link-local", "Link-local Only"),
                        ("shared", "Shared"), ("disabled", "Disabled")]
        ipv6_method_current = None
        for i, opt in enumerate(ipv6_methods):
            ipv6_method_dropdown.append(opt[0], opt[1])
            if opt[0] == self.connection_full["ipv6"]["method"]:
                ipv6_method_current = opt[0]
                ipv6_method_dropdown.set_active(i)
        ipv6_method_dropdown.connect("changed", self.ipv6_method_change, ipv6_method_box)
        ipv6_method_dropdown.set_entry_text_column(0)
        ipv6_method_grid.attach(ipv6_method_label, 0, 0, 2, 1)
        ipv6_method_grid.attach(ipv6_method_dropdown, 2, 0, 2, 1)
        self.page_ipv6.add(ipv6_method_grid)
        self.build_ipv6_method_box(ipv6_method_current, ipv6_method_box)
        self.page_ipv6.add(ipv6_method_box)

        # ---- WIRELESS ----
        if self.wireless:
            wireless_mode_grid = self._gtk.HomogeneousGrid()
            wireless_mode_grid.set_hexpand(True)
            wireless_mode_label = Gtk.Label(label="Mode:")
            wireless_mode_label.set_halign(Gtk.Align.END)
            wireless_mode_dropdown = Gtk.ComboBoxText()
            wireless_modes = [("infrastructure", _("Client")), ("mesh", _("Mesh")), ("adhoc", _("Ad-hoc")), ("ap", _("AP"))]
            wireless_mode_current = None
            for i, opt in enumerate(wireless_modes):
                wireless_mode_dropdown.append(opt[0], opt[1])
                if opt[0] == self.connection_full["wireless"]["mode"]:
                    wireless_mode_current = opt[0]
                    wireless_mode_dropdown.set_active(i)
            wireless_mode_dropdown.connect("changed", self.wireless_mode_change)
            wireless_mode_dropdown.set_entry_text_column(0)
            wireless_mode_grid.attach(wireless_mode_label, 0, 0, 2, 1)
            wireless_mode_grid.attach(wireless_mode_dropdown, 2, 0, 2, 1)
            self.page_wireless.add(wireless_mode_grid)

            ssid_grid = self._gtk.HomogeneousGrid()
            ssid_grid.set_hexpand(True)
            ssid_label = Gtk.Label(label="SSID:")
            ssid_label.set_halign(Gtk.Align.END)
            ssid_entry = Gtk.Entry()
            ssid_entry.set_text(self.connection_full["wireless"]["ssid"])
            ssid_entry.connect("changed", self.change_ssid)
            entries.append(ssid_entry)
            ssid_grid.attach(ssid_label, 0, 0, 2, 1)
            ssid_grid.attach(ssid_entry, 2, 0, 2, 1)
            self.page_wireless.add(ssid_grid)

            wireless_security_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            wireless_security_grid = self._gtk.HomogeneousGrid()
            wireless_security_grid.set_hexpand(True)
            wireless_security_label = Gtk.Label(label="Security:")
            wireless_security_label.set_halign(Gtk.Align.END)
            wireless_security_dropdown = Gtk.ComboBoxText()
            wireless_securitys = [("none", "WEP"), ("ieee8021x", "Dynamic WEP"), ("wpa-psk", "WPA-PSK"), ("sae", "SAE"),
                                  ("owe", "OWE"), ("wpa-eap", "WPA-Enterprise"),
                                  ("wpa-eap-suite-b-192", "WPA3-Enterprise Suite B")]
            wireless_security_current = None
            for i, opt in enumerate(wireless_securitys):
                wireless_security_dropdown.append(opt[0], opt[1])
                if opt[0] == self.connection_full["wireless-security"]["key-mgmt"]:
                    wireless_security_current = opt[0]
                    wireless_security_dropdown.set_active(i)
            wireless_security_dropdown.connect("changed", self.wireless_security_change, wireless_security_box)
            wireless_security_dropdown.set_entry_text_column(0)
            wireless_security_grid.attach(wireless_security_label, 0, 0, 2, 1)
            wireless_security_grid.attach(wireless_security_dropdown, 2, 0, 2, 1)
            self.page_wireless.add(wireless_security_grid)
            self.build_wireless_security_box(wireless_security_current, wireless_security_box)
            self.page_wireless.add(wireless_security_box)

        for entry in entries:
            entry.connect("button-press-event", self._screen.show_keyboard)
            entry.set_hexpand(True)
            entry.set_vexpand(False)

        self._screen.show_all()

    def build_ipv4_method_box(self, method, box, show=False):
        def build_dns():
            dns_grid = self._gtk.HomogeneousGrid()
            dns_grid.set_hexpand(True)
            dns_label = Gtk.Label(label="DNS (comma separated):")
            dns_label.set_halign(Gtk.Align.END)
            dns_entry = Gtk.Entry()
            dns_entry.set_text(self.connection_full["ipv4"]["dns"]
                               if self.connection_full["ipv4"]["dns"] != "--" else "")
            dns_entry.connect("changed", self.change_ipv4_dns)
            dns_entry.connect("button-press-event", self._screen.show_keyboard)
            dns_entry.set_hexpand(True)
            dns_entry.set_vexpand(False)
            dns_grid.attach(dns_label, 0, 0, 2, 1)
            dns_grid.attach(dns_entry, 2, 0, 2, 1)
            box.add(dns_grid)
            if show:
                self._screen.show_all()

        def build_ip():
            ip_grid = self._gtk.HomogeneousGrid()
            ip_grid.set_hexpand(True)
            ip_label = Gtk.Label(label="IP:")
            ip_label.set_halign(Gtk.Align.END)
            ip_entry = Gtk.Entry()
            ip_entry.set_text(self.connection_full["ipv4"]["addresses"]
                               if self.connection_full["ipv4"]["addresses"] != "--" else "")
            ip_entry.connect("changed", self.change_ipv4_ip)
            ip_entry.connect("button-press-event", self._screen.show_keyboard)
            ip_entry.set_hexpand(True)
            ip_entry.set_vexpand(False)
            ip_grid.attach(ip_label, 0, 0, 2, 1)
            ip_grid.attach(ip_entry, 2, 0, 2, 1)
            box.add(ip_grid)

            gateway_grid = self._gtk.HomogeneousGrid()
            gateway_grid.set_hexpand(True)
            gateway_label = Gtk.Label(label="Gateway:")
            gateway_label.set_halign(Gtk.Align.END)
            gateway_entry = Gtk.Entry()
            gateway_entry.set_text(self.connection_full["ipv4"]["gateway"]
                              if self.connection_full["ipv4"]["gateway"] != "--" else "")
            gateway_entry.connect("changed", self.change_ipv4_gateway)
            gateway_entry.connect("button-press-event", self._screen.show_keyboard)
            gateway_entry.set_hexpand(True)
            gateway_entry.set_vexpand(False)
            gateway_grid.attach(gateway_label, 0, 0, 2, 1)
            gateway_grid.attach(gateway_entry, 2, 0, 2, 1)
            box.add(gateway_grid)

        for ch in box.get_children():
            box.remove(ch)

        if method is None:
            return
        elif method == "auto":
            build_dns()
        elif method == "manual":
            build_ip()
            build_dns()
        elif method == "shared":
            build_ip()
            build_dns()
        elif method == "link-local":
            return
        elif method == "disabled":
            return

    def build_ipv6_method_box(self, method, box, show=False):
        def build_dns():
            dns_grid = self._gtk.HomogeneousGrid()
            dns_grid.set_hexpand(True)
            dns_label = Gtk.Label(label="DNS (comma separated):")
            dns_label.set_halign(Gtk.Align.END)
            dns_entry = Gtk.Entry()
            dns_entry.set_text(self.connection_full["ipv6"]["dns"]
                               if self.connection_full["ipv6"]["dns"] != "--" else "")
            dns_entry.connect("changed", self.change_ipv6_dns)
            dns_entry.connect("button-press-event", self._screen.show_keyboard)
            dns_entry.set_hexpand(True)
            dns_entry.set_vexpand(False)
            dns_grid.attach(dns_label, 0, 0, 2, 1)
            dns_grid.attach(dns_entry, 2, 0, 2, 1)
            box.add(dns_grid)

        def build_ip():
            ip_grid = self._gtk.HomogeneousGrid()
            ip_grid.set_hexpand(True)
            ip_label = Gtk.Label(label="IP:")
            ip_label.set_halign(Gtk.Align.END)
            ip_entry = Gtk.Entry()
            ip_entry.set_text(self.connection_full["ipv6"]["addresses"]
                               if self.connection_full["ipv6"]["addresses"] != "--" else "")
            ip_entry.connect("changed", self.change_ipv6_ip)
            ip_entry.connect("button-press-event", self._screen.show_keyboard)
            ip_entry.set_hexpand(True)
            ip_entry.set_vexpand(False)
            ip_grid.attach(ip_label, 0, 0, 2, 1)
            ip_grid.attach(ip_entry, 2, 0, 2, 1)
            box.add(ip_grid)

            gateway_grid = self._gtk.HomogeneousGrid()
            gateway_grid.set_hexpand(True)
            gateway_label = Gtk.Label(label="Gateway:")
            gateway_label.set_halign(Gtk.Align.END)
            gateway_entry = Gtk.Entry()
            gateway_entry.set_text(self.connection_full["ipv6"]["gateway"]
                              if self.connection_full["ipv6"]["gateway"] != "--" else "")
            gateway_entry.connect("changed", self.change_ipv6_gateway)
            gateway_entry.connect("button-press-event", self._screen.show_keyboard)
            gateway_entry.set_hexpand(True)
            gateway_entry.set_vexpand(False)
            gateway_grid.attach(gateway_label, 0, 0, 2, 1)
            gateway_grid.attach(gateway_entry, 2, 0, 2, 1)
            box.add(gateway_grid)

        for ch in box.get_children():
            box.remove(ch)

        if method is None:
            return
        elif method == "auto":
            build_dns()
        elif method == "manual":
            build_ip()
            build_dns()
        elif method == "shared":
            build_ip()
            build_dns()
        elif method == "link-local":
            return
        elif method == "disabled":
            return

    def build_wireless_security_box(self, security, box, show=False):

        for ch in box.get_children():
            box.remove(ch)

        if security is None:
            wip = Gtk.Label(label="--- NOT IMPLEMENTED YET ---")
            wip.set_halign(Gtk.Align.CENTER)
            box.add(wip)
        elif security == "none":  # WEP
            wip = Gtk.Label(label="--- NOT IMPLEMENTED YET ---")
            wip.set_halign(Gtk.Align.CENTER)
            box.add(wip)
        elif security == "ieee8021x":  # Dynamic WEP
            wip = Gtk.Label(label="--- NOT IMPLEMENTED YET ---")
            wip.set_halign(Gtk.Align.CENTER)
            box.add(wip)
        elif security == "wpa-psk":  # WPA-PSK:
            wpa_pass_grid = self._gtk.HomogeneousGrid()
            wpa_pass_grid.set_hexpand(True)
            wpa_pass_label = Gtk.Label(label="Password:")
            wpa_pass_label.set_halign(Gtk.Align.END)
            wpa_pass_entry = Gtk.Entry()
            wpa_pass_entry.set_text(self.connection_full["wireless-security"]["psk"])
            wpa_pass_entry.connect("changed", self.change_wpa_password)
            wpa_pass_entry.connect("button-press-event", self._screen.show_keyboard)
            wpa_pass_entry.set_hexpand(True)
            wpa_pass_entry.set_vexpand(False)
            wpa_pass_entry.set_visibility(False)
            wpa_pass_grid.attach(wpa_pass_label, 0, 0, 2, 1)
            wpa_pass_grid.attach(wpa_pass_entry, 2, 0, 2, 1)
            box.add(wpa_pass_grid)
        elif security == "sae":  # SAE
            wip = Gtk.Label(label="--- NOT IMPLEMENTED YET ---")
            wip.set_halign(Gtk.Align.CENTER)
            box.add(wip)
        elif security == "owe":  # Opportunistic Wireless Encryption
            wip = Gtk.Label(label="--- NOT IMPLEMENTED YET ---")
            wip.set_halign(Gtk.Align.CENTER)
            box.add(wip)
        elif security == "wpa-eap":  # WPA-Enterprise
            wip = Gtk.Label(label="--- NOT IMPLEMENTED YET ---")
            wip.set_halign(Gtk.Align.CENTER)
            box.add(wip)
        elif security == "wpa-eap-suite-b-192":  # WPA3-Enterprise Suite B
            wip = Gtk.Label(label="--- NOT IMPLEMENTED YET ---")
            wip.set_halign(Gtk.Align.CENTER)
            box.add(wip)
    def change_name(self, widget):
        self.changed_fields["connection.id"] = widget.get_text()

    def change_autoconnect(self, widget, active):
        self.changed_fields["connection.autoconnect"] = widget.get_active()

    def change_cloned_mac(self, widget):
        if self.wireless:
            self.changed_fields["wireless.cloned-mac-address"] = widget.get_text()
        else:
            self.changed_fields["ethernet.cloned-mac-address"] = widget.get_text()

    def ipv4_method_change(self, widget, ipv4_method_box):
        tree_iter = widget.get_active_iter()
        model = widget.get_model()
        value = model[tree_iter][1]
        self.changed_fields["ipv4.method"] = value
        self.build_ipv4_method_box(value, ipv4_method_box, True)
        self._screen.show_all()

    def ipv6_method_change(self, widget, ipv6_method_box):
        tree_iter = widget.get_active_iter()
        model = widget.get_model()
        value = model[tree_iter][1]
        self.changed_fields["ipv6.method"] = value
        self.build_ipv6_method_box(value, ipv6_method_box, True)
        self._screen.show_all()

    def change_ipv4_ip(self, widget):
        self.changed_fields["ipv4.addresses"] = widget.get_text()

    def change_ipv4_gateway(self, widget):
        self.changed_fields["ipv4.gateway"] = widget.get_text()

    def change_ipv4_dns(self, widget):
        self.changed_fields["ipv4.dns"] = widget.get_text()

    def change_ipv6_ip(self, widget):
        self.changed_fields["ipv6.addresses"] = widget.get_text()

    def change_ipv6_gateway(self, widget):
        self.changed_fields["ipv6.gateway"] = widget.get_text()

    def change_ipv6_dns(self, widget):
        self.changed_fields["ipv6.dns"] = widget.get_text()

    def wireless_mode_change(self, widget):
        tree_iter = widget.get_active_iter()
        model = widget.get_model()
        value = model[tree_iter][1]
        self.changed_fields["wireless.mode"] = value

    def wireless_security_change(self, widget, wireless_security_box):
        tree_iter = widget.get_active_iter()
        model = widget.get_model()
        value = model[tree_iter][1]
        self.changed_fields["wireless-security.key-mgmt"] = value
        self.build_wireless_security_box(value, wireless_security_box, True)
        self._screen.show_all()

    def change_wpa_password(self, widget):
        self.changed_fields["wireless-security.psk"] = widget.get_text()

    def change_ssid(self, widget):
        self.changed_fields["802-11-wireless.ssid"] = widget.get_text()

    def save_changes(self, widget):
        print(json.dumps(self.changed_fields, indent=2))
        rsp, code = self._screen.tpcclient.send_request(f"network-manager/modify-connection/{self.connection['id']}", "POST",
                                            body=self.changed_fields, keep_err_code=True)
        logging.info(f"rsp: {rsp}, code: {code}")
        if code == 200:
            #self.rebuild_pages()
            self._screen._menu_go_back()
        else:
            self._screen.show_popup_message(rsp["stderr"], 3)

    def revert_changes(self, widget):
        print(json.dumps(self.changed_fields, indent=2))
        self.rebuild_pages()

    def refetch_connection(self):
        conn = self._screen.tpcclient.send_request(f"network-manager/show-connection/{self.connection['id']}")

        extra = {}

        for key in conn:
            if key.endswith("-ethernet"):
                extra["ethernet"] = conn[key]
            if key.endswith("-wireless"):
                extra["wireless"] = conn[key]
            if key.endswith("-wireless-security"):
                extra["wireless-security"] = conn[key]

        for key in extra:
            conn[key] = extra[key]

        self.connection_full = conn

    def activate(self):
        self.rebuild_pages()