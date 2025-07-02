from typing import Optional, List
import asyncio
from datetime import datetime
from pathlib import Path
import hashlib
import re
import time

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, TextArea, OptionList, Input, Button
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer

from pilgrim.models.entry import Entry
from pilgrim.models.travel_diary import TravelDiary
from pilgrim.models.photo import Photo
from pilgrim.ui.screens.modals.add_photo_modal import AddPhotoModal
from pilgrim.ui.screens.modals.edit_photo_modal import EditPhotoModal
from pilgrim.ui.screens.modals.confirm_delete_modal import ConfirmDeleteModal
from pilgrim.ui.screens.modals.file_picker_modal import FilePickerModal
from pilgrim.ui.screens.rename_entry_modal import RenameEntryModal


class EditEntryScreen(Screen):
    TITLE = "Pilgrim - Edit"

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+s", "save", "Save"),
        ("ctrl+n", "new_entry", "New Entry"),
        ("ctrl+shift+n", "next_entry", "Next Entry"),
        ("ctrl+shift+p", "prev_entry", "Previous Entry"),
        ("ctrl+r", "rename_entry", "Rename Entry"),
        ("f8", "toggle_sidebar", "Toggle Photos"),
        ("f9", "toggle_focus", "Toggle Focus"),
        ("escape", "back_to_list", "Back to List"),
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

    def _generate_photo_hash(self, photo: Photo) -> str:
        """Generate a short, unique hash for a photo"""
        unique_string = f"{photo.name}_{photo.id}_{photo.addition_date}"
        hash_object = hashlib.md5(unique_string.encode())
        return hash_object.hexdigest()[:8]

    def _fuzzy_search(self, query: str, photos: List[Photo]) -> List[Photo]:
        """Fuzzy search for photos by name or hash"""
        if not query:
            return []
        
        query = query.lower()
        results = []
        
        for photo in photos:
            photo_hash = self._generate_photo_hash(photo)
            photo_name = photo.name.lower()
            
            # Check if query is in name (substring match)
            if query in photo_name:
                results.append((photo, 1, f"Name match: {query} in {photo.name}"))
                continue
            
            # Check if query is in hash (substring match)
            if query in photo_hash:
                results.append((photo, 2, f"Hash match: {query} in {photo_hash}"))
                continue
            
            # Fuzzy match for name (check if all characters are present in order)
            if self._fuzzy_match(query, photo_name):
                results.append((photo, 3, f"Fuzzy name match: {query} in {photo.name}"))
                continue
            
            # Fuzzy match for hash
            if self._fuzzy_match(query, photo_hash):
                results.append((photo, 4, f"Fuzzy hash match: {query} in {photo_hash}"))
                continue
        
        # Sort by priority (lower number = higher priority)
        results.sort(key=lambda x: x[1])
        return [photo for photo, _, _ in results]

    def _fuzzy_match(self, query: str, text: str) -> bool:
        """Check if query characters appear in text in order (fuzzy match)"""
        if not query:
            return True
        
        query_idx = 0
        for char in text:
            if query_idx < len(query) and char == query[query_idx]:
                query_idx += 1
                if query_idx == len(query):
                    return True
        return False

    def _show_photo_tooltip(self, hash_value: str, cursor_position: tuple = None):
        """Show tooltip with photo info when typing hash"""
        # Temporarily disabled - using notifications instead
        pass

    def _hide_tooltip(self):
        """Hide the current tooltip"""
        # Temporarily disabled
        pass

    def _check_hash_tooltips(self, text: str):
        """Check for hash patterns and show tooltips"""
        # Temporarily disabled - using notifications instead
        pass

    def _get_cursor_position(self) -> tuple:
        """Get current cursor position for tooltip placement"""
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

    def _update_photo_notification(self, message: str, severity: str = "info", timeout: int = 5):
        """Update existing notification or create new one"""
        # Cancel previous timer if exists
        if self._notification_timer:
            self._notification_timer.stop()
            self._notification_timer = None
        
        # Update existing notification or create new one
        if self._active_notification:
            # Try to update existing notification
            try:
                self._active_notification.update(message)
                print(f"DEBUG: Updated existing notification: {message}")
            except:
                # If update fails, create new notification
                self._active_notification = self.notify(message, severity=severity, timeout=timeout)
                print(f"DEBUG: Created new notification: {message}")
        else:
            # Create new notification
            self._active_notification = self.notify(message, severity=severity, timeout=timeout)
            print(f"DEBUG: Created new notification: {message}")
        
        # Set timer to clear notification after inactivity
        self._notification_timer = self.set_timer(timeout, self._clear_photo_notification)
    
    def _show_photo_suggestion(self, message: str, timeout: int = 5):
        # Temporarily disabled
        pass
    
    def _hide_photo_suggestion(self):
        # Temporarily disabled
        pass

    def _clear_photo_notification(self):
        """Clear the active photo notification"""
        self._active_notification = None
        self._notification_timer = None
        print("DEBUG: Cleared photo notification")

    def _resolve_photo_references(self, text: str) -> str:
        """Resolve photo references in text to actual photo information"""
        def replace_photo_ref(match):
            name_part = match.group(1) if match.group(1) else ""
            hash_part = match.group(2)
            
            photos = self._load_photos_for_diary(self.diary_id)
            
            # Find photo by hash (most reliable)
            matching_photos = [p for p in photos if self._generate_photo_hash(p) == hash_part]
            
            if matching_photos:
                photo = matching_photos[0]
                return f"\n[📷 {photo.name}]({photo.filepath})\n" + (f"*{photo.caption}*\n" if photo.caption else "")
            else:
                return f"\n[❌ Photo not found: hash={hash_part}]\n"
        
        # Match both formats: [[photo:name:hash]] and [[photo::hash]]
        return re.sub(r'\[\[photo:([^:]*):([a-f0-9]{8})\]\]', replace_photo_ref, text)

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
            photos = self._load_photos_for_diary(self.diary_id)

            # Clear existing options safely
            self.photo_list.clear_options()

            # Add 'Ingest Photo' option at the top
            self.photo_list.add_option("➕ Ingest Photo")

            if not photos:
                self.photo_info.update("No photos found for this diary")
                self.help_text.update("📸 No photos available\n\nUse Photo Manager to add photos")
                return

            # Add photos to the list with hash
            for photo in photos:
                # Show name and hash in the list
                photo_hash = self._generate_photo_hash(photo)
                self.photo_list.add_option(f"📷 {photo.name} \\[{photo_hash}\\]")

            self.photo_info.update(f"📸 {len(photos)} photos in diary")
            
            # Updated help text with hash information
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
            
        # Get selected photo
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
        photo_hash = self._generate_photo_hash(selected_photo)
        
        # Insert photo reference using hash format without escaping
        # Using raw string to avoid markup conflicts with [[
        photo_ref = f"[[photo::{photo_hash}]]"
        
        # Insert at cursor position
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
        self.app.push_screen(
            AddPhotoModal(diary_id=self.diary_id),
            self.handle_add_photo_result
        )

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
            # Get the selected photo with adjusted index
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

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handles photo selection in the sidebar"""
        if not self.sidebar_visible:
            return
            
        photos = self._load_photos_for_diary(self.diary_id)
        if not photos or event.option_index <= 0:  # Skip 'Ingest Photo' option
            return
            
        # Adjust index because of 'Ingest Photo' at the top
        photo_index = event.option_index - 1
        if photo_index >= len(photos):
            return
            
        selected_photo = photos[photo_index]
        photo_hash = self._generate_photo_hash(selected_photo)
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
            
            # Check for hash patterns and show tooltips
            self._check_hash_tooltips(current_content)
            
            # Check for photo reference pattern
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
        print("DEBUG: on_key called with", event.key, "sidebar_focused:", self.sidebar_focused, "sidebar_visible:", self.sidebar_visible)
        # Sidebar contextual shortcuts
        if self.sidebar_focused and self.sidebar_visible:
            print("DEBUG: Processing sidebar shortcut for key:", event.key)
            if event.key == "i":
                print("DEBUG: Calling action_insert_photo")
                self.action_insert_photo()
                event.stop()
            elif event.key == "n":
                print("DEBUG: Calling action_ingest_new_photo")
                self.action_ingest_new_photo()
                event.stop()
            elif event.key == "d":
                print("DEBUG: Calling action_delete_photo")
                self.action_delete_photo()
                event.stop()
            elif event.key == "e":
                print("DEBUG: Calling action_edit_photo")
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