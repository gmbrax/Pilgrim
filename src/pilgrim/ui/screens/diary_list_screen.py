from typing import Optional, Tuple
import asyncio

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Label, Static, OptionList, Button
from textual.binding import Binding
from textual.containers import Vertical, Container, Horizontal

from pilgrim.models.travel_diary import TravelDiary
from pilgrim.ui.screens.about_screen import AboutScreen
from pilgrim.ui.screens.diary_settings_screen import SettingsScreen
from pilgrim.ui.screens.edit_diary_modal import EditDiaryModal
from pilgrim.ui.screens.new_diary_modal import NewDiaryModal
from pilgrim.ui.screens.edit_entry_screen import EditEntryScreen

from pilgrim.service.backup_service import BackupService


class DiaryListScreen(Screen):
    TITLE = "Pilgrim - Main"

    BINDINGS = [
        Binding("n", "new_diary", "New diary"),
        Binding("^q", "quit", "Quit Pilgrim"),
        Binding("enter", "open_selected_diary", "Open diary"),
        Binding("e", "edit_selected_diary", "Edit diary"),
        Binding("r", "force_refresh", "Force refresh"),
        Binding("s", "diary_settings", "Open The Selected Diary Settings"),
    ]

    def __init__(self):
        super().__init__()
        self.selected_diary_index = None
        self.diary_id_map = {}
        self.is_refreshing = False

        self.header = Header()
        self.footer = Footer()
        self.diary_list = OptionList(classes="DiaryListScreen-DiaryListOptions")
        self.new_diary_button = Button("New diary", id="new_diary", classes="DiaryListScreen-NewDiaryButton")
        self.edit_diary_button = Button("Edit diary", id="edit_diary", classes="DiaryListScreen-EditDiaryButton")
        self.open_diary = Button("Open diary", id="open_diary", classes="DiaryListScreen-OpenDiaryButton")
        self.buttons_grid = Horizontal(
            self.new_diary_button, self.edit_diary_button, self.open_diary,
            classes="DiaryListScreen-ButtonsGrid"
        )
        self.tips = Static(
            "Tip: use ↑↓ to navigate • ENTER to Select • "
            "TAB to alternate the fields • SHIFT + TAB to alternate back • "
            "Ctrl+P for command palette • R to force refresh",
            classes="DiaryListScreen-DiaryListTips"
        )
        self.container = Container(
            self.diary_list, self.buttons_grid, self.tips,
            classes="DiaryListScreen-DiaryListContainer"
        )

    def compose(self) -> ComposeResult:
        yield self.header
        yield self.container
        yield self.footer

    def on_mount(self) -> None:
        # Uses synchronous version for initial mount
        self.refresh_diaries()
        self.update_buttons_state()

    def refresh_diaries(self):
        """Synchronous version of refresh"""
        try:
            service_manager = self.app.service_manager
            travel_diary_service = service_manager.get_travel_diary_service()

            # Uses synchronous method
            diaries = travel_diary_service.read_all()

            # Saves current state
            current_diary_id = None
            if (self.selected_diary_index is not None and
                    self.selected_diary_index in self.diary_id_map):
                current_diary_id = self.diary_id_map[self.selected_diary_index]

            # Clears and rebuilds
            self.diary_list.clear_options()
            self.diary_id_map = {}

            if not diaries:
                self.diary_list.add_option("[dim]No diaries found. Press 'N' to create a new one![/dim]")
                self.selected_diary_index = None
            else:
                new_selected_index = 0

                for index, diary in enumerate(diaries):
                    self.diary_id_map[index] = diary.id
                    self.diary_list.add_option(f"[b]{diary.name}[/b]\n[dim]ID: {diary.id}[/dim]")

                    # Maintains selection if possible
                    if current_diary_id and diary.id == current_diary_id:
                        new_selected_index = index

                self.selected_diary_index = new_selected_index

                # Updates highlight
                self.set_timer(0.05, lambda: self._update_highlight(new_selected_index))

            # Forces visual refresh
            self.diary_list.refresh()
            self.update_buttons_state()

        except Exception as e:
            self.notify(f"Error loading diaries: {str(e)}")

    def _update_highlight(self, index: int):
        """Updates the OptionList highlight"""
        try:
            if index < len(self.diary_list.options):
                self.diary_list.highlighted = index
                self.diary_list.refresh()
        except Exception as e:
            self.notify(f"Error updating highlight: {str(e)}")

    async def async_refresh_diaries(self):
        """Async version of refresh"""
        if self.is_refreshing:
            return

        self.is_refreshing = True

        try:
            service_manager = self.app.service_manager
            travel_diary_service = service_manager.get_travel_diary_service()

            # Usa método síncrono agora
            diaries = travel_diary_service.read_all()

            # Saves current state
            current_diary_id = None
            if (self.selected_diary_index is not None and
                    self.selected_diary_index in self.diary_id_map):
                current_diary_id = self.diary_id_map[self.selected_diary_index]

            # Clears and rebuilds
            self.diary_list.clear_options()
            self.diary_id_map = {}

            if not diaries:
                self.diary_list.add_option("[dim]No diaries found. Press 'N' to create a new one![/dim]")
                self.selected_diary_index = None
            else:
                new_selected_index = 0

                for index, diary in enumerate(diaries):
                    self.diary_id_map[index] = diary.id
                    self.diary_list.add_option(f"[b]{diary.name}[/b]\n[dim]ID: {diary.id}[/dim]")

                    if current_diary_id and diary.id == current_diary_id:
                        new_selected_index = index

                self.selected_diary_index = new_selected_index
                self.set_timer(0.05, lambda: self._update_highlight(new_selected_index))

            self.diary_list.refresh()
            self.update_buttons_state()

        except Exception as e:
            self.notify(f"Error loading diaries: {str(e)}")
        finally:
            self.is_refreshing = False

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        """Handle when an option is highlighted"""
        if self.diary_id_map and event.option_index in self.diary_id_map:
            self.selected_diary_index = event.option_index
        else:
            self.selected_diary_index = None

        self.update_buttons_state()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle when an option is selected"""
        if self.diary_id_map and event.option_index in self.diary_id_map:
            self.selected_diary_index = event.option_index
            self.action_open_diary()
        else:
            self.selected_diary_index = None

        self.update_buttons_state()

    def update_buttons_state(self):
        """Updates button states"""
        has_selection = (self.selected_diary_index is not None and
                         self.selected_diary_index in self.diary_id_map)

        self.edit_diary_button.disabled = not has_selection
        self.open_diary.disabled = not has_selection

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks"""
        button_id = event.button.id

        if button_id == "new_diary":
            self.action_new_diary()
        elif button_id == "edit_diary":
            self.action_edit_selected_diary()
        elif button_id == "open_diary":
            self.action_open_diary()

    def action_new_diary(self):
        """Action to create new diary"""
        self.app.push_screen(NewDiaryModal(),self._on_new_diary_submitted)

    def _on_new_diary_submitted(self, result):
        """Callback after diary creation"""
        if result:  # Se result não é string vazia, o diário foi criado
            self.notify(f"Returning to diary list...")
            # Atualiza a lista de diários
            self.refresh_diaries()
        else:
            self.notify(f"Creation canceled...")

    def _on_screen_resume(self) -> None:
        super()._on_screen_resume()
        self.refresh_diaries()

    def action_edit_selected_diary(self):
        """Action to edit selected diary"""
        if self.selected_diary_index is not None:
            diary_id = self.diary_id_map.get(self.selected_diary_index)
            if diary_id:
                self.app.push_screen(
                    EditDiaryModal(diary_id=diary_id),
                    self._on_edited_diary_name_submitted
                )
        else:
            self.notify("Select a diary to edit")

    def action_open_diary(self):
        """Action to open selected diary"""
        if self.selected_diary_index is not None:
            diary_id = self.diary_id_map.get(self.selected_diary_index)
            if diary_id:
                self.app.push_screen(EditEntryScreen(diary_id=diary_id))
                self.notify(f"Opening diary ID: {diary_id}")
            else:
                self.notify("Invalid diary ID")
        else:
            self.notify("Select a diary to open")

    def _on_edited_diary_name_submitted(self, result: Optional[Tuple[int, str]]) -> None:
        """Callback after diary editing"""
        if result:
            diary_id, name = result
            self.notify(f"Updating diary ID {diary_id} to '{name}'...")
            # Schedules async update
            self.call_later(self._async_update_diary, diary_id, name)
        else:
            self.notify("Edit canceled")

    async def _async_update_diary(self, diary_id: int, name: str):
        """Updates the diary asynchronously"""
        try:
            service = self.app.service_manager.get_travel_diary_service()
            updated_diary = await service.async_update(diary_id, name)

            if updated_diary:
                self.notify(f"Diary '{name}' updated!")
                # Forces refresh after update
                await self.async_refresh_diaries()
            else:
                self.notify("Error: Diary not found")

        except Exception as e:
            self.notify(f"Error updating: {str(e)}")

    def action_force_refresh(self):
        """Forces manual refresh"""
        self.notify("Forcing refresh...")
        # Tries both versions
        self.refresh_diaries()  # Synchronous
        self.call_later(self.async_refresh_diaries)  # Asynchronous

    def action_open_selected_diary(self):
        """Action for ENTER binding"""
        self.action_open_diary()

    def action_about_cmd(self):
        self.app.push_screen(AboutScreen())

    def action_quit(self):
        """Action to quit the application"""
        self.app.exit()

    def action_diary_settings(self):
        if self.selected_diary_index is not None:
            diary_id = self.diary_id_map.get(self.selected_diary_index)
            if diary_id:
                self.app.push_screen(SettingsScreen(diary_id=diary_id))
            else:
                self.notify("Invalid diary ID")
        else:
            self.notify("Select a diary to open the settings")


    def action_backup(self):
        session = self.app.service_manager.get_session()
        if session:
            backup_service = BackupService(session)
            result_operation,result_data = backup_service.create_backup()
        else:
            self.notify("You must be logged in to perform this action")
        if result_operation:
            self.notify(f"Backup result: {result_data}")
        else:
            self.notify(f"Error performing backup {result_data}")
            raise Exception("Error performing backup")
            self.app.exit()

