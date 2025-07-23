from textual.containers import Container
from textual.widgets import Header, Footer, Label, Button,Input
from textual.screen import Screen
from textual.binding import Binding
from textual import on


class DeleteDiaryModal(Screen):

    BINDINGS = [
        Binding("escape","cancel","Cancel"),
    ]
    def __init__(self, diary_id: int,diary_name:str):
        super().__init__()
        self.diary_id = diary_id
        self.diary_name = diary_name
        self.user_input = Input(placeholder=f"Type diary name to confirm: ({self.diary_name})",id="DeleteDiaryModal-UserInput")
        self.delete_button = Button("Delete Diary",id="DeleteDiaryModal-DeleteButton",disabled=True)
        self.cancel_button = Button("Cancel",id="DeleteDiaryModal-CancelButton")
        self.result = None

    def compose(self):
        yield Header()
        yield Container(
            Label("Are you sure you want to delete this diary?"),
            self.user_input,
            Container(
                self.delete_button,
                self.cancel_button,
                id="DeleteDiaryModal-ButtonContainer",
                classes="DeleteDiaryModal-ButtonContainer"
            ),
            id="DeleteDiaryModal-MainContainer",
            classes="DeleteDiaryModal-MainContainer"
        )
        yield Footer()

    @on(Input.Changed,"#DeleteDiaryModal-UserInput")
    def on_user_input_changed(self, event):
        input_text = event.value.strip()

        if input_text == self.diary_name:
            self.delete_button.disabled = False
        else:
            self.delete_button.disabled = True

    @on(Button.Pressed,"#DeleteDiaryModal-DeleteButton")
    def on_delete_button_pressed(self, event):
        self.result = True
        self.dismiss()


    @on(Button.Pressed,"#DeleteDiaryModal-CancelButton")
    def on_cancel_button_pressed(self, event):
        self.action_cancel()


    def action_cancel(self):
        self.dismiss()
