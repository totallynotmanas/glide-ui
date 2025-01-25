from textual.app import App
from textual.containers import Center
from textual.widgets import Button, Input, Footer, Header, Static, LoadingIndicator
import time

class GlideLogin(Static):
    def compose(self):
        yield Center(Input(placeholder="IP Address:"
                           , id="Address_IP"
                           , max_length=15
                           , value="0.0.0.0")
                           )
        yield Center(Input(placeholder="Port:"
                           , type="number"
                           , id="Port"
                           ,value="3")
                           )
        yield Center(Input(placeholder="Username:"
                           , max_length=10
                           , id="Username"
                           , value="sd")
                           #place @ symbol in starting of username
                           )
        yield Center(Button("Login"
                            , variant="success"
                            , id="Login")
                            )

    def action_Login(self):
        ip = self.query_one("#Address_IP").value
        port = self.query_one("#Port").value
        username = self.query_one("#Username").value
        ip_check = ip.split(".")
        if len(ip_check) != 4:
            self.action_notify("Invalid IP Address", severity="error")
            return False
        else:
            for i in ip_check:
                if int(i) < 0 or int(i) > 255:
                    self.action_notify("Invalid IP Address", severity="error")
                    return False
                
        if int(port) < 1 or int(port) > 65535:
            self.action_notify("Invalid Port Number", severity="error")
            return False
        
        if  not username.isalnum() or "!@#$%^&*()_+-={}[]|:;<>?,/".find(username) != -1:
            self.action_notify("Invalid Username", severity="error")
            return False
        else:
            if username[0]==".":
                self.action_notify("Invalid Username", severity="error")
                return False
            for i in range(1,len(username)):
                if username[i]=="." and username[i-1]==".":
                    self.action_notify("Invalid Username", severity="error")
                    return False
        self.action_notify("Login Successful",)
        self.add_class("loading")
        return True


    


class RecieveWidget(Static):
    def compose(self):
        pass

class GlideApp(App):
    BINDINGS = [
        ("d","toggle_dark_mode","dark mode toggle"),
        ]

    CSS_PATH = "glideui.tcss"

    def compose(self):
        yield Header(icon="/|\ ") 
        yield GlideLogin()
        yield LoadingIndicator(disabled=False)
        yield Footer()

    def action_toggle_dark_mode(self):
         self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        if event.button.id == "Login":
            Check = self.query_one("GlideLogin").action_Login()
            
            if Check == True:
                self.add_class("loading")
                time.wait(5)
                self.remove_class("loading")
        



if __name__ == "__main__":
    GlideApp().run()