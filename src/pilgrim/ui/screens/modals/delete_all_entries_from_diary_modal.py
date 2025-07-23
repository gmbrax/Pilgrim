
from textual.widgets import Button

from textual import on

from pilgrim.ui.screens.modals.delete_yes_confirmation_modal import DeleteYesConfirmationModal


class DeleteAllEntriesModal(DeleteYesConfirmationModal):
    def __init__(self,diary_id:int):
        super().__init__(diary_id)
        self.head_text.update("Are you sure you want to delete all entries from this diary?")



    @on(Button.Pressed, "#DeleteDiaryModal-DeleteButton")
    def on_delete_button_pressed(self, event):
        self.result = True
        self.dismiss()

