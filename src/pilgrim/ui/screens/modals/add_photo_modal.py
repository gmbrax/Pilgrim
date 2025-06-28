import os
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
            self.result = {
                "filepath": filepath.strip(),
                "name": name.strip(),
                "caption": caption.strip() if caption.strip() else None
            }
            self.dismiss()
        elif event.button.id == "cancel-button":
            self.dismiss()

    def handle_file_picker_result(self, result: str | None) -> None:
        if result:
            self.query_one("#filepath-input", Input).value = result 