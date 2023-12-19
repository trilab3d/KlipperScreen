import logging
import os

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango, GLib, Gdk

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
        self.do_schedule_refresh = True
        self.service_counter = 0

        self.refresh_button = self._gtk.Button('refresh', _('Refresh'), 'color1')
        self.refresh_button.connect("clicked", self.refresh_omaha)
        self.refresh_button.set_vexpand(False)
        self.refresh_button.set_hexpand(True)

        self.download_button = self._gtk.Button('arrow-down', _('Download'), 'color1')
        self.download_button.connect("clicked", self.download)
        self.download_button.set_vexpand(False)
        self.download_button.set_hexpand(True)

        self.update_button = self._gtk.Button('arrow-up', _('Update'), 'color2')
        self.update_button.connect("clicked", self.show_update_info)
        self.update_button.set_vexpand(False)
        self.update_button.set_hexpand(True)

        self.install_usb_button = self._gtk.Button('arrow-right', _('Install'), 'color1')
        self.install_usb_button.connect("clicked", self.install_usb_update)
        self.install_usb_button.set_vexpand(False)
        self.install_usb_button.set_hexpand(True)

        self.discard_usb_button = self._gtk.Button('arrow-left', _('Discard'), 'color1')
        self.discard_usb_button.connect("clicked", self.discard_usb_update)
        self.discard_usb_button.set_vexpand(False)
        self.discard_usb_button.set_hexpand(True)

        self.reboot = self._gtk.Button('refresh', _('Restart'), 'color3')
        self.reboot.connect("clicked", self.reboot_poweroff, "reboot")
        self.reboot.set_vexpand(False)
        #shutdown = self._gtk.Button('shutdown', _('Shutdown'), 'color4')
        #shutdown.connect("clicked", self.reboot_poweroff, "poweroff")
        #shutdown.set_vexpand(False)

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

        self.button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.button_box.set_hexpand(True)
        self.button_box.set_vexpand(False)
        #self.button_box.set_halign(Gtk.Align.CENTER)
        self.button_box.set_homogeneous(True)
        #self.button_box.set_size_request(self._gtk.content_width, -1)

        self.get_updates()
        GLib.timeout_add_seconds(3, self.get_updates)

        infogrid.attach(self.update_header, 0, 0, 1, 1)
        infogrid.attach(self.update_label, 0, 1, 1, 1)

        scroll.add(infogrid)

        event_box = Gtk.EventBox()
        event_box.add(scroll)
        event_box.connect("button-press-event", self.header_clicked)

        grid.attach(event_box, 0, 0, 1, 1)
        grid.attach(self.button_box, 0, 1, 1, 1)
        grid.attach(self.reboot, 0, 2, 1, 1)
        #grid.attach(shutdown, 0, 4, 1, 1)
        self.content.add(grid)

    def activate(self):
        self.do_schedule_refresh = True
        self.get_updates()
        self.service_counter = 0
        GLib.timeout_add_seconds(3, self.get_updates)

    def deactivate(self):
        self.do_schedule_refresh = False

    def get_updates(self):
        self.fetch_settings()
        is_printing = self._screen.printer.data['print_stats']['state'] == 'printing'
        self.reboot.set_sensitive(not is_printing)
        try:
            update_resp = self._screen.tpcclient.send_request(f"check_update")
            #logging.info(f"update_resp: {update_resp}")
            for child in self.button_box.get_children():
                self.button_box.remove(child)
            if update_resp["update_status"] == "UPDATE_AVAILABLE":
                self.update_header.set_markup("<span size='xx-large'>"+_("New update available")+"</span>")
                self.update_label.set_label(f"{_('Current version')}: {update_resp['current_version']}\n"
                                            f"{_('Update version')}: {update_resp['update_version']}\n"
                                            f"{_('Release notes')}:\n{update_resp['release_notes']}")
                self.button_box.add(self.download_button)
            elif update_resp["update_status"] == "DOWNLOADING":
                self.update_header.set_markup("<span size='xx-large'>"+_("Downloading")+"</span>")
                self.update_label.set_label(f"{_('Current version')}: {update_resp['current_version']}\n"
                                            f"{_('Update version')}: {update_resp['update_version']}\n"
                                            f"{_('Progress')}: {update_resp['progress']*100}%\n"
                                            f"{_('Release notes')}:\n{update_resp['release_notes']}")
            elif update_resp["update_status"] == "UNPACKING":
                self.update_header.set_markup("<span size='xx-large'>"+_("Unpacking")+"</span>")
                self.update_label.set_label(f"{_('Current version')}: {update_resp['current_version']}\n"
                                            f"{_('Update version')}: {update_resp['update_version']}\n"
                                            f"{_('Progress')}: {update_resp['progress']}%\n"
                                            f"{_('Release notes')}:\n{update_resp['release_notes']}")
            elif update_resp["update_status"] == "INSTALLED":
                self.update_header.set_markup("<span size='xx-large'>"+_("Update ready")+"</span>")
                self.update_label.set_label(f"{_('Current version')}: {update_resp['current_version']}\n"
                                            f"{_('Update version')}: {update_resp['update_version']}\n"
                                            f"{_('Release notes')}:\n{update_resp['release_notes']}")
                self.button_box.add(self.update_button)
                self.update_button.set_sensitive(not is_printing)
            elif update_resp["update_status"] == "UP_TO_DATE":
                self.update_header.set_markup("<span size='xx-large'>"+_("System is up to date")+"</span>")
                self.update_label.set_label(f"{_('Current version')}: {update_resp['current_version']}")
                self.button_box.add(self.refresh_button)
            elif update_resp["update_status"] == "DOWNLOAD_FAILED":
                self.update_header.set_markup("<span size='xx-large'>"+_("Download failed")+"</span>")
                self.update_label.set_label(f"{_('Current version')}: {update_resp['current_version']}\n"
                                            f"{_('Update version')}: {update_resp['update_version']}\n"
                                            f"{_('Release notes')}:\n{update_resp['release_notes']}")
                self.button_box.add(self.download_button)
            elif update_resp["update_status"] == "USB_UPDATE_AVAILABLE":
                self.update_header.set_markup("<span size='xx-large'>"+_("Update found on USB")+"</span>")
                self.update_label.set_label(f"{_('Current version')}: {update_resp['current_version']}\n"
                                            f"{_('Update version')}: {update_resp['update_version']}")
                self.button_box.add(self.install_usb_button)
            elif update_resp["update_status"] == "USB_UNPACKING":
                self.update_header.set_markup("<span size='xx-large'>"+_("Unpacking")+"</span>")
                self.update_label.set_label(f"{_('Current version')}: {update_resp['current_version']}\n"
                                            f"{_('Update version')}: {update_resp['update_version']}")
            elif update_resp["update_status"] == "USB_INSTALLED":
                self.update_header.set_markup("<span size='xx-large'>"+_("USB update ready")+"</span>")
                self.update_label.set_label(f"{_('Current version')}: {update_resp['current_version']}\n"
                                            f"{_('Update version')}: {update_resp['update_version']}")
                self.button_box.add(self.update_button)
                self.button_box.add(self.discard_usb_button)
                is_printing = self._screen.printer.data['print_stats']['state'] == 'printing'
                self.update_button.set_sensitive(not is_printing)
            else:
                self.update_header.set_markup("")
                self.update_label.set_label("")
        except:
            self.update_header.set_markup("")
            self.update_label.set_label("")

        self._screen.close_popup_message()
        self.content.show_all()
        return self.do_schedule_refresh

    def download(self, widget):
        self._screen.tpcclient.send_request(f"download_update","POST")

    def refresh_omaha(self, widget):
        self._screen.tpcclient.send_request(f"refresh_updater", "POST")

    def install_usb_update(self, widget):
        self._screen.tpcclient.send_request(f"install_usb_update","POST")

    def discard_usb_update(self, widget):
        self._screen.tpcclient.send_request(f"discard_usb_update","POST")

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
        if self.service_counter == 7:
            self._config.set("main", "view_group", "service")
            self._screen.reload_panels()
            return
        else:
            self.service_counter = 0
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


    def fetch_settings(self):
        settings = self._screen.tpcclient.send_request("/settings")

    def header_clicked(self, widget, argument):
        self.service_counter += 1
        logging.info(f"Service counter: {self.service_counter}")