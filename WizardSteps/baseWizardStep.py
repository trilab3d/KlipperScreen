
class BaseWizardStep():
    def __init__(self, screen):
        self._screen = screen
        self.content = None
        self.wizard_manager = None

    def activate(self, wizard):
        self.wizard_manager = wizard

    def update_loop(self):
        pass

    def on_cancel(self):
        pass

