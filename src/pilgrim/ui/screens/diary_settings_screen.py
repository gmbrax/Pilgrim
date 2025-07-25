
from textual.widgets import Static
from textual.containers import Container
from textual.widgets import Header, Footer, Label, Button,Checkbox
from textual.screen import Screen
from textual.reactive import reactive
from textual.binding import Binding
from textual import on

from pilgrim.ui.screens.modals.delete_all_entries_from_diary_modal import DeleteAllEntriesModal
from pilgrim.ui.screens.modals.delete_all_photos_from_diary_modal import DeleteAllPhotosModal
from pilgrim.ui.screens.modals.delete_diary_modal import DeleteDiaryModal


class SettingsScreen(Screen):
    is_changed = reactive(False)
    BINDINGS = [
        Binding("escape","cancel","Cancel"),
    ]

    def __init__(self,diary_id:int):
        super().__init__()
        self.current_diary = self.app.service_manager.get_travel_diary_service().read_by_id(diary_id)

        self.header = Header()
        self.footer = Footer()
        self.title = "Settings"

        self.diary_name = Static(self.current_diary.name,id="DiarySettingsScreen-DiaryName")
        self.notify(str(self.app.config_manager))
        self.is_the_diary_set_to_auto_open =  self.app.config_manager.get_auto_open_diary() == self.current_diary.name
        self.diary_entry_count = Static(str(len(self.current_diary.entries)))
        self.diary_photo_count = Static(str(len(self.current_diary.photos)))
        self.save_button = Button("Save",id="DiarySettingsScreen-SaveButton" )
        self.cancel_button = Button("Cancel",id="DiarySettingsScreen-cancel_button")
        self.apply_button = Button("Apply",id="DiarySettingsScreen-ApplyButton")

        self.delete_diary_button = Button("Delete Diary",id="DiarySettingsScreen-DeleteDiaryButton")
        self.delete_all_entries_button = Button("Delete All Entries",id="DiarySettingsScreen-DeleteAllEntriesButton")
        self.delete_all_photos_button = Button("Delete All Photos",id="DiarySettingsScreen-DeleteAllPhotosButton")
        self.set_auto_open_to_this_diary = Checkbox(id="set_auto_open_to_this_diary",value=self.is_the_diary_set_to_auto_open)
        self.delete_diary_button_container = Container(
            Label("Delete Diary:"),

            self.delete_diary_button,
            id="DiarySettingsScreen-DeleteDiaryButtonContainer",
            classes="DiarySettingsScreen-DeleteDiaryButtonContainer Button_Container"
        )
        self.delete_all_entries_button_container = Container(
            Label("Delete All Entries:"),
            self.delete_all_entries_button,

            id="DiarySettingsScreen-DeleteAllEntriesButtonContainer",
            classes="DiarySettingsScreen-DeleteAllEntriesButtonContainer Button_Container"
        )
        self.delete_all_photos_button_container = Container(
            Label("Delete All Photos:"),
            self.delete_all_photos_button,


            id="DiarySettingsScreen-DeleteAllPhotosButtonContainer",
            classes="DiarySettingsScreen-DeleteAllPhotosButtonContainer Button_Container"
        )
        self.diary_name_container = Container(
            Label("Diary Name:"),
            self.diary_name,
            id="DiarySettingsScreen-DiaryNameContainer",
            classes="DiarySettingsScreen-DiaryNameContainer Data_Container"

        )
        self.diary_entry_count_container = Container(
            Label("Diary Entries:"),
            self.diary_entry_count,
            id="DiarySettingsScreen-DiaryEntryCountContainer",
            classes="DiarySettingsScreen-DiaryEntryCountContainer Data_Container"
        )
        self.set_auto_open_to_this_diary_container = Container(
            Label("Set Open This Diary On App Start?:"),
            self.set_auto_open_to_this_diary,
            id="DiarySettingsScreen-SetAutoOpenToThisDiaryContainer",
            classes="DiarySettingsScreen-SetAutoOpenToThisDiaryContainer Data_Container"

        )
        self.diary_photo_count_container = Container(
            Label("Diary Photos:"),
            self.diary_photo_count,
            id="DiarySettingsScreen-DiaryPhotoCountContainer",
            classes="DiarySettingsScreen-DiaryPhotoCountContainer Data_Container"
        )

        self.diary_info_container = Container(

            self.diary_name_container,
            self.diary_entry_count_container,
            self.diary_photo_count_container,
            self.set_auto_open_to_this_diary_container,
            id="DiarySettingsScreen-DiaryInfoContainer",
            classes="DiarySettingsScreen-DiaryInfoContainer",
                                              )

        self.diary_denger_zone_container = Container(
            self.delete_diary_button_container,
            self.delete_all_entries_button_container,
            self.delete_all_photos_button_container,
            id="DiarySettingsScreen-DiaryDengerZoneContainer",
            classes="DiarySettingsScreen-DiaryDengerZoneContainer"
        )
        self.button_container = Container(
            self.save_button,
            self.apply_button,
            self.cancel_button,
            id="DiarySettingsScreen-ButtonContainer",
            classes="DiarySettingsScreen-ButtonContainer"
        )
        self.main = Container(
            self.diary_info_container,
            self.diary_denger_zone_container,
            self.button_container,
            id="DiarySettingsScreen-MainContainer",
            classes="DiarySettingsScreen-MainContainer"
        )
        self.diary_info_container.border_title = "Diary Info"
        self.diary_denger_zone_container.border_title = "Denger Zone"

    @on(Checkbox.Changed, "#set_auto_open_to_this_diary")
    def on_checkbox_changed(self, event):
        self.is_changed =  not self.is_changed


    @on(Button.Pressed, "#DiarySettingsScreen-cancel_button")
    def on_cancel_button_pressed(self, event):
        self.action_cancel()

    @on(Button.Pressed, "#DiarySettingsScreen-DeleteDiaryButton")
    def on_delete_diary_button_pressed(self, event):
        self.app.push_screen(DeleteDiaryModal(diary_id=self.current_diary.id,diary_name=self.current_diary.name))

    @on(Button.Pressed, "#DiarySettingsScreen-DeleteAllEntriesButton")
    def on_delete_all_entries_button_pressed(self, event):
        self.app.push_screen(DeleteAllEntriesModal(diary_id=self.current_diary.id))

    @on(Button.Pressed, "#DiarySettingsScreen-DeleteAllPhotosButton")
    def on_delete_all_photos_button_pressed(self, event):
        self.app.push_screen(DeleteAllPhotosModal(diary_id=self.current_diary.id))

    def action_cancel(self):
        if self.is_changed:
            self.notify("Cancel button pressed, but changes are not saved",severity="error")
            return
        self.dismiss()

    @on(Button.Pressed, "#DiarySettingsScreen-SaveButton")
    def on_save_button_pressed(self, event):
        self.action_save()

    @on(Button.Pressed, "#DiarySettingsScreen-ApplyButton")
    def on_apply_button_pressed(self, event):
        self.action_apply()


    def watch_is_changed(self, value):
        label = self.set_auto_open_to_this_diary_container.query_one(Label)
        if value:
            label.add_class("DiarySettingsScreen-SetAutoOpenToThisDiaryContainer-Not-Saved-Label")
        else:
            label.remove_class("DiarySettingsScreen-SetAutoOpenToThisDiaryContainer-Not-Saved-Label")

    def compose(self):
        yield Header()
        yield self.main
        yield Footer()

    def on_mount(self):
        if self.app.config_manager.get_auto_open_diary() == self.current_diary.name:
            self.call_after_refresh(self.set_checkbox_state)

    def set_checkbox_state(self):
        self.set_auto_open_to_this_diary.value = True

    def _set_auto_open_diary(self,value):

        self.app.config_manager.set_auto_open_diary(value)
        self.app.config_manager.save_config()
        self.is_changed = False

    def _get_auto_open_diary(self):
        return self.app.config_manager.get_auto_open_diary()

    def _make_auto_open_diary_value(self):
        value = None
        if self.set_auto_open_to_this_diary.value:
            value = self.current_diary.name
        return value


    def action_save(self):

        if not self.is_changed:
            self.dismiss()
            return

        value = self._make_auto_open_diary_value()
        current_auto_open = self._get_auto_open_diary()


        if current_auto_open is None:
            self._set_auto_open_diary(value)
            self.notify("Settings saved")
            self.dismiss()
            return


        if current_auto_open == self.current_diary.name:
            if value is None:

                self._set_auto_open_diary(None)
                self.notify("Auto-open disabled")
            else:

                self.is_changed = False
                self.notify("No changes made")
            self.dismiss()
            return


        if value is not None:

            self._set_auto_open_diary(value)
            self.notify(f"Auto-open changed from '{current_auto_open}' to '{self.current_diary.name}'")
            self.dismiss()
        else:

            self.is_changed = False
            self.notify("No changes made")
            self.dismiss()


    def action_apply(self):

        if not self.is_changed:
            return

        value = self._make_auto_open_diary_value()
        current_auto_open = self._get_auto_open_diary()


        if current_auto_open is None:
            self._set_auto_open_diary(value)
            self.notify("Settings applied")
            return


        if current_auto_open == self.current_diary.name:
            if value is None:

                self._set_auto_open_diary(None)
                self.notify("Auto-open disabled")
            else:

                self.is_changed = False
                self.notify("No changes made")
            return


        if value is not None:

            self._set_auto_open_diary(value)
            self.notify(f"Auto-open changed from '{current_auto_open}' to '{self.current_diary.name}'")
        else:

            self.is_changed = False
            self.notify("No changes made")