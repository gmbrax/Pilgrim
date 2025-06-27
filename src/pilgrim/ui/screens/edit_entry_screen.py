from typing import Optional, List
import asyncio
from datetime import datetime
from pathlib import Path

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, TextArea, OptionList, Input, Button
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer

from pilgrim.models.entry import Entry
from pilgrim.models.travel_diary import TravelDiary
from pilgrim.models.photo import Photo
from pilgrim.ui.screens.modals.add_photo_modal import AddPhotoModal
from pilgrim.ui.screens.modals.file_picker_modal import FilePickerModal
from pilgrim.ui.screens.rename_entry_modal import RenameEntryModal


class EditEntryScreen(Screen):
    TITLE = "Pilgrim - Edit"

    BINDINGS = [
        Binding("ctrl+s", "save", "Save"),
        Binding("ctrl+n", "next_entry", "Next/New Entry"),
        Binding("ctrl+b", "prev_entry", "Previous Entry"),
        Binding("ctrl+r", "rename_entry", "Rename Entry"),
        Binding("escape", "back_to_list", "Back to List"),
        Binding("f8", "toggle_sidebar", "Toggle Sidebar"),
        Binding("f9", "toggle_focus", "Focus Sidebar/Editor"),
    ]

    def __init__(self, diary_id: int = 1):
        print("DEBUG: EditEntryScreen INIT")
        super().__init__()
        self.diary_id = diary_id
        self.diary_name = f"Diary {diary_id}"
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
        self.sidebar_visible = False
        self.sidebar_focused = False
        self._sidebar_opened_once = False

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

        # Sidebar widgets
        self.sidebar_title = Static("📸 Photos", classes="EditEntryScreen-sidebar-title")
        self.photo_list = OptionList(id="photo_list", classes="EditEntryScreen-sidebar-photo-list")
        self.photo_info = Static("", classes="EditEntryScreen-sidebar-photo-info")
        self.help_text = Static("", classes="EditEntryScreen-sidebar-help")

        # Sidebar container: photo list and info in a flexible container, help_text fixed at bottom
        self.sidebar_content = Vertical(
            self.photo_list,
            self.photo_info,
            id="sidebar_content",
            classes="EditEntryScreen-sidebar-content"
        )
        self.sidebar = Vertical(
            self.sidebar_title,
            self.sidebar_content,
            self.help_text,  # Always at the bottom, never scrolls
            id="sidebar",
            classes="EditEntryScreen-sidebar"
        )

        # Main container
        self.main = Container(
            self.sub_header,
            self.text_entry,
            id="EditEntryScreen_MainContainer",
            classes="EditEntryScreen-main-container"
        )

        # Footer
        self.footer = Footer(classes="EditEntryScreen-footer")

    def _update_footer_context(self):
        """Forces footer refresh to show updated bindings"""
        self.refresh()

    def compose(self) -> ComposeResult:
        print("DEBUG: EditEntryScreen COMPOSE", getattr(self, 'sidebar_visible', None))
        yield self.header
        yield Horizontal(
            self.main,
            self.sidebar,
            id="content_container",
            classes="EditEntryScreen-content-container"
        )
        yield self.footer

    def on_mount(self) -> None:
        """Called when the screen is mounted"""
        self.sidebar.display = False
        self.sidebar_visible = False
        
        # First update diary info, then refresh entries
        self.update_diary_info()
        self.refresh_entries()
        
        # Initialize footer with editor context
        self._update_footer_context()

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
                self.diary_name = f"Diary {self.diary_id}"
                self.diary_info.update(f"Diary: {self.diary_name}")
                self.notify(f"Diary {self.diary_id} not found, using default name")
        except Exception as e:
            self.diary_name = f"Diary {self.diary_id}"
            self.diary_info.update(f"Diary: {self.diary_name}")
            self.notify(f"Error loading diary info: {str(e)}")
        
        self._ensure_diary_info_updated()

    def _ensure_diary_info_updated(self):
        """Ensures the diary info widget is always updated with current diary name"""
        try:
            self.diary_info.update(f"Diary: {self.diary_name}")
        except Exception as e:
            self.diary_info.update(f"Diary: {self.diary_id}")

    def refresh_entries(self):
        """Synchronous version of refresh"""
        try:
            service_manager = self.app.service_manager
            entry_service = service_manager.get_entry_service()

            all_entries = entry_service.read_all()
            self.entries = [entry for entry in all_entries if entry.fk_travel_diary_id == self.diary_id]
            self.entries.sort(key=lambda x: x.id)

            if self.entries:
                self.next_entry_id = max(entry.id for entry in self.entries) + 1
            else:
                self.next_entry_id = 1

            self._update_entry_display()
            self._update_sub_header()

        except Exception as e:
            self.notify(f"Error loading entries: {str(e)}")
        
        self._ensure_diary_info_updated()

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
        if self.sidebar_visible:
            self._update_sidebar_content()

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

    def _update_sidebar_content(self):
        """Updates the sidebar content with photos for the current diary"""
        photos = self._load_photos_for_diary(self.diary_id)

        # Clear existing options safely
        self.photo_list.clear_options()

        # Add 'Ingest Photo' option at the top
        self.photo_list.add_option("➕ Ingest Photo")

        if not photos:
            self.photo_info.update("No photos found for this diary")
            self.help_text.update("📸 No photos available\n\nUse Photo Manager to add photos")
            return

        # Add photos to the list
        for photo in photos:
            self.photo_list.add_option(f"📷 {photo.name}")

        self.photo_info.update(f"📸 {len(photos)} photos in diary")
        
        # English, visually distinct help text
        help_text = (
            "[b]⌨️  Sidebar Shortcuts[/b]\n"
            "[b][green]i[/green][/b]: Insert photo into entry\n"
            "[b][green]n[/green][/b]: Add new photo\n"
            "[b][green]d[/green][/b]: Delete selected photo\n"
            "[b][green]e[/green][/b]: Edit selected photo\n"
            "[b][yellow]Tab[/yellow][/b]: Back to editor\n"
            "[b][yellow]F8[/yellow][/b]: Show/hide sidebar\n"
            "[b][yellow]F9[/yellow][/b]: Focus Sidebar/Editor"
        )
        self.help_text.update(help_text)

    def _load_photos_for_diary(self, diary_id: int) -> List[Photo]:
        """Loads all photos for the specific diary"""
        try:
            service_manager = self.app.service_manager
            photo_service = service_manager.get_photo_service()
            
            all_photos = photo_service.read_all()
            photos = [photo for photo in all_photos if photo.fk_travel_diary_id == diary_id]
            photos.sort(key=lambda x: x.id)
            return photos
        except Exception as e:
            self.notify(f"Error loading photos: {str(e)}")
            return []

    def action_toggle_sidebar(self):
        """Toggles the sidebar visibility"""
        print("DEBUG: TOGGLE SIDEBAR", self.sidebar_visible)
        self.sidebar_visible = not self.sidebar_visible
        
        if self.sidebar_visible:
            self.sidebar.display = True
            self._update_sidebar_content()
            # Notification when opening the sidebar for the first time
            if not self._sidebar_opened_once:
                self.notify(
                    "Sidebar opened! Context-specific shortcuts are always visible in the sidebar help panel.",
                    severity="info"
                )
                self._sidebar_opened_once = True
        else:
            self.sidebar.display = False
            self.sidebar_focused = False  # Reset focus when hiding
            self.text_entry.focus()  # Return focus to editor
        
        # Update footer after context change
        self._update_footer_context()
        self.refresh(layout=True)

    def action_toggle_focus(self):
        """Toggles focus between editor and sidebar"""
        print("DEBUG: TOGGLE FOCUS", self.sidebar_visible, self.sidebar_focused)
        if not self.sidebar_visible:
            # If sidebar is not visible, show it and focus it
            self.action_toggle_sidebar()
            return
        
        self.sidebar_focused = not self.sidebar_focused
        if self.sidebar_focused:
            self.photo_list.focus()
        else:
            self.text_entry.focus()
        
        # Update footer after focus change
        self._update_footer_context()

    def action_insert_photo(self):
        """Insert selected photo into text"""
        if not self.sidebar_focused or not self.sidebar_visible:
            self.notify("Use F9 to focus the sidebar before using this shortcut.", severity="warning")
            return
            
        # Get selected photo
        if self.photo_list.highlighted is None:
            self.notify("No photo selected", severity="warning")
            return
            
        photos = self._load_photos_for_diary(self.diary_id)
        if self.photo_list.highlighted >= len(photos):
            return
            
        selected_photo = photos[self.photo_list.highlighted]
        
        # Insert photo reference into text
        photo_ref = f"\n[📷 {selected_photo.name}]({selected_photo.filepath})\n"
        if selected_photo.caption:
            photo_ref += f"*{selected_photo.caption}*\n"
        
        # Insert at cursor position or at end
        current_text = self.text_entry.text
        cursor_position = len(current_text)  # Insert at end for now
        new_text = current_text + photo_ref
        self.text_entry.text = new_text
        
        self.notify(f"Inserted photo: {selected_photo.name}")

    def action_ingest_new_photo(self):
        """Ingest a new photo using modal"""
        if not self.sidebar_focused or not self.sidebar_visible:
            self.notify("Use F9 to focus the sidebar before using this shortcut.", severity="warning")
            return
        
        # Open add photo modal
        self.app.push_screen(
            AddPhotoModal(diary_id=self.diary_id),
            self.handle_add_photo_result
        )

    def handle_add_photo_result(self, result: dict | None) -> None:
        """Callback that processes the add photo modal result."""
        if result is None:
            self.notify("Add photo cancelled")
            return

        # Schedule async creation
        self.call_later(self._async_create_photo, result)

    async def _async_create_photo(self, photo_data: dict):
        """Creates a new photo asynchronously"""
        try:
            service_manager = self.app.service_manager
            photo_service = service_manager.get_photo_service()

            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            new_photo = photo_service.create(
                filepath=Path(photo_data["filepath"]),
                name=photo_data["name"],
                travel_diary_id=self.diary_id,
                addition_date=current_date,
                caption=photo_data["caption"]
            )

            if new_photo:
                self.notify(f"Photo '{new_photo.name}' added successfully!")
                # Refresh sidebar content
                if self.sidebar_visible:
                    self._update_sidebar_content()
            else:
                self.notify("Error creating photo")

        except Exception as e:
            self.notify(f"Error creating photo: {str(e)}")

    def action_delete_photo(self):
        """Delete selected photo"""
        if not self.sidebar_focused or not self.sidebar_visible:
            self.notify("Use F9 to focus the sidebar before using this shortcut.", severity="warning")
            return
            
        if self.photo_list.highlighted is None:
            self.notify("No photo selected", severity="warning")
            return
            
        photos = self._load_photos_for_diary(self.diary_id)
        if self.photo_list.highlighted >= len(photos):
            return
            
        selected_photo = photos[self.photo_list.highlighted]
        
        # Confirm deletion
        self.notify(f"Deleting photo: {selected_photo.name}")
        
        # Schedule async deletion
        self.call_later(self._async_delete_photo, selected_photo)

    async def _async_delete_photo(self, photo: Photo):
        """Deletes a photo asynchronously"""
        try:
            service_manager = self.app.service_manager
            photo_service = service_manager.get_photo_service()

            result = photo_service.delete(photo)

            if result:
                self.notify(f"Photo '{photo.name}' deleted successfully!")
                # Refresh sidebar content
                if self.sidebar_visible:
                    self._update_sidebar_content()
            else:
                self.notify("Error deleting photo")

        except Exception as e:
            self.notify(f"Error deleting photo: {str(e)}")

    def action_edit_photo(self):
        """Edit selected photo using modal"""
        if not self.sidebar_focused or not self.sidebar_visible:
            self.notify("Use F9 to focus the sidebar before using this shortcut.", severity="warning")
            return
            
        if self.photo_list.highlighted is None:
            self.notify("No photo selected", severity="warning")
            return
            
        photos = self._load_photos_for_diary(self.diary_id)
        if self.photo_list.highlighted >= len(photos):
            return
            
        selected_photo = photos[self.photo_list.highlighted]
        
        # Open edit photo modal
        self.app.push_screen(
            EditPhotoModal(photo=selected_photo),
            self.handle_edit_photo_result
        )

    def handle_edit_photo_result(self, result: dict | None) -> None:
        """Callback that processes the edit photo modal result."""
        if result is None:
            self.notify("Edit photo cancelled")
            return

        # Get the selected photo
        photos = self._load_photos_for_diary(self.diary_id)
        if self.photo_list.highlighted is None or self.photo_list.highlighted >= len(photos):
            self.notify("Photo no longer available", severity="error")
            return
            
        selected_photo = photos[self.photo_list.highlighted]
        
        # Schedule async update
        self.call_later(self._async_update_photo, selected_photo, result)

    async def _async_update_photo(self, original_photo: Photo, photo_data: dict):
        """Updates a photo asynchronously"""
        try:
            service_manager = self.app.service_manager
            photo_service = service_manager.get_photo_service()

            # Create updated photo object
            updated_photo = Photo(
                filepath=photo_data["filepath"],
                name=photo_data["name"],
                addition_date=original_photo.addition_date,
                caption=photo_data["caption"],
                entries=original_photo.entries,
                id=original_photo.id
            )

            result = photo_service.update(original_photo, updated_photo)

            if result:
                self.notify(f"Photo '{updated_photo.name}' updated successfully!")
                # Refresh sidebar content
                if self.sidebar_visible:
                    self._update_sidebar_content()
            else:
                self.notify("Error updating photo")

        except Exception as e:
            self.notify(f"Error updating photo: {str(e)}")

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handles photo selection in the sidebar"""
        if not self.sidebar_visible:
            return
        # If 'Ingest Photo' is selected (always index 0)
        if event.option_index == 0:
            self.action_ingest_new_photo()
            return
        photos = self._load_photos_for_diary(self.diary_id)
        # Adjust index because of 'Ingest Photo' at the top
        photo_index = event.option_index - 1
        if not photos or photo_index >= len(photos):
            return
        selected_photo = photos[photo_index]
        self.notify(f"Selected photo: {selected_photo.name}")
        # Update photo info with details
        photo_details = f"📷 {selected_photo.name}\n"
        photo_details += f"📅 {selected_photo.addition_date}\n"
        if selected_photo.caption:
            photo_details += f"💬 {selected_photo.caption}\n"
        photo_details += f"📁 {selected_photo.filepath}"
        self.photo_info.update(photo_details)

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

    def on_focus(self, event) -> None:
        """Captures focus changes to update footer"""
        # Check if focus changed to/from sidebar
        if hasattr(event.widget, 'id'):
            if event.widget.id == "photo_list":
                self.sidebar_focused = True
                self._update_footer_context()
            elif event.widget.id == "text_entry":
                self.sidebar_focused = False
                self._update_footer_context()

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

            current_date = datetime.now()

            new_entry = entry_service.create(
                travel_diary_id=self.diary_id,
                title=self.new_entry_title,
                text=content,
                date=current_date
            )

            if new_entry:
                self.entries.append(new_entry)
                self.entries.sort(key=lambda x: x.id)

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

    def on_key(self, event):
        # Sidebar contextual shortcuts
        if self.sidebar_focused and self.sidebar_visible:
            if event.key == "i":
                self.action_insert_photo()
                event.stop()
            elif event.key == "n":
                self.action_ingest_new_photo()
                event.stop()
            elif event.key == "d":
                self.action_delete_photo()
                event.stop()
            elif event.key == "e":
                self.action_edit_photo()
                event.stop()
        # Shift+Tab: remove indent
        elif self.focused is self.text_entry and event.key == "shift+tab":
            textarea = self.text_entry
            row, col = textarea.cursor_location
            lines = textarea.text.splitlines()
            if row < len(lines):
                line = lines[row]
                if line.startswith('\t'):
                    lines[row] = line[1:]
                    textarea.text = '\n'.join(lines)
                    textarea.cursor_location = (row, max(col - 1, 0))
                elif line.startswith('    '):  # 4 spaces
                    lines[row] = line[4:]
                    textarea.text = '\n'.join(lines)
                    textarea.cursor_location = (row, max(col - 4, 0))
                elif line.startswith(' '):
                    n = len(line) - len(line.lstrip(' '))
                    to_remove = min(n, 4)
                    lines[row] = line[to_remove:]
                    textarea.text = '\n'.join(lines)
                    textarea.cursor_location = (row, max(col - to_remove, 0))
            event.stop()
        # Tab: insert tab
        elif self.focused is self.text_entry and event.key == "tab":
            self.text_entry.insert('\t')
            event.stop() 