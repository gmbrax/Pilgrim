from pathlib import Path
from typing import Iterable

from textual.app import App, SystemCommand
from textual.screen import Screen


from pilgrim.service.servicemanager import ServiceManager
from pilgrim.ui.screens.about_screen import AboutScreen
from pilgrim.ui.screens.diary_list_screen import DiaryListScreen
from pilgrim.ui.screens.edit_entry_screen import EditEntryScreen
from pilgrim.utils import ConfigManager

CSS_FILE_PATH = Path(__file__).parent / "styles" / "pilgrim.css"


class UIApp(App):
    CSS_PATH = CSS_FILE_PATH

    def __init__(self,service_manager: ServiceManager, config_manager: ConfigManager, **kwargs):
        super().__init__(**kwargs)
        self.service_manager = service_manager
        self.config_manager = config_manager


    def on_mount(self) -> None:
        """Called when the app starts. Loads the main screen."""
        self.push_screen(DiaryListScreen())

    def get_system_commands(self, screen: Screen) -> Iterable[SystemCommand]:
        """Return commands based on current screen."""

        # Commands for DiaryListScreen
        if isinstance(screen, DiaryListScreen):
            yield SystemCommand(
                "About Pilgrim",
                "Open About Pilgrim",
                screen.action_about_cmd
            )
            yield SystemCommand(
                "Backup Database",
                "Backup the Database",
                screen.action_backup
            )

        elif isinstance(screen, AboutScreen):
            yield SystemCommand(
                "Back to List",
                "Return to the diary list",
                screen.dismiss
            )

        elif isinstance(screen, EditEntryScreen):
            yield SystemCommand(
                "Back to Diary List",
                "Return to the diary list",
                screen.action_back_to_list
            )

        # Always include quit command
        yield SystemCommand(
            "Quit Application",
            "Exit Pilgrim",
            self.action_quit
        )