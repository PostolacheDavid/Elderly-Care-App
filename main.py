from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.properties import StringProperty

USER_CREDITENTIALS = {
    "doctor": {"password": "doctor123", "role": "doctor"},
    "elder": {"password": "elder123", "role": "elder"},
    "caregiver": {"password": "care123", "role": "caregiver"}
}

class LoginScreen(Screen):
    def login(self):
        username = self.ids.username.text.strip()
        password = self.ids.password.text.strip()

        if username in USER_CREDITENTIALS and USER_CREDITENTIALS[username]["password"] == password:
            user_role = USER_CREDITENTIALS[username]["role"]
            main_screen = self.manager.get_screen("main")

            main_screen.user_role = user_role
            main_screen.username = username
            main_screen.update_ui()

            self.manager.current = "main"
        else:
            self.ids.login_status.text = "Invalid Creditentials!"
    
    def forgot_password(self):
        print("user_name123")

class MainScreen(Screen):
    user_role = StringProperty("")

    def on_enter(self):
        self.update_ui()

    def update_ui(self):
        if self.user_role == "doctor":
            self.ids.welcome_label.text = "Welcome, Doctor!"
            self.ids.elder_section.opacity = 0
            self.ids.caregiver_section.opacity = 0
        elif self.user_role == "elder":
            self.ids.welcome_label.text = "Welcome, Elder!"
            self.ids.doctor_section.opacity = 0
            self.ids.caregiver_section.opacity = 0
        elif self.user_role == "caregiver":
            self.ids.welcome_label.text = "Welcome, Caregiver!"
            self.ids.doctor_section.opacity = 0
            self.ids.elder_section.opacity = 0


class MainApp(MDApp):
    def build(self):
        sm = ScreenManager()

        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(MainScreen(name="main"))

        return sm
    
    def on_menu_click(self):
        print("Menu button clicked!")
    
    def on_magnify_click(self):
        print("Magnify button clicked!")

if __name__ == '__main__':
    MainApp().run()