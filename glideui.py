from textual.app import App, ComposeResult
from textual.containers import Center, Container, HorizontalGroup
from textual.widgets import Button, Input, Footer, Header, Static, LoadingIndicator, OptionList, Label
from textual.screen import ModalScreen
from textual import on 
import socket
from textual.widgets.option_list import Option, Separator
import os
import time

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
        yield Center(Input(placeholder="Paste the path of file here."
                           ,id="path"))
        yield Center(Button("Send", id="Send"))

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
        with Center():
            with HorizontalGroup():
                yield Button("Accept", id="Accept", variant="success")
                yield Button("Reject", id="Reject", variant="error")

    def action_refresh_requests(self, requests):
        reqs = requests
        if requests == None:
            self.action_notify("No requests available so far!",severity="warning")
            return
        self.query_one("#reqs_list").clear_options()
        for req in reqs:
            self.query_one("#reqs_list").add_option(Option(req[0]+" : "+req[1], id=req[0]+" : "+req[1]))

    def action_remove_request(self, request):
        self.query_one("#reqs_list").remove_option(request)


class GlideApp(App):
    BINDINGS = [
        ("d","toggle_dark_mode","dark mode toggle"),
        ("x","disconnect","disconnect and exit")
        ]

    CSS_PATH = "glideui.tcss"
    socket = None
    logged_in = False

    def compose(self):
        yield Header(icon="/|\ ") 
        if not self.logged_in:
            yield GlideLogin()
        if self.logged_in:
            yield SendWidget()
            yield RecieveWidget()
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
            
            if Check[0]:
                Lcheck = self.LoginTCP(Check[1], int(Check[2]), Check[3])
                if Lcheck == 2:
                    self.logged_in = True
                    self.refresh(recompose=True)
                    
        
        elif event.button.id == "refresh_users":
            connected_users = self.getConnectedUsers()
            self.query_one("SendWidget").action_refresh_users(connected_users)

        elif event.button.id == "Send":
            self.sendFile()

        elif event.button.id == "Recieve":
            requests = self.getRequests()
            self.query_one("RecieveWidget").action_refresh_requests(requests)

        elif event.button.id == "Accept":
            self.acceptReq()

        elif event.button.id == "Reject":
            self.rejectReq()

                

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

      
    def sendFile(self,):
        path = self.query_one("#path").value
        user_index = self.query_one("#users_list").highlighted
        user = self.query_one("#users_list").get_option_at_index(user_index).id
        self.query_one("RecieveWidget").action_notify(str(user))
        if user == None:
            self.query_one("RecieveWidget").action_notify("No user selected", severity="error")
            return
        if path == "":
            self.query_one("RecieveWidget").action_notify("No file path provided", severity="error")
            return
        
        try:
            file_size = os.path.getsize(path)   
        except FileNotFoundError:
            self.query_one("RecieveWidget").action_notify(f"The file '{path}' does not exist.")
            
        
        file = open(path,"rb")
        file_name = path.split("\\")[-1]
        
        path_bytes = bytes(str(path), "utf-8")
        file_name_bytes = bytes(file_name, "utf-8")
        username_bytes = bytes(str(user), "utf-8")

        self.socket.sendall(b"\x09\x03"+file_name_bytes+b"\00"+username_bytes+b"\00")
        print(b"\x09\x03"+file_name_bytes+b"\00"+username_bytes+b"\00")
        check = self.socket.recv(1)
        if check == b"\x00":
            check = self.socket.recv(1)
        if check == b"\x04":
            self.query_one("RecieveWidget").action_notify("User not found", severity="error")
            return
        elif check == b"\x0d":
            self.query_one("RecieveWidget").action_notify("Request sent", severity="success")
        elif check == b"\x07":
            pass
        else:
            self.query_one("RecieveWidget").action_notify(f"{check}Error sending request", severity="error")
            return
        
        self.socket.sendall(b"\x05"+file_name_bytes+b"\00"+file_size.to_bytes(4, byteorder='big'))
        print(file_size.to_bytes(4, byteorder='big'))
        chunks_ex = file_size // 1024

        for i in range(chunks_ex):
            chunk = file.read(1024)
            self.socket.sendall(b"\x06"+file_name_bytes+b"\00"+(1024).to_bytes(2, byteorder='big')+chunk)

        left_bytes = file_size - chunks_ex *  1024
        chunk = file.read(left_bytes)
        self.socket.sendall(b"\x06"+file_name_bytes+b"\00"+left_bytes.to_bytes(2, byteorder='big')+chunk)

    def acceptReq(self):
        request_index = self.query_one("#reqs_list").highlighted
        if request_index == None:
            self.query_one("RecieveWidget").action_notify("No request selected", severity="error")
            return
        request = self.query_one("#reqs_list").get_option_at_index(request_index).id
        print(request)
        if request == None:
            self.query_one("RecieveWidget").action_notify("No request selected", severity="error")
            return

        request_user = request.split(" : ")[0]
        request_filename = request.split(" : ")[1]
        self.socket.sendall(b"\x09\x04"+bytes(request_user, "utf-8")+b"\00")
        print("checked")
        self.receiveFile(request,request_filename)

    def receiveFile(self, request, request_filename, path=""):
        """ Receives a file from the server and saves it at the given path """

        check = self.socket.recv(1)
        check = self.socket.recv(1)
        print(f"Received header: {check}")

        if check == b"\x00":
            check = self.socket.recv(1)
            print(f"Received additional check byte: {check}")

        if check == b"\x0a":
            self.query_one("RecieveWidget").action_notify("Request accept failed", severity="error")
            return

        elif check == b"\x05":
            # Receive file name
            file_name_cur = b""
            while True:
                file_byte = self.socket.recv(1)
                if file_byte == b"\x00":
                    break
                file_name_cur += file_byte
        
            file_name_string = file_name_cur.decode("utf-8")
        
            # Receive file size
            file_size_bytes = self.socket.recv(4)
            file_size = int.from_bytes(file_size_bytes, "big")

            if file_size == 0:
                print("Server sent file size as 0. No data will be written.")
                self.query_one("RecieveWidget").action_notify("Error: Server sent empty file", severity="error")
                return

            print(f"Receiving file: {file_name_string}, Size: {file_size} bytes")

            file_path = os.path.join(path, request_filename)
            with open(file_path, "wb") as file:
                received_bytes = 0

                while received_bytes < file_size:
                    check = self.socket.recv(1)
                    if not check:
                        print("Connection closed by server unexpectedly.")
                        return
                    if check != b"\x06":
                        print(f"Unexpected chunk header: {check}")
                        self.query_one("RecieveWidget").action_notify("Error receiving file", severity="error")
                        return
                    file_name_cur = b""
                    while True:
                        file_byte = self.socket.recv(1)
                        if file_byte == b"\x00":
                            break
                        file_name_cur += file_byte

                    # Receive chunk size
                    chunk_size_bytes = self.socket.recv(2)
                    chunk_size = int.from_bytes(chunk_size_bytes, byteorder="big")

                    if chunk_size > 1024 or chunk_size <= 0:
                        print(f"Invalid chunk size: {chunk_size}")
                        return

                    # Receive chunk data reliably
                    chunk = b""
                    while len(chunk) < chunk_size:
                        part = self.socket.recv(chunk_size - len(chunk))
                        if not part:
                            print("Connection lost while receiving chunk")
                            self.query_one("RecieveWidget").action_notify("Error receiving file", severity="error")
                            return
                        chunk += part

                    file.write(chunk)
                    received_bytes += len(chunk)

                    print(f"Received {received_bytes}/{file_size} bytes...")

            self.query_one("RecieveWidget").action_notify("File received", severity="success")
            print(f"File '{request_filename}' received successfully!")

        else:
            self.query_one("RecieveWidget").action_notify("Error receiving file", severity="error")
     
        
    def rejectReq(self):
        request_index = self.query_one("#reqs_list").highlighted
        if request_index == None:
            self.query_one("RecieveWidget").action_notify("No request selected", severity="error")
            return
        request = self.query_one("#reqs_list").get_option_at_index(request_index).id
        print(request)
        if request == None:
            self.query_one("RecieveWidget").action_notify("No request selected", severity="error")
            return

        request_user = request.split(" : ")[0]
        request_filename = request.split(" : ")[1]
        self.socket.sendall(b"\x09\x05"+bytes(request_user, "utf-8")+b"\00")
        check = self.socket.recv(1)
        if check == b"\x0b":
            self.query_one("RecieveWidget").action_notify("Request rejected", severity="success")
            self.query_one("RecieveWidget").action_remove_request(request)


    
        



if __name__ == "__main__":
    app = GlideApp()
    app.run()