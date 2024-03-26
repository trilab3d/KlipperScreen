import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
from ks_includes.screen_panel import ScreenPanel


PRESET_FIELDS = {
    "reduced": [
        "system_info_minimal",
        "statistics_print_basic"
    ],
    "standard": [
        "system_info_minimal",
        "system_info_full",
        "statistics_print_basic",
        "statistics_print_extended",
        "statictics_region"
    ],
}

def create_panel(*args, **kvargs):
    return Privacy(*args, **kvargs)

class Privacy(ScreenPanel):
    def __init__(self, screen, title, **kvargs):
        super().__init__(screen, title)

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.content.add(self.box)

        self.grid = Gtk.Grid()
        self.grid.set_margin_top(20)
        self.grid.set_hexpand(True)
        scroll = self._gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.add(self.grid)
        self.box.add(scroll)

        self.btn_save = self._gtk.Button("settings", _("Save"), "color1")
        self.btn_save.set_hexpand(False)
        self.btn_save.set_vexpand(False)
        self.btn_save.connect("clicked", self.save_changes)
        btn_discard = self._gtk.Button("cancel", _("Discard"), "color1")
        btn_discard.set_hexpand(False)
        btn_discard.set_vexpand(False)
        btn_discard.connect("clicked", self.revert_changes)

        self.button_panel = self._gtk.HomogeneousGrid()
        # self.button_panel
        self.box.add(self.button_panel)
        self.button_panel.attach(btn_discard, 0, 0, 1, 1)
        self.button_panel.attach(self.btn_save, 1, 0, 1, 1)

        self.privacy_info = {}
        self.setts = {}
        self.changed_fields = []

        self.fetch_tpc()
        self.rebuild_pages()

    def rebuild_pages(self):
        for ch in self.grid.get_children():
            self.grid.remove(ch)

        preset_label = Gtk.Label(label=f"<span size='x-large'>"+_("Privacy Preset")+":</span>", use_markup=True)
        preset_label.set_halign(Gtk.Align.START)
        preset_label.set_line_wrap(True)
        preset_label.set_hexpand(True)
        preset_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        preset_label.set_margin_top(10)
        preset_label.set_margin_left(10)

        preset_dropdown = Gtk.ComboBoxText()
        presets = [
            ("reduced", _("Reduced")),
            ("standard", _("Standard")),
            ("custom",_("Custom"))]
        preset_current = None
        for i, opt in enumerate(presets):
            preset_dropdown.append(opt[0], opt[1])
            if opt[0] != "custom" and PRESET_FIELDS[opt[0]] == self.changed_fields:
                preset_current = opt[0]
                preset_dropdown.set_active(i)
        if preset_current == None:
            preset_current = "custom"
            preset_dropdown.set_active(len(presets)-1)
        preset_dropdown.connect("changed", self.change_preset)
        preset_dropdown.set_entry_text_column(0)
        dropdown_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        dropdown_box.set_hexpand(False)
        dropdown_box.set_vexpand(False)
        blank_box = Gtk.Box()
        blank_box.set_hexpand(True)
        blank_box.set_vexpand(True)
        dropdown_box.add(blank_box)
        dropdown_box.add(preset_dropdown)

        self.grid.attach(preset_label, 0, 0, 2, 1)
        self.grid.attach(dropdown_box, 1, 0, 1, 1)

        if preset_current == "custom":
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
                switch.set_active(option in self.changed_fields)
                switch.set_hexpand(False)
                switch.set_vexpand(False)
                switch.set_size_request(-1, 20)
                switch.connect("notify::active", self.change_option, option)
                self.grid.attach(label, 0, i+1, 2, 1)
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
                self.grid.attach(switch_box, 1, i+1, 1, 1)

        self._screen.show_all()

    def change_option(self, widget, active, option):
        if widget.get_active():
            if option not in self.changed_fields:
                self.changed_fields.append(option)
        else:
            if option in self.changed_fields:
                self.changed_fields.remove(option)

    def change_preset(self, widget):
        tree_iter = widget.get_active_iter()
        model = widget.get_model()
        value = model[tree_iter][1]

        if value == "custom":
            self.changed_fields = self.privacy_info["privacy_options"]
        else:
            self.changed_fields = PRESET_FIELDS[value]

        self.rebuild_pages()

    def fetch_tpc(self):
        self.privacy_info = self._screen.tpcclient.send_request("/privacy_info")
        self.setts = self._screen.tpcclient.send_request("/settings")
        self.changed_fields = self.setts["privacy"]

    def save_changes(self, widget):
        settings = {
            "privacy": self.changed_fields,
        }
        self._screen.tpcclient.send_request(f"settings", "POST", body=settings)
        self._screen._menu_go_back()

    def revert_changes(self, widget):
        self.fetch_tpc()
        self.rebuild_pages()

    def activate(self):
        self.fetch_tpc()
        self.rebuild_pages()