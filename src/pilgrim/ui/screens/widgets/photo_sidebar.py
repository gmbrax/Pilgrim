from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Static, OptionList
from textual.widgets.option_list import Option

from pilgrim.models.photo import Photo


class PhotoSidebar(Vertical):
    class PhotoSelected(Message):
        def __init__(self, photo_id: int) -> None:
            self.photo_id = photo_id
            super().__init__()

    class InsertPhotoReference(Message):
        def __init__(self, photo_hash: str) -> None:
            self.photo_hash = photo_hash
            super().__init__()

    class IngestNewPhoto(Message):
        pass

    class EditPhoto(Message):
        def __init__(self, photo_id: int) -> None:
            self.photo_id = photo_id
            super().__init__()

    class DeletePhoto(Message):
        def __init__(self, photo_id: int) -> None:
            self.photo_id = photo_id
            super().__init__()

    def __init__(self, **kwargs):
        super().__init__(id="sidebar", classes="EditEntryScreen-sidebar", **kwargs)
        self.cached_photos = []

    def compose(self) -> ComposeResult:
        yield Static("Photos", classes="EditEntryScreen-sidebar-title")
        yield Vertical(
            OptionList(id="photo_list", classes="EditEntryScreen-sidebar-photo-list"),
            Static("", id="photo_info", classes="EditEntryScreen-sidebar-photo-info"),
            id="sidebar_content",
            classes="EditEntryScreen-sidebar-content"
        )
        yield Static("", id="help_text", classes="EditEntryScreen-sidebar-help")

    def _get_selected_photo(self) -> Photo | None:
        """Busca a foto selecionada na lista."""
        photo_list = self.query_one("#photo_list", OptionList)
        if photo_list.highlighted is None:
            return None

        option = photo_list.get_option_at_index(photo_list.highlighted)
        if option.id == "ingest":
            return None

        try:
            photo_id = int(str(option.id).split("_")[1])
            return next((p for p in self.cached_photos if p.id == photo_id), None)
        except (IndexError, ValueError):
            return None

    def update_photo_list(self, photos: list[Photo]):
        """Método público para a tela principal popular a lista de fotos."""
        self.cached_photos = photos
        photo_list = self.query_one("#photo_list", OptionList)
        photo_list.clear_options()

        # Adiciona opção de ingest
        photo_list.add_option(Option("➕ Ingest New Photo", id="ingest"))

        # Adiciona fotos
        for photo in self.cached_photos:
            photo_hash = str(photo.photo_hash)[:8]
            photo_list.add_option(
                Option(f"{photo.name} [{photo_hash}]", id=f"photo_{photo.id}")
            )

        # Atualiza info
        photo_info = self.query_one("#photo_info", Static)
        if not self.cached_photos:
            photo_info.update("No photos in diary")
        else:
            photo_info.update(f"{len(self.cached_photos)} photos in diary")

    def on_option_list_option_selected(self, event: OptionList.OptionSelected):
        """Lida com a seleção de um item na lista."""
        if event.option.id == "ingest":
            self.post_message(self.IngestNewPhoto())
        else:
            # Emite PhotoSelected para outras opções
            try:
                photo_id = int(str(event.option.id).split("_")[1])
                self.post_message(self.PhotoSelected(photo_id))
            except (IndexError, ValueError):
                pass

    def on_key(self, event) -> None:
        """Lida com os atalhos de teclado quando a barra lateral está em foco."""
        key = event.key

        if key == "n":
            self.post_message(self.IngestNewPhoto())
            event.stop()
            return

        selected_photo = self._get_selected_photo()
        if not selected_photo:
            return

        if key == "i":
            self.post_message(self.InsertPhotoReference(selected_photo.photo_hash[:8]))
            event.stop()
        elif key == "e":
            self.post_message(self.EditPhoto(selected_photo.id))  # Corrigido: passa o ID
            event.stop()
        elif key == "d":
            self.post_message(self.DeletePhoto(selected_photo.id))  # Corrigido: passa o ID
            event.stop()

    def on_mount(self) -> None:
        """Inicializa a lista com a opção padrão."""
        photo_list = self.query_one("#photo_list", OptionList)
        photo_list.add_option(Option("➕ Ingest New Photo", id="ingest"))