import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, Pango
from threading import Thread
import os
import logging
import requests
import qrcode

from panels.privacy import PRESET_FIELDS
from panels.hostname import HOSTNAME_REGEX

from WizardSteps.baseWizardStep import BaseWizardStep
from WizardSteps.prusaConnectSteps import CONNECT_PARAMS

class Welcome(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_exit = False

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("prusa_logo", self._screen.gtk.content_width * .945,-1)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" + _("Welcome to your new Prusa Pro HT90 printer!") + "</span>")
        heating_label.set_line_wrap(True)
        heating_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(heating_label)
        continue_button = self._screen.gtk.Button(label=_("Start"), style=f"color1")
        continue_button.set_vexpand(False)
        continue_button.connect("clicked", self.continue_pressed)
        self.content.add(continue_button)

    def continue_pressed(self, widget):
        # TODO - get proper T&C
        #self.wizard_manager.set_step(TermsAndConditions(self._screen))
        self.wizard_manager.set_step(Timezone(self._screen))

class TermsAndConditions(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_exit = False

    def activate(self, wizard):
        super().activate(wizard)
        self.content = self._screen.gtk.ScrolledWindow()
        self.content.set_vexpand(True)
        self.content.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content.add(self.box)
        #img = self._screen.gtk.Image("placeholder43", self._screen.gtk.content_width * .945,-1)
        #self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" + _("Terms and Conditions") + "</span>")
        heating_label.set_line_wrap(True)
        heating_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.box.add(heating_label)
        with open("terms_and_conditions.txt","r") as f:
            conditions = self._screen.gtk.Label(f.read())
            conditions.set_margin_top(20)
            conditions.set_margin_left(10)
            conditions.set_line_wrap(True)
            conditions.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
            self.box.add(conditions)
        continue_button = self._screen.gtk.Button(label=_("Accept"), style=f"color1")
        continue_button.set_vexpand(False)
        continue_button.connect("clicked", self.continue_pressed)
        self.box.add(continue_button)

    def continue_pressed(self, widget):
        self.wizard_manager.set_step(Timezone(self._screen))


class Timezone(BaseWizardStep):
    def __init__(self, screen, zone_stack=None):
        super().__init__(screen)
        self.can_exit = False
        self.zone_stack = zone_stack if zone_stack is not None else [self._screen._config.timezones]
        self.can_back = len(self.zone_stack) > 1

    def activate(self, wizard):
        super().activate(wizard)
        self.content = self._screen.gtk.ScrolledWindow()
        self.content.set_vexpand(True)
        self.content.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content.add(self.box)
        #img = self._screen.gtk.Image("placeholder43", self._screen.gtk.content_width * .945,-1)
        #self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("Configure Your Timezone") + "</span>")
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.box.add(label)

        for zone in self.zone_stack[-1]:
            name = Gtk.Label()
            name.set_markup(f"<big><b>{zone}</b></big>")
            name.set_hexpand(True)
            name.set_vexpand(True)
            name.set_halign(Gtk.Align.START)
            name.set_valign(Gtk.Align.CENTER)
            name.set_line_wrap(True)
            name.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)

            labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            labels.add(name)

            dev = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            dev.get_style_context().add_class("frame-item")
            dev.set_hexpand(True)
            dev.set_vexpand(False)
            dev.set_valign(Gtk.Align.CENTER)

            dev.add(labels)
            if type(self.zone_stack[-1][zone]) == str:
                select = self._screen.gtk.Button("settings", style="color3")
                select.connect("clicked", self.set_timezone, self.zone_stack[-1][zone])
            else:
                select = self._screen.gtk.Button("load", style="color3")
                select.connect("clicked", self.set_subzone, self.zone_stack[-1][zone])
            select.set_hexpand(False)
            select.set_halign(Gtk.Align.END)
            dev.add(select)

            self.box.add(dev)

    def set_subzone(self, widget, zone):
        self.wizard_manager.set_step(Timezone(self._screen, [*self.zone_stack, zone]))

    def set_timezone(self, widget, zone):
        os.system("echo Network > /opt/init_state")
        os.system(f"timedatectl set-timezone {zone}")
        os.system(f"cp -P /etc/timezone /opt/timezone")  # to have timezone persistent between updates
        os.system(f"cp -P /etc/localtime /opt/localtime")
        # self._screen.restart_ks()
        os.system("systemctl restart klipper-screen")

    def on_back(self):
        self.wizard_manager.set_step(Timezone(self._screen, self.zone_stack[0:-1]))
        return True


class Network(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_exit = False

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content.set_vexpand(True)
        img = self._screen.gtk.Image("init_network", self._screen.gtk.content_width * .945,-1)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" + _("Network Configuration") + "</span>")
        heating_label.set_line_wrap(True)
        heating_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(heating_label)
        button = self._screen.gtk.Button(label=_("Open Network Configuration"), style=f"color1")
        button.set_vexpand(False)
        button.connect("clicked", self.open_network)
        self.content.add(button)
        button = self._screen.gtk.Button(label=_("Continue With Network Test"), style=f"color1")
        button.set_vexpand(False)
        button.connect("clicked", self.test_network)
        self.content.add(button)

        # button = self._screen.gtk.Button(label=_("Configure Wired Connection"), style=f"color1")
        # button.set_vexpand(False)
        # button.connect("clicked", self.configure_wired)
        # self.content.add(button)
        # button = self._screen.gtk.Button(label=_("Configure Wireless Connection"), style=f"color1")
        # button.set_vexpand(False)
        # button.connect("clicked", self.configure_wireless)
        # self.content.add(button)
        button = self._screen.gtk.Button(label=_("Skip network configuration"), style=f"color1")
        button.set_vexpand(False)
        button.connect("clicked", self.skip_pressed)
        self.content.add(button)

    def open_network(self, widget):
        self._screen.show_panel("Network", "network_manager", "network_manager", 1, False)

    def test_network(self, widget):
        self.wizard_manager.set_step(NetworkTest(self._screen))

    def configure_wired(self, widget):
        self.wizard_manager.set_step(WiredNetwork(self._screen))

    def configure_wireless(self, widget):
        self.wizard_manager.set_step(WirelessNetwork(self._screen))

    def skip_pressed(self, widget):
        self.wizard_manager.set_step(NoNetworkWarning(self._screen))


class WiredNetwork(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_exit = False
        self.can_back = True

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content.set_vexpand(True)
        img = self._screen.gtk.Image("make_sure_ethernet_connected", self._screen.gtk.content_width * .945,-1)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" + _("Make sure ethernet cable is connected") + "</span>")
        heating_label.set_line_wrap(True)
        heating_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(heating_label)
        button = self._screen.gtk.Button(label=_("Continue"), style=f"color1")
        button.set_vexpand(False)
        button.connect("clicked", self.continue_pressed)
        self.content.add(button)

    def continue_pressed(self, widget):
        self.wizard_manager.set_step(NetworkTest(self._screen))

    def on_back(self):
        self.wizard_manager.set_step(Network(self._screen))
        return True


class WirelessNetwork(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_exit = False
        self.can_back = True

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content.set_vexpand(True)
        img = self._screen.gtk.Image("wifi_settings", self._screen.gtk.content_width * .945,-1)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" + _("Make sure wireless adapter is connected") + "</span>")
        heating_label.set_line_wrap(True)
        heating_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(heating_label)
        button = self._screen.gtk.Button(label=_("Continue"), style=f"color1")
        button.set_vexpand(False)
        button.connect("clicked", self.continue_pressed)
        self.content.add(button)

    def continue_pressed(self, widget):
        #self.wizard_manager.set_step(NetworkTest(self._screen))
        pass

    def on_back(self):
        self.wizard_manager.set_step(Network(self._screen))
        return True

class NetworkTest(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_exit = False

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content.set_vexpand(True)
        img = self._screen.gtk.Image("trilab_network_check", self._screen.gtk.content_width * .945,-1)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" + _("Checking Network connection.") + "</span>")
        heating_label.set_line_wrap(True)
        heating_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(heating_label)

    def update_loop(self):
        r = requests.get("https://google.com")
        if r.status_code == 200:
            self.wizard_manager.set_wizard_data("network_working", True)
            self.wizard_manager.set_step(NetworkTestSucesfull(self._screen))
        else:
            self.wizard_manager.set_wizard_data("network_working", False)
            self.wizard_manager.set_step(NetworkTestFailure(self._screen))

class NetworkTestSucesfull(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_exit = False

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content.set_vexpand(True)
        img = self._screen.gtk.Image("network_check_success", self._screen.gtk.content_width * .945,-1)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" + _("Network Connection test was successful") + "</span>")
        heating_label.set_line_wrap(True)
        heating_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(heating_label)
        button = self._screen.gtk.Button(label=_("Continue"), style=f"color1")
        button.set_vexpand(False)
        button.connect("clicked", self.continue_pressed)
        self.content.add(button)

    def continue_pressed(self, widget):
        self.wizard_manager.set_step(Privacy(self._screen))

class NetworkTestFailure(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_exit = False

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content.set_vexpand(True)
        img = self._screen.gtk.Image("network_check_error", self._screen.gtk.content_width * .945,-1)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" + _("Network Connection test was not successful") + "</span>")
        heating_label.set_line_wrap(True)
        heating_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(heating_label)
        button = self._screen.gtk.Button(label=_("Configure another connection method"), style=f"color1")
        button.set_vexpand(False)
        button.connect("clicked", self.another_method_pressed)
        self.content.add(button)
        button = self._screen.gtk.Button(label=_("Continue anyway"), style=f"color1")
        button.set_vexpand(False)
        button.connect("clicked", self.skip_pressed)
        self.content.add(button)

    def another_method_pressed(self, widget):
        self.wizard_manager.set_step(Network(self._screen))

    def skip_pressed(self, widget):
        self.wizard_manager.set_step(NoNetworkWarning(self._screen))

class NoNetworkWarning(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_exit = False

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content.set_vexpand(True)
        img = self._screen.gtk.Image("warning", self._screen.gtk.content_width * .945,-1)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" +
            _("Without working internet connection, functionality may be limited.") + "</span>")
        heating_label.set_line_wrap(True)
        heating_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(heating_label)
        button = self._screen.gtk.Button(label=_("Configure network"), style=f"color1")
        button.set_vexpand(False)
        button.connect("clicked", self.network_pressed)
        self.content.add(button)
        button = self._screen.gtk.Button(label=_("Continue without network"), style=f"color1")
        button.set_vexpand(False)
        button.connect("clicked", self.continue_pressed)
        self.content.add(button)

    def network_pressed(self, widget):
        self.wizard_manager.set_step(Network(self._screen))

    def continue_pressed(self, widget):
        self.wizard_manager.set_step(Privacy(self._screen))

class Privacy(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_exit = False

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content.set_vexpand(True)
        img = self._screen.gtk.Image("privacy_settings", self._screen.gtk.content_width * .945,-1)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" +
            _("Configure privacy settings") + "</span>")
        heating_label.set_line_wrap(True)
        heating_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(heating_label)
        button = self._screen.gtk.Button(label=_("Reduced logging"), style=f"color1")
        button.set_vexpand(False)
        button.connect("clicked", self.reduced_pressed)
        self.content.add(button)
        button = self._screen.gtk.Button(label=_("Recommended logging"), style=f"color1")
        button.set_vexpand(False)
        button.connect("clicked", self.recommended_pressed)
        self.content.add(button)
        button = self._screen.gtk.Button(label=_("Custom logging"), style=f"color1")
        button.set_vexpand(False)
        button.connect("clicked", self.custom_pressed)
        self.content.add(button)

    def reduced_pressed(self, widget):
        settings = {
            "privacy": PRESET_FIELDS["reduced"],
        }
        requests.post("http://127.0.0.1/tpc/settings", json=settings)
        self.wizard_manager.set_step(Done(self._screen))

    def recommended_pressed(self, widget):
        settings = {
            "privacy": PRESET_FIELDS["standard"],
        }
        requests.post("http://127.0.0.1/tpc/settings", json=settings)
        self.wizard_manager.set_step(PrinterName(self._screen))

    def custom_pressed(self, widget):
        self.wizard_manager.set_step(PrivacyCustom(self._screen))

class PrivacyCustom(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_exit = False
        self.can_back = True
        self.privacy_info = requests.get("http://127.0.0.1/tpc/privacy_info").json()
        self.privacy_options = self.privacy_info["privacy_options"]

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content.set_vexpand(True)
        self.grid = Gtk.Grid()
        self.grid.set_margin_top(20)
        self.grid.set_hexpand(True)
        scroll = self._screen.gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.add(self.grid)
        self.content.add(scroll)
        for i, option in enumerate(self.privacy_info["privacy_options"]):
            label = Gtk.Expander(label=f"<span size='x-large'>{option.replace('_', ' ')}:</span>", use_markup=True)
            label.set_halign(Gtk.Align.START)
            label.set_hexpand(True)
            label.set_margin_top(25)
            label.set_margin_left(10)
            desc = Gtk.Label(label=self.privacy_info["privacy_option_descriptions"][option])
            desc.set_halign(Gtk.Align.START)
            desc.set_line_wrap(True)
            desc.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
            desc.set_margin_top(10)
            desc.set_margin_left(20)
            label.add(desc)
            switch = Gtk.Switch()
            switch.set_active(option in self.privacy_options)
            switch.set_hexpand(False)
            switch.set_vexpand(False)
            switch.set_size_request(-1, 20)
            switch.connect("notify::active", self.change_option, option)
            self.grid.attach(label, 0, i + 1, 2, 1)
            switch_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            switch_box.set_hexpand(False)
            switch_box.set_vexpand(False)
            blank_box = Gtk.Box()
            blank_box.set_hexpand(True)
            blank_box.set_vexpand(True)
            switch_box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            switch_box2.set_hexpand(False)
            switch_box2.set_vexpand(False)
            switch_box2.add(blank_box)
            switch_box2.add(switch)
            switch_box.add(switch_box2)
            self.grid.attach(switch_box, 1, i + 1, 1, 1)

        button = self._screen.gtk.Button(label=_("Continue"), style=f"color1")
        button.set_vexpand(False)
        button.connect("clicked", self.continue_pressed)
        self.content.add(button)

    def change_option(self, widget, active, option):
        if widget.get_active():
            if option not in self.privacy_options:
                self.privacy_options.append(option)
        else:
            if option in self.privacy_options:
                self.privacy_options.remove(option)

    def continue_pressed(self, widget):
        settings = {
            "privacy": self.privacy_options,
        }
        requests.post("http://127.0.0.1/tpc/settings", json=settings)
        self.wizard_manager.set_step(PrinterName(self._screen))

    def on_back(self):
        self.wizard_manager.set_step(Privacy(self._screen))
        return True

class PrinterName(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_exit = False
        self.changed_fields = {}

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content.set_vexpand(True)
        #TODO - Entry can't be too low on screen, because keyboard is rendered bellow
        #img = self._screen.gtk.Image("placeholder43", self._screen.gtk.content_width * .945, -1)
        #self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" +
            _("Choose name for the printer") + "</span>")
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(label)
        label = self._screen.gtk.Label("")
        label.set_margin_top(10)
        label.set_markup(
            "<span size='small'>" +
            _("This name will be used as local network name") + "</span>")
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(label)

        grid = self._screen.gtk.HomogeneousGrid()
        grid.set_hexpand(True)
        grid.set_vexpand(True)
        grid.set_margin_top(30)
        grid.set_margin_left(10)
        grid.set_margin_right(10)
        hostname_label = Gtk.Label(label=_("Printer Name:"))
        hostname_label.set_halign(Gtk.Align.END)
        hostname_entry = Gtk.Entry()
        hostname_entry.set_text(os.popen(f"hostname").read().strip())
        hostname_entry.connect("changed", self.change_hostname)
        hostname_entry.set_visibility(True)
        hostname_entry.connect("button-press-event", self._screen.show_keyboard)
        hostname_entry.set_hexpand(True)
        hostname_entry.set_vexpand(False)
        self._screen.show_keyboard(hostname_entry)
        grid.attach(hostname_label, 0, 0, 1, 1)
        grid.attach(hostname_entry, 1, 0, 3, 1)
        self.content.add(grid)

        self.button = self._screen.gtk.Button(label=_("Continue"), style=f"color1")
        self.button.set_vexpand(False)
        self.button.connect("clicked", self.continue_pressed)
        self.content.add(self.button)

    def change_hostname(self, widget):
        hostname = widget.get_text()
        self.changed_fields["hostname"] = hostname
        if HOSTNAME_REGEX.match(hostname):
            context = widget.get_style_context()
            context.remove_class("entry-invalid")
            self.button.set_sensitive(True)
        else:
            context = widget.get_style_context()
            context.add_class("entry-invalid")
            self.button.set_sensitive(False)

    def continue_pressed(self, widget):
        if "hostname" in self.changed_fields:
            b = {
                "hostname": self.changed_fields["hostname"]
            }
            requests.post("http://127.0.0.1/tpc/set_hostname", json=b)
        self._screen.remove_keyboard()
        self.wizard_manager.set_step(PrusaConnectDialog(self._screen))

class PrusaConnectDialog(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_exit = False
        self.changed_fields = {}

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content.set_vexpand(True)
        img = self._screen.gtk.Image("prusa-connect", self._screen.gtk.content_width * .945, -1)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" +
            _("Configure Prusa Connect") + "</span>")
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(label)
        label = self._screen.gtk.Label("")
        label.set_margin_top(10)
        label.set_markup(
            "<span size='small'>" +
            _("You will need a smartphone, computer, or another device with a working browser "
              "and internet connection to proceed.") + "</span>")
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(label)

        button = self._screen.gtk.Button(label=_("Continue"), style=f"color1")
        button.set_vexpand(False)
        button.connect("clicked", self.continue_pressed)
        self.content.add(button)

        button = self._screen.gtk.Button(label=_("Skip Prusa Connect configuration"), style=f"color1")
        button.set_vexpand(False)
        button.connect("clicked", self.skip_pressed)
        self.content.add(button)

    def continue_pressed(self, widget):
        self.wizard_manager.set_step(PrusaConnectInProgress(self._screen))

    def skip_pressed(self, widget):
        self.wizard_manager.set_step(Done(self._screen))

class PrusaConnectInProgress(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_back = True
    def activate(self, wizard):
        super().activate(wizard)

        try:
            r = requests.get(f"http://127.0.0.1:5001/connection").json()
            if "registration" in r:
                if r["registration"] == "FINISHED":
                    self.wizard_manager.set_step(PrusConnectDone(self._screen))
                    return

            r = requests.post(f"http://127.0.0.1:5001/connection", json=CONNECT_PARAMS).json()
            self.code = r["code"]
            self.url = r["url"]
            logging.info(f"Continue on {self.url}")
            self.skip = False
        except:
            self._screen.show_popup_message("Error on PrusaConnect module, skipping PrusaConnect configuration. "
                                            "You can configure it later.", 2)
            self.wizard_manager.set_step(Done(self._screen))
            return
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(self.url)
        qr.make(fit=True)
        qr_pil = qr.make_image(fill_color="black", back_color="white")
        qr_pil.save("/tmp/ConnectQRCode.png")
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size("/tmp/ConnectQRCode.png", -1, -1)

        img = Gtk.Image.new_from_pixbuf(pixbuf)
        self.content.add(img)

        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='xx-large'>" + self.code + "</span>")
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_line_wrap(True)
        self.content.add(label)

        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("Scan this QR code and continue on your mobile device.") + "\n" +
            _("Alternatively, you can visit") + " <span color='#7777FF'>prusa.io/add</span> " +
            _("and provide code manually") + "</span>")
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_line_wrap(True)
        self.content.add(label)

    def update_loop(self):
        r = requests.get(f"http://127.0.0.1:5001/connection").json()
        if "registration" in r:
            if r["registration"] == "FINISHED":
                self.wizard_manager.set_step(PrusConnectDone(self._screen))

    def on_back(self):
        self.wizard_manager.set_step(PrusaConnectDialog(self._screen))
        return True

class PrusConnectDone(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_back = True

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("prusa-connect-ok", self._screen.gtk.content_width * .945, 450)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" + _("Your Connect is configured successfully") + "</span>")
        self.content.add(heating_label)
        button = self._screen.gtk.Button(label=_("Continue"), style=f"color1")
        button.set_vexpand(False)
        button.connect("clicked", self.continue_pressed)
        self.content.add(button)

    def continue_pressed(self, widget):
        self.wizard_manager.set_step(Done(self._screen))

class Done(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_exit = False

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content.set_vexpand(True)
        img = self._screen.gtk.Image("success_combined", self._screen.gtk.content_width * .945, -1)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" +
            _("Printer was successfully configured.") + "</span>")
        heating_label.set_line_wrap(True)
        heating_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(heating_label)
        button = self._screen.gtk.Button(label=_("Continue"), style=f"color1")
        button.set_vexpand(False)
        button.connect("clicked", self.continue_pressed)
        self.content.add(button)

    def continue_pressed(self, widget):
        os.system("rm /opt/init_state")
        os.system("systemctl restart klipper-screen")