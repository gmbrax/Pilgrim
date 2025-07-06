from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Label, Input, Button


class EditDiaryModal(ModalScreen[tuple[int,str]]):
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, diary_id: int):
        super().__init__()
        self.diary_id = diary_id
        self.current_diary_name = self.app.service_manager.get_travel_diary_service().read_by_id(self.diary_id).name
        self.name_input = Input(value=self.current_diary_name, id="edit_diary_name_input", classes="EditDiaryModal-NameInput")

    def compose(self) -> ComposeResult:
        with Vertical(id="edit_diary_dialog", classes="EditDiaryModal-Dialog"):
            yield Label("Edit Diary", classes="EditDiaryModal-Title")
            yield Label("New Diary Name:")
            yield self.name_input
            with Horizontal(classes="EditDiaryModal-ButtonsContainer"):
                yield Button("Save", variant="primary", id="save_diary_button", classes="EditDiaryModal-SaveButton")
                yield Button("Cancel", variant="default", id="cancel_button", classes="EditDiaryModal-CancelButton")

    def on_mount(self) -> None:
        """Focuses on the input field and moves cursor to the end of text."""
        self.name_input.focus()
        self.name_input.cursor_position = len(self.name_input.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save_diary_button":
            new_diary_name = self.name_input.value.strip()
            if new_diary_name and new_diary_name != self.current_diary_name:
                self.dismiss((self.diary_id, new_diary_name))
            elif new_diary_name == self.current_diary_name:
                self.notify("No changes made.", severity="warning")
                self.dismiss(None)
            else:
                self.notify("Diary name cannot be empty.", severity="warning")
                self.name_input.focus()
        elif event.button.id == "cancel_button":
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)