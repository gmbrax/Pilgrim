from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Input, Button
from textual.containers import Container, Horizontal
from pilgrim.models.photo import Photo
import hashlib

class EditPhotoModal(Screen):
    """Modal for editing an existing photo (name and caption only)"""
    def __init__(self, photo: Photo):
        super().__init__()
        self.photo = photo
        self.result = None



    def compose(self) -> ComposeResult:
        # Generate hash for this photo
        photo_hash = None
        
        yield Container(
            Static("✏️ Edit Photo", classes="EditPhotoModal-Title"),
            Static("File path (read-only):", classes="EditPhotoModal-Label"),
            Input(
                value=self.photo.filepath, 
                id="filepath-input", 
                classes="EditPhotoModal-Input",
                disabled=True
            ),
            Static("Photo name:", classes="EditPhotoModal-Label"),
            Input(
                value=self.photo.name, 
                placeholder="Enter photo name...", 
                id="name-input", 
                classes="EditPhotoModal-Input"
            ),
            Static("Caption (optional):", classes="EditPhotoModal-Label"),
            Input(
                value=self.photo.caption or "", 
                placeholder="Enter caption...", 
                id="caption-input", 
                classes="EditPhotoModal-Input"
            ),
            Static(f"🔗 Photo Hash: {self.photo.photo_hash[:8]}", classes="EditPhotoModal-Hash"),
            Static("Reference formats:", classes="EditPhotoModal-Label"),
            Static(f"\\[\\[photo::{self.photo.photo_hash[:8]}\\]\\]", classes="EditPhotoModal-Reference"),
            Horizontal(
                Button("Save Changes", id="save-button", classes="EditPhotoModal-Button"),
                Button("Cancel", id="cancel-button", classes="EditPhotoModal-Button"),
                classes="EditPhotoModal-Buttons"
            ),
            classes="EditPhotoModal-Dialog"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-button":
            name = self.query_one("#name-input", Input).value
            caption = self.query_one("#caption-input", Input).value
            
            if not name.strip():
                self.notify("Photo name is required", severity="error")
                return
            
            # Return the updated photo data
            self.result = {
                "filepath": self.photo.filepath,  # Keep original filepath
                "name": name.strip(),
                "caption": caption.strip() if caption.strip() else None
            }
            self.dismiss(self.result)
            
        elif event.button.id == "cancel-button":
            self.dismiss()

    def on_mount(self) -> None:
        """Focus on the name input when modal opens"""
        self.query_one("#name-input", Input).focus() 