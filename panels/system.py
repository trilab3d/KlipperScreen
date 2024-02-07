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
        self.service_sequence = ""

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

        self.export_logs_button = self._gtk.Button('logs', _('Export Logs to USB'), 'color2')
        self.export_logs_button.connect("clicked", self.export_logs)
        self.export_logs_button.set_vexpand(False)
        self.export_logs_button.set_hexpand(True)

        scroll = self._gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        infogrid = Gtk.Grid()
        infogrid.get_style_context().add_class("system-program-grid")

        self.icon_ok = self._gtk.Image("complete", self._gtk.content_width * .9, self._gtk.content_height * .2)
        self.icon_update = self._gtk.Image("update-available", self._gtk.content_width * .9, self._gtk.content_height * .2)
        self.icon_update_usb = self._gtk.Image("update-available-usb", self._gtk.content_width * .9, self._gtk.content_height * .2)
        self.icon_downloading = self._gtk.Image("update-downloading", self._gtk.content_width * .9, self._gtk.content_height * .2)
        self.icon_unpacking = self._gtk.Image("unpacking", self._gtk.content_width * .9, self._gtk.content_height * .2)
        self.icon_unpacking_usb = self._gtk.Image("unpacking-usb", self._gtk.content_width * .9, self._gtk.content_height * .2)
        self.icon_installed = self._gtk.Image("info", self._gtk.content_width * .9, self._gtk.content_height * .2)
        self.icon_installed_usb = self._gtk.Image("info", self._gtk.content_width * .9, self._gtk.content_height * .2)
        self.icon_warning = self._gtk.Image("warning", self._gtk.content_width * .9, self._gtk.content_height * .2)

        self.icon_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.icon_box.set_hexpand(True)
        self.icon_box.set_vexpand(False)
        self.icon_box.set_homogeneous(True)
        self.icon_box.add(self.icon_ok)

        self.update_header = Gtk.Label()
        self.update_header.set_hexpand(True)  # align to center
        self.update_header.set_margin_top(40)
        self.update_label = Gtk.Label()
        self.update_label.set_hexpand(False)
        self.update_label.set_halign(Gtk.Align.START)
        self.update_label.set_margin_top(5)
        self.update_label.set_line_wrap(True)
        self.release_notes_label = Gtk.Label()
        self.release_notes_label.set_line_wrap(True)
        #self.release_notes_label.set_margin_top(5)
        self.release_notes_label.set_halign(Gtk.Align.START)


        self.progress = Gtk.ProgressBar()
        self.progress.set_fraction(0)
        self.progress.set_show_text(False)
        self.progress.set_hexpand(True)
        #self.progress.get_style_context().add_class("progressbar_thin")

        self.progress_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.progress_box.set_hexpand(True)
        self.progress_box.set_vexpand(False)
        self.progress_box.set_homogeneous(True)

        self.button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.button_box.set_hexpand(True)
        self.button_box.set_vexpand(False)
        self.button_box.set_homogeneous(True)

        self.get_updates()
        GLib.timeout_add_seconds(3, self.get_updates)

        event_box_icon = Gtk.EventBox()
        event_box_icon.set_margin_top(20)
        event_box_icon.add(self.icon_box)
        event_box_icon.connect("button-press-event", self.service_sequence_add, "I")

        event_box_labels = Gtk.EventBox()
        grid_text = Gtk.Grid()
        grid_labels = Gtk.Grid()
        grid_labels.set_halign(Gtk.Align.CENTER)
        event_box_labels.set_margin_top(20)
        event_box_labels.add(grid_text)
        #grid_text.attach(self.update_header, 0, 0, 1, 1)
        grid_text.attach(grid_labels, 0, 1, 1, 1)
        grid_labels.attach(self.progress_box, 0, 0, 1, 1)
        grid_labels.attach(self.update_label, 0, 1, 1, 1)
        grid_labels.attach(self.release_notes_label, 0, 2, 1, 1)
        event_box_labels.connect("button-press-event", self.service_sequence_add, "L")

        infogrid.attach(self.update_header, 0, 0, 1, 1)
        infogrid.attach(event_box_icon, 0, 1, 1, 1)
        infogrid.attach(event_box_labels, 0, 2, 1, 1)

        scroll.add(infogrid)

        grid.attach(scroll, 0, 0, 1, 1)
        grid.attach(self.button_box, 0, 1, 1, 1)
        self.content.add(grid)

    def activate(self):
        self.do_schedule_refresh = True
        self.get_updates()
        self.service_sequence = ""
        GLib.timeout_add_seconds(3, self.get_updates)

    def deactivate(self):
        self.do_schedule_refresh = False

    def get_updates(self):
        self.fetch_settings()
        is_printing = self._screen.printer.data['print_stats']['state'] == 'printing'
        try:
            update_resp = self._screen.tpcclient.send_request(f"check_update")
            #logging.info(f"update_resp: {update_resp}")
            for child in self.button_box.get_children():
                self.button_box.remove(child)
            for child in self.progress_box.get_children():
                self.progress_box.remove(child)
            for child in self.icon_box.get_children():
                self.icon_box.remove(child)
            if update_resp["update_status"] == "UPDATE_AVAILABLE":
                self.update_header.set_markup("<span size='xx-large'>"+_("New update available")+"</span>")
                self.update_label.set_markup(f"<b>{_('Current version')}</b>: {update_resp['current_version']}\n"
                                            f"<b>{_('Update version')}</b>: {update_resp['update_version']}")
                self.release_notes_label.set_markup(f"<b>{_('Release notes')}</b>:\n{update_resp['release_notes']}")
                self.icon_box.add(self.icon_update)
                self.button_box.add(self.download_button)
            elif update_resp["update_status"] == "DOWNLOADING":
                self.update_header.set_markup("<span size='xx-large'>"+_("Downloading")+f" ({int(float(update_resp['progress']))}%)</span>")
                self.update_label.set_markup(f"<b>{_('Current version')}</b>: {update_resp['current_version']}\n"
                                            f"<b>{_('Update version')}</b>: {update_resp['update_version']}")
                self.release_notes_label.set_markup(f"<b>{_('Release notes')}</b>:\n{update_resp['release_notes']}")
                self.icon_box.add(self.icon_downloading)
                self.progress.set_fraction(float(update_resp['progress'])/100)
                self.progress_box.add(self.progress)
            elif update_resp["update_status"] == "UNPACKING":
                self.update_header.set_markup("<span size='xx-large'>"+_("Unpacking")+f" ({int(float(update_resp['progress']))}%)</span>")
                self.update_label.set_markup(f"<b>{_('Current version')}</b>: {update_resp['current_version']}\n"
                                            f"<b>{_('Update version')}</b>: {update_resp['update_version']}")
                self.release_notes_label.set_markup(f"<b>{_('Release notes')}</b>:\n{update_resp['release_notes']}")
                self.icon_box.add(self.icon_unpacking)
                self.progress.set_fraction(float(update_resp['progress']) / 100)
                self.progress_box.add(self.progress)
            elif update_resp["update_status"] == "INSTALLED":
                self.update_header.set_markup("<span size='xx-large'>"+_("Update ready")+"</span>")
                self.update_label.set_markup(f"<b>{_('Current version')}</b>: {update_resp['current_version']}\n"
                                            f"<b>{_('Update version')}</b>: {update_resp['update_version']}")
                self.release_notes_label.set_markup(f"<b>{_('Release notes')}</b>:\n{update_resp['release_notes']}")
                self.icon_box.add(self.icon_installed)
                self.progress.set_fraction(1)
                self.progress_box.add(self.progress)
                self.button_box.add(self.update_button)
                self.button_box.add(self.export_logs_button)
                self.update_button.set_sensitive(not is_printing)
            elif update_resp["update_status"] == "UP_TO_DATE":
                self.update_header.set_markup("<span size='xx-large'>"+_("System is up to date")+"</span>")
                self.update_label.set_markup(f"<b>{_('Current version')}</b>: {update_resp['current_version']}")
                self.release_notes_label.set_label("")
                self.icon_box.add(self.icon_ok)
                self.button_box.add(self.refresh_button)
                self.button_box.add(self.export_logs_button)
            elif update_resp["update_status"] == "DOWNLOAD_FAILED":
                self.update_header.set_markup("<span size='xx-large'>"+_("Download failed")+"</span>")
                self.update_label.set_markup(f"<b>{_('Current version')}</b>: {update_resp['current_version']}\n"
                                            f"<b>{_('Update version')}</b>: {update_resp['update_version']}")
                self.release_notes_label.set_markup(f"<b>{_('Release notes')}</b>:\n{update_resp['release_notes']}")
                self.icon_box.add(self.icon_warning)
                self.button_box.add(self.download_button)
                self.button_box.add(self.export_logs_button)
            elif update_resp["update_status"] == "USB_UPDATE_AVAILABLE":
                self.update_header.set_markup("<span size='xx-large'>"+_("Update found on USB")+"</span>")
                self.update_label.set_markup(f"<b>{_('Current version')}</b>: {update_resp['current_version']}\n"
                                            f"<b>{_('Update version')}</b>: {update_resp['update_version']}")
                self.release_notes_label.set_label("")
                self.icon_box.add(self.icon_update_usb)
                self.button_box.add(self.install_usb_button)
                self.button_box.add(self.export_logs_button)
            elif update_resp["update_status"] == "USB_UNPACKING":
                self.update_header.set_markup("<span size='xx-large'>"+_("Unpacking")+f" ({int(float(update_resp['progress']))}%)</span>")
                self.update_label.set_markup(f"<b>{_('Current version')}</b>: {update_resp['current_version']}\n"
                                            f"<b>{_('Update version')}</b>: {update_resp['update_version']}\n")
                self.release_notes_label.set_label("")
                self.icon_box.add(self.icon_unpacking_usb)
                self.progress.set_fraction(float(update_resp['progress']) / 100)
                self.progress_box.add(self.progress)
                self.button_box.add(self.export_logs_button)
            elif update_resp["update_status"] == "USB_INSTALLED":
                self.update_header.set_markup("<span size='xx-large'>"+_("USB update ready")+"</span>")
                self.update_label.set_markup(f"<b>{_('Current version')}</b>: {update_resp['current_version']}\n"
                                            f"<b>{_('Update version')}</b>: {update_resp['update_version']}")
                self.release_notes_label.set_label("")
                self.icon_box.add(self.icon_installed_usb)
                self.button_box.add(self.update_button)
                self.button_box.add(self.discard_usb_button)
                is_printing = self._screen.printer.data['print_stats']['state'] == 'printing'
                self.update_button.set_sensitive(not is_printing)
                self.button_box.add(self.export_logs_button)
            else:
                self.update_header.set_markup("")
                self.update_label.set_label("")
                self.release_notes_label.set_label("")
                self.button_box.add(self.export_logs_button)
        except Exception as e:
            logging.error(e)
            self.update_header.set_markup("")
            self.update_label.set_label("")

        #self._screen.close_popup_message()
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

    def export_logs(self, widget):
        if not os.path.exists("/mnt/part4/opt/gcodes/usb"):
            self._screen.show_popup_message("USB storage missing", 3)
            return
        os.system("rm -rf /tmp/log-export")
        os.system("mkdir /tmp/log-export")
        os.system("cp /tmp/moonraker.log* /tmp/log-export")
        os.system("cp /tmp/klippy.log* /tmp/log-export")
        os.system("cp /tmp/tpc.log /tmp/log-export")
        p = os.popen("echo $(hostname)-logs-$(date +%m%b%y-%H-%M-%S).tar.gz",'r',1)
        filename = p.read().strip()
        p.close()
        os.system(f"tar -C /tmp/ -czvf /tmp/log-export/{filename} log-export")
        os.system("cp /tmp/log-export/*.tar.gz /mnt/part4/opt/gcodes/usb")
        os.system(f"sync")
        self._screen.show_popup_message(f"Logs exported to {filename}", 1)

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

    def fetch_settings(self):
        settings = self._screen.tpcclient.send_request("/settings")

    def service_sequence_add(self, widget, argument, letter):
        self.service_sequence += letter
        logging.info(f"Service sequence: {self.service_sequence}")
        if self.service_sequence == "LLILLII":
            self._config.set("main", "view_group", "service")
            self._screen.reload_panels()