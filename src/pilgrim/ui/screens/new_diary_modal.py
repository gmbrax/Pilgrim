from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Label, Input, Button

from pilgrim.ui.screens.edit_entry_screen import EditEntryScreen


class NewDiaryModal(ModalScreen[str]):
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "create_diary", "Create",priority=True),
    ]
    def __init__(self,autoopen=True):
        """
        Initialize the NewDiaryModal with optional automatic opening of the created diary.
        
        Parameters:
            autoopen (bool): If True, the newly created diary will open automatically after creation. Defaults to True.
        """
        super().__init__()
        self.auto_open = autoopen
        self.name_input = Input(id="NewDiaryModal-NameInput",classes="NewDiaryModal-NameInput") # This ID is fine, it's specific to the input

    def compose(self) -> ComposeResult:

        """
        Constructs and yields the UI layout for the new diary modal dialog.
        
        Returns:
            ComposeResult: An iterable of widgets forming the modal, including title, input field, and action buttons.
        """
        with Vertical(id="new_diary_dialog",classes="NewDiaryModal-Dialog"):
            yield Label("Create a new diary", classes="NewDiaryModal-Title")
            yield Label("Diary Name:")
            yield self.name_input
            with Horizontal(classes="NewDiaryModal-ButtonsContainer"):
                yield Button("Create", variant="primary", id="create_diary_button",
                             classes="NewDiaryModal-CreateDiaryButton")
                yield Button("Cancel", variant="default", id="cancel_button",
                             classes="NewDiaryModal-CancelButton")

    def on_mount(self):
          self.name_input.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Handle button press events for the modal.
        
        Triggers diary creation when the "Create" button is pressed, or dismisses the modal when the "Cancel" button is pressed.
        """
        if event.button.id == "create_diary_button":
            self.action_create_diary()
        elif event.button.id == "cancel_button":
            self.dismiss()

    def action_cancel(self) -> None:
        """
        Cancels the modal dialog and dismisses it without returning a diary name.
        """
        self.dismiss("")

    def action_create_diary(self) -> None:
        """
        Validates the diary name input and initiates asynchronous diary creation if valid.
        
        If the input is empty, displays a warning notification and refocuses the input field.
        """
        diary_name = self.name_input.value.strip()
        if diary_name:

            self.call_later(self._async_create_diary, diary_name)

        else:
            self.notify("Diary name cannot be empty.", severity="warning")
            self.name_input.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """
        Handles submission of the diary name input field and initiates diary creation if triggered from the correct input.
        """
        if event.input.id == "NewDiaryModal-NameInput":
            self.action_create_diary()

    async def _async_create_diary(self, name: str):

        """
        Asynchronously creates a new diary entry with the given name and handles post-creation actions.
        
        If creation succeeds, dismisses the modal with the diary name, optionally opens the diary for editing, and shows a success notification. If creation fails or an exception occurs, displays an error notification.
        """
        try:
            service = self.app.service_manager.get_travel_diary_service()
            created_diary = await service.async_create(name)
            if created_diary:
                self.dismiss(name)

                if self.auto_open:
                    self.app.push_screen(EditEntryScreen(diary_id=created_diary.id))

                self.notify(f"Diary: '{name}' created!")
            else:
                self.notify("Error Creating the diary")
        except Exception as e:
            self.notify(f"Exception on creating the diary: {str(e)}")





