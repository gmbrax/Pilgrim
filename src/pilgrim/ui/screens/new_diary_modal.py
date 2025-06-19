from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Label, Input, Button

class NewDiaryModal(ModalScreen[str]):
    BINDINGS = [
        ("escape", "cancel", "Cancelar"),
    ]
    def __init__(self):
        super().__init__()
        self.name_input = Input(id="NewDiaryModal-NameInput") # This ID is fine, it's specific to the input

    def compose(self) -> ComposeResult:
        # CHANGE THIS LINE: Use the ID that matches your CSS
        with Vertical(id="new_diary_dialog"): # <--- Changed ID here to match CSS
            yield Label("Create a new diary", classes="dialog-title")
            yield Label("Diary Name:")
            yield self.name_input
            with Horizontal(classes="dialog-buttons"):
                yield Button("Create", variant="primary", id="create_diary_button")
                yield Button("Cancel", variant="default", id="cancel_button")

    def on_mount(self):
          self.name_input.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Lida com os cliques dos botões."""
        if event.button.id == "create_diary_button":
            diary_name = self.name_input.value.strip()
            if diary_name:
                self.dismiss(diary_name)
            else:
                self.notify("O nome do diário não pode estar vazio.", severity="warning")
                self.name_input.focus()
        elif event.button.id == "cancel_button":
            self.dismiss("")

    def action_cancel(self) -> None:
        """Ação para cancelar a modal."""
        self.dismiss("")