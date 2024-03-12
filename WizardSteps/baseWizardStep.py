
class BaseWizardStep():
    def __init__(self, screen):
        self._screen = screen
        self.content = None
        self.wizard_manager = None
        self.can_back = False
        self.can_exit = True

    def activate(self, wizard):
        self.wizard_manager = wizard
        self.wizard_manager._screen.base_panel.show_back(self.can_back, self.can_exit)

    def update_loop(self):
        pass

    def on_cancel(self):
        pass

    def on_back(self):
        return False
