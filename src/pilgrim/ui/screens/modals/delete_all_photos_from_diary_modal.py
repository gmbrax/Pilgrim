
from textual.widgets import Button

from textual import on

from pilgrim.ui.screens.modals.delete_yes_confirmation_modal import DeleteYesConfirmationModal


class DeleteAllPhotosModal(DeleteYesConfirmationModal):
    def __init__(self,diary_id:int):
        super().__init__(diary_id)
        self.head_text.update("Are you sure you want to delete all photos from this diary?")
        self.delete_button.add_class("DeleteDiaryModal-DeleteButton")



    @on(Button.Pressed, ".DeleteDiaryModal-DeleteButton")
    def on_delete_button_pressed(self, event):

        from pilgrim.ui.screens.diary_list_screen import DiaryListScreen

        self.result = True
        self._delete_all_photo()
        self.dismiss()
        self.app.push_screen(DiaryListScreen())
        
    def _delete_all_photo(self):
        diary = self.app.service_manager.get_travel_diary_service().read_by_id(self.diary_id)
        if self.app.service_manager.get_travel_diary_service().delete_all_photos(diary):
            self.notify("All photos deleted successfully")
        else:
            self.notify("Failed to delete all photos")