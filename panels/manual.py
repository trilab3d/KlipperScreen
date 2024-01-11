import commonmark
from commonmark import node
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Pango

from ks_includes.KlippyGcodes import KlippyGcodes
from ks_includes.screen_panel import ScreenPanel


def create_panel(*args):
    return ManualPanel(*args)


class ManualPanel(ScreenPanel):

    def __init__(self, screen, title):
        super().__init__(screen, title)
        self.content.add(self.parse_markup())

        textview = Gtk.TextView()
        textbuffer = textview.get_buffer()
        textview.set_editable(False)
        textview.set_cursor_visible(False)

        #self.content.add(textview)

        textbuffer.set_text("Click here to visit OpenAI: ")

        # Create a tag for clickable link
        tag = textbuffer.create_tag("link", foreground="blue", underline=Pango.Underline.SINGLE)
        start_iter = textbuffer.get_end_iter()
        textbuffer.insert(start_iter, "OpenAI Website")
        end_iter = textbuffer.get_end_iter()

        # Apply the tag
        textbuffer.apply_tag(tag, start_iter, end_iter)

        # Connect the event signal for clickable link
        textview.connect("event", self.on_textview_event, textbuffer, tag)

    def on_textview_event(self, textview, event, textbuffer, tag):
        print(f"textview: {textview}")
        print(f"event {event.type}")
        print(f"tag {tag}")
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 1:
            x, y = textview.window_to_buffer_coords(Gtk.TextWindowType.WIDGET, int(event.x), int(event.y))
            iter = textview.get_iter_at_location(x, y)

    def parse_markup(self):
        with open("mans/home.md") as f:
            txt = f.read()

        parser = commonmark.Parser()
        ast = parser.parse(txt)

        root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        root_box.set_hexpand(True)
        root_box.set_margin_top(10)
        root_box.set_margin_bottom(10)
        root_box.set_margin_start(10)
        root_box.set_margin_end(10)

        element = {"parent": None, "subnode": None, "gtk_element": root_box}
        heading_level = 0
        for subnode, entered in ast.walker():

            if node.is_container(subnode):
                if entered:
                    gkt_element = box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
                    box.set_hexpand(True)
                    box.set_halign(Gtk.Align.START)
                    if subnode.t == "list":
                        box.set_margin_left(10)
                    elif subnode.t == "item":
                        label = self._gtk.Label(f"{subnode.list_data['start']}. ")
                        label.set_halign(Gtk.Align.START)
                        label.set_valign(Gtk.Align.START)
                        gkt_element = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
                        gkt_element.set_hexpand(True)
                        gkt_element.set_halign(Gtk.Align.START)
                        gkt_element.add(label)
                        gkt_element.add(box)
                    elif subnode.t == "heading":
                        heading_level = subnode.level
                    n = {"parent": element, "gtk_element": box, "subnode": subnode}
                    element["gtk_element"].add(gkt_element)
                    element = n
                else:
                    if subnode.t == "heading":
                        heading_level = 0
                    element = element["parent"]
            else:
                label = self._gtk.Label("")
                if heading_level == 1:
                    size = "size='xx-large'"
                    label.set_margin_top(10)
                    label.set_margin_bottom(10)
                elif heading_level == 2:
                    size = "size='x-large'"
                    label.set_margin_top(10)
                    label.set_margin_bottom(10)
                elif heading_level == 3:
                    size = "size='large'"
                    label.set_margin_top(10)
                    label.set_margin_bottom(10)
                else:
                    size = ""
                label.set_markup(f"<span {size}>{subnode.literal}</span>")
                label.set_halign(Gtk.Align.START)
                element["gtk_element"].add(label)

        def find_in_stack(stack,type):
            while True:
                if stack["subnode"] is None:
                    return None
                if stack["subnode"].t == type:
                    return stack["subnode"]
                if stack["parent"] is None:
                    return None
                stack = stack["parent"]

        return root_box

