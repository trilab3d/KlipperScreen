import commonmark
from commonmark import node
import gi
import os

gi.require_version("Gtk", "3.0")
#gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, Gdk, Pango, WebKit2

from ks_includes.KlippyGcodes import KlippyGcodes
from ks_includes.screen_panel import ScreenPanel


def create_panel(*args):
    return ManualPanel(*args)


class ManualPanel(ScreenPanel):

    def __init__(self, screen, title):
        super().__init__(screen, title)

        scrolled_window = Gtk.ScrolledWindow()
        self.webview = WebKit2.WebView()
        self.webview.load_uri(f"file://{os.path.abspath('mans/index.html')}")
        self.webview.connect('decide-policy', self.on_decide_policy)
        scrolled_window.add(self.webview)
        scrolled_window.set_vexpand(True)

        self.content.add(scrolled_window)

    def on_decide_policy(self, web_view, decision, decision_type):
        return False
        if decision_type == WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
            navigation_action = decision.get_navigation_action()
            request = navigation_action.get_request()
            uri = request.get_uri()
            print(f"Link clicked: {uri}")
            if uri.endswith("index.html"):
                return False

            # Custom handling of the link click
            # For example, open the link in an external browser
            if True:
                decision.ignore()
                return True  # Return True to stop the default handler

        return False  # Return False to allow the default handler

    def back(self):
        if self.webview.can_go_back():
            self.webview.go_back()
            return True
        return False


