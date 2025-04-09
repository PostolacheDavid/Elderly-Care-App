from plyer import filechooser
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty
from database import check_user
from database import submit_doctor_request, get_pending_doctors, approve_doctor
from kivymd.uix.navigationdrawer import MDNavigationLayout, MDNavigationDrawer
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from functools import partial
import os
import shutil

class ApproveItem(MDBoxLayout):
    full_name = StringProperty()
    email = StringProperty()
    doctor_id = NumericProperty()

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

    def show_popup(self, message):
        dialog = MDDialog(
            title="Doctor Registration",
            text=message,
            buttons = [
                MDFlatButton (
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()

    def open_file_chooser(self):
        file_paths = filechooser.open_file(
            title="Select a photo",
            filters=[("Images", "*.jpg;*.jpeg;*.png")],
            multiple=False
        )

        if file_paths:
            self.selected_photo_path = file_paths[0]
            print(f"Selected file: {self.selected_photo_path}")

    def submit_request(self):
        full_name = self.ids.full_name.text.strip()
        email = self.ids.email.text.strip()
        password = self.ids.password.text.strip()
        confirm_pass = self.ids.rewrite_password.text.strip()

        if not full_name or not email or not password or not confirm_pass:
            self.show_popup("All fields are required.")
            return

        if password != confirm_pass:
            self.show_popup("Passwords do not match")
            return
        
        if not self.selected_photo_path:
            self.show_popup("Please select a photo before submitting.")
            return
        
        try:
            with open(self.selected_photo_path, "rb") as f:
                photo_data = f.read()

            success = submit_doctor_request(full_name, email, password, photo_data)
            if success:
                self.show_popup("Request has been sent successfully!")
            else:
                self.show_popup("Failed to submit request.")
        except Exception as e:
            self.show_popup(f"An error occurred:\n{e}")




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
        elif self.user_role == "admin":
            self.ids.health_manager.current = "admin"

    def approve_account(self, doctor_id):
        if approve_doctor(doctor_id):
            print(f"Doctor ID {doctor_id} approved!")
            self.approve_accounts_screen()
        else:
            print("Approval failed.")

    def approve_accounts_screen(self):
        self.ids.health_manager.current = "admin_approve_accounts"
        container = self.ids.approve_list
        container.clear_widgets()

        pending_list = get_pending_doctors()

        for doctor in pending_list:
            item = ApproveItem(
                full_name=doctor["full_name"],
                email=doctor["email"],
                doctor_id=doctor["id"]
            )
            container.add_widget(item)

 

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