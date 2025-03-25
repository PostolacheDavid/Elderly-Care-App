from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.properties import StringProperty
from database import check_user
from kivymd.uix.navigationdrawer import MDNavigationLayout, MDNavigationDrawer

class LoginScreen(Screen):

    def clean_text(self):
        self.ids.username.text = ""
        self.ids.password.text = ""
        self.ids.login_status.text = ""

    def login(self):

        username = self.ids.username.text.strip()
        password = self.ids.password.text.strip()

        user_role = check_user(username, password)

        if user_role:
            main_screen = self.manager.get_screen("main")

            main_screen.user_role = user_role
            main_screen.username = username
            main_screen.update_ui()

            self.manager.current = "main"
            self.clean_text()
        else:
            self.ids.login_status.text = "Invalid Creditentials"

class MainScreen(Screen):
    user_role = StringProperty("")

    def on_enter(self):
        self.update_ui()

    def update_ui(self):
        if self.user_role == "doctor":
            self.ids.health_manager.current = "doctor_health"
        elif self.user_role == "elder":
            self.ids.health_manager.current = "elder_health"
        elif self.user_role == "caregiver":
            self.ids.health_manager.current = "caregiver_health"


class MainApp(MDApp):
    def build(self):
        sm = ScreenManager()

        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(MainScreen(name="main"))

        return sm
    
    def close_drawer(self):
        nav_drawer = self.root.get_screen("main").ids.nav_drawer
        nav_drawer.set_state("close")
    
    def log_out(self):
        self.close_drawer()
        self.root.current = "login"

if __name__ == '__main__':
    MainApp().run()