import logging
import secrets

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango

from WizardSteps.baseWizardStep import BaseWizardStep


DEFAULT_USER = "admin"


class PasswordRequired(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_back = False
        self.can_exit = False
        self.user_entry = None
        self.password_entry = None
        self.enabled_switch = None
        self.save_button = None

    def activate(self, wizard):
        super().activate(wizard)

        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        heading = self._screen.gtk.Label("")
        heading.set_margin_top(20)
        heading.set_markup(
            "<span size='large'>" + _("Web interface authentication") + "</span>")
        heading.set_line_wrap(True)
        heading.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(heading)

        info = self._screen.gtk.Label("")
        info.set_margin_top(20)
        info.set_margin_left(10)
        info.set_margin_right(10)
        info.set_markup(
            _("The web interface is unprotected. We want to make sure this is intended. "
              "Set a username and password, or disable authentication."
              "You can change this later in Settings/Security"))
        info.set_line_wrap(True)
        info.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(info)

        grid = self._screen.gtk.HomogeneousGrid()
        grid.set_hexpand(True)
        grid.set_margin_top(30)
        grid.set_margin_left(10)
        grid.set_margin_right(10)

        user_label = Gtk.Label(label=_("User:"))
        user_label.set_halign(Gtk.Align.END)
        self.user_entry = Gtk.Entry()
        self.user_entry.set_text(DEFAULT_USER)
        self.user_entry.connect("changed", self._on_field_changed)
        self.user_entry.connect("button-press-event", self._screen.show_keyboard)
        self.user_entry.set_hexpand(True)
        grid.attach(user_label, 0, 0, 1, 1)
        grid.attach(self.user_entry, 1, 0, 2, 1)

        password_label = Gtk.Label(label=_("Password:"))
        password_label.set_halign(Gtk.Align.END)
        self.password_entry = Gtk.Entry()
        self.password_entry.set_visibility(False)
        self.password_entry.connect("changed", self._on_field_changed)
        self.password_entry.connect("button-press-event", self._screen.show_keyboard)
        self.password_entry.set_hexpand(True)
        grid.attach(password_label, 0, 1, 1, 1)
        grid.attach(self.password_entry, 1, 1, 2, 1)

        enabled_label = Gtk.Label(label=_("Enabled:"))
        enabled_label.set_halign(Gtk.Align.END)
        self.enabled_switch = Gtk.Switch()
        self.enabled_switch.set_active(True)
        self.enabled_switch.set_halign(Gtk.Align.START)
        self.enabled_switch.connect("notify::active", self._on_switch_toggled)
        grid.attach(enabled_label, 0, 2, 1, 1)
        grid.attach(self.enabled_switch, 1, 2, 1, 1)

        scroll = self._screen.gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.add(grid)
        self.content.add(scroll)

        self.save_button = self._screen.gtk.Button(label=_("Save"), style="color1")
        self.save_button.set_vexpand(False)
        self.save_button.connect("clicked", self._save_pressed)
        self.content.add(self.save_button)

        self._update_save_sensitive()

    def _on_field_changed(self, _widget):
        self._update_save_sensitive()

    def _on_switch_toggled(self, switch, _gparam):
        self.password_entry.set_sensitive(switch.get_active())
        self._update_save_sensitive()

    def _update_save_sensitive(self):
        user = self.user_entry.get_text().strip()
        password = self.password_entry.get_text()
        enabled = self.enabled_switch.get_active()
        if enabled:
            self.save_button.set_sensitive(bool(user) and bool(password))
        else:
            self.save_button.set_sensitive(bool(user))

    def _save_pressed(self, _widget):
        user = self.user_entry.get_text().strip()
        enabled = self.enabled_switch.get_active()
        if enabled:
            password = self.password_entry.get_text()
        else:
            password = secrets.token_urlsafe(24)

        tpc = self._screen.tpcclient
        tpc.send_request("credentials", "POST", body={"user": user, "password": password})
        tpc.send_request("settings", "POST", body={"locked": enabled})

        self._screen.remove_keyboard()
        self._screen.state_ready()
