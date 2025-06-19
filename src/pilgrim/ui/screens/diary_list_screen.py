from typing import Optional, Tuple
import asyncio

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Label, Static, OptionList, Button
from textual.binding import Binding
from textual.containers import Vertical, Container, Horizontal

from pilgrim.models.travel_diary import TravelDiary
from pilgrim.ui.screens.edit_diary_modal import EditDiaryModal
from pilgrim.ui.screens.new_diary_modal import NewDiaryModal


class DiaryListScreen(Screen):
    TITLE = "Pilgrim - Main"

    BINDINGS = [
        Binding("n", "new_diary", "New diary"),
        Binding("^q", "quit", "Quit Pilgrim"),
        Binding("enter", "open_selected_diary", "Open diary"),
        Binding("e", "edit_selected_diary", "Edit diary"),
        Binding("r", "force_refresh", "Force refresh"),
    ]

    def __init__(self):
        super().__init__()
        self.selected_diary_index = None
        self.diary_id_map = {}
        self.is_refreshing = False

        self.header = Header()
        self.footer = Footer()
        self.diary_list = OptionList(classes="DiaryListScreen-DiaryListOptions")
        self.new_diary_button = Button("New diary", id="new_diary", classes="DiaryListScreen-NewDiaryButton")
        self.edit_diary_button = Button("Edit diary", id="edit_diary", classes="DiaryListScreen-EditDiaryButton")
        self.open_diary = Button("Open diary", id="open_diary", classes="DiaryListScreen-OpenDiaryButton")
        self.buttons_grid = Horizontal(
            self.new_diary_button, self.edit_diary_button, self.open_diary,
            classes="DiaryListScreen-ButtonsGrid"
        )
        self.tips = Static(
            "Tip: use ↑↓ to navigate • ENTER to Select • "
            "TAB to alternate the fields • SHIFT + TAB to alternate back • "
            "Ctrl+P for command palette • R to force refresh",
            classes="DiaryListScreen-DiaryListTips"
        )
        self.container = Container(
            self.diary_list, self.buttons_grid, self.tips,
            classes="DiaryListScreen-DiaryListContainer"
        )

    def compose(self) -> ComposeResult:
        yield self.header
        yield self.container
        yield self.footer

    def on_mount(self) -> None:
        # Usa versão síncrona para o mount inicial
        self.refresh_diaries()
        self.update_buttons_state()

    def refresh_diaries(self):
        """Versão síncrona do refresh"""
        try:
            service_manager = self.app.service_manager
            travel_diary_service = service_manager.get_travel_diary_service()

            # Usa método síncrono
            diaries = travel_diary_service.read_all()

            # Salva o estado atual
            current_diary_id = None
            if (self.selected_diary_index is not None and
                    self.selected_diary_index in self.diary_id_map):
                current_diary_id = self.diary_id_map[self.selected_diary_index]

            # Limpa e reconstrói
            self.diary_list.clear_options()
            self.diary_id_map = {}

            if not diaries:
                self.diary_list.add_option("[dim]Nenhum diário encontrado. Pressione 'N' para criar um novo![/dim]")
                self.selected_diary_index = None
            else:
                new_selected_index = 0

                for index, diary in enumerate(diaries):
                    self.diary_id_map[index] = diary.id
                    self.diary_list.add_option(f"[b]{diary.name}[/b]\n[dim]ID: {diary.id}[/dim]")

                    # Mantém a seleção se possível
                    if current_diary_id and diary.id == current_diary_id:
                        new_selected_index = index

                self.selected_diary_index = new_selected_index

                # Atualiza o highlight
                self.set_timer(0.05, lambda: self._update_highlight(new_selected_index))

            # Força refresh visual
            self.diary_list.refresh()
            self.update_buttons_state()

        except Exception as e:
            self.notify(f"Erro ao carregar diários: {str(e)}")

    def _update_highlight(self, index: int):
        """Atualiza o highlight do OptionList"""
        try:
            if index < len(self.diary_list.options):
                self.diary_list.highlighted = index
                self.diary_list.refresh()
        except Exception as e:
            self.notify(f"Erro ao atualizar highlight: {str(e)}")

    async def async_refresh_diaries(self):
        """Versão assíncrona do refresh"""
        if self.is_refreshing:
            return

        self.is_refreshing = True

        try:
            service_manager = self.app.service_manager
            travel_diary_service = service_manager.get_travel_diary_service()

            # Usa método assíncrono
            diaries = await travel_diary_service.async_read_all()

            # Salva o estado atual
            current_diary_id = None
            if (self.selected_diary_index is not None and
                    self.selected_diary_index in self.diary_id_map):
                current_diary_id = self.diary_id_map[self.selected_diary_index]

            # Limpa e reconstrói
            self.diary_list.clear_options()
            self.diary_id_map = {}

            if not diaries:
                self.diary_list.add_option("[dim]Nenhum diário encontrado. Pressione 'N' para criar um novo![/dim]")
                self.selected_diary_index = None
            else:
                new_selected_index = 0

                for index, diary in enumerate(diaries):
                    self.diary_id_map[index] = diary.id
                    self.diary_list.add_option(f"[b]{diary.name}[/b]\n[dim]ID: {diary.id}[/dim]")

                    if current_diary_id and diary.id == current_diary_id:
                        new_selected_index = index

                self.selected_diary_index = new_selected_index
                self.set_timer(0.05, lambda: self._update_highlight(new_selected_index))

            self.diary_list.refresh()
            self.update_buttons_state()

        except Exception as e:
            self.notify(f"Erro ao carregar diários: {str(e)}")
        finally:
            self.is_refreshing = False

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        """Handle quando uma opção é destacada"""
        if self.diary_id_map and event.option_index in self.diary_id_map:
            self.selected_diary_index = event.option_index
        else:
            self.selected_diary_index = None

        self.update_buttons_state()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle quando uma opção é selecionada"""
        if self.diary_id_map and event.option_index in self.diary_id_map:
            self.selected_diary_index = event.option_index
            self.action_open_diary()
        else:
            self.selected_diary_index = None

        self.update_buttons_state()

    def update_buttons_state(self):
        """Atualiza o estado dos botões"""
        has_selection = (self.selected_diary_index is not None and
                         self.selected_diary_index in self.diary_id_map)

        self.edit_diary_button.disabled = not has_selection
        self.open_diary.disabled = not has_selection

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle cliques nos botões"""
        button_id = event.button.id

        if button_id == "new_diary":
            self.action_new_diary()
        elif button_id == "edit_diary":
            self.action_edit_selected_diary()
        elif button_id == "open_diary":
            self.action_open_diary()

    def action_new_diary(self):
        """Ação para criar novo diário"""
        self.app.push_screen(NewDiaryModal(),self._on_new_diary_submitted)

    def _on_new_diary_submitted(self,result):
        self.notify(str(result))
        if result:
            self.notify(f"Creating Diary:{result}'...")
            self.call_later(self._async_create_diary,result)
        else:
            self.notify(f"Canceled...")

    async def _async_create_diary(self,name: str):

        try:
            service = self.app.service_manager.get_travel_diary_service()
            created_diary = await service.async_create(name)
            if created_diary:
                self.diary_id_map[created_diary.id] = created_diary.id
                await self.async_refresh_diaries()
                self.notify(f"Diary: '{name}' created!")
            else:
                self.notify("Error Creating the diary")
        except Exception as e:
            self.notify(f"Exception on creating the diary: {str(e)}")



    def action_edit_selected_diary(self):
        """Ação para editar diário selecionado"""
        if self.selected_diary_index is not None:
            diary_id = self.diary_id_map.get(self.selected_diary_index)
            if diary_id:
                self.app.push_screen(
                    EditDiaryModal(diary_id=diary_id),
                    self._on_edited_diary_name_submitted
                )
        else:
            self.notify("Selecione um diário para editar")

    def action_open_diary(self):
        """Ação para abrir diário selecionado"""
        if self.selected_diary_index is not None:
            diary_id = self.diary_id_map.get(self.selected_diary_index)
            self.notify(f"Abrindo diário ID: {diary_id}")
        else:
            self.notify("Selecione um diário para abrir")

    def _on_edited_diary_name_submitted(self, result: Optional[Tuple[int, str]]) -> None:
        """Callback após edição do diário"""
        if result:
            diary_id, name = result
            self.notify(f"Atualizando diário ID {diary_id} para '{name}'...")
            # Agenda a atualização assíncrona
            self.call_later(self._async_update_diary, diary_id, name)
        else:
            self.notify("Edição cancelada")

    async def _async_update_diary(self, diary_id: int, name: str):
        """Atualiza o diário de forma assíncrona"""
        try:
            service = self.app.service_manager.get_travel_diary_service()
            updated_diary = await service.async_update(diary_id, name)

            if updated_diary:
                self.notify(f"Diário '{name}' atualizado!")
                # Força refresh após a atualização
                await self.async_refresh_diaries()
            else:
                self.notify("Erro: Diário não encontrado")

        except Exception as e:
            self.notify(f"Erro ao atualizar: {str(e)}")

    def action_force_refresh(self):
        """Força refresh manual"""
        self.notify("Forçando refresh...")
        # Tenta ambas as versões
        self.refresh_diaries()  # Síncrona
        self.call_later(self.async_refresh_diaries)  # Assíncrona

    def action_open_selected_diary(self):
        """Ação do binding ENTER"""
        self.action_open_diary()