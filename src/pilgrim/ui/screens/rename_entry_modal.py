from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Label, Input, Button


class RenameEntryModal(ModalScreen[str]):
    """A modal screen to rename a diary entry."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, current_name: str):
        super().__init__()
        self._current_name = current_name
        self.name_input = Input(
            value=self._current_name,
            placeholder="Type the new name...",
            id="rename_input",
            classes="RenameEntryModal-name-input"
        )

    def compose(self) -> ComposeResult:
        with Vertical(id="rename_entry_dialog", classes="RenameEntryModal-dialog"):
            yield Label("Rename Entry", classes="dialog-title RenameEntryModal-title")
            yield Label("New Entry Title:", classes="RenameEntryModal-label")
            yield self.name_input
            with Horizontal(classes="dialog-buttons RenameEntryModal-buttons"):
                yield Button("Save", variant="primary", id="save", classes="RenameEntryModal-save-button")
                yield Button("Cancel", variant="default", id="cancel", classes="RenameEntryModal-cancel-button")

    def on_mount(self) -> None:
        """Focuses on the input when the screen is mounted."""
        self.name_input.focus()
        self.name_input.cursor_position = len(self.name_input.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handles button clicks."""
        if event.button.id == "save":
            new_name = self.name_input.value.strip()
            if new_name:
                self.dismiss(new_name)  # Returns the new name
            else:
                self.dismiss(None)  # Considers empty name as cancellation
        else:
            self.dismiss(None)  # Returns None for cancellation

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Allows saving by pressing Enter."""
        new_name = event.value.strip()
        if new_name:
            self.dismiss(new_name)
        else:
            self.dismiss(None)
    
    def action_cancel(self) -> None:
        self.dismiss(None) 