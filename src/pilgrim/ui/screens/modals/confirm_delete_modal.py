from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Button
from textual.containers import Container, Horizontal
from pilgrim.models.photo import Photo

class ConfirmDeleteModal(Screen):
    """Modal for confirming photo deletion"""
    def __init__(self, photo: Photo):
        super().__init__()
        self.photo = photo
        self.result = None

    def compose(self) -> ComposeResult:
        yield Container(
            Static("🗑️ Confirm Deletion", classes="ConfirmDeleteModal-Title"),
            Static(f"Are you sure you want to delete the photo '{self.photo.name}'?", classes="ConfirmDeleteModal-Message"),
            Static("This action cannot be undone.", classes="ConfirmDeleteModal-Warning"),
            Horizontal(
                Button("Delete", variant="error", id="delete-button", classes="ConfirmDeleteModal-Button"),
                Button("Cancel", variant="default", id="cancel-button", classes="ConfirmDeleteModal-Button"),
                classes="ConfirmDeleteModal-Buttons"
            ),
            classes="ConfirmDeleteModal-Dialog"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "delete-button":
            self.result = True
            self.dismiss(True)
        elif event.button.id == "cancel-button":
            self.dismiss(False) 