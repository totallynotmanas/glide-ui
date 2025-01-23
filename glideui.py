from textual.app import App
from textual.widgets import Footer, Header

class GlideApp(App):
    BINDINGS = [
        ("d","toggle_dark_mode","dark mode toggle"),
        ]

    def compose(self):
        yield Header()
        yield Footer()

    def action_toggle_dark_mode(self):
         self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )


if __name__ == "__main__":
    GlideApp().run()