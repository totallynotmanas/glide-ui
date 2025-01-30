from textual.app import App
from textual.containers import Center
from textual.widgets import Button, Input, Footer, Header, Static, LoadingIndicator, OptionList, Placeholder
import socket
from textual.widgets.option_list import Option, Separator
import os

class GlideLogin(Static):
    def compose(self):
        
        yield Center(Input(placeholder="IP Address"
                           , id="Address_IP"
                           , max_length=15
                           , value="10.12.188.235")
                           )
        yield Center(Input(placeholder="Port"
                           , type="number"
                           , id="Port"
                           ,value="8000")
                           )
        yield Center(Input(placeholder="Username"
                           , max_length=10
                           , id="Username"
                           , value="user")
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
            return (False,None,None,None)
        else:
            for i in ip_check:
                if int(i) < 0 or int(i) > 255:
                    self.action_notify("Invalid IP Address", severity="error")
                    return (False,)
                
        if int(port) < 1 or int(port) > 65535:
            self.action_notify("Invalid Port Number", severity="error")
            return (False,None,None,None)
        
        if  not username.isalnum() or "!@#$%^&*()_+-={}[]|:;<>?,/".find(username) != -1:
            self.action_notify("Invalid Username", severity="error")
            return (False,None,None,None)
        else:
            if username[0]==".":
                self.action_notify("Invalid Username", severity="error")
                return (False,None,None,None)
            for i in range(1,len(username)):
                if username[i]=="." and username[i-1]==".":
                    self.action_notify("Invalid Username", severity="error")
                    return (False,None,None,None)
                
        return (True, ip, port, username)
    
class SendWidget(Static):
    def compose(self):
        yield Center(Button("Refresh", id="refresh_users"))
        yield Center(OptionList( id="users_list"))

    def action_refresh_users(self, connected_users):
        users = connected_users
        if users == None:
            self.action_notify("No other user(s) connected", severity="warning")
            return
        self.query_one("#users_list").clear_options()
        for user in users:
            self.query_one("#users_list").add_option(Option(user, id=user))
        
        

class RecieveWidget(Static):
    def compose(self):
        yield Center(Button("Recieve", id="Recieve"))
        yield Center(OptionList( id="reqs_list"))
    
    def action_refresh_requests(self, requests):
        reqs = requests
        if requests == None:
            self.action_notify("No requests available so far!",severity="warning")
            return
        self.query_one("#reqs_list").clear_options()
        for req in reqs:
            self.query_one("#reqs_list").add_option(Option(req[0]+" : "+req[1], id=req[0]))


class GlideApp(App):
    BINDINGS = [
        ("d","toggle_dark_mode","dark mode toggle"),
        ("x","disconnect","disconnect and exit")
        ]

    CSS_PATH = "glideui.tcss"
    socket = None

    def compose(self):
        yield Header(icon="/|\ ") 
        yield SendWidget()
        yield RecieveWidget()
        yield GlideLogin()
        yield Footer()


    def action_toggle_dark_mode(self):
         self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )
         
    def action_disconnect(self):
        if hasattr(self, 'socket') and self.socket:
            self.socket.sendall(b"\x0C")
            self.action_bell()
            self.exit()
            self.socket.close()
        else:
            self.query_one("GlideLogin").action_notify("No active connection to disconnect", severity="error")

    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        if event.button.id == "Login":
            Check = self.query_one("GlideLogin").action_Login()
            
            if Check[0] == True:
                Lcheck = self.LoginTCP(Check[1], int(Check[2]), Check[3])
                if Lcheck == 2:
                    self.add_class("Loading")
                    self.query_one("GlideLogin").visible = False
                    self.query_one("SendWidget").add_class("Loading")
                    self.query_one("RecieveWidget").visible= True
                    self.query_one("SendWidget").visible= True
        
        elif event.button.id == "refresh_users":
            connected_users = self.getConnectedUsers()
            self.query_one("SendWidget").action_refresh_users(connected_users)

        elif event.button.id == "Recieve":
            requests = self.getRequests()
            self.query_one("RecieveWidget").action_refresh_requests(requests)
                

    def LoginTCP(self,ip, port, username):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try :
            self.socket.connect((ip, port))
        except:
            self.query_one("GlideLogin").action_notify("Connection Failed", severity="error")
            return 1
        user_string = b"\x01" + bytes(username, "utf-8") + b"\x00"
        self.socket.sendall(user_string)
        LoginCheck = self.socket.recv(1)
        if LoginCheck == b"\x02":
            self.query_one("GlideLogin").action_notify("Login Successful")
            
            return 2
        elif LoginCheck == b"\x03":
            self.query_one("GlideLogin").action_notify("Username invalid", severity="error")
            return 3
        elif LoginCheck == b"\x04":
            self.query_one("GlideLogin").action_notify("User already logged in", severity="error")
            return 4

    def getConnectedUsers(self):
        self.socket.sendall(b"\x09\x01")
        check = self.socket.recv(1)
        if check == b"\x07":
            num_users_bytes = self.socket.recv(2)
            num_users = int.from_bytes(num_users_bytes, "big")
            users = []
            while num_users > 0:
                user_cur=b""
                while True:
                    user = self.socket.recv(1)
                    if user == b"\x00":
                        break
                    else:
                        user_cur += user
                user_string = user_cur.decode("utf-8")
                users.append(user_string)
                num_users -= 1
            
            return users
        
    def getRequests(self):
        self.socket.sendall(b"\x09\x02")
        check = self.socket.recv(1)
        if check == b"\x08":
            num_requests_bytes = self.socket.recv(2)
            num_requests = int.from_bytes(num_requests_bytes, "big")
            requests = []
            while num_requests > 0:
                request_cur_user=b""
                while True:
                    request = self.socket.recv(1)
                    if request == b"\x00":
                        break
                    else:
                        request_cur_user += request
                request_user_string = request_cur_user.decode("utf-8")
                request_cur_filename=b""
                while True:
                    request_filename = self.socket.recv(1)
                    if request_filename == b"\x00":
                        break
                    else:
                        request_cur_filename += request_filename
                request_filename_string = request_cur_filename.decode("utf-8")
                requests.append([request_user_string,request_filename_string])
                self.query_one("RecieveWidget").action_notify(str(requests))
                num_requests -= 1
            
            return requests

      
    def sendFile(self,path):
        try:
            file_size = os.path.getsize(path)   
        except FileNotFoundError:
            print(f"The file '{path}' does not exist.")
            return
        file = open(path,"rb")
        file_name = path.split("\\")[-1]
        file_name_bytes = bytes(file_name, "utf-8")
        self.socket.sendall(b"\x05"+file_name_bytes+b"\00"+file_size.to_bytes(4, byteorder='big'))
        chunks_ex = file_size // 1024
        for i in range(chunks_ex):
            chunk = file.read(1024)
            self.socket.sendall(b"\x06"+file_name_bytes+b"\00"+(1024).to_bytes(2, byteorder='big')+chunk)
        left_bytes = file_size - chunks_ex*1024
        chunk = file.read(left_bytes)
        self.socket.sendall(b"\x06"+file_name_bytes+b"\00"+left_bytes.to_bytes(2, byteorder='big')+chunk)
        

    
        



if __name__ == "__main__":
    app = GlideApp()
    app.run()