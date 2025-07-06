import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from pilgrim.models.entry import Entry
from pilgrim.models.photo import Photo
from pilgrim.models.travel_diary import TravelDiary
from pilgrim.ui.screens.modals.add_photo_modal import AddPhotoModal
from pilgrim.ui.screens.modals.confirm_delete_modal import ConfirmDeleteModal
from pilgrim.ui.screens.modals.edit_photo_modal import EditPhotoModal
from pilgrim.ui.screens.modals.file_picker_modal import FilePickerModal
from pilgrim.ui.screens.rename_entry_modal import RenameEntryModal
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, TextArea, OptionList


class EditEntryScreen(Screen):
    TITLE = "Pilgrim - Edit"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+s", "save", "Save"),
        Binding("ctrl+n", "new_entry", "New Entry"),
        Binding("ctrl+shift+n", "next_entry", "Next Entry"),
        Binding("ctrl+shift+p", "prev_entry", "Previous Entry"),
        Binding("ctrl+r", "rename_entry", "Rename Entry"),
        Binding("f8", "toggle_sidebar", "Toggle Photos"),
        Binding("f9", "toggle_focus", "Toggle Focus"),
        Binding("escape", "back_to_list", "Back to List"),
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
        self._active_tooltip = None
        self._last_photo_suggestion_notification = None
        self._last_photo_suggestion_type = None
        self._active_notification = None
        self._notification_timer = None
        self.references = []
        self.cached_photos = []

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
        """Force footer refresh to show updated bindings"""
        self.refresh()

    def _get_cursor_position(self) -> tuple:
        """Get the current cursor position for tooltip placement"""
        try:
            # Get cursor position from text area
            cursor_location = self.text_entry.cursor_location
            if cursor_location:
                # Get the text area region
                text_region = self.text_entry.region
                if text_region:
                    # Calculate position relative to text area
                    # Position tooltip below the current line, not over it
                    x = text_region.x + min(cursor_location[0], text_region.width - 40)  # Keep within bounds
                    y = text_region.y + cursor_location[1] + 2  # 2 lines below cursor
                    return (x, y)
        except:
            pass
        return None


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
        # self.app.mount(self._photo_suggestion_widget)  # Temporarily disabled

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
        try:
            self._load_photos_for_diary(self.diary_id)

            # Clear existing options safely
            self.photo_list.clear_options()

            # Add the 'Ingest Photo' option at the top
            self.photo_list.add_option("➕ Ingest Photo")

            if not self.cached_photos:
                self.photo_info.update("No photos found for this diary")
                self.help_text.update("📸 No photos available\n\nUse Photo Manager to add photos")
                return

            # Add photos to the list with hash
            for photo in self.cached_photos:
                # Show name and hash in the list
                photo_hash = str(photo.photo_hash)[:8]
                self.photo_list.add_option(f"📷 {photo.name} \\[{photo_hash}\]")

            self.photo_info.update(f"📸 {len(self.cached_photos)} photos in diary")

            # Updated help a text with hash information
            help_text = (
                "[b]⌨️  Sidebar Shortcuts[/b]\n"
                "[b][green]i[/green][/b]: Insert photo into entry\n"
                "[b][green]n[/green][/b]: Add new photo\n"
                "[b][green]d[/green][/b]: Delete selected photo\n"
                "[b][green]e[/green][/b]: Edit selected photo\n"
                "[b][yellow]Tab[/yellow][/b]: Back to editor\n"
                "[b][yellow]F8[/yellow][/b]: Show/hide sidebar\n"
                "[b][yellow]F9[/yellow][/b]: Switch focus (if needed)\n\n"
                "[b]📝 Photo References[/b]\n"
                "Use: \\[\\[photo:name:hash\\]\\]\n"
                "Or: \\[\\[photo::hash\\]\\]"
            )
            self.help_text.update(help_text)
        except Exception as e:
            self.notify(f"Error updating sidebar: {str(e)}", severity="error")
            # Set fallback content
            self.photo_info.update("Error loading photos")
            self.help_text.update("Error loading sidebar content")

    def _load_photos_for_diary(self, diary_id: int):
        """Loads all photos for the specific diary"""
        try:
            service_manager = self.app.service_manager
            photo_service = service_manager.get_photo_service()

            all_photos = photo_service.read_all()
            self.cached_photos = [photo for photo in all_photos if photo.fk_travel_diary_id == diary_id]
            self.cached_photos.sort(key=lambda x: x.id)

        except Exception as e:
            self.notify(f"Error loading photos: {str(e)}")


    def action_toggle_sidebar(self):
        """Toggles the sidebar visibility"""
        try:
            print("DEBUG: TOGGLE SIDEBAR", self.sidebar_visible)
            self.sidebar_visible = not self.sidebar_visible

            if self.sidebar_visible:
                self.sidebar.display = True
                self._update_sidebar_content()
                # Automatically focus the sidebar when opening
                self.sidebar_focused = True
                self.photo_list.focus()
                # Notification when opening the sidebar for the first time
                if not self._sidebar_opened_once:
                    self.notify(
                        "Sidebar opened and focused! Use the shortcuts shown in the help panel.",
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
        except Exception as e:
            self.notify(f"Error toggling sidebar: {str(e)}", severity="error")
            # Reset state on error
            self.sidebar_visible = False
            self.sidebar_focused = False
            self.sidebar.display = False

    def action_toggle_focus(self):
        """Toggles focus between editor and sidebar"""
        print("DEBUG: TOGGLE FOCUS called", self.sidebar_visible, self.sidebar_focused)
        if not self.sidebar_visible:
            # If sidebar is not visible, show it and focus it
            print("DEBUG: Sidebar not visible, opening it")
            self.action_toggle_sidebar()
            return

        self.sidebar_focused = not self.sidebar_focused
        print("DEBUG: Sidebar focused changed to", self.sidebar_focused)
        if self.sidebar_focused:
            self.photo_list.focus()
        else:
            self.text_entry.focus()

        # Update footer after focus change
        self._update_footer_context()

    def action_insert_photo(self):
        """Insert selected photo into text"""

        if not self.sidebar_focused or not self.sidebar_visible:
            self.notify("Use F8 to open the sidebar first.", severity="warning")
            return

        # Get a selected photo
        if self.photo_list.highlighted is None:
            self.notify("No photo selected", severity="warning")
            return

        # Adjust index because of 'Ingest Photo' at the top
        photo_index = self.photo_list.highlighted - 1

        self._load_photos_for_diary(self.diary_id)
        if photo_index < 0 or photo_index >= len(self.cached_photos):
            self.notify("No photo selected", severity="warning")
            return

        selected_photo = self.cached_photos[photo_index]
        photo_hash = selected_photo.photo_hash[:8]

        # Insert photo reference using hash format without escaping
        # Using raw string to avoid markup conflicts with [[
        photo_ref = f"[[photo::{photo_hash}]]"

        # Insert at the cursor position
        self.text_entry.insert(photo_ref)

        # Switch focus back to editor
        self.sidebar_focused = False
        self.text_entry.focus()

        # Update footer context
        self._update_footer_context()

        # Show selected photo info
        photo_details = f"📷 {selected_photo.name}\n"
        photo_details += f"🔗 {photo_hash}\n"
        photo_details += f"📅 {selected_photo.addition_date}\n"
        photo_details += f"💬 {selected_photo.caption or 'No caption'}\n"
        photo_details += f"📁 {selected_photo.filepath}\n\n"
        photo_details += f"[b]Reference formats:[/b]\n"
        photo_details += f"\\[\\[photo:{selected_photo.name}:{photo_hash}\\]\\]\n"
        photo_details += f"\\[\\[photo::{photo_hash}\\]\\]"

        self.photo_info.update(photo_details)

        # Show notification without escaping brackets
        self.notify(f"Inserted photo: {selected_photo.name} \\[{photo_hash}\\]", severity="information")

    def action_ingest_new_photo(self):
        """Ingest a new photo using modal"""
        if not self.sidebar_focused or not self.sidebar_visible:
            self.notify("Use F8 to open the sidebar first.", severity="warning")
            return

        # Open add photo modal
        try:
            self.notify("Trying to push the modal screen...")
            self.app.push_screen(
                AddPhotoModal(diary_id=self.diary_id),
                self.handle_add_photo_result
            )
        except Exception as e:
            self.notify(f"Error: {str(e)}", severity="error")
            self.app.notify("Error: {str(e)}", severity="error")

    def handle_add_photo_result(self, result: dict | None) -> None:
        """Callback that processes the add photo modal result."""
        if result is None:
            self.notify("Add photo cancelled")
            return

        # Photo was already created in the modal, just refresh the sidebar
        if self.sidebar_visible:
            self._update_sidebar_content()
        self.notify(f"Photo '{result['name']}' added successfully!")

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
            self.notify("Use F8 to open the sidebar first.", severity="warning")
            return

        if self.photo_list.highlighted is None:
            self.notify("No photo selected", severity="warning")
            return

        # Adjust index because of 'Ingest Photo' at the top
        photo_index = self.photo_list.highlighted - 1

        photos = self._load_photos_for_diary(self.diary_id)
        if photo_index < 0 or photo_index >= len(photos):
            self.notify("No photo selected", severity="warning")
            return

        selected_photo = photos[photo_index]

        # Open confirm delete modal
        self.app.push_screen(
            ConfirmDeleteModal(photo=selected_photo),
            self.handle_delete_photo_result
        )

    def handle_delete_photo_result(self, result: bool) -> None:
        """Callback that processes the delete photo modal result."""
        if result:
            # Get the selected photo with an adjusted index
            photos = self._load_photos_for_diary(self.diary_id)
            photo_index = self.photo_list.highlighted - 1  # Adjust for 'Ingest Photo' at top

            if self.photo_list.highlighted is None or photo_index < 0 or photo_index >= len(photos):
                self.notify("Photo no longer available", severity="error")
                return

            selected_photo = photos[photo_index]

            # Schedule async deletion
            self.call_later(self._async_delete_photo, selected_photo)
        else:
            self.notify("Delete cancelled")

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
            self.notify("Use F8 to open the sidebar first.", severity="warning")
            return

        if self.photo_list.highlighted is None:
            self.notify("No photo selected", severity="warning")
            return

        # Adjust index because of 'Ingest Photo' at the top
        photo_index = self.photo_list.highlighted - 1

        photos = self._load_photos_for_diary(self.diary_id)
        if photo_index < 0 or photo_index >= len(photos):
            self.notify("No photo selected", severity="warning")
            return

        selected_photo = photos[photo_index]

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

        # Get the selected photo with adjusted index
        photos = self._load_photos_for_diary(self.diary_id)
        photo_index = self.photo_list.highlighted - 1  # Adjust for 'Ingest Photo' at top

        if self.photo_list.highlighted is None or photo_index < 0 or photo_index >= len(photos):
            self.notify("Photo no longer available", severity="error")
            return

        selected_photo = photos[photo_index]

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
                entries=original_photo.entries if original_photo.entries is not None else [],
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

    def _get_linked_photos_from_text(self) -> Optional[List[Photo]]:
        """
        Validates photo references in the text against the memory cache.
        Checks for:
        - Malformed references
        - Incorrect hash length
        - Invalid or ambiguous hashes
        Returns a list of unique photos (no duplicates even if referenced multiple times).
        """
        text = self.text_entry.text
        
        # First check for malformed references
        malformed_pattern = r"\[\[photo::([^\]]*)\](?!\])"  # Missing ] at the end
        malformed_matches = re.findall(malformed_pattern, text)
        if malformed_matches:
            for match in malformed_matches:
                self.notify(f"❌ Malformed reference: '\\[\\[photo::{match}\\]' - Missing closing '\\]'", severity="error", timeout=10)
            return None

        # Look for incorrect format references
        invalid_format = r"\[\[photo:[^:\]]+\]\]"  # [[photo:something]] without ::
        invalid_matches = re.findall(invalid_format, text)
        if invalid_matches:
            for match in invalid_matches:
                escaped_match = match.replace("[", "\\[").replace("]", "\\]")
                self.notify(f"❌ Invalid format: '{escaped_match}' - Use '\\[\\[photo::hash\\]\\]'", severity="error", timeout=10)
            return None

        # Now look for all references to validate
        pattern = r"\[\[photo::([^\]]+)\]\]"
        # Use set to get unique references only
        all_refs = set(re.findall(pattern, text))
        
        if not all_refs:
            return []  # No references, valid operation

        self._load_photos_for_diary(self.diary_id)
        linked_photos: List[Photo] = []
        processed_hashes = set()  # Keep track of processed hashes to avoid duplicates

        for ref in all_refs:
            # Skip if we already processed this hash
            if ref in processed_hashes:
                continue

            # Validate hash length
            if len(ref) != 8:
                self.notify(
                    f"❌ Invalid hash: '{ref}' - Must be exactly 8 characters long",
                    severity="error",
                    timeout=10
                )
                return None

            # Validate if contains only valid hexadecimal characters
            if not re.match(r"^[0-9A-Fa-f]{8}$", ref):
                self.notify(
                    f"❌ Invalid hash: '{ref}' - Use only hexadecimal characters (0-9, A-F)",
                    severity="error",
                    timeout=10
                )
                return None

            # Search for photos matching the hash
            found_photos = [p for p in self.cached_photos if p.photo_hash.startswith(ref)]

            if len(found_photos) == 0:
                self.notify(
                    f"❌ Hash not found: '{ref}' - No photo matches this hash",
                    severity="error",
                    timeout=10
                )
                return None
            elif len(found_photos) > 1:
                self.notify(
                    f"❌ Ambiguous hash: '{ref}' - Matches multiple photos",
                    severity="error",
                    timeout=10
                )
                return None
            else:
                linked_photos.append(found_photos[0])
                processed_hashes.add(ref)  # Mark this hash as processed

        # Convert list to set and back to list to ensure uniqueness of photos
        return list(set(linked_photos))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handles photo selection in the sidebar"""
        if not self.sidebar_visible:
            return

        # Handle "Ingest Photo" option
        if event.option_index == 0:  # First option is "Ingest Photo"
            self.action_ingest_new_photo()
            return

        photos = self._load_photos_for_diary(self.diary_id)
        if not photos:
            return

        # Adjust index because of 'Ingest Photo' at the top
        photo_index = event.option_index - 1
        if photo_index >= len(photos):
            return

        selected_photo = photos[photo_index]
        photo_hash = selected_photo.photo_hash[:8]
        self.notify(f"Selected photo: {selected_photo.name} \\[{photo_hash}\\]")

        # Update photo info with details including hash
        photo_details = f"📷 {selected_photo.name}\n"
        photo_details += f"🔗 {photo_hash}\n"
        photo_details += f"📅 {selected_photo.addition_date}\n"
        if selected_photo.caption:
            photo_details += f"💬 {selected_photo.caption}\n"
        photo_details += f"📁 {selected_photo.filepath}\n\n"
        photo_details += f"[b]Reference formats:[/b]\n"
        photo_details += f"\\[\\[photo:{selected_photo.name}:{photo_hash}\\]\\]\n"
        photo_details += f"\\[\\[photo::{photo_hash}\\]\\]"

        self.photo_info.update(photo_details)

    def on_text_area_changed(self, event) -> None:
        """Detects text changes and shows photo tooltips"""
        if (hasattr(self, 'text_entry') and not self.text_entry.read_only and
                not getattr(self, '_updating_display', False) and hasattr(self, '_original_content')):
            current_content = self.text_entry.text



            # Check for a photo reference pattern
            # self._check_photo_reference(current_content)  # Temporarily disabled

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
        # Check if the focus changed to/from sidebar
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
        """Salva a entrada após validar e coletar as fotos referenciadas."""
        photos_to_link = self._get_linked_photos_from_text()

        if photos_to_link is None:
            self.notify("⚠️ Saving was canceled ", severity="error")
            return

        content = self.text_entry.text.strip()
        if self.is_new_entry:
            if not content:
                self.notify("Empty entry cannot be saved")
                return
            # Passe a lista de fotos para o método de criação
            self.call_later(self._async_create_entry, content, photos_to_link)
        else:
            # Passe a lista de fotos para o método de atualização
            self.call_later(self._async_update_entry, content, photos_to_link)

    async def _async_create_entry(self, content: str, photos_to_link: List[Photo]):
        """Cria uma nova entrada e associa as fotos referenciadas."""
        service_manager = self.app.service_manager
        db_session = service_manager.get_db_session()
        try:
            entry_service = service_manager.get_entry_service()

            # O service.create deve criar o objeto em memória, mas NÃO fazer o commit ainda.
            new_entry = entry_service.create(
                travel_diary_id=self.diary_id,
                title=self.new_entry_title,
                text=content,
                date=datetime.now(),
                photos=photos_to_link
            )

            if new_entry:
               # A partir daqui, é só atualizar a UI como você já fazia
                self.entries.append(new_entry)
                self.entries.sort(key=lambda x: x.id)

                for i, entry in enumerate(self.entries):
                    if entry.id == new_entry.id:
                        self.current_entry_index = i
                        break

                self.is_new_entry = False
                self.has_unsaved_changes = False
                self._original_content = new_entry.text  # Pode ser o texto com hashes curtos
                self.new_entry_title = "New Entry"
                self.next_entry_id = max(entry.id for entry in self.entries) + 1

                self._update_entry_display()
                self.notify(f"✅ New Entry: '{new_entry.title}' Successfully saved")
            else:
                self.notify("❌ Error creating the Entry")

        except Exception as e:
            self.notify(f"❌ Error creating the entry: {str(e)}")

    async def _async_update_entry(self, updated_content: str, photos_to_link: List[Photo]):
        """Atualiza uma entrada existente e sua associação de fotos."""
        service_manager = self.app.service_manager

        try:
            if not self.entries:
                self.notify("No Entry to update")
                return
            entry_service = service_manager.get_entry_service()
            current_entry = self.entries[self.current_entry_index]
            entry_result : Entry = Entry(
                title=current_entry.title,
                text=updated_content,
                photos=photos_to_link,
                date=current_entry.date,
                travel_diary_id=self.diary_id

            )
            entry_service.update(current_entry, entry_result)

            # A partir daqui, é só atualizar a UI
            self.has_unsaved_changes = False
            self._original_content = updated_content  # Pode ser o texto com hashes curtos
            self._update_sub_header()
            self.notify(f"✅ Entry: '{current_entry.title}' sucesfully saved")

        except Exception as e:
           # Desfaz as mudanças em caso de erro
            self.notify(f"❌ Error on updating the entry:: {str(e)}")

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