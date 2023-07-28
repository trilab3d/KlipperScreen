import logging
import os

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango, GLib

from ks_includes.screen_panel import ScreenPanel


def create_panel(*args):
    return SystemPanel(*args)


# Same as ALLOWED_SERVICES in moonraker
# https://github.com/Arksine/moonraker/blob/master/moonraker/components/machine.py
ALLOWED_SERVICES = (
    "crowsnest",
    "MoonCord",
    "moonraker",
    "moonraker-telegram-bot",
    "klipper",
    "KlipperScreen",
    "sonar",
    "webcamd",
)


class SystemPanel(ScreenPanel):
    def __init__(self, screen, title):
        super().__init__(screen, title)
        self.refresh = None
        self.update_dialog = None
        grid = self._gtk.HomogeneousGrid()
        grid.set_row_homogeneous(False)

        self.update_all = self._gtk.Button('arrow-up', _('Full Update'), 'color1')
        self.update_all.set_label(_('Update'))
        self.update_all.connect("clicked", self.show_update_info)
        self.update_all.set_vexpand(False)
        self.refresh = self._gtk.Button('refresh', _('Refresh'), 'color2')
        self.refresh.connect("clicked", self.refresh_updates)
        self.refresh.set_vexpand(False)

        reboot = self._gtk.Button('refresh', _('Restart'), 'color3')
        reboot.connect("clicked", self.reboot_poweroff, "reboot")
        reboot.set_vexpand(False)
        shutdown = self._gtk.Button('shutdown', _('Shutdown'), 'color4')
        shutdown.connect("clicked", self.reboot_poweroff, "poweroff")
        shutdown.set_vexpand(False)

        scroll = self._gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        infogrid = Gtk.Grid()
        infogrid.get_style_context().add_class("system-program-grid")

        self.update_header = Gtk.Label()
        self.update_label = Gtk.Label()
        self.update_header.set_hexpand(True)  # align to center
        self.update_label.set_hexpand(False)
        self.update_label.set_line_wrap(True)
        self.update_header.set_margin_top(60)

        self.get_updates()

        infogrid.attach(self.update_header, 0, 0, 1, 1)
        infogrid.attach(self.update_label, 0, 1, 1, 1)


        scroll.add(infogrid)

        grid.attach(scroll, 0, 0, 1, 1)
        grid.attach(self.update_all, 0, 1, 1, 1)
        grid.attach(self.refresh, 0, 2, 1, 1)
        grid.attach(reboot, 0, 3, 1, 1)
        grid.attach(shutdown, 0, 4, 1, 1)
        self.content.add(grid)

    def activate(self):
        self.get_updates()

    def refresh_updates(self, widget=None):
        self.refresh.set_sensitive(False)
        self._screen.show_popup_message(_("Checking for updates, please wait..."), level=1)
        GLib.timeout_add_seconds(1, self.get_updates)

    def get_updates(self):
        update_resp = self._screen.tpcclient.send_request(f"check_update")
        if update_resp["download_pending"]:
            self.update_header.set_markup("<span size='xx-large'>Update available</span>")
            self.update_label.set_label(f"Current version: {update_resp['current_version']}")
            self.update_all.set_label(_('Download and Update'))
        elif update_resp["update_available"]:
            self.update_header.set_markup("<span size='xx-large'>Update available</span>")
            self.update_label.set_label(f"Current version: {update_resp['current_version']}\n"
                                        f"Update version: {update_resp['update_version']}\n"
                                        f"Changelog:\n{update_resp['release_notes']}")
            self.update_all.set_label(_('Update'))
            self.update_all.set_sensitive(True)
        else:
            self.update_header.set_markup("<span size='xx-large'>No update available</span>")
            self.update_label.set_label(f"Current version: {update_resp['current_version']}")
            self.update_all.set_label(_('Update'))
            self.update_all.set_sensitive(False)

        self.refresh.set_sensitive(True)
        self._screen.close_popup_message()

    def show_update_info(self, widget):

        scroll = self._gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox.set_halign(Gtk.Align.CENTER)
        vbox.set_valign(Gtk.Align.CENTER)

        label = Gtk.Label()
        label.set_line_wrap(True)

        label.set_markup('<b>' + _("Perform a full upgrade?") + '</b>')
        vbox.add(label)

        scroll.add(vbox)

        buttons = [
            {"name": _("Update"), "response": Gtk.ResponseType.OK},
            {"name": _("Cancel"), "response": Gtk.ResponseType.CANCEL}
        ]
        dialog = self._gtk.Dialog(self._screen, buttons, scroll, self.update_confirm)
        dialog.set_title(_("Update"))

    def restart(self, widget, program):
        if program not in ALLOWED_SERVICES:
            return

        logging.info(f"Restarting service: {program}")
        self._screen._ws.send_method("machine.services.restart", {"service": program})

    def update_confirm(self, dialog, response_id):
        self._gtk.remove_dialog(dialog)
        if response_id == Gtk.ResponseType.OK:
            logging.debug(f"Updating system...")
            self._screen.tpcclient.send_request("perform_update","POST")

    def reset_confirm(self, dialog, response_id, program):
        self._gtk.remove_dialog(dialog)
        if response_id == Gtk.ResponseType.OK:
            logging.debug(f"Recovering hard {program}")
            self.reset_repo(self, program, True)
        if response_id == Gtk.ResponseType.APPLY:
            logging.debug(f"Recovering soft {program}")
            self.reset_repo(self, program, False)

    def reset_repo(self, widget, program, hard):
        if self._screen.updating:
            return
        self._screen.base_panel.show_update_dialog()
        msg = _("Starting recovery for") + f' {program}...'
        self._screen._websocket_callback("notify_update_response",
                                         {'application': {program}, 'message': msg, 'complete': False})
        logging.info(f"Sending machine.update.recover name: {program} hard: {hard}")
        self._screen._ws.send_method("machine.update.recover", {"name": program, "hard": hard})

    def reboot_poweroff(self, widget, method):
        scroll = self._gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox.set_halign(Gtk.Align.CENTER)
        vbox.set_valign(Gtk.Align.CENTER)
        if method == "reboot":
            label = Gtk.Label(label=_("Are you sure you wish to reboot the system?"))
        else:
            label = Gtk.Label(label=_("Are you sure you wish to shutdown the system?"))
        vbox.add(label)
        scroll.add(vbox)
        buttons = [
            {"name": _("OK"), "response": Gtk.ResponseType.OK},
            {"name": _("Cancel"), "response": Gtk.ResponseType.CANCEL}
        ]
        dialog = self._gtk.Dialog(self._screen, buttons, scroll, self.reboot_poweroff_confirm, method)
        if method == "reboot":
            dialog.set_title(_("Restart"))
        else:
            dialog.set_title(_("Shutdown"))

    def reboot_poweroff_confirm(self, dialog, response_id, method):
        self._gtk.remove_dialog(dialog)
        if response_id == Gtk.ResponseType.OK:
            if method == "reboot":
                os.system("systemctl reboot")
            else:
                os.system("systemctl poweroff")
        elif response_id == Gtk.ResponseType.APPLY:
            if method == "reboot":
                self._screen._ws.send_method("machine.reboot")
            else:
                self._screen._ws.send_method("machine.shutdown")
