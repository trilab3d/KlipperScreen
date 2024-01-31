import os

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Pango

from ks_includes.screen_panel import ScreenPanel


def create_panel(*args):
    return SettingsPanel(*args)


class SettingsPanel(ScreenPanel):
    def __init__(self, screen, title):
        super().__init__(screen, title)
        self.do_schedule_refresh = True
        self.printers = self.settings = self.langs = {}
        self.menu = ['settings_menu']
        options = self._config.get_configurable_options().copy()
        #options.append({"lang": {
        #    "name": _("Language"),
        #    "type": "menu",
        #    "menu": "lang"
        #}})
        options.append({"time_zone": {
            "name": _("Time Zone"),
            "type": "panel",
            "panel_title": "Time Zone",
            "panel_type": "timezone"
        }})
        options.insert(0,{"hostname": {
            "name": _("Printer Name"),
            "type": "panel",
            "panel_title": "Hostname",
            "panel_type": "hostname"
        }})

        self.nonlocal_options = {
            "enable_door_sensor": {"name": _("Door sensor"), "type": "binary",
                                    "value_getter": self._door_sensor_getter, "callback": self._door_sensor_callback},
            "enable_filament_sensor": {"name": _("Filament sensor"), "type": "binary",
                                   "value_getter": self._filament_sensor_getter, "callback": self._filament_sensor_callback},
        }

        options.insert(1, {"enable_door_sensor": self.nonlocal_options["enable_door_sensor"]})
        options.insert(2, {"enable_filament_sensor": self.nonlocal_options["enable_filament_sensor"]})

        for nlo in self.nonlocal_options:
            self.nonlocal_options[nlo]["section"] = "_nonlocal"
            self.nonlocal_options[nlo]["label"] = None
            self.nonlocal_options[nlo]["control"] = None
            self.nonlocal_options[nlo]["update_deadtime"] = 0
            #obj = {}
            #obj[nlo] = self.nonlocal_options[nlo]
            #options.append(obj)

        self.labels['settings_menu'] = self._gtk.ScrolledWindow()
        self.labels['settings'] = Gtk.Grid()
        self.labels['settings_menu'].add(self.labels['settings'])
        for option in options:
            name = list(option)[0]
            # this can't be removed from config.py. KS won't start. I don't know why :/
            if (name == 'theme'
                    or (name == 'view_group' and self._config.get_main_config().get('view_group') == 'basic')
                    or (name == 'show_heater_power' and self._config.get_main_config().get('view_group') == 'basic')):
                continue
            self.add_option('settings', self.settings, name, option[name])

        self.labels['lang_menu'] = self._gtk.ScrolledWindow()
        self.labels['lang'] = Gtk.Grid()
        self.labels['lang_menu'].add(self.labels['lang'])
        for lang in self._config.lang_list:
            self.langs[lang] = {
                "name": lang,
                "type": "lang",
            }
            self.add_option("lang", self.langs, lang, self.langs[lang])

        self.labels['printers_menu'] = self._gtk.ScrolledWindow()
        self.labels['printers'] = Gtk.Grid()
        self.labels['printers_menu'].add(self.labels['printers'])
        for printer in self._config.get_printers():
            pname = list(printer)[0]
            self.printers[pname] = {
                "name": pname,
                "section": f"printer {pname}",
                "type": "printer",
                "moonraker_host": printer[pname]['moonraker_host'],
                "moonraker_port": printer[pname]['moonraker_port'],
            }
            self.add_option("printers", self.printers, pname, self.printers[pname])

        self.content.add(self.labels['settings_menu'])
        self.update_nonlocals()
        GLib.timeout_add_seconds(1, self.update_nonlocals)

    def activate(self):
        self.do_schedule_refresh = True
        self.update_nonlocals()
        GLib.timeout_add_seconds(1, self.update_nonlocals)
        while len(self.menu) > 1:
            self.unload_menu()

    def deactivate(self):
        self.do_schedule_refresh = False

    def back(self):
        if len(self.menu) > 1:
            self.unload_menu()
            return True
        return False

    def add_option(self, boxname, opt_array, opt_name, option):
        if option['type'] is None:
            return
        name = Gtk.Label()
        name.set_markup(f"<big><b>{option['name']}</b></big>")
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
        if option['type'] == "binary":
            switch = Gtk.Switch()
            if option['section'] == '_nonlocal':
                switch.connect("notify::active", option['callback'], option)
                option['label'] = name
                option['control'] = switch
            else:
                switch.set_active(self._config.get_config().getboolean(option['section'], opt_name))
                switch.connect("notify::active", self.switch_config_option, option['section'], opt_name,
                               option['callback'] if "callback" in option else None)
            dev.add(switch)
        elif option['type'] == "dropdown":
            dropdown = Gtk.ComboBoxText()
            for i, opt in enumerate(option['options']):
                dropdown.append(opt['value'], opt['name'])
                if opt['value'] == self._config.get_config()[option['section']].get(opt_name, option['value']):
                    dropdown.set_active(i)
            dropdown.connect("changed", self.on_dropdown_change, option['section'], opt_name,
                             option['callback'] if "callback" in option else None)
            dropdown.set_entry_text_column(0)
            dev.add(dropdown)
        elif option['type'] == "scale":
            dev.set_orientation(Gtk.Orientation.VERTICAL)
            scale = Gtk.Scale.new_with_range(orientation=Gtk.Orientation.HORIZONTAL,
                                             min=option['range'][0], max=option['range'][1], step=option['step'])
            scale.set_hexpand(True)
            scale.set_value(int(self._config.get_config().get(option['section'], opt_name, fallback=option['value'])))
            scale.set_digits(0)
            scale.connect("button-release-event", self.scale_moved, option['section'], opt_name)
            dev.add(scale)
        elif option['type'] == "printer":
            box = Gtk.Box()
            box.set_vexpand(False)
            label = Gtk.Label(f"{option['moonraker_host']}:{option['moonraker_port']}")
            box.add(label)
            dev.add(box)
        elif option['type'] == "menu":
            open_menu = self._gtk.Button("load", style="color3")
            open_menu.connect("clicked", self.load_menu, option['menu'], option['name'])
            open_menu.set_hexpand(False)
            open_menu.set_halign(Gtk.Align.END)
            dev.add(open_menu)
        elif option['type'] == "panel":
            open_menu = self._gtk.Button("load", style="color3")
            open_menu.connect("clicked", self.show_panel, option['panel_type'], option['panel_title'])
            open_menu.set_hexpand(False)
            open_menu.set_halign(Gtk.Align.END)
            dev.add(open_menu)
        elif option['type'] == "lang":
            select = self._gtk.Button("load", style="color3")
            select.connect("clicked", self._screen.change_language, option['name'])
            select.set_hexpand(False)
            select.set_halign(Gtk.Align.END)
            dev.add(select)

        opt_array[opt_name] = {
            "name": option['name'],
            "row": dev
        }

        #opts = sorted(list(opt_array), key=lambda x: opt_array[x]['name'])
        opts = list(opt_array)
        pos = opts.index(opt_name)

        self.labels[boxname].insert_row(pos)
        self.labels[boxname].attach(opt_array[opt_name]['row'], 0, pos, 1, 1)
        self.labels[boxname].show_all()

    def show_panel(self, widget, type, title):
        self._screen.show_panel(title, type, title, 1, False)

    def update_nonlocals(self):
        for nlo in self.nonlocal_options:
            opt = self.nonlocal_options[nlo]
            opt["value_getter"](opt)

        self._screen.show_all()
        return self.do_schedule_refresh

    def _door_sensor_getter(self, obj):
        door_sensor = self._screen.printer.data['door_sensor']
        #obj["label"].set_text("")
        if not obj["update_deadtime"]:
            obj["control"].set_sensitive(True)
            if obj["control"].get_active() != door_sensor["enabled"]:
                obj["update_deadtime"] = 1
                obj["control"].set_active(door_sensor["enabled"])
        else:
            obj["control"].set_sensitive(False)
            obj["update_deadtime"] -= 1
        if door_sensor["enabled"]:
            badge = f" (<span foreground='#00FF00'>{_('Closed')}</span>)" if door_sensor["door_closed"] else \
                f" (<span foreground='#FF0000'>{_('Opened')}</span>)"
        else:
            badge = f" (<span foreground='#666666'>{_('Disabled')}</span>)"
        obj["label"].set_markup(f"<big><b>{obj['name']}{badge}</b></big>")

    def _door_sensor_callback(self, switch, gparam, obj):
        self._screen._ws.klippy.gcode_script(f"SET_DOOR_SENSOR_DISABLED DISABLED={0 if switch.get_active() else 1}")
        self._screen.show_all()
        if "loaded" not in obj:
            obj["loaded"] = True
            if switch.get_active():
                return
        obj["control"].set_sensitive(False)
        obj["update_deadtime"] = 3

    def _filament_sensor_getter(self, obj):
        filament_sensor = self._screen.printer.data['filament_switch_sensor fil_sensor']
        #obj["label"].set_text("")
        if not obj["update_deadtime"]:
            obj["control"].set_sensitive(True)
            if obj["control"].get_active() != filament_sensor["enabled"]:
                obj["update_deadtime"] = 1
                obj["control"].set_active(filament_sensor["enabled"])
        else:
            obj["control"].set_sensitive(False)
            obj["update_deadtime"] -= 1
        if filament_sensor["enabled"]:
            badge = f" (<span foreground='#00FF00'>{_('Filament')}</span>)" if filament_sensor["filament_detected"] else \
                f" (<span foreground='#FF0000'>{_('No Filament')}</span>)"
        else:
            badge = f" (<span foreground='#666666'>{_('Disabled')}</span>)"
        obj["label"].set_markup(f"<big><b>{obj['name']}{badge}</b></big>")

    def _filament_sensor_callback(self, switch, gparam, obj):
        self._screen._ws.klippy.gcode_script(f"SET_FILAMENT_SENSOR SENSOR=fil_sensor ENABLE={1 if switch.get_active() else 0}")
        self._screen.show_all()
        if "loaded" not in obj:
            obj["loaded"] = True
            if switch.get_active():
                return
        obj["update_deadtime"] = 3
        obj["control"].set_sensitive(False)