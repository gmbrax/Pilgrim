from pathlib import Path

from textual.app import App

from pilgrim.service.servicemanager import ServiceManager
from pilgrim.ui.screens.diary_list_screen import DiaryListScreen

CSS_FILE_PATH = Path(__file__).parent / "styles" / "pilgrim.css"


class UIApp(App):
    CSS_PATH = CSS_FILE_PATH

    def __init__(self,service_manager: ServiceManager):
        super().__init__()
        self.service_manager = service_manager


    def on_mount(self) -> None:
        """Chamado quando a app inicia. Carrega a tela principal."""
        self.push_screen(DiaryListScreen())
