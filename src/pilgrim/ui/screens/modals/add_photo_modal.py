from pathlib import Path
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Input, Button
from textual.containers import Horizontal, Container
from .file_picker_modal import FilePickerModal

class AddPhotoModal(Screen):
    """Modal for adding a new photo"""
    def __init__(self, diary_id: int):
        super().__init__()
        self.diary_id = diary_id
        self.result = None
        self.created_photo = None


    def compose(self) -> ComposeResult:
        yield Container(
            Static("📷 Add New Photo", classes="AddPhotoModal-Title"),
            Static("File path:", classes="AddPhotoModal-Label"),
            Horizontal(
                Input(placeholder="Enter file path...", id="filepath-input", classes="AddPhotoModal-Input"),
                Button("Escolher arquivo...", id="choose-file-button", classes="AddPhotoModal-Button"),
                classes="AddPhotoModal-FileRow"
            ),
            Static("Photo name:", classes="AddPhotoModal-Label"),
            Input(placeholder="Enter photo name...", id="name-input", classes="AddPhotoModal-Input"),
            Static("Caption (optional):", classes="AddPhotoModal-Label"),
            Input(placeholder="Enter caption...", id="caption-input", classes="AddPhotoModal-Input"),
            Horizontal(
                Button("Add Photo", id="add-button", classes="AddPhotoModal-Button"),
                Button("Cancel", id="cancel-button", classes="AddPhotoModal-Button"),
                classes="AddPhotoModal-Buttons"
            ),
            classes="AddPhotoModal-Dialog"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "choose-file-button":
            self.app.push_screen(
                FilePickerModal(),
                self.handle_file_picker_result
            )
            return
        if event.button.id == "add-button":
            filepath = self.query_one("#filepath-input", Input).value
            name = self.query_one("#name-input", Input).value
            caption = self.query_one("#caption-input", Input).value
            if not filepath.strip() or not name.strip():
                self.notify("File path and name are required", severity="error")
                return
            
            # Try to create the photo in the database
            self.call_later(self._async_create_photo, {
                "filepath": filepath.strip(),
                "name": name.strip(),
                "caption": caption.strip() if caption.strip() else None
            })
        elif event.button.id == "cancel-button":
            self.dismiss()

    async def _async_create_photo(self, photo_data: dict):
        """Creates a new photo asynchronously using PhotoService"""


        try:
            service_manager = self.app.service_manager
            photo_service = service_manager.get_photo_service()

            if photo_service.check_photo_by_hash(photo_service.hash_file(photo_data["filepath"]),self.diary_id):
                self.notify("Photo already exists in database", severity="error")
                return

            new_photo = photo_service.create(
                filepath=Path(photo_data["filepath"]),
                name=photo_data["name"],
                travel_diary_id=self.diary_id,
                caption=photo_data["caption"]
            )

            if new_photo:
                self.created_photo = new_photo

                
                self.notify(f"Photo '{new_photo.name}' added successfully!\nHash: {new_photo.photo_hash[:8]}\nReference: \\[\\[photo:{new_photo.name}:{new_photo.photo_hash[:8]}\\]\\]",
                           severity="information", timeout=5)
                
                # Return the created photo data to the calling screen
                self.result = {
                    "filepath": photo_data["filepath"],
                    "name": photo_data["name"],
                    "caption": photo_data["caption"],
                    "photo_id": new_photo.id,
                    "hash": new_photo.photo_hash
                }
                self.dismiss(self.result)
            else:
                self.notify("Error creating photo in database", severity="error")

        except Exception as e:
            self.notify(f"Error creating photo: {str(e)}", severity="error")

    def handle_file_picker_result(self, result: str | None) -> None:
        if result:
            # Set the filepath input value
            filepath_input = self.query_one("#filepath-input", Input)
            filepath_input.value = result
            # Trigger the input change event to update the UI
            filepath_input.refresh()
            # Auto-fill the name field with the filename (without extension)
            filename = Path(result).stem
            name_input = self.query_one("#name-input", Input)
            if not name_input.value.strip():
                name_input.value = filename
                name_input.refresh()
        else:
            # User cancelled the file picker
            self.notify("File selection cancelled", severity="information") 