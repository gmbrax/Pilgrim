from textual.app import App

from pilgrim.service.servicemanager import ServiceManager


class UIApp(App):
    def __init__(self,service_manager: ServiceManager):
        super().__init__()
        self.service_manager = service_manager
