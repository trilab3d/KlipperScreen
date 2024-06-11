import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
from threading import Thread
import os
import logging
import requests

from panels.privacy import PRESET_FIELDS

from WizardSteps.baseWizardStep import BaseWizardStep

NOZZLE_DICTIONARY = {
    "HF": "HF",
    "ObX": "ObXidian",
    "HT": "HT"
}

class PrintDetail(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_exit = True
        self.can_back = True

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        filename = self.wizard_manager.title
        self.wizard_manager.set_wizard_data("filename", filename)
        fileinfo = self._screen.files.get_file_info(filename)
        pixbuf = self.wizard_manager.get_file_image(filename, self._screen.gtk.content_width * .945, self._screen.height * .6)
        if pixbuf is not None:
            img = Gtk.Image.new_from_pixbuf(pixbuf)
            img.set_vexpand(False)
        else:
            img = self._screen.gtk.Image("thumbnail", self._screen.gtk.content_width * .945, -1)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_margin_left(10)
        heating_label.set_margin_right(10)
        heating_label.set_markup(
            "<span size='x-large'>" + (filename if filename else "None") + "</span>")
        heating_label.set_line_wrap(True)
        heating_label.set_line_wrap_mode(Pango.WrapMode.CHAR)
        self.content.add(heating_label)

        info_box = Gtk.Box()
        info_box.set_hexpand(True)
        self.content.add(info_box)
        grid = self._screen.gtk.HomogeneousGrid()
        grid.set_margin_top(20)
        grid.set_vexpand(True)
        grid.set_hexpand(True)
        grid.set_row_homogeneous(False)
        info_box.add(grid)

        # filament
        fname = fileinfo["filament_name"].split('@')[0].strip() if "filament_name" in fileinfo else "UNKNOWN"
        ftype = fileinfo["filament_type"] if "filament_type" in fileinfo else "UNKNOWN"
        self.wizard_manager.set_wizard_data("filament_type", ftype)
        if ('save_variables' in self._screen.printer.data):
            save_variables = self._screen.printer.data['save_variables']['variables']
            floaded = save_variables['loaded_filament'] if 'loaded_filament' in save_variables else "NONE"
            floaded = floaded.replace("-","")
        else:
            floaded = "UNKNOWN"
        self.wizard_manager.set_wizard_data("filament_loaded", floaded)
        box = Gtk.Box()
        box.set_spacing(4)
        box.set_halign(Gtk.Align.START)
        box.set_orientation(Gtk.Orientation.VERTICAL)
        box.add(self._screen.gtk.Label(_("Filament"), "property-name", xalign=0.0))
        box2 = Gtk.Box()
        box2.set_spacing(4)
        box2.set_halign(Gtk.Align.START)
        box2.set_orientation(Gtk.Orientation.HORIZONTAL)
        lbl = self._screen.gtk.Label(ftype)
        box2.add(lbl)
        if ftype == floaded:
            img = self._screen.gtk.Image("complete", -1, 16)
            self.filament_ok = True
        else:
            img = self._screen.gtk.Image("cancel-orange", -1, 16)
            self.filament_ok = False
        box2.add(img)
        box.add(box2)
        box.set_margin_start(12)
        grid.attach(box, 0, 0, 1, 1)

        #Nozzle
        filament_notes = fileinfo["filament_notes"] if "filament_notes" in fileinfo else None
        nozzle_diameter = fileinfo["nozzle_diameter"] if "filament_notes" in fileinfo else None
        if filament_notes and nozzle_diameter and filament_notes in NOZZLE_DICTIONARY:
            nozzle_wanted = f"{nozzle_diameter} {NOZZLE_DICTIONARY[filament_notes]}"
        else:
            nozzle_wanted = "UNKNOWN"
        self.wizard_manager.set_wizard_data("nozzle_wanted", nozzle_wanted)
        if ('save_variables' in self._screen.printer.data):
            save_variables = self._screen.printer.data['save_variables']['variables']
            nozzle_current = save_variables['nozzle'] if 'nozzle' in save_variables else "NONE"
        else:
            nozzle_current = "UNKNOWN"
        self.wizard_manager.set_wizard_data("nozzle_current", nozzle_current)
        box = Gtk.Box()
        box.set_spacing(4)
        box.set_halign(Gtk.Align.START)
        box.set_orientation(Gtk.Orientation.VERTICAL)
        box.add(self._screen.gtk.Label(_("Nozzle"), "property-name", xalign=0.0))
        box2 = Gtk.Box()
        box2.set_spacing(4)
        box2.set_halign(Gtk.Align.START)
        box2.set_orientation(Gtk.Orientation.HORIZONTAL)
        lbl = self._screen.gtk.Label(nozzle_wanted)
        box2.add(lbl)
        if nozzle_current == nozzle_wanted:
            img = self._screen.gtk.Image("complete", -1, 16)
            self.nozzle_ok = True
        else:
            img = self._screen.gtk.Image("cancel-orange", -1, 16)
            self.nozzle_ok = False
        box2.add(img)
        box.add(box2)
        box.set_margin_start(12)
        grid.attach(box, 0, 1, 1, 1)

        # Estimated time
        box = Gtk.Box()
        box.set_spacing(4)
        box.set_halign(Gtk.Align.START)
        box.set_orientation(Gtk.Orientation.VERTICAL)
        box.add(self._screen.gtk.Label(_("Estimated time"), "property-name", xalign=0.0))
        box2 = Gtk.Box()
        box2.set_spacing(4)
        box2.set_halign(Gtk.Align.START)
        box2.set_orientation(Gtk.Orientation.HORIZONTAL)
        lbl = self._screen.gtk.Label("#TODO#")
        box2.add(lbl)
        box.add(box2)
        box.set_margin_start(12)
        grid.attach(box, 0, 2, 1, 1)

        # Filament usage
        fusage = fileinfo["filament_total"]/1000 if "filament_total" in fileinfo else -1
        box = Gtk.Box()
        box.set_spacing(4)
        box.set_halign(Gtk.Align.START)
        box.set_orientation(Gtk.Orientation.VERTICAL)
        box.add(self._screen.gtk.Label(_("Filament usage"), "property-name", xalign=0.0))
        box2 = Gtk.Box()
        box2.set_spacing(4)
        box2.set_halign(Gtk.Align.START)
        box2.set_orientation(Gtk.Orientation.HORIZONTAL)
        lbl = self._screen.gtk.Label(f"{fusage:.1f}m")
        box2.add(lbl)
        box.add(box2)
        box.set_margin_start(12)
        grid.attach(box, 1, 0, 1, 1)

        # Total weight
        tw = int(fileinfo["filament_weight_total"]) if "filament_weight_total" in fileinfo else -1
        box = Gtk.Box()
        box.set_spacing(4)
        box.set_halign(Gtk.Align.START)
        box.set_orientation(Gtk.Orientation.VERTICAL)
        box.add(self._screen.gtk.Label(_("Total weight"), "property-name", xalign=0.0))
        box2 = Gtk.Box()
        box2.set_spacing(4)
        box2.set_halign(Gtk.Align.START)
        box2.set_orientation(Gtk.Orientation.HORIZONTAL)
        lbl = self._screen.gtk.Label(f"{tw}g")
        box2.add(lbl)
        box.add(box2)
        box.set_margin_start(12)
        grid.attach(box, 1, 1, 1, 1)

        # Layer height
        lh = fileinfo["layer_height"] if "layer_height" in fileinfo else -1
        box = Gtk.Box()
        box.set_spacing(4)
        box.set_halign(Gtk.Align.START)
        box.set_orientation(Gtk.Orientation.VERTICAL)
        box.add(self._screen.gtk.Label(_("Layer height"), "property-name", xalign=0.0))
        box2 = Gtk.Box()
        box2.set_spacing(4)
        box2.set_halign(Gtk.Align.START)
        box2.set_orientation(Gtk.Orientation.HORIZONTAL)
        lbl = self._screen.gtk.Label(f"{lh}mm")
        box2.add(lbl)
        box.add(box2)
        box.set_margin_start(12)
        grid.attach(box, 1, 2, 1, 1)

        button_grid = self._screen.gtk.HomogeneousGrid(self._screen.gtk.width - 20, self._screen.gtk.width / 4 + 4)
        button_grid.set_vexpand(False)
        self.content.add(button_grid)

        if not self.filament_ok:
            if floaded == "NONE":
                button = self._screen.gtk.Button("filament", None, "color1")
                label = self._screen.gtk.Label("Load")
                button.connect("clicked", self.load_button_pressed)
                (width, height) = button.get_size_request()
                button.set_size_request(width, width)
                box = Gtk.Box()
                box.set_orientation(Gtk.Orientation.VERTICAL)
                box.add(button)
                box.add(label)
                button_grid.attach(box, 0, 0, 1, 1)
            else:
                button = self._screen.gtk.Button("filament", None, "color1")
                label = self._screen.gtk.Label("Unload")
                button.connect("clicked", self.unload_button_pressed)
                (width, height) = button.get_size_request()
                button.set_size_request(width, width)
                box = Gtk.Box()
                box.set_orientation(Gtk.Orientation.VERTICAL)
                box.add(button)
                box.add(label)
                button_grid.attach(box, 0, 0, 1, 1)

        if not self.nozzle_ok:
            button = self._screen.gtk.Button("revo", None, "color1")
            label = self._screen.gtk.Label("Nozzle Change")
            button.connect("clicked", self.nozzle_change_button_pressed)
            (width, height) = button.get_size_request()
            button.set_size_request(width, width)
            box = Gtk.Box()
            box.set_orientation(Gtk.Orientation.VERTICAL)
            box.add(button)
            box.add(label)
            button_grid.attach(box, 1, 0, 1, 1)

        button = self._screen.gtk.Button("print", None, "color1")
        label = self._screen.gtk.Label("Print")
        button.connect("clicked", self.print_pressed)
        (width, height) = button.get_size_request()
        button.set_size_request(width, width)
        box = Gtk.Box()
        box.set_orientation(Gtk.Orientation.VERTICAL)
        box.add(button)
        box.add(label)
        button_grid.attach(box, 2, 0, 1, 1)

    def nozzle_change_button_pressed(self, widget):
        self._screen.show_panel("Nozzle Change", "wizard", "Nozzle Change", 1, False,
                                wizard="changeNozzleSteps.CooldownPrompt", wizard_name="Nozzle Change")

    def load_button_pressed(self, widget):
        self._screen.show_panel("Load Filament", "wizard", "Load Filament", 1, False,
                                wizard="loadWizardSteps.CheckLoaded", wizard_name="Load Filament")

    def unload_button_pressed(self, widget):
        self._screen.show_panel("Unload Filament", "wizard", "Unload Filament", 1, False,
                                wizard="unloadWizardSteps.SelectFilament", wizard_name="Unload Filament")

    def print_pressed(self, widget):
        if self.nozzle_ok and self.filament_ok:
            filename = self.wizard_manager.get_wizard_data("filename")
            logging.info(f"Starting print: {filename}")
            self._screen._ws.klippy.print_start(filename)
        else:
            self.wizard_manager.set_step(MismatchDetected(self._screen))

class MismatchDetected(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_exit = True
        self.can_back = True

    def activate(self, wizard):
        super().activate(wizard)
        filename = self.wizard_manager.get_wizard_data("filename")
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("warning", self._screen.gtk.content_width * .945, self._screen.gtk.content_height * .3)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("Mismatch between actual printer configuration and selected file.") + "</span>")
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(label)

        grid = self._screen.gtk.HomogeneousGrid()
        grid.set_margin_top(20)
        grid.set_vexpand(True)
        grid.set_hexpand(True)
        grid.set_row_homogeneous(False)
        self.content.add(grid)

        box = Gtk.Box()
        box.set_spacing(4)
        box.set_halign(Gtk.Align.START)
        box.set_orientation(Gtk.Orientation.VERTICAL)
        lbl = self._screen.gtk.Label(f"Required", xalign=0.0)
        box.add(lbl)
        box.set_margin_bottom(8)
        box.set_margin_start(12)
        grid.attach(box, 0, 0, 1, 1)

        filament_type = self.wizard_manager.get_wizard_data("filament_type")
        filament_loaded = self.wizard_manager.get_wizard_data("filament_loaded")
        if filament_type != filament_loaded:
            box = Gtk.Box()
            box.set_spacing(4)
            box.set_halign(Gtk.Align.START)
            box.set_orientation(Gtk.Orientation.VERTICAL)
            box.add(self._screen.gtk.Label(_("Filament"), "property-name", xalign=0.0))
            lbl = self._screen.gtk.Label(self.wizard_manager.get_wizard_data("filament_type"), xalign=0.0)
            box.add(lbl)
            box.set_margin_start(12)
            grid.attach(box, 0, 1, 1, 1)

        nozzle_wanted = self.wizard_manager.get_wizard_data("nozzle_wanted")
        nozzle_current = self.wizard_manager.get_wizard_data("nozzle_current")
        if nozzle_current != nozzle_wanted:
            box = Gtk.Box()
            box.set_spacing(4)
            box.set_halign(Gtk.Align.START)
            box.set_orientation(Gtk.Orientation.VERTICAL)
            box.add(self._screen.gtk.Label(_("Nozzle"), "property-name", xalign=0.0))
            lbl = self._screen.gtk.Label(self.wizard_manager.get_wizard_data("nozzle_wanted"), xalign=0.0)
            box.add(lbl)
            box.set_margin_start(12)
            grid.attach(box, 0, 2, 1, 1)

        box = Gtk.Box()
        box.set_spacing(4)
        box.set_halign(Gtk.Align.START)
        box.set_orientation(Gtk.Orientation.VERTICAL)
        lbl = self._screen.gtk.Label(f"Actual", xalign=0.0)
        box.add(lbl)
        box.set_margin_bottom(8)
        box.set_margin_start(12)
        grid.attach(box, 1, 0, 1, 1)

        if filament_type != filament_loaded:
            box = Gtk.Box()
            box.set_spacing(4)
            box.set_halign(Gtk.Align.START)
            box.set_orientation(Gtk.Orientation.VERTICAL)
            box.add(self._screen.gtk.Label(_("Filament"), "property-name", xalign=0.0))
            filament_loaded = self.wizard_manager.get_wizard_data("filament_loaded")
            lbl = self._screen.gtk.Label(filament_loaded, xalign=0.0)
            box.add(lbl)
            box.set_margin_start(12)
            grid.attach(box, 1, 1, 1, 1)

        if nozzle_current != nozzle_wanted:
            box = Gtk.Box()
            box.set_spacing(4)
            box.set_halign(Gtk.Align.START)
            box.set_orientation(Gtk.Orientation.VERTICAL)
            box.add(self._screen.gtk.Label(_("Nozzle"), "property-name", xalign=0.0))
            lbl = self._screen.gtk.Label(nozzle_current, xalign=0.0)
            box.add(lbl)
            box.set_margin_start(12)
            grid.attach(box, 1, 2, 1, 1)

        if filament_type != filament_loaded:
            if filament_loaded == "NONE":
                nozzle_change_button = self._screen.gtk.Button(label=_("Open filament load wizard"), style=f"color1")
                nozzle_change_button.set_vexpand(False)
                nozzle_change_button.connect("clicked", self.load_button_pressed)
                self.content.add(nozzle_change_button)
            else:
                nozzle_change_button = self._screen.gtk.Button(label=_("Open filament unload wizard"), style=f"color1")
                nozzle_change_button.set_vexpand(False)
                nozzle_change_button.connect("clicked", self.unload_button_pressed)
                self.content.add(nozzle_change_button)

        if nozzle_current != nozzle_wanted:
            nozzle_change_button = self._screen.gtk.Button(label=_("Open nozzle change wizard"), style=f"color1")
            nozzle_change_button.set_vexpand(False)
            nozzle_change_button.connect("clicked", self.nozzle_change_button_pressed)
            self.content.add(nozzle_change_button)

        nozzle_change_button = self._screen.gtk.Button(label=_("Print anyway"), style=f"color1")
        nozzle_change_button.set_vexpand(False)
        nozzle_change_button.connect("clicked", self.print_button_pressed)
        self.content.add(nozzle_change_button)

    def nozzle_change_button_pressed(self, widget):
        self._screen.show_panel("Nozzle Change", "wizard", "Nozzle Change", 1, False,
                                wizard="changeNozzleSteps.CooldownPrompt", wizard_name="Nozzle Change")

    def load_button_pressed(self, widget):
        self._screen.show_panel("Load Filament", "wizard", "Load Filament", 1, False,
                                wizard="loadWizardSteps.CheckLoaded", wizard_name="Load Filament")

    def unload_button_pressed(self, widget):
        self._screen.show_panel("Unload Filament", "wizard", "Unload Filament", 1, False,
                                wizard="unloadWizardSteps.SelectFilament", wizard_name="Unload Filament")

    def print_button_pressed(self, widget):
        filename = self.wizard_manager.get_wizard_data("filename")
        logging.info(f"Starting print: {filename}")
        self._screen._ws.klippy.print_start(filename)