import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, Pango
import os
import logging
import configparser
from WizardSteps.baseWizardStep import BaseWizardStep

SEARCH_PATH = "/mnt/part4/opt/gcodes/usb/"
#SEARCH_PATH = "/home/thugmek/Desktop/usb-mockup/"

IMPORTABLE_UNITS = ["service::connect"]
REQUIRED_OPTIONS = {"service::connect": ["hostname", "tls", "port", "token"]}

class SelectFile(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_back = True

    def activate(self, wizard):
        super().activate(wizard)
        self.content = self._screen.gtk.ScrolledWindow()
        self.content.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.content.add(box)

        if not os.path.exists(SEARCH_PATH):
            self.wizard_manager.set_step(NoUSB(self._screen))

        self.files = []
        for file in os.listdir(SEARCH_PATH):
            logging.info(file)
            if file.endswith(".ini") or file.endswith(".htnb"):
                self.files.append(file)

        logging.info(self.files)

        for file in self.files:
            name = Gtk.Label()
            name.set_markup(f"<big><b>{file}</b></big>")
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
            select = self._screen.gtk.Button("load", style="color3")
            select.connect("clicked", self.select_file, file)
            select.set_hexpand(False)
            select.set_halign(Gtk.Align.END)
            dev.add(select)

            box.add(dev)
    def select_file(self, widget, file):
        if file.endswith(".htnb"):
            self.wizard_manager.set_step(PersistentArchiveDetail(self._screen, file))
        else:
            self.wizard_manager.set_step(ConfigDetail(self._screen, file))

class NoUSB(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_back = True

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("placeholder43", self._screen.gtk.content_width * .945,-1)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("No USB disk found") + "</span>")
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(label)
        continue_button = self._screen.gtk.Button(label=_("Retry"), style=f"color1")
        continue_button.set_vexpand(False)
        continue_button.connect("clicked", self.continue_pressed)
        self.content.add(continue_button)

    def continue_pressed(self, widget):
        self.wizard_manager.set_step(SelectFile(self._screen))

class ConfigDetail(BaseWizardStep):
    def __init__(self, screen, file):
        super().__init__(screen)
        self.can_back = True
        self.file = file

    def activate(self, wizard):
        super().activate(wizard)

        self.varfile = configparser.ConfigParser()
        logging.info("reading saved_variables")
        try:
            self.varfile.read(SEARCH_PATH + self.file)
        except:
            self.wizard_manager.set_step(InvalidFile(self._screen, self.file))
            return
        logging.info(f"varfile.sections(): {self.varfile.sections()}")

        self.sections = []
        for section in self.varfile.sections():
            if section in IMPORTABLE_UNITS:
                self.sections.append(section)

        if len(self.sections) == 0:
            self.wizard_manager.set_step(InvalidFile(self._screen, self.file))
            return

        logging.info(f"Importable sections: {self.sections}")
        for section in self.sections:
            options = self.varfile.options(section)
            for opt in REQUIRED_OPTIONS[section]:
                if opt not in options:
                    self.wizard_manager.set_step(InvalidFile(self._screen, self.file))
                    return

        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("placeholder43", self._screen.gtk.content_width * .945,-1)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("Found valid config file.") + "</span>")
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(label)
        button = self._screen.gtk.Button(label=_("Import"), style=f"color1")
        button.set_vexpand(False)
        button.connect("clicked", self.import_pressed)
        self.content.add(button)

    def on_back(self):
        self.wizard_manager.set_step(SelectFile(self._screen))
        return True

    def import_pressed(self, widget):
        logging.info(f"import_pressed")
        for section in self.sections:
            logging.info(f"section: {section}")
            if section == "service::connect":
                try:
                    self._screen.tpcclient.send_request(f"settings", "POST", body={
                        "connect": {
                            "enable": True,
                            "hostname": self.varfile.get(section,"hostname"),
                            "port": self.varfile.getint(section,"port"),
                            "tls": self.varfile.getboolean(section,"tls"),
                            "token": self.varfile.get(section,"token"),
                            "camera_token": ""
                        }})
                    os.system("systemctl restart prusa-connect-ht90")
                    self.wizard_manager.set_step(ImportSucesfull(self._screen))
                except:
                    self._screen.show_popup_message("Import config failed", 3)
                    return

class PersistentArchiveDetail(BaseWizardStep):
    def __init__(self, screen, file):
        super().__init__(screen)
        self.can_back = True
        self.file = file

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("placeholder43", self._screen.gtk.content_width * .945,-1)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("Found persistent bundle") + "</span>")
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(label)
        button = self._screen.gtk.Button(label=_("Import"), style=f"color1")
        button.set_vexpand(False)
        button.connect("clicked", self.import_pressed)
        self.content.add(button)

    def on_back(self):
        self.wizard_manager.set_step(SelectFile(self._screen))
        return True

    def import_pressed(self, widget):
        logging.info(f"PersistentArchiveDetail.import_pressed. file:{self.file}")
        os.system(f"tar xf {SEARCH_PATH+self.file} -C /")
        os.system("/etc/init.d/network-manager reload")
        os.system("/etc/init.d/network-manager restart")
        os.system("nmcli connection reload")
        os.system("hostname $(cat /opt/hostname)")
        os.system("reboot")

class InvalidFile(BaseWizardStep):
    def __init__(self, screen, file):
        super().__init__(screen)
        self.can_back = True
        self.file = file

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("placeholder43", self._screen.gtk.content_width * .945,-1)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("File") + f" {self.file} " + _("is invalid") + "</span>")
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(label)

    def on_back(self):
        self.wizard_manager.set_step(SelectFile(self._screen))
        return True

class ImportSucesfull(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_back = True

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("placeholder43", self._screen.gtk.content_width * .945,-1)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("Config file was imported successfully") + "</span>")
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(label)

