from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.properties import StringProperty
from database import check_user
from kivymd.uix.navigationdrawer import MDNavigationLayout, MDNavigationDrawer
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.boxlayout import BoxLayout
import os
import shutil

class FileChooserContent(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = 10
        self.spacing = 10
        self.size_hint_y = None
        self.height = "400dp"

        self.chooser = FileChooserListView(
            filters=["*.png", "*.jpg", "*.jpeg"],
            size_hint=(1, 1)
        )
        self.add_widget(self.chooser)

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

class DoctorRegisterScreen(Screen):
    selected_photo_path = None
    file_dialog = None

    def open_file_chooser(self):
        self.file_chooser_content = FileChooserContent()

        self.file_dialog = MDDialog (
            title="Select a photo",
            type="custom",
            md_bg_color=(0.2, 0.2, 0.2, 1),
            content_cls=self.file_chooser_content,
            buttons=[
                MDFlatButton(text="Cancel", on_release=lambda *x: self.file_dialog.dismiss()),
                MDFlatButton(text="Select", on_release=self.select_file),
            ]
        )
        self.file_dialog.open()

    def select_file(self, *args):
        filechooser = self.file_chooser_content.chooser
        if filechooser.selection:
            self.selected_photo_path = filechooser.selection[0]
            self.ids.file_name_label.text = os.path.basename(self.selected_photo_path)
            print(f"Selcted file ${self.selected_photo_path}")
        shutil.copy(self.selected_photo_path, "assets")
        self.file_dialog.dismiss()

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

    dialog = None

    def build(self):
        sm = ScreenManager()

        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(DoctorRegisterScreen(name="doctor_register"))

        return sm
    
    def close_drawer(self):
        nav_drawer = self.root.get_screen("main").ids.nav_drawer
        nav_drawer.set_state("close")
    
    def show_logout_dialog(self):
        if not self.dialog:
            self.dialog = MDDialog(
                title="Log Out?",
                text="Are you sure you want to log out?",
                buttons = [
                    MDFlatButton(
                        text="Cancel",
                        on_release=self.close_dialog
                    ),
                    MDFlatButton(
                        text="Yes",
                        on_release=self.confirm_logout

                    ),
                ],
            )
        self.dialog.open()

    def close_dialog(self, *args):
        if self.dialog:
            self.dialog.dismiss()

    def confirm_logout(self, *args):
        self.dialog.dismiss()
        self.close_drawer()
        self.root.current = "login"

if __name__ == '__main__':
    MainApp().run()