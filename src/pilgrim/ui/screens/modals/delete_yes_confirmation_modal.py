from textual.containers import Container
from textual.widgets import Header, Footer, Label, Button,Input
from textual.screen import Screen
from textual.binding import Binding
from textual import on


class DeleteYesConfirmationModal(Screen):
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]
    def __init__(self,diary_id:int):
        super().__init__()
        self.diary_id = diary_id
        self.user_input = Input(placeholder="Type 'Yes, I do ' to confirm",id="DeleteYesConfirmationModal-UserInput")
        self.delete_button = Button("Delete",id="DeleteYesConfirmationModal-DeleteButton",disabled=True)
        self.cancel_button = Button("Cancel",id="DeleteYesConfirmationModal-CancelButton")
        self.head_text = Label("Are you sure you want to delete this diary?",id="DeleteYesConfirmationModal-HeadText")
        self.second_head_text = Label("This action cannot be undone.",id="DeleteYesConfirmationModal-SecondHeadText")
        self.delete_modal_container = Container(
            self.head_text,
            self.second_head_text,
            self.user_input,
            Container(
                self.delete_button,
                self.cancel_button,
                id="DeleteYesConfirmationModal-DeleteButtonContainer",
                classes="DeleteYesConfirmationModal-DeleteButtonContainer"
            ),
            id="DeleteYesConfirmationModal-DeleteModalContainer",
            classes="DeleteYesConfirmationModal-DeleteModalContainer"
        )
        self.result = None

    @on(Input.Changed,"#DeleteYesConfirmationModal-UserInput")
    def on_user_input_changed(self, event):
        input_text = event.value.strip()
        if input_text == "Yes, I do":
            self.delete_button.disabled = False
        else:
            self.delete_button.disabled = True

    @on(Button.Pressed,"#DeleteYesConfirmationModal-CancelButton")
    def on_cancel_button_pressed(self, event):
        self.action_cancel()

    def action_cancel(self):
        self.dismiss()
        self.app.push_screen(SettingsScreen(diary=travel_diary[0]))

    def compose(self):
        yield Header()
        yield Footer()
        yield self.delete_modal_container