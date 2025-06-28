import os
from pathlib import Path
from typing import Iterable
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, DirectoryTree, Button
from textual.containers import Horizontal, Container

class ImageDirectoryTree(DirectoryTree):
    """DirectoryTree that only shows image files"""
    
    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        """Filter to show only directories and image files"""
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
        return [
            path for path in paths 
            if path.is_dir() or path.suffix.lower() in image_extensions
        ]

class FilePickerModal(Screen):
    """Modal for picking an image file using DirectoryTree"""
    
    def __init__(self, start_path=None):
        super().__init__()
        self.start_path = Path(start_path or os.getcwd())
        # Start one level up to make navigation easier
        self.current_path = self.start_path.parent
        self.result = None

    def compose(self) -> ComposeResult:
        yield Container(
            Static(f"Current: {self.current_path}", id="title", classes="FilePickerModal-Title"),
            ImageDirectoryTree(str(self.current_path), id="directory-tree"),
            Horizontal(
                Button("Up", id="up-button", classes="FilePickerModal-Button"),
                Button("Cancel", id="cancel-button", classes="FilePickerModal-Button"),
                classes="FilePickerModal-Buttons"
            ),
            classes="FilePickerModal-Dialog"
        )

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Handle file selection"""
        file_path = event.path
        # Check if it's an image file
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
        if file_path.suffix.lower() in image_extensions:
            self.result = str(file_path)
            self.dismiss()
        else:
            self.notify("Please select an image file", severity="warning")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "up-button":
            # Navigate to parent directory
            parent = self.current_path.parent
            if parent != self.current_path:
                self.current_path = parent
                self.query_one("#title", Static).update(f"Current: {self.current_path}")
                # Reload the directory tree
                tree = self.query_one("#directory-tree", ImageDirectoryTree)
                tree.path = str(self.current_path)
                tree.reload()
        elif event.button.id == "cancel-button":
            self.dismiss() 