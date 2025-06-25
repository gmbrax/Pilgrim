from typing import Optional, List
import asyncio
from datetime import datetime

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, TextArea
from textual.binding import Binding
from textual.containers import Container, Horizontal

from pilgrim.models.entry import Entry
from pilgrim.models.travel_diary import TravelDiary
from pilgrim.ui.screens.rename_entry_modal import RenameEntryModal


class EditEntryScreen(Screen):
    TITLE = "Pilgrim - Edit"

    BINDINGS = [
        Binding("ctrl+s", "save", "Save"),
        Binding("ctrl+n", "next_entry", "Next/New Entry"),
        Binding("ctrl+b", "prev_entry", "Previous Entry"),
        Binding("ctrl+r", "rename_entry", "Rename Entry"),
        Binding("escape", "back_to_list", "Back to List")
    ]

    def __init__(self, diary_id: int = 1):
        super().__init__()
        self.diary_id = diary_id
        self.diary_name = f"Diary {diary_id}"  # Use a better default name
        self.current_entry_index = 0
        self.entries: List[Entry] = []
        self.is_new_entry = False
        self.has_unsaved_changes = False
        self.new_entry_content = ""
        self.new_entry_title = "New Entry"
        self.next_entry_id = 1
        self._updating_display = False
        self._original_content = ""
        self.is_refreshing = False

        # Main header
        self.header = Header(name="Pilgrim v6", classes="EditEntryScreen-header")

        # Sub-header widgets
        self.diary_info = Static(f"Diary: {self.diary_name}", id="diary_info", classes="EditEntryScreen-diary-info")
        self.entry_info = Static("Loading...", id="entry_info", classes="EditEntryScreen-entry-info")
        self.status_indicator = Static("Saved", id="status_indicator", classes="EditEntryScreen-status-indicator")

        # Sub-header container
        self.sub_header = Horizontal(
            self.diary_info,
            Static(classes="spacer EditEntryScreen-spacer"),
            self.entry_info,
            self.status_indicator,
            id="sub_header",
            classes="EditEntryScreen-sub-header"
        )

        # Text area
        self.text_entry = TextArea(id="text_entry", classes="EditEntryScreen-text-entry")

        # Main container
        self.main = Container(
            self.sub_header,
            self.text_entry,
            id="EditEntryScreen_MainContainer",
            classes="EditEntryScreen-main-container"
        )

        # Footer
        self.footer = Footer(classes="EditEntryScreen-footer")

    def compose(self) -> ComposeResult:
        yield self.header
        yield self.main
        yield self.footer

    def on_mount(self) -> None:
        """Called when the screen is mounted"""
        # First update diary info, then refresh entries
        self.update_diary_info()
        self.refresh_entries()

    def update_diary_info(self):
        """Updates diary information"""
        try:
            service_manager = self.app.service_manager
            travel_diary_service = service_manager.get_travel_diary_service()
            
            diary = travel_diary_service.read_by_id(self.diary_id)
            if diary:
                self.diary_name = diary.name
                self.diary_info.update(f"Diary: {self.diary_name}")
            else:
                # If diary not found, try to get a default name
                self.diary_name = f"Diary {self.diary_id}"
                self.diary_info.update(f"Diary: {self.diary_name}")
                self.notify(f"Diary {self.diary_id} not found, using default name")
        except Exception as e:
            # If there's an error, use a default name but don't break the app
            self.diary_name = f"Diary {self.diary_id}"
            self.diary_info.update(f"Diary: {self.diary_name}")
            self.notify(f"Error loading diary info: {str(e)}")
        
        # Always ensure the diary info is updated
        self._ensure_diary_info_updated()

    def _ensure_diary_info_updated(self):
        """Ensures the diary info widget is always updated with current diary name"""
        try:
            self.diary_info.update(f"Diary: {self.diary_name}")
        except Exception as e:
            # If even this fails, at least try to show something
            self.diary_info.update(f"Diary: {self.diary_id}")

    def refresh_entries(self):
        """Synchronous version of refresh"""
        try:
            service_manager = self.app.service_manager
            entry_service = service_manager.get_entry_service()

            # Get all entries for this diary
            all_entries = entry_service.read_all()
            self.entries = [entry for entry in all_entries if entry.fk_travel_diary_id == self.diary_id]
            
            # Sort by ID
            self.entries.sort(key=lambda x: x.id)

            # Update next entry ID
            if self.entries:
                self.next_entry_id = max(entry.id for entry in self.entries) + 1
            else:
                self.next_entry_id = 1

            self._update_entry_display()
            self._update_sub_header()

        except Exception as e:
            self.notify(f"Error loading entries: {str(e)}")
        
        # Ensure diary info is updated even if entries fail to load
        self._ensure_diary_info_updated()

    async def async_refresh_entries(self):
        """Asynchronous version of refresh"""
        if self.is_refreshing:
            return

        self.is_refreshing = True

        try:
            service_manager = self.app.service_manager
            entry_service = service_manager.get_entry_service()

            # For now, use synchronous method since mock doesn't have async
            all_entries = entry_service.read_all()
            self.entries = [entry for entry in all_entries if entry.fk_travel_diary_id == self.diary_id]
            
            # Sort by ID
            self.entries.sort(key=lambda x: x.id)

            # Update next entry ID
            if self.entries:
                self.next_entry_id = max(entry.id for entry in self.entries) + 1
            else:
                self.next_entry_id = 1

            self._update_entry_display()
            self._update_sub_header()

        except Exception as e:
            self.notify(f"Error loading entries: {str(e)}")
        finally:
            self.is_refreshing = False

    def _update_status_indicator(self, text: str, css_class: str):
        """Helper to update status indicator text and class."""
        self.status_indicator.update(text)
        self.status_indicator.remove_class("saved", "not-saved", "new", "read-only")
        self.status_indicator.add_class(css_class)

    def _update_sub_header(self):
        """Updates the sub-header with current entry information."""
        if not self.entries and not self.is_new_entry:
            self.entry_info.update("No entries")
            self._update_status_indicator("Saved", "saved")
            return

        if self.is_new_entry:
            self.entry_info.update(f"New Entry: {self.new_entry_title}")
            if self.has_unsaved_changes:
                self._update_status_indicator("Not Saved", "not-saved")
            else:
                self._update_status_indicator("New", "new")
        else:
            current_entry = self.entries[self.current_entry_index]
            entry_text = f"Entry: \\[{self.current_entry_index + 1}/{len(self.entries)}] {current_entry.title}"
            self.entry_info.update(entry_text)
            self._update_status_indicator("Saved", "saved")

    def _save_current_state(self):
        """Saves the current state before navigating"""
        if self.is_new_entry:
            self.new_entry_content = self.text_entry.text
        elif self.entries and self.has_unsaved_changes:
            current_entry = self.entries[self.current_entry_index]
            current_entry.text = self.text_entry.text

    def _finish_display_update(self):
        """Finishes the display update by reactivating change detection"""
        self._updating_display = False
        self._update_sub_header()

    def _update_entry_display(self):
        """Updates the display of the current entry"""
        if not self.entries and not self.is_new_entry:
            self.text_entry.text = f"No entries found for diary '{self.diary_name}'\n\nPress Ctrl+N to create a new entry."
            self.text_entry.read_only = True
            self._original_content = self.text_entry.text
            self._update_sub_header()
            return

        self._updating_display = True

        if self.is_new_entry:
            self.text_entry.text = self.new_entry_content
            self.text_entry.read_only = False
            self._original_content = self.new_entry_content
            self.has_unsaved_changes = False
        else:
            current_entry = self.entries[self.current_entry_index]
            self.text_entry.text = current_entry.text
            self.text_entry.read_only = False
            self._original_content = current_entry.text
            self.has_unsaved_changes = False

        self.call_after_refresh(self._finish_display_update)

    def on_text_area_changed(self, event) -> None:
        """Detects text changes to mark as unsaved"""
        if (hasattr(self, 'text_entry') and not self.text_entry.read_only and
                not getattr(self, '_updating_display', False) and hasattr(self, '_original_content')):
            current_content = self.text_entry.text
            if current_content != self._original_content:
                if not self.has_unsaved_changes:
                    self.has_unsaved_changes = True
                    self._update_sub_header()
            else:
                if self.has_unsaved_changes:
                    self.has_unsaved_changes = False
                    self._update_sub_header()

    def action_back_to_list(self) -> None:
        """Goes back to the diary list"""
        if self.is_new_entry and not self.text_entry.text.strip() and not self.has_unsaved_changes:
            self.app.pop_screen()
            self.notify("Returned to diary list")
            return

        if self.has_unsaved_changes or (self.is_new_entry and self.text_entry.text.strip()):
            self.notify("There are unsaved changes! Use Ctrl+S to save before leaving.")
            return

        self.app.pop_screen()
        self.notify("Returned to diary list")

    def action_next_entry(self) -> None:
        """Goes to the next entry"""
        self._save_current_state()

        if not self.entries:
            if not self.is_new_entry:
                self.is_new_entry = True
                self._update_entry_display()
                self.notify("New entry created")
            else:
                self.notify("Already in a new entry")
            return

        if self.is_new_entry:
            self.notify("Already at the last position (new entry)")
        elif self.current_entry_index < len(self.entries) - 1:
            self.current_entry_index += 1
            self._update_entry_display()
            current_entry = self.entries[self.current_entry_index]
            self.notify(f"Navigating to: {current_entry.title}")
        else:
            self.is_new_entry = True
            self._update_entry_display()
            self.notify("New entry created")

    def action_prev_entry(self) -> None:
        """Goes to the previous entry"""
        self._save_current_state()

        if not self.entries:
            self.notify("No entries to navigate")
            return

        if self.is_new_entry:
            if self.entries:
                self.is_new_entry = False
                self.current_entry_index = len(self.entries) - 1
                self._update_entry_display()
                current_entry = self.entries[self.current_entry_index]
                self.notify(f"Navigating to: {current_entry.title}")
            else:
                self.notify("No previous entries")
        elif self.current_entry_index > 0:
            self.current_entry_index -= 1
            self._update_entry_display()
            current_entry = self.entries[self.current_entry_index]
            self.notify(f"Navigating to: {current_entry.title}")
        else:
            self.notify("Already at the first entry")

    def action_rename_entry(self) -> None:
        """Opens a modal to rename the entry."""
        if not self.entries and not self.is_new_entry:
            self.notify("No entry to rename", severity="warning")
            return

        if self.is_new_entry:
            current_name = self.new_entry_title
        else:
            current_entry = self.entries[self.current_entry_index]
            current_name = current_entry.title

        self.app.push_screen(
            RenameEntryModal(current_name=current_name),
            self.handle_rename_result
        )

    def handle_rename_result(self, new_name: str | None) -> None:
        """Callback that processes the rename modal result."""
        if new_name is None:
            self.notify("Rename cancelled")
            return

        if not new_name.strip():
            self.notify("Name cannot be empty", severity="error")
            return

        if self.is_new_entry:
            old_name = self.new_entry_title
            self.new_entry_title = new_name
            self.notify(f"New entry title changed to '{new_name}'")
        else:
            current_entry = self.entries[self.current_entry_index]
            old_name = current_entry.title
            current_entry.title = new_name
            self.notify(f"Title changed from '{old_name}' to '{new_name}'")

        self.has_unsaved_changes = True
        self._update_sub_header()

    def action_save(self) -> None:
        """Saves the current entry"""
        if self.is_new_entry:
            content = self.text_entry.text.strip()
            if not content:
                self.notify("Empty entry cannot be saved")
                return

            # Schedule async creation
            self.call_later(self._async_create_entry, content)
        else:
            # Schedule async update
            self.call_later(self._async_update_entry)

    async def _async_create_entry(self, content: str):
        """Creates a new entry asynchronously"""
        try:
            service_manager = self.app.service_manager
            entry_service = service_manager.get_entry_service()

            # Get current date
            current_date = datetime.now().strftime("%d/%m/%Y")

            new_entry = entry_service.create(
                travel_diary_id=self.diary_id,
                title=self.new_entry_title,
                text=content,
                date=current_date
            )

            if new_entry:
                self.entries.append(new_entry)
                self.entries.sort(key=lambda x: x.id)

                # Find the new entry index
                for i, entry in enumerate(self.entries):
                    if entry.id == new_entry.id:
                        self.current_entry_index = i
                        break

                self.is_new_entry = False
                self.has_unsaved_changes = False
                self._original_content = new_entry.text
                self.new_entry_title = "New Entry"
                self.next_entry_id = max(entry.id for entry in self.entries) + 1

                self._update_entry_display()
                self.notify(f"New entry '{new_entry.title}' saved successfully!")
            else:
                self.notify("Error creating entry")

        except Exception as e:
            self.notify(f"Error creating entry: {str(e)}")

    async def _async_update_entry(self):
        """Updates the current entry asynchronously"""
        try:
            if not self.entries:
                self.notify("No entry to update")
                return

            current_entry = self.entries[self.current_entry_index]
            updated_content = self.text_entry.text

            # Create updated entry object
            updated_entry = Entry(
                title=current_entry.title,
                text=updated_content,
                date=current_entry.date,
                travel_diary_id=current_entry.fk_travel_diary_id,
                id=current_entry.id
            )

            service_manager = self.app.service_manager
            entry_service = service_manager.get_entry_service()

            result = entry_service.update(current_entry, updated_entry)

            if result:
                current_entry.text = updated_content
                self.has_unsaved_changes = False
                self._original_content = updated_content
                self._update_sub_header()
                self.notify(f"Entry '{current_entry.title}' saved successfully!")
            else:
                self.notify("Error updating entry")

        except Exception as e:
            self.notify(f"Error updating entry: {str(e)}")

    def action_force_refresh(self):
        """Forces manual refresh"""
        self.notify("Forcing refresh...")
        self.refresh_entries()
        self.call_later(self.async_refresh_entries) 