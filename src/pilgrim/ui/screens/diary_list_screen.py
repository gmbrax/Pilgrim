from click import prompt
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Label, Static, OptionList, Button
from textual.binding import Binding
from textual.containers import Vertical, Container, Horizontal


class DiaryListScreen(Screen):
    TITLE = "Pilgrim - Main"

    BINDINGS = [
        Binding("n", "new_diary", "Novo Diário"),
        Binding("^q", "quit", "Sair"),
    ]

    def __init__(self):
        super().__init__()
        self.selected_diary_index = None  # Armazena o índice do diário selecionado

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("Pilgrim", classes="app-title"),
            Label("Select a diary"),
            OptionList(id="option-list", classes="diary-options"),
            Horizontal(
                Button("New diary", id="new-diary"),

                Button("Edit diary", id="edit-diary"),
                Button("🔄 Refresh", id="refresh-btn"),
                classes="actions-buttons",
            ),
            classes="dialog-container"
        )
        yield Static(
            "Tip: use ↑↓ to navigate • ENTER to Select • "
            "TAB to alternate the fields • SHIFT + TAB to alternate back ",
            classes="tips"
        )
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_diaries()
        self.update_buttons_state()  # Atualiza estado inicial dos botões

    def refresh_diaries(self):
        try:
            service_manager = self.app.service_manager
            option_list = self.query_one(".diary-options")
            option_list.clear_options()
            travel_diary_service = service_manager.get_travel_diary_service()
            diaries = travel_diary_service.read_all()

            if not diaries:
                # Para OptionList vazio, você pode adicionar uma string simples
                option_list.add_option("[dim]Nenhum diário encontrado. Pressione 'N' para criar um novo![/dim]")
            else:
                for diary in diaries:
                    # Adiciona cada opção como string com markup rich
                    option_list.add_option(f"[b]{diary.name}[/b]\n[dim]ID: {diary.id}[/dim]")

        except Exception as e:
            self.notify("Error: " + str(e))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle quando uma opção é selecionada"""
        diaries = self.app.service_manager.get_travel_diary_service().read_all()

        if diaries and event.option_index < len(diaries):
            self.selected_diary_index = event.option_index
            selected_diary = diaries[event.option_index]
            self.notify(f"Diário selecionado: {selected_diary.name}")
        else:
            # Caso seja a opção "nenhum diário encontrado"
            self.selected_diary_index = None

        self.update_buttons_state()

    def update_buttons_state(self):
        """Atualiza o estado dos botões baseado na seleção"""
        edit_button = self.query_one("#edit-diary")


        # Só habilita os botões se há um diário selecionado
        has_selection = self.selected_diary_index is not None
        edit_button.disabled = not has_selection


    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle cliques nos botões"""
        button_id = event.button.id

        if button_id == "new-diary":
            self.action_new_diary()
        elif button_id == "edit-diary":
            self.action_edit_diary()
        elif button_id == "refresh-btn":
            self.refresh_diaries()
            self.notify("Lista atualizada manualmente!")

    def action_new_diary(self):
        """Ação para criar novo diário"""
        self.notify("Criando novo diário...")
        # Aqui você pode navegar para uma tela de criação de diário

    def action_edit_diary(self):
        """Ação para editar diário selecionado"""
        if self.selected_diary_index is not None:
            diaries = self.app.service_manager.get_travel_diary_service().read_all()
            if self.selected_diary_index < len(diaries):
                selected_diary = diaries[self.selected_diary_index]
                self.notify(f"Editando diário: {selected_diary.name}")
                # Aqui você pode navegar para uma tela de edição
                # self.app.push_screen(EditDiaryScreen(diary=selected_diary))

    def refresh_diaries(self):
        """Atualiza a lista de diários no OptionList"""
        try:
            service_manager = self.app.service_manager
            option_list = self.query_one("#option-list")  # Usando ID em vez de classe

            # Debug
            current_count = len(option_list.options) if hasattr(option_list, 'options') else 0
            self.notify(f"OptionList atual tem {current_count} opções")

            option_list.clear_options()

            travel_diary_service = service_manager.get_travel_diary_service()
            diaries = travel_diary_service.read_all()

            self.notify(f"Carregando {len(diaries)} diários do serviço")

            if not diaries:
                option_list.add_option("[dim]Nenhum diário encontrado. Pressione 'N' para criar um novo![/dim]")
                self.selected_diary_index = None
            else:
                for diary in diaries:
                    option_list.add_option(f"[b]{diary.name}[/b]\n[dim]ID: {diary.id}[/dim]")

                # Valida se a seleção ainda é válida
                if (self.selected_diary_index is not None and
                        self.selected_diary_index >= len(diaries)):
                    self.selected_diary_index = None

        except Exception as e:
            self.notify("Error no refresh_diaries: " + str(e))