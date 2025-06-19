from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Label, Input, Button


class EditDiaryModal(ModalScreen[tuple[int,str]]):
    BINDINGS = [
        ("escape", "cancel", "Cancelar"),
    ]

    def __init__(self, diary_id: int):
        super().__init__()
        self.diary_id = diary_id
        self.current_diary_name = self.app.service_manager.get_travel_diary_service().read_by_id(self.diary_id).name
        self.name_input = Input(value=self.current_diary_name, id="edit_diary_name_input")

    def compose(self) -> ComposeResult:
        with Vertical(id="edit_diary_dialog"):
            yield Label(f"Editar Diário: {self.current_diary_name}", classes="dialog-title")
            yield Label("Novo Nome do Diário:")
            yield self.name_input
            with Horizontal(classes="dialog-buttons"):
                yield Button("Salvar", variant="primary", id="save_diary_button")
                yield Button("Cancelar", variant="default", id="cancel_button")

    def on_mount(self) -> None:
        """Foca no campo de entrada e move o cursor para o final do texto."""
        self.name_input.focus()
        self.name_input.cursor_position = len(self.name_input.value)
        # REMOVIDA A LINHA QUE CAUSA O ERRO: self.name_input.select_text()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save_diary_button":
            new_diary_name = self.name_input.value.strip()
            if new_diary_name and new_diary_name != self.current_diary_name:
                self.dismiss((self.diary_id, new_diary_name))
            elif new_diary_name == self.current_diary_name:
                self.notify("Nenhuma alteração feita.", severity="warning")
                self.dismiss(None)
            else:
                self.notify("O nome do diário não pode estar vazio.", severity="warning")
                self.name_input.focus()
        elif event.button.id == "cancel_button":
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)