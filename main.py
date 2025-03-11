from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder

USER_CREDITENTIALS = {
    "doctor": "doctor123",
    "elder": "elder123",
    "caregiver": "caregiver"
}

class LoginScreen(Screen):
    def login(self):
        username = self.ids.username.text.strip()
        password = self.ids.password.text.strip()

        if username in USER_CREDITENTIALS and USER_CREDITENTIALS[username] == password:
            self.manager.current = "main"
        else:
            self.ids.login_status.text = "[color=ff0000]Invalid Creditentials![/color]"
    
    def forgot_password(self):
        print("user_name123")

class MainScreen(Screen):
    pass

class MainApp(MDApp):
    def build(self):
        return Builder.load_file("main.kv")
    
    def on_menu_click(self):
        print("Menu button clicked!")
    
    def on_magnify_click(self):
        print("Magnify button clicked!")

if __name__ == '__main__':
    MainApp().run()