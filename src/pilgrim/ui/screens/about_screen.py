from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Header, Footer, Button, Label, TextArea
from textual.containers import Container

class AboutScreen(Screen[bool]):
    """Screen to display application information."""

    TITLE = "Pilgrim - About"

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
    ]

    def __init__(self):
        super().__init__()
        self.header = Header()
        self.footer = Footer()
        self.app_title = Label("Pilgrim", id="AboutScreen_AboutTitle",classes="AboutScreen_AboutTitle")
        self.content = Label("A TUI Based Travel Diary Application", id="AboutScreen_AboutContent",
                             classes="AboutScreen_AboutContent")
        self.version = Label("Version: 0.0.1", id="AboutScreen_AboutVersion",
                             classes="AboutScreen_AboutVersion")
        self.developer = Label("Developed By: Gustavo Henrique Miranda ", id="AboutScreen_AboutAuthor")
        self.contact = Label("git.gustavomiranda.xyz", id="AboutScreen_AboutContact",
                             classes="AboutScreen_AboutContact")
        self.license = TextArea(id="AboutScreen_AboutLicense",
                                classes="AboutScreen_AboutLicense")
        self.license.text = """Copyright (c) 2025 GHMiranda. 

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."""
        self.license.read_only = True
        self.about_container = Container(self.app_title, self.content, self.version, self.developer,
                                         self.contact, id="AboutScreen_SubContainer",
                                         classes="AboutScreen_SubContainer")
        self.container = Container(self.about_container, self.license, id="AboutScreen_AboutContainer",
                                   classes="AboutScreen_AboutContainer")

    def compose(self) -> ComposeResult:
        yield self.header
        yield self.container
        yield self.footer

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handles button clicks."""
        if "about-close-button" in event.button.classes:
            self.dismiss(False)
        elif "about-info-button" in event.button.classes:
            self.notify("More information would be displayed here!", title="Info")

    def action_dismiss(self, **kwargs) -> None:
        """Closes the about box using dismiss.
        :param **kwargs:
        """
        self.dismiss(False)

    def on_key(self, event) -> None:
        """Intercepts specific keys."""
        if event.key == "escape":
            self.dismiss(False)
            event.prevent_default()
        elif event.key == "enter":
            self.dismiss(False)
            event.prevent_default()