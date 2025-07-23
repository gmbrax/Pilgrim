
from textual.widgets import Static
from textual.containers import Container
from textual.widgets import Header, Footer, Label, Button,Checkbox,Input
from textual.screen import Screen
from textual.reactive import reactive
from textual.binding import Binding
from textual import on

from pilgrim import TravelDiary
from pilgrim.ui.screens.modals.delete_all_entries_from_diary_modal import DeleteAllEntriesModal
from pilgrim.ui.screens.modals.delete_all_photos_from_diary_modal import DeleteAllPhotosModal
from pilgrim.ui.screens.modals.delete_diary_modal import DeleteDiaryModal


class SettingsScreen(Screen):
    is_changed = reactive(False)
    BINDINGS = [
        Binding("escape","cancel","Cancel"),
    ]

    def __init__(self,diary:TravelDiary):
        super().__init__()
        self.current_diary = diary

        self.header = Header()
        self.footer = Footer()
        self.title = "Settings"

        self.diary_name = Static(self.current_diary.name,id="DiarySettingsScreen-DiaryName")
        self.is_the_diary_set_to_auto_open =  False
        self.diary_entry_count = Static("0")
        self.diary_photo_count = Static("0")
        self.save_button = Button("Save")
        self.cancel_button = Button("Cancel",id="DiarySettingsScreen-cancel_button")
        self.apply_button = Button("Apply")
        self.backup_diary_button = Button("Backup Diary")
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
        self.backup_diary_button_container = Container(
            Label("Backup Diary:"),
            self.backup_diary_button,
            id="DiarySettingsScreen-BackupDiaryButtonContainer",
            classes="DiarySettingsScreen-BackupDiaryButtonContainer Button_Container"
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
            self.backup_diary_button_container,
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
        self.notify("Checkboxed")

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
        self.app.exit()


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
        pass

    def set_checkbox_state(self):
        self.set_auto_open_to_this_diary.value = True