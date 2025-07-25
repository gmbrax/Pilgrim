import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from pilgrim.models.entry import Entry
from pilgrim.models.photo import Photo
from pilgrim.ui.screens.modals.add_photo_modal import AddPhotoModal
from pilgrim.ui.screens.modals.confirm_delete_modal import ConfirmDeleteModal
from pilgrim.ui.screens.modals.edit_photo_modal import EditPhotoModal
from pilgrim.ui.screens.rename_entry_modal import RenameEntryModal

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, TextArea, OptionList

from pilgrim.ui.screens.widgets.photo_sidebar import PhotoSidebar


class EditEntryScreen(Screen):
    TITLE = "Pilgrim - Edit"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+s", "save", "Save"),
        Binding("shift+f5", "new_entry", "New Entry"),
        Binding("f5", "next_entry", "Next Entry"),
        Binding("f4", "prev_entry", "Previous Entry"),
        Binding("ctrl+r", "rename_entry", "Rename Entry"),
        Binding("f8", "toggle_sidebar", "Toggle Photos"),
        Binding("f9", "toggle_focus", "Toggle Focus"),
        Binding("escape", "back_to_list", "Back to List"),
    ]

    def __init__(self, diary_id: int = 1,create_new: bool = True):
        super().__init__()

        if create_new:
            self.current_entry_index = -1
            self.is_new_entry = True
            self.next_entry_id = None

        else:
            self.is_new_entry = False
            self.current_entry_index = 0
            self.next_entry_id = 1
        self.new_entry_title = ""
        self.new_entry_content = ""
        self.diary_id = diary_id
        self.diary_name = f"Diary {diary_id}"
        self.entries: List[Entry] = []
        self.has_unsaved_changes = False
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

        self.sidebar = PhotoSidebar()

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
        except Exception:
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
            if self.has_unsaved_changes:
                self._update_status_indicator("Not Saved", "not-saved")
            else:
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

    def action_toggle_sidebar(self):
        self.sidebar_visible = not self.sidebar_visible
        self.sidebar.display = self.sidebar_visible
        if self.sidebar_visible:
            # Chama o novo worker síncrono
            self.run_worker(self._load_and_update_sidebar_worker, exclusive=True, thread=True)

            self.sidebar.focus()
        else:
            self.text_entry.focus()

    def _load_and_update_sidebar_worker(self):
        """
        Worker que roda em uma thread para carregar as fotos sem travar a UI.
        """
        # A lógica de buscar os dados pode ser feita diretamente    ,
        # pois já estamos em uma thread de segundo plano.
        photo_service = self.app.service_manager.get_photo_service()
        all_photos = photo_service.read_all()
        self.cached_photos = [p for p in all_photos if p.fk_travel_diary_id == self.diary_id]

        # MUDANÇA 2: Não podemos atualizar a UI diretamente de outra thread.
        # Usamos 'call_from_thread' para agendar a atualização de forma segura.
        self.app.call_from_thread(self.sidebar.update_photo_list, self.cached_photos)

    def on_photo_sidebar_insert_photo_reference(self, message: PhotoSidebar.InsertPhotoReference):
        """Reage à mensagem para inserir uma referência de foto."""
        photo_ref = f"[[photo::{message.photo_hash}]]"
        self.text_entry.insert(photo_ref)
        self.text_entry.focus()

    def on_photo_sidebar_ingest_new_photo(self, message: PhotoSidebar.IngestNewPhoto):
        """Reage à mensagem para ingerir uma nova foto."""

        def refresh_sidebar_after_add(result):
            if result:
                self.notify(f"Photo '{result['name']}' added successfully!")
                self.run_worker(self._load_and_update_sidebar)

        self.app.push_screen(
            AddPhotoModal(diary_id=self.diary_id),
            refresh_sidebar_after_add
        )

    def on_photo_sidebar_edit_photo(self, message: PhotoSidebar.EditPhoto):
        """Reage à mensagem para editar uma foto."""

        def refresh_sidebar_after_edit(result):
            if result:
                self.notify(f"Photo '{result['name']}' updated successfully!")
                self.run_worker(self._load_and_update_sidebar)

        self.app.push_screen(
            EditPhotoModal(photo=message.photo),
            refresh_sidebar_after_edit
        )

    def on_photo_sidebar_delete_photo(self, message: PhotoSidebar.DeletePhoto):
        """Reage à mensagem para deletar uma foto."""

        def refresh_sidebar_after_delete(result):
            if result:
                self.notify(f"Photo '{message.photo.name}' deleted successfully!")
                self.run_worker(self._load_and_update_sidebar)

        self.app.push_screen(
            ConfirmDeleteModal(photo=message.photo),
            refresh_sidebar_after_delete
        )

    def action_toggle_focus(self):
        """Toggles focus between editor and sidebar"""
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
        photo_details = f"Name: {selected_photo.name}\n"
        photo_details += f"Hash: {photo_hash}\n"
        photo_details += f"Date: {selected_photo.addition_date}\n"
        if selected_photo.caption:
            photo_details += f"Caption: {selected_photo.caption}\n"
        else:
            photo_details += "Caption: No Caption\n"
        photo_details += "[b]Reference formats:[/b]\n"
        photo_details += f"\\[\\[photo::{photo_hash}]]"

        self.photo_info.update(photo_details)

    def on_text_area_changed(self, event) -> None:
        """Detects text changes and updates status"""
        # Skip if we're currently updating the display
        if getattr(self, '_updating_display', False):
            return
            
        # Skip if text area is read-only
        if not hasattr(self, 'text_entry') or self.text_entry.read_only:
            return
            
        # Skip if we don't have original content to compare against
        if not hasattr(self, '_original_content'):
            return
            
        current_content = self.text_entry.text
        
        # Check if content has changed
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
            if self.new_entry_title == "":
               self.app.push_screen(RenameEntryModal(current_name=""), lambda result: self._handle_save_after_rename(result,content,
                                                                                               photos_to_link))
            else:
                self.call_later(self._async_create_entry, content, photos_to_link)
        else:
            # Passe a lista de fotos para o método de atualização
            self.call_later(self._async_update_entry, content, photos_to_link)

    def _handle_save_after_rename(self, result: str | None, content: str, photos_to_link: List[Photo]) -> None:
        if result is None:
            self.notify("Save cancelled")
            return
        self.new_entry_title = result
        self.call_later(self._async_create_entry, content, photos_to_link)

    async def _async_create_entry(self, content: str, photos_to_link: List[Photo]):
        """Creates a new entry and links the referenced photos."""
        try:
            service_manager = self.app.service_manager
            entry_service = service_manager.get_entry_service()

            new_entry = entry_service.create(
                travel_diary_id=self.diary_id,
                title=self.new_entry_title,
                text=content,
                date=datetime.now(),
                photos=photos_to_link
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
                self.new_entry_title = ""
                self.next_entry_id = max(entry.id for entry in self.entries) + 1

                self._update_entry_display()
                self.notify(f"Entry '{new_entry.title}' saved successfully!")
            else:
                self.notify("Error creating entry")

        except Exception as e:
            self.notify(f"Error creating entry: {str(e)}")

    async def _async_update_entry(self, updated_content: str, photos_to_link: List[Photo]):
        """Updates an existing entry and its photo links."""
        try:
            if not self.entries:
                self.notify("No entry to update")
                return

            service_manager = self.app.service_manager
            entry_service = service_manager.get_entry_service()
            current_entry = self.entries[self.current_entry_index]

            entry_result = Entry(
                id=current_entry.id,
                title=current_entry.title,
                text=updated_content,
                photos=photos_to_link,
                date=current_entry.date,
                travel_diary_id=self.diary_id,
                fk_travel_diary_id=self.diary_id
            )

            result = entry_service.update(current_entry, entry_result)

            if result:
                self.has_unsaved_changes = False
                self._original_content = updated_content
                self._update_sub_header()
                self.notify(f"Entry '{current_entry.title}' saved successfully!")
            else:
                self.notify("Error updating entry")

        except Exception as e:
            self.notify(f"Error updating entry: {str(e)}")

    def check_key(self, event):
        """Check for custom key handling before bindings are processed"""

        # Sidebar shortcuts
        if self.sidebar_focused and self.sidebar_visible:
            sidebar_keys = ["i", "n", "d", "e"]
            if event.key in sidebar_keys:
                if event.key == "i":
                    self.action_insert_photo()
                elif event.key == "n":
                    self.action_ingest_new_photo()
                elif event.key == "d":
                    self.action_delete_photo()
                elif event.key == "e":
                    self.action_edit_photo()
                return True  # Indica que o evento foi processado

        # Text area shortcuts
        elif self.focused is self.text_entry:
            if event.key in ["tab", "shift+tab"]:
                if event.key == "shift+tab":
                    self._handle_shift_tab()
                elif event.key == "tab":
                    self.text_entry.insert('\t')
                return True  # Indica que o evento foi processado

        return False  # Não foi processado, continuar com bindings

    def _handle_shift_tab(self):
        """Handle shift+tab for removing indentation"""
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

    def on_key(self, event):
        if self.check_key(event):
            event.stop()
            return

    def on_footer_action(self, event) -> None:
        """Handle clicks on footer actions (Textual 3.x)."""
        action = event.action
        method = getattr(self, f"action_{action}", None)
        if method:
            method()
        else:
            self.notify(f"No action found for: {action}", severity="warning")