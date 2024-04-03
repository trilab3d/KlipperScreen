import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
from threading import Thread
import os
import logging
import requests

from WizardSteps.baseWizardStep import BaseWizardStep

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
        self.wizard_manager.set_step(TermsAndConditions(self._screen))

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
        img = self._screen.gtk.Image("placeholder43", self._screen.gtk.content_width * .945,-1)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" + _("Network Configuration") + "</span>")
        heating_label.set_line_wrap(True)
        heating_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(heating_label)
        button = self._screen.gtk.Button(label=_("Configure Wired Connection"), style=f"color1")
        button.set_vexpand(False)
        button.connect("clicked", self.configure_wired)
        self.content.add(button)
        button = self._screen.gtk.Button(label=_("Configure Wireless Connection"), style=f"color1")
        button.set_vexpand(False)
        button.connect("clicked", self.configure_wireless)
        self.content.add(button)
        button = self._screen.gtk.Button(label=_("Skip network configuration"), style=f"color1")
        button.set_vexpand(False)
        button.connect("clicked", self.skip_pressed)
        self.content.add(button)

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

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content.set_vexpand(True)
        img = self._screen.gtk.Image("placeholder43", self._screen.gtk.content_width * .945,-1)
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


class WirelessNetwork(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_exit = False

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content.set_vexpand(True)
        img = self._screen.gtk.Image("placeholder43", self._screen.gtk.content_width * .945,-1)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" + _("TODO...") + "</span>")
        heating_label.set_line_wrap(True)
        heating_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(heating_label)
        button = self._screen.gtk.Button(label=_("Continue"), style=f"color1")
        button.set_vexpand(False)
        button.connect("clicked", self.continue_pressed)
        self.content.add(button)

    def continue_pressed(self, widget):
        self.wizard_manager.set_step(NetworkTest(self._screen))

class NetworkTest(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_exit = False

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content.set_vexpand(True)
        img = self._screen.gtk.Image("placeholder43", self._screen.gtk.content_width * .945,-1)
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
            self.wizard_manager.set_step(NetworkTestSucesfull(self._screen))
        else:
            self.wizard_manager.set_step(NetworkTestFailure(self._screen))

class NetworkTestSucesfull(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_exit = False

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content.set_vexpand(True)
        img = self._screen.gtk.Image("placeholder43", self._screen.gtk.content_width * .945,-1)
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
        img = self._screen.gtk.Image("placeholder43", self._screen.gtk.content_width * .945,-1)
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
        img = self._screen.gtk.Image("placeholder43", self._screen.gtk.content_width * .945,-1)
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
        self.wizard_manager.set_step(NoNetworkWarning(self._screen))

class Privacy(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_exit = False

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content.set_vexpand(True)
        img = self._screen.gtk.Image("placeholder43", self._screen.gtk.content_width * .945,-1)
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
        # TODO
        self.wizard_manager.set_step(Done(self._screen))

    def recommended_pressed(self, widget):
        # TODO
        self.wizard_manager.set_step(Done(self._screen))

    def custom_pressed(self, widget):
        self.wizard_manager.set_step(PrivacyCustom(self._screen))

class PrivacyCustom(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_exit = False
        self.can_back = True

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content.set_vexpand(True)
        img = self._screen.gtk.Image("placeholder43", self._screen.gtk.content_width * .945,-1)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" +
            _("TODO...") + "</span>")
        heating_label.set_line_wrap(True)
        heating_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(heating_label)
        button = self._screen.gtk.Button(label=_("Reduced logging"), style=f"color1")
        button.set_vexpand(False)
        button = self._screen.gtk.Button(label=_("Continue"), style=f"color1")
        button.set_vexpand(False)
        button.connect("clicked", self.continue_pressed)
        self.content.add(button)

    def continue_pressed(self, widget):
        # TODO
        self.wizard_manager.set_step(Done(self._screen))

    def on_back(self):
        self.wizard_manager.set_step(Privacy(self._screen))
        return True


class Done(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_exit = False

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content.set_vexpand(True)
        img = self._screen.gtk.Image("placeholder43", self._screen.gtk.content_width * .945, -1)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" +
            _("Printer was configured.") + "</span>")
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