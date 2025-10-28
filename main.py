from plyer import filechooser
import webbrowser
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from database import check_user
from database import submit_doctor_request, get_pending_doctors, approve_doctor, create_linked_user, get_elders_by_doctor, add_elder_medication, get_medications_for_elder, get_elder_id_for_caregiver, delete_elder_medication, get_medications_with_id_for_elder, add_medical_control, get_controls_for_elder, delete_medical_control, add_elder_document, get_documents_for_elder, get_document_data, delete_elder_document, add_exercise_for_elder, get_exercises_for_elder, update_user_profile, get_user_email, update_linked_user_password, get_caregivers_by_doctor, update_linked_user_profile, get_all_users, reject_doctor, delete_user_by_id, get_users_by_doctor_id
from kivymd.uix.navigationdrawer import MDNavigationLayout, MDNavigationDrawer
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.button import MDFlatButton
from functools import partial
from kivy.uix.image import Image
from kivy.core.image import Image as CoreImage
import os
import shutil
import io
import base64
import json
from kivymd.uix.list import OneLineListItem
from kivy.factory import Factory
from kivymd.toast import toast
from kivy.clock import Clock
from kivymd.uix.textfield import MDTextField
from plyer import utils
from kivymd.toast import toast
from plyer import storagepath
from datetime import datetime
from kivy.utils import platform

class ViewDoctorDocumentsScreen(Screen):
    def load_data(self, doctor_id):
        self.doctor_id = doctor_id
        self.elders = get_elders_by_doctor(doctor_id)
        self.ids.elder_dropdown.values = [elder["username"] for elder in self.elders]

    def select_document(self, selection):
        if selection:
            self.selected_path = selection[0]
            print(f"[INFO] Fișier selectat: {self.selected_path}")
            if self.ids.get("selected_file_label"):
                self.ids.selected_file_label.text = os.path.basename(self.selected_path)
        else:
            self.selected_path = None
            if self.ids.get("selected_file_label"):
                self.ids.selected_file_label.text = "Niciun fișier selectat"

    def open_file_chooser(self):
        from kivy.utils import platform
        if platform == "android":
            try:
                #type: ignore
                from android.permissions import request_permissions, Permission #type: ignore
                request_permissions([
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE
                ])
            except Exception as e:
                print(f"[WARN] Nu s-au putut cere permisiunile: {e}")
        from plyer import filechooser
        filechooser.open_file(on_selection=self.select_document)

    def upload_document(self):
        import os
        from database import add_elder_document

        selected_elder_name = self.ids.elder_dropdown.text
        elder = next((e for e in self.elders if e["username"] == selected_elder_name), None)

        if not elder:
            print("[ERROR] Niciun elder selectat.")
            return

        if not hasattr(self, "selected_path") or not self.selected_path:
            print("[ERROR] Niciun fișier selectat.")
            return

        try:
            with open(self.selected_path, "rb") as f:
                file_data = f.read()
                filename = os.path.basename(self.selected_path)
        except Exception as e:
            print(f"[ERROR] Eroare la citirea fișierului: {e}")
            return

        success = add_elder_document(elder["id"], self.doctor_id, filename, file_data)

        if success:
            print("[INFO] Fișierul a fost încărcat cu succes.")
        else:
            print("[ERROR] Încărcarea a eșuat.")

class ElderControlItem(MDBoxLayout):
    name = StringProperty()
    goal = StringProperty()
    details = StringProperty()
    scheduled_at = StringProperty()

class DoctorControlItem(MDBoxLayout):
    control_id = NumericProperty()
    name       = StringProperty()
    goal       = StringProperty()
    details    = StringProperty()
    scheduled_at = StringProperty()


class MedicationSearchDialog(MDBoxLayout):
    def __init__(self, callback, meds_data, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        self.full_data = meds_data
        self.dialog = None
        self.filter_medications("")

    def filter_medications(self, search_text):
        filtered = [
            {
                "text": med.get("Denumire comerciala", "Necunoscut"),
                "on_release": lambda med=med: self.select_med(med)
            }
            for med in self.full_data
            if search_text.lower() in med.get("Denumire comerciala", "").lower()
        ]
        self.ids.med_rv.data = filtered

    def select_med(self, med):
        self.callback(med)
        if self.dialog:
            self.dialog.dismiss()

class ViewMedicationsScreen(MDScreen):
    def on_pre_enter(self):
        app = MDApp.get_running_app()
        if app.root.get_screen("main").user_role == "elder":
            app.root.get_screen("main").view_medications_screen()
            print("Elder is viewing meds – refreshing list")


class DoctorMedItem(MDBoxLayout):
    med_id = NumericProperty()
    denumire = StringProperty()
    forma = StringProperty()
    concentratie = StringProperty()
    frecventa = StringProperty()
    observatii = StringProperty()

class ApproveItem(MDBoxLayout):
    full_name = StringProperty()
    email = StringProperty()
    doctor_id = NumericProperty()
    image_texture = ObjectProperty(None)
    photo_data = ObjectProperty()

    def on_image_data(self, instance, value):
        if value:
            image = CoreImage(io.BytesIO(value), ext='png')
            self.image_texture = image.texture

class LoginScreen(Screen):

    def clean_text(self):
        self.ids.username.text = ""
        self.ids.password.text = ""
        self.ids.login_status.text = ""

    def login(self):

        username = self.ids.username.text.strip()
        password = self.ids.password.text.strip()

        user_data = check_user(username, password)

        if user_data:
            role, user_id = user_data
            main_screen = self.manager.get_screen("main")

            main_screen.user_role = role
            main_screen.user_id = user_id
            main_screen.username = username
            main_screen.ensure_android_permissions()
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
            title="Înregistrare Doctor",
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
        # Pe Android, cerem permisiuni la runtime
        if platform == "android":
            try:
                #type: ignore
                from android.permissions import request_permissions, Permission #type: ignore
                request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
            except Exception as e:
                print(f"[WARN] Nu s-au putut cere permisiunile: {e}")

        # Deschide file chooser
        filechooser.open_file(on_selection=self.handle_file_selection)

    def handle_file_selection(self, selection):
        if selection:
            self.selected_photo_path = selection[0]
            print(f"[INFO] Poză selectată: {self.selected_photo_path}")
        else:
            print("[WARN] Nicio poză selectată.")

    def submit_request(self):
        full_name = self.ids.full_name.text.strip()
        email = self.ids.email.text.strip()
        password = self.ids.password.text.strip()
        confirm = self.ids.rewrite_password.text.strip()

        # Validari
        if not full_name or not email or not password or not confirm:
            self.show_popup("Toate câmpurile sunt obligatorii.")
            return

        if password != confirm:
            self.show_popup("Parolele nu coincid.")
            return

        if not self.selected_photo_path:
            self.show_popup("Nu ai selectat nicio poză.")
            return

        # Citeste fisierul foto
        try:
            with open(self.selected_photo_path, 'rb') as f:
                photo_data = f.read()
        except Exception as e:
            self.show_popup(f"Eroare la citirea pozei: {e}")
            return

        # Trimite catre baza de date
        success = submit_doctor_request(full_name, email, password, photo_data)

        if success:
            self.show_popup("Cererea a fost trimisă cu succes!")
            self.clear_form()
        else:
            self.show_popup("Eroare la trimiterea cererii. Încearcă alt email.")

    def clear_form(self):
        self.ids.full_name.text = ""
        self.ids.email.text = ""
        self.ids.password.text = ""
        self.ids.rewrite_password.text = ""
        self.selected_photo_path = None

    def show_popup(self, message):
        from kivymd.uix.dialog import MDDialog
        dialog = MDDialog(title="Info", text=message, size_hint=(0.8, None))
        dialog.open()
    

class MainScreen(Screen):
    user_role = StringProperty("")
    user_id = NumericProperty(0)
    selected_user_for_edit = ObjectProperty(None, allownone=True)
    selected_user_id = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.elders_list = []
        self.selected_user_for_edit = None

    def ensure_android_permissions(self):
        if platform == "android":
            try:
                from plyer import permission

                needed = [
                    permission.Permission.WRITE_EXTERNAL_STORAGE,
                    permission.Permission.READ_EXTERNAL_STORAGE
                ]
                permission.request_permissions(needed)

                granted = permission.check_permission(permission.Permission.WRITE_EXTERNAL_STORAGE)

                if not granted:
                    # Afiseaza alerta
                    dialog = MDDialog(
                        title="Permisiuni Necesare",
                        text=(
                            "Această aplicație necesită acces la spațiul de stocare al dispozitivului pentru a salva și vizualiza fișiere.\n"
                            "Fără permisiune, anumite funcții nu vor funcționa corect."
                        ),
                        buttons=[
                            MDFlatButton(text="OK", on_release=lambda x: dialog.dismiss())
                        ]
                    )
                    dialog.open()

            except Exception as e:
                print(f"[WARN] Permission request failed: {e}")

    def on_kv_post(self, base_widget):
        meds_path = os.path.join(os.path.dirname(__file__), "meds.json")
        try:
            with open(meds_path, "r", encoding="utf-8") as f:
                self.meds_data = json.load(f)
        except Exception as e:
            print(f"Error loading meds.json: {e}")
            self.meds_data = []

    def preview_image(self, image_bytes):
        if not image_bytes:
            return

        image_widget = Image(
            texture=CoreImage(io.BytesIO(image_bytes), ext="png").texture,
            size_hint=(1, None),
            height=dp(300),
            allow_stretch=True,
        )

        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(10),
            size_hint_y=None,
            height=image_widget.height + dp(60)
        )
        content.add_widget(image_widget)

        dialog = MDDialog(
            title="Vizualizare fotografie",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="ÎNCHIDE",
                    size_hint=(None, None),
                    width=dp(100),
                    height=dp(36),
                    pos_hint={"center_x": 0.5},
                    on_release=lambda x: dialog.dismiss()
                )
            ],
            auto_dismiss=False
        )
        dialog.open()

    def on_enter(self):
        self.update_ui()

    def update_ui(self):
        """
        Reimprospatarea interfetei principale de fiecare data cand utilizatorul se conecteaza, schimba filele sau revine
        la tabloul de bord. Aceasta va:
        1. Schimba panoul tabloului de bord Health pe baza self.user_role
        2. Preia si stocheaza adresa de e-mail actualizata
        3. Seteaza campurile de text ale filei Account cu numele de utilizator/e-mailul
        4. Sterge orice intrari de parola reziduale
        """
        #Panel Selection bazat pe roluri
        if self.user_role == "doctor":
            self.ids.health_manager.current = "doctor_health"
        elif self.user_role == "elder":
            self.ids.health_manager.current = "elder_health"
        elif self.user_role == "caregiver":
            self.ids.health_manager.current = "caregiver_health"
            #In caz ca e nevoie de id-ul elder-ului
            self.elder_id = get_elder_id_for_caregiver(self.user_id)
        elif self.user_role == "admin":
            self.ids.health_manager.current = "admin"

        #Obtine mail-ul din baza de date
        try:
            self.email = get_user_email(self.user_id) or ""
        except Exception as e:
            print(f"[ERROR] could not fetch email for user_id={self.user_id}: {e}")
            self.email = ""

        #Initializeaza campurile formularului Cont, daca exista
        if hasattr(self.ids, "account_username"):
            self.ids.account_username.text = self.username or ""
        if hasattr(self.ids, "account_email"):
            self.ids.account_email.text = self.email

        #Curatare intrari parola ramase
        if hasattr(self.ids, "account_password"):
            self.ids.account_password.text = ""
        if hasattr(self.ids, "account_password_confirm"):
            self.ids.account_password_confirm.text = ""

    def approve_account(self, doctor_id):
        if approve_doctor(doctor_id):
            print(f"Doctor ID {doctor_id} approved!")
            self.approve_accounts_screen()
        else:
            print("Approval failed.")

    def reject_account(self, doctor_id):
        if reject_doctor(doctor_id):
            toast("Cererea a fost respinsă.")
            self.approve_accounts_screen()
        else:
            toast("Eroare la respingerea cererii.")

    def approve_accounts_screen(self):
        self.ids.health_manager.current = "admin_approve_accounts"
        container = self.ids.approve_list
        container.clear_widgets()

        pending_list = get_pending_doctors()

        for doctor in pending_list:
            image_texture = None
            photo_data = doctor["photo"] if "photo" in doctor else None

            if photo_data:
                image_texture = CoreImage(io.BytesIO(photo_data), ext="png").texture

            item = ApproveItem(
                full_name=doctor["full_name"],
                email=doctor["email"],
                doctor_id=doctor["id"],
                image_texture=image_texture,
                photo_data=photo_data
            )
            if doctor["photo"]:
                image = CoreImage(io.BytesIO(doctor["photo"]), ext="png")
                item.image_texture = image.texture

            container.add_widget(item)

    def create_elder_screen(self):
        self.ids.health_manager.current = "create_elder"

    def create_caregiver_screen(self):
        self.ids.health_manager.current = "create_caregiver"

    def submit_elder(self):
        full_name = self.ids.elder_full_name.text.strip()
        email = self.ids.elder_email.text.strip()
        password = self.ids.elder_password.text.strip()
        confirm_pass = self.ids.elder_confirm_password.text.strip()

        if not all([full_name, email, password, confirm_pass]):
            self.show_popup("Toate câmpurile sunt obligatorii.")
            return

        if password != confirm_pass:
            self.show_popup("Parolele nu se potrivesc.")
            return

        success = create_linked_user(full_name, email, password, "elder", self.user_id)

        if success:
            self.show_popup("Cont elder creat cu succes.")
        else:
            self.show_popup("Nu s-a reușit creearea contului.")

    def submit_caregiver(self):
        full_name = self.ids.caregiver_full_name.text.strip()
        email = self.ids.caregiver_email.text.strip()
        password = self.ids.caregiver_password.text.strip()
        confirm_pass = self.ids.caregiver_confirm_password.text.strip()
        elder_username = self.selected_elder_username

        if not all([full_name, email, password, confirm_pass, elder_username]):
            self.show_popup("Toate câmpurile sunt obligatorii")
            return

        if password != confirm_pass:
            self.show_popup("Parolele nu se potrivesc.")
            return

        elder = next((e for e in self.elders_list if e["username"] == elder_username), None)

        if not elder:
            self.show_popup("Elder-ul selectat nu a fost găsit.")
            return

        success = create_linked_user(full_name, email, password, "caregiver", self.user_id, elder["id"])

        if success:
            self.show_popup("Cont creat cu succes.")
        else:
            self.show_popup("Nu s-a reușit creearea contului.")

    def show_popup(self, message):
        dialog = MDDialog(
            title="Observație",
            text=message,
            buttons=[MDFlatButton(text="OK", on_release=lambda x: dialog.dismiss())]
        )
        dialog.open()

    def open_elder_menu(self):
        #Deschidere sau actualizare meniu derulant de selectare a persoanelor varstnice
        #Obtinere lista varstnicilor pentru medicul actual (ID-ul utilizatorului ar trebui sa fie disponibil)
        doctor_id = self.user_id
        self.elders_list = get_elders_by_doctor(doctor_id)  #Obtinere lista elderi

        #Creare elemente de meniu pentru fiecare nume de utilizator senior
        menu_items = []
        for elder in self.elders_list:
            menu_items.append({
                "text": elder["username"],            
                "viewclass": "OneLineListItem",      
                #Cand se face clic pe acest element, se apeleaza un handler de selectie cu acest elder
                "on_release": lambda x=elder: self.select_elder(x)
            })

        #Daca exista deja un meniu derulant, se inchide pentru a actualiza elementele
        if hasattr(self, "elder_menu"):
            self.elder_menu.dismiss()

        #Crearea unui nou meniu derulant pentru lista curenta de varstnici
        self.elder_menu = MDDropdownMenu(
            caller=self.ids.elder_field, 
            items=menu_items,
            width_mult=4
        )
        self.elder_menu.open()

    def select_elder(self, elder):
        #Gestionare selectie a unui elder din meniul derulant.
        self.ids.elder_field.text = elder["username"]
        self.selected_elder_username = elder["username"]
        self.elder_menu.dismiss()
        self.ids.elder_field.focus = False

    def set_elder_dropdown(self, text):
        self.ids.elder_dropdown.set_item(text)
        self.elder_menu.dismiss()

    def load_elder_medications_for_caregiver(self):
        #Gasim elder_id asociat caregiver-ului
        elder_id = get_elder_id_for_caregiver(self.user_id)  #trebuie ca self.user_id sa fie setat corect la login

        if elder_id is None:
            self.show_alert_dialog("Acest îngrijitor nu are asociat niciun pacient.")
            return

        #Luam medicamentele elder-ului
        medications = get_medications_for_elder(elder_id)

        #Golim lista actuala
        self.ids.medications_list.clear_widgets()

        #Populam cu medicamente
        for med in medications:
            label = MDLabel(
                text=f"\n\n{med['denumire_comerciala']} \n {med['forma_farmaceutica']} \n {med['concentratie']} \n {med['frecventa']} \n {med.get('observatii', '')}",
                size_hint_y=None,
                height=dp(40)
            )
            self.ids.medications_list.add_widget(label)

        #Navigam la ecranul cu medicamente
        self.ids.health_manager.current = "view_medications_care"


    def load_medications(self):
        try:
            with open("meds.json", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Eroare la încărcarea meds.json: {e}")
            return []
        
    def load_medications_for_caregiver(self):
        elder_id = get_elder_id_for_caregiver(self.user_id)
        if elder_id is None:
            return

        medications = get_medications_for_elder(elder_id)
        self.ids.caregiver_medications_list.clear_widgets()

        for med in medications:
            layout = MDBoxLayout(
                orientation="vertical",
                size_hint_y=None,
                height=dp(140),
                padding=(dp(10), dp(10)),
                spacing=dp(5)
            )

            fields = [
                f"Denumire comercială: {med['denumire_comerciala']}",
                f"Formă farmaceutică: {med['forma_farmaceutica']}",
                f"Concentrație: {med['concentratie']}",
                f"Frecvență: {med['frecventa']}",
                f"Observații: {med['observatii']}"
            ]

            for text in fields:
                layout.add_widget(MDLabel(text=text, theme_text_color="Primary"))

            self.ids.caregiver_medications_list.add_widget(layout)

        
    def open_medication_dialog(self):
        if not hasattr(self, "meds_data") or not self.meds_data:
            return

        content = MedicationSearchDialog(callback=self.select_medication, meds_data=self.meds_data)
        
        self.dialog = MDDialog(
            title="Selectează medicament",
            type="custom",
            content_cls=content,
            buttons=[],
        )
        
        content.dialog = self.dialog

        self.dialog.open()
        
    def open_medication_menu(self):
        menu_items = []
        for med in self.meds_data:
            text = med.get("Denumire comerciala", "Necunoscut")
            menu_items.append({
                "text": text,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=med: self.select_medication(x)
            })

        if hasattr(self, "med_menu"):
            self.med_menu.dismiss()

        self.med_menu = MDDropdownMenu(
            caller=self.ids.med_name,
            items=menu_items,
            width_mult=4
        )
        self.med_menu.open()

    def select_medication(self, med):
        self.selected_medication_from_list = med
        self.ids.med_name.text = med.get("Denumire comerciala", "")
        self.ids.med_forma.text = med.get("Forma farmaceutica", "")
        self.ids.med_conc.text = med.get("Concentratie", "")
        
        if hasattr(self, "med_menu"):
            self.med_menu.dismiss()

        if hasattr(self, "dialog"):
            self.dialog.dismiss()


    def add_medication_screen(self):
        self.ids.health_manager.current = "add_medication"
        print("EXEMPLU MEDICAMENT:", self.meds_data[0])
    
    def view_medications_doctor(self, elder_id):
        print(f"[DEBUG] view_medications_doctor() called with elder_id={elder_id}")
        try:
            medications = get_medications_with_id_for_elder(elder_id)
            print(f"[DEBUG] get_medications_with_id_for_elder({elder_id}) returned: {medications!r}")
        except Exception as e:
            print(f"[ERROR] get_medications_with_id_for_elder({elder_id}) raised exception: {e}")
            medications = []

        container = self.ids.doctor_meds_list
        container.clear_widgets()

        if not medications:
            print("[DEBUG] No medications found; adding ‘no meds’ label.")
            container.add_widget(
                MDLabel(
                    text="There is no registered medication.",
                    halign="center",
                    size_hint_y=None,
                    height=dp(50)
                )
            )
            return

        for med in medications:
            print(f"[DEBUG] Adding widget for med: {med}")
            item = Factory.DoctorMedItem(
                med_id=med["id"],
                denumire=med["denumire_comerciala"],
                forma=med["forma_farmaceutica"],
                concentratie=med["concentratie"],
                frecventa=med["frecventa"],
                observatii=med["observatii"]
            )
            container.add_widget(item)


    def open_elder_menu_for_doctor_view(self):
        print("[DEBUG] open_elder_menu_for_doctor_view() called")

        print(f"[DEBUG] About to call get_elders_by_doctor with doctor_id={self.user_id}")

        try:
            self.elders_list = get_elders_by_doctor(self.user_id)
            print(f"[DEBUG] Elders for doctor_id={self.user_id}: {self.elders_list}")
        except Exception as e:
            print(f"[ERROR] get_elders_by_doctor({self.user_id}) raised exception: {e}")
            self.elders_list = []

        menu_items = [
            {
                "text": elder["username"],
                "viewclass": "OneLineListItem",
                "on_release": lambda x=elder: self.select_elder_for_doctor_view(x)
            }
            for elder in self.elders_list
        ]

        if hasattr(self, "doctor_elder_menu"):
            self.doctor_elder_menu.dismiss()

        self.doctor_elder_menu = MDDropdownMenu(
            caller=self.ids.doctor_elder_dropdown,
            items=menu_items,
            width_mult=4
        )
        self.doctor_elder_menu.open()

    def load_elder_medications(self):
        try:
            medications = get_medications_for_elder(self.user_id)
            self.ids.elder_medications_list.clear_widgets()

            for med in medications:
                item = OneLineListItem(
                    text=f"{med['denumire_comerciala']} - {med['frecventa']}"
                )
                self.ids.elder_medications_list.add_widget(item)
        except Exception as e:
            print(f"[EROARE] Nu s-au putut încărca medicamentele elderului: {e}")

    
    def view_medications_screen(self):
        try:
            self.ids.medications_list.clear_widgets()

            medications = get_medications_for_elder(self.user_id)
            if not medications:
                self.ids.medications_list.add_widget(
                    MDLabel(text="Nu există medicamente.", theme_text_color="Hint")
                )
                return

            for med in medications:
                self.ids.medications_list.add_widget(
                    MDLabel(
                        text=f"Denumire comercială: {med['denumire_comerciala']}",
                        theme_text_color="Primary",
                        size_hint_y=None,
                        height=dp(24)
                    )
                )
                self.ids.medications_list.add_widget(
                    MDLabel(text="", size_hint_y=None, height=dp(4))
                )

                self.ids.medications_list.add_widget(
                    MDLabel(
                        text=f"Formă farmaceutică: {med['forma_farmaceutica']}",
                        theme_text_color="Primary",
                        size_hint_y=None,
                        height=dp(24)
                    )
                )
                self.ids.medications_list.add_widget(
                    MDLabel(text="", size_hint_y=None, height=dp(4))
                )

                self.ids.medications_list.add_widget(
                    MDLabel(
                        text=f"Concentrație: {med['concentratie']}",
                        theme_text_color="Primary",
                        size_hint_y=None,
                        height=dp(24)
                    )
                )
                self.ids.medications_list.add_widget(
                    MDLabel(text="", size_hint_y=None, height=dp(4))
                )

                self.ids.medications_list.add_widget(
                    MDLabel(
                        text=f"Frecvență: {med['frecventa']}",
                        theme_text_color="Primary",
                        size_hint_y=None,
                        height=dp(24)
                    )
                )
                self.ids.medications_list.add_widget(
                    MDLabel(text="", size_hint_y=None, height=dp(0.5))
                )

                self.ids.medications_list.add_widget(
                    MDLabel(
                        text=f"Observații: {med['observatii']}",
                        theme_text_color="Primary",
                        size_hint_y=None,
                        height=dp(24)
                    )
                )

                self.ids.medications_list.add_widget(
                    MDLabel(text="", size_hint_y=None, height=dp(12))
                )

        except Exception as e:
            print(f"[EROARE] Nu s-au putut încărca medicamentele elderului: {e}")



    def select_elder_med(self, elder):
        self.ids.med_elder.text = elder["username"]
        self.selected_elder_for_med = elder
        self.med_elder_menu.dismiss()

    def submit_medication(self):
        try:
            elder = self.selected_elder_for_med
        except AttributeError:
            self.show_popup("Selectează un pacient.")
            return

        if not self.selected_medication_from_list:
            self.show_popup("Selectează un medicament.")
            return

        denumire = self.selected_medication_from_list.get("Denumire comerciala", "")
        forma = self.selected_medication_from_list.get("Forma farmaceutica", "")
        conc = self.selected_medication_from_list.get("Concentratie", "")
        frequency = self.ids.med_frequency.text.strip()

        success = add_elder_medication(
            elder_id=elder["id"],
            doctor_id=self.user_id,
            denumire_comerciala=denumire,
            forma_farmaceutica=forma,
            concentratie=conc,
            observatii=self.ids.med_notes.text,
            frecventa=frequency
        )

        if success:
            self.show_popup("Medicament adăugat cu succes!")
            self.clear_med_fields()
            self.selected_medication_from_list = None

            if self.user_role == "elder":
                self.view_medications_screen()
                print("Elder is viewing meds – refreshing list")

        else:
            self.show_popup("Eroare la salvarea medicamentului.")


    def clear_med_fields(self):
        self.ids.med_elder.text = ""
        self.ids.med_name.text = ""
        self.ids.med_forma.text = ""
        self.ids.med_conc.text = ""
        self.ids.med_notes.text = ""

    def delete_medication_dialog(self, med_id):
        dialog = MDDialog(
            title="Confirmare",
            text="Ești sigur că vrei să ștergi acest medicament?",
            buttons=[
                MDFlatButton(text="Anulează", on_release=lambda x: dialog.dismiss()),
                MDFlatButton(text="Șterge", on_release=lambda x: self.confirm_delete_medication(dialog, med_id)),
            ],
        )
        dialog.open()

    def confirm_delete_medication(self, dialog, med_id):
        dialog.dismiss()
        if delete_elder_medication(med_id):
            toast("Medicament șters.")

            if self.user_role == "doctor":
                try:
                    elder_id = self.selected_elder_for_med["id"]
                    self.view_medications_doctor(elder_id)
                except AttributeError:
                    pass
            elif self.user_role == "elder":
                self.view_medications_screen()


    def select_elder_for_doctor_view(self, elder):
        print(f"[DEBUG] select_elder_for_doctor_view() called with elder: {elder}")
        self.doctor_elder_menu.dismiss()
        self.view_medications_doctor(elder["id"])
        Clock.schedule_once(lambda dt: self.view_medications_doctor(elder["id"]), 0.01)


    def open_view_medications_doctor_screen(self):
        self.ids.health_manager.current = "view_medications_doctor"
        self.open_elder_menu_for_doctor_view()

    def open_elder_menu_med(self):
        #Completeaza si deschide o lista derulanta cu varstnicii acestui medic atunci cand campul „Selecteaza pacientul” este selectat in Adaugare medicament.
        self.elders_list = get_elders_by_doctor(self.user_id)
        menu_items = [
            {
                "text": elder["username"],
                "viewclass": "OneLineListItem",
                "on_release": lambda x=elder: self.select_elder_med(x)
            }
            for elder in self.elders_list
        ]

        if hasattr(self, "med_elder_menu"):
            self.med_elder_menu.dismiss()

        self.med_elder_menu = MDDropdownMenu(
            caller=self.ids.med_elder,
            items=menu_items,
            width_mult=4
        )
        self.med_elder_menu.open()
    
    def open_doctor_controls_screen(self):
        self.ids.health_manager.current = "view_controls_doctor"
        self.open_elder_menu_for_controls()

    def open_elder_menu_for_controls(self):
        self.elders_list = get_elders_by_doctor(self.user_id)
        menu_items = [
            {
                "text": elder["username"],
                "viewclass": "OneLineListItem",
                "on_release": lambda x=elder: self.select_elder_for_controls(x)
            }
            for elder in self.elders_list
        ]
        if hasattr(self, "doctor_controls_menu"):
            self.doctor_controls_menu.dismiss()

        self.doctor_controls_menu = MDDropdownMenu(
            caller=self.ids.doctor_controls_elder_dropdown,
            items=menu_items,
            width_mult=4
        )
        self.doctor_controls_menu.open()

    def select_elder_for_controls(self, elder):
        self.doctor_controls_menu.dismiss()

        self.selected_elder_for_control = elder

        self.ids.doctor_controls_elder_dropdown.text = elder["username"]

        self.view_controls_for_doctor(elder["id"])


    def view_controls_for_doctor(self, doctor_id=None):
        """doctor_id este ID-ul medicului conectat.
        Vom prelua toate controalele pentru varstnicul selectat in prezent, apoi vom adauga
        cate un DoctorControlItem per inregistrare.
        """
        self.ids.health_manager.current = "view_controls_doctor"

        elder_id = self.selected_elder_for_control["id"]

        controls = get_controls_for_elder(elder_id)
        print(f"[DEBUG] controls for elder_id={elder_id}: {controls!r}")

        container = self.ids.controls_list_doctor
        container.clear_widgets()

        if not controls:
            container.add_widget(
                MDLabel(
                    text="No scheduled controls.",
                    halign="center",
                    size_hint_y=None,
                    height=dp(50),
                )
            )
        else:
            for ctrl in controls:
                sched_str = str(ctrl["scheduled_at"])
                item = Factory.DoctorControlItem(
                    control_id=ctrl["id"],
                    name=ctrl["name"],
                    goal=ctrl["goal"],
                    details=ctrl["details"],
                    scheduled_at=sched_str,
                )
                container.add_widget(item)
    
    def delete_control_dialog(self, control_id):
        dialog = MDDialog(
            title="Confirmare Ștergere",
            text="Ești sigur că vrei să ștergi acest control medical?",
            buttons=[
                MDFlatButton(text="Anulează", on_release=lambda x: dialog.dismiss()),
                MDFlatButton(
                    text="Șterge",
                    on_release=lambda x: self.confirm_delete_control(dialog, control_id),
                ),
            ],
        )
        dialog.open()
    
    def confirm_delete_control(self, dialog, control_id):
        dialog.dismiss()
        if delete_medical_control(control_id):
            toast("Control șters.")
            try:
                self.view_controls_for_doctor(self.last_elder_for_controls)
            except Exception:
                pass
    
    def submit_control(self, elder_id, doctor_id, name, goal, details, datetime_str):
        scheduled_at = f"{datetime_str}:00"
        success = add_medical_control(elder_id, doctor_id, name, goal, details, scheduled_at)
        if success:
            toast("Control adăugat cu succes!")
            self.last_elder_for_controls = elder_id
            self.view_controls_for_doctor(elder_id)
        else:
            self.show_popup("Eroare la adăugarea controlului.")

    
    def view_controls_for_elder(self):
        """ Apelat atunci cand un elder isi acceseaza propriul GridCard „Controale Medicale”.
            Pur si simplu se preia user_id-ul elder-ului ca elder_id, apoi listeaza controalele doar pentru citire. """
        elder_id = self.user_id
        print(f"[DEBUG] view_controls_for_elder() called for elder_id={elder_id}")
        self.ids.health_manager.current = "view_controls_elder"
        container = self.ids.elder_controls_list
        container.clear_widgets()

        controls = get_controls_for_elder(elder_id)
        if not controls:
            container.add_widget(
                MDLabel(
                    text="Nu există controale medicale înregistrate.",
                    halign="center",
                    size_hint_y=None,
                    height=dp(50),
                )
            )
            return

        for ctrl in controls:
            sched_str = str(ctrl["scheduled_at"])
            item = Factory.ElderControlItem(
                name=ctrl["name"],
                goal=ctrl["goal"],
                details=ctrl["details"],
                scheduled_at=sched_str,
            )
            container.add_widget(item)

    def view_controls_for_caregiver(self):
        """ Apelat atunci cand un ingrijitor isi acceseaza GridCard-ul „Controale medicale”.
        Gasim elder_id-ul atribuit ingrijitorului respectiv, apoi afisam controalele varstnicului respectiv
        in acelasi ecran „view_controls_elder” pe care l-ar vedea un elder. """

        elder_id = get_elder_id_for_caregiver(self.user_id)
        if elder_id is None:
            self.show_popup("Acest îngrijitor nu are asociat niciun pacient.")
            return

        print(f"[DEBUG] view_controls_for_caregiver() called for elder_id={elder_id}")

        self.ids.health_manager.current = "view_controls_elder"

        container = self.ids.elder_controls_list
        container.clear_widgets()

        controls = get_controls_for_elder(elder_id)

        if not controls:
            container.add_widget(
                MDLabel(
                    text="Nu există controale medicale înregistrate.",
                    halign="center",
                    size_hint_y=None,
                    height=dp(50),
                )
            )
            return

        for ctrl in controls:
            sched_str = str(ctrl["scheduled_at"])
            item = Factory.ElderControlItem(
                name=ctrl["name"],
                goal=ctrl["goal"],
                details=ctrl["details"],
                scheduled_at=sched_str,
            )
            container.add_widget(item)
    
    def open_doctor_docs_screen(self):
        self.ids.health_manager.current = "doctor_docs"
        self.open_elder_menu_for_docs()

    def open_elder_menu_for_docs(self):
        self.elders_list = get_elders_by_doctor(self.user_id)
        items = [{
            "text": e["username"],
            "viewclass": "OneLineListItem",
            "on_release": lambda x=e: self.select_elder_for_docs(x)
        } for e in self.elders_list]
        if hasattr(self, "docs_elder_menu"): self.docs_elder_menu.dismiss()
        self.docs_elder_menu = MDDropdownMenu(
            caller=self.ids.doc_docs_elder_dropdown,
            items=items, width_mult=4
        )
        self.docs_elder_menu.open()

    def select_elder_for_docs(self, elder):
        self.selected_elder_for_docs = elder
        self.ids.doc_docs_elder_dropdown.text = elder["username"]
        self.docs_elder_menu.dismiss()
        self.view_documents_for_doctor(elder["id"])

    def open_file_chooser_for_doc(self):
        file_paths = filechooser.open_file(
            title="Select a document to upload",
            filters=[("All files", "*.*")],
            multiple=False
        )
        if not file_paths:
            return

        path = file_paths[0]
        try:
            with open(path, "rb") as f:
                data = f.read()
        except Exception as e:
            self.show_popup(f"Nu s-a putut citi fișierul:\n{e}")
            return

        fname = os.path.basename(path)
        if add_elder_document(self.selected_elder_for_docs["id"], self.user_id, fname, data):
            toast("Document încărcat cu succes.")
            self.view_documents_for_doctor(self.selected_elder_for_docs["id"])
        else:
            self.show_popup("Încărcarea documentului a eșuat.")

    def view_documents_for_doctor(self, elder_id):
        docs = get_documents_for_elder(elder_id)
        container = self.ids.docs_list_doctor
        container.clear_widgets()
        if not docs:
            container.add_widget(MDLabel(text="No documents.", halign="center",
                                         size_hint_y=None, height=dp(40)))
        else:
            for d in docs:
                btn = MDRaisedButton(
                    text=d["filename"],
                    size_hint_y=None, height=dp(40),
                    on_release=lambda x, doc_id=d["id"]: self.download_and_open(doc_id)
                )

                del_btn = MDRaisedButton(
                    text="Delete",
                    size_hint=(None, None), size=(dp(80), dp(32)),
                    pos_hint={"right": 1},
                    on_release=lambda x, doc_id=d["id"]: self.delete_doc_dialog(doc_id)
                )
                row = MDBoxLayout(size_hint_y=None, height=dp(48), spacing=dp(4))
                row.add_widget(btn)
                row.add_widget(del_btn)
                container.add_widget(row)

    def delete_doc_dialog(self, doc_id):
        d = MDDialog(
            title="Ștergere?",
            text="Ștergi acest document?",
            buttons=[
                MDFlatButton(text="Nu", on_release=lambda x: d.dismiss()),
                MDFlatButton(text="Da",
                    on_release=lambda x: self.confirm_delete_doc(d, doc_id))
            ])
        d.open()

    def confirm_delete_doc(self, dialog, doc_id):
        dialog.dismiss()
        if delete_elder_document(doc_id):
            toast("Șters.")
            self.view_documents_for_doctor(self.selected_elder_for_docs["id"])

    def view_documents_screen(self):
        if self.user_role == "caregiver":
            eid = get_elder_id_for_caregiver(self.user_id)
        else:
            eid = self.user_id
        docs = get_documents_for_elder(eid)
        container = self.ids.docs_list_elder
        container.clear_widgets()
        if not docs:
            container.add_widget(MDLabel(text="No documents.", halign="center",
                                         size_hint_y=None, height=dp(40)))
        else:
            for d in docs:
                container.add_widget(
                    MDRaisedButton(
                      text=d["filename"],
                      size_hint_y=None, height=dp(40),
                      on_release=lambda x, doc_id=d["id"]: self.download_and_open(doc_id)
                    )
                )
        self.ids.health_manager.current = "view_docs"

    def download_and_open(self, doc_id):
        row = get_document_data(doc_id)
        if not row:
            self.show_popup("Documentul nu a fost găsit.")
            return

        fname, data = row

        try:
            download_dir = storagepath.get_downloads_dir()
            if not download_dir:
                raise Exception("Nu s-a găsit fișierul downloads.")
        except Exception as e:
            self.show_popup(f"Nu s-a găsit calea pentru descărcare:\n{e}")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base, ext = os.path.splitext(fname)
        final_name = f"{base}_{timestamp}{ext}"
        final_path = os.path.join(download_dir, final_name)

        try:
            with open(final_path, "wb") as f:
                f.write(data)
            toast(f"Descărcat la: {final_name}")
        except Exception as e:
            self.show_popup(f"Nu s-a reușit descărcarea fișierului:\n{e}")

    def open_doctor_exercises_screen(self):
        self.ids.health_manager.current = "doctor_exercises"
        self.load_exercises_for_doctor()

    def open_elder_menu_for_exercises(self):
        self.elders_list = get_elders_by_doctor(self.user_id)
        items = [{
            "text": e["username"], "viewclass": "OneLineListItem",
            "on_release": lambda x=e: self.select_elder_for_exercises(x)
        } for e in self.elders_list]
        if hasattr(self, "ex_elder_menu"): self.ex_elder_menu.dismiss()
        self.ex_elder_menu = MDDropdownMenu(
            caller=self.ids.ex_elder_dropdown, items=items, width_mult=4
        )
        self.ex_elder_menu.open()

    def select_elder_for_exercises(self, elder):
        self.ex_elder_menu.dismiss()
        self.selected_elder_for_ex = elder
        self.ids.ex_elder_dropdown.text = elder["username"]
        self.load_exercises_for_doctor()

    def load_exercises_for_doctor(self):
        elder_id = getattr(self, "selected_elder_for_ex", {}).get("id")
        if not elder_id:
            return

        exs = get_exercises_for_elder(elder_id)
        container = self.ids.exercises_list_doctor
        container.clear_widgets()

        if not exs:
            container.add_widget(
                MDLabel(
                    text="No exercises assigned.",
                    halign="center",
                    size_hint_y=None,
                    height=dp(50),
                )
            )
            return

        for ex_data in exs:
            card = Factory.GridCard(
                text=f"[b]{ex_data['title']}[/b]\n{ex_data['description']}",
                on_release=lambda instance, ed=ex_data: webbrowser.open(ed["video_url"])
            )
            container.add_widget(card)

    def open_add_exercise_dialog(self):
        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(10),
            size_hint_y=None,
        )

        self.ex_title = MDTextField(hint_text="Title", size_hint_y=None, height=dp(48))
        self.ex_desc  = MDTextField(hint_text="Description", multiline=True,
                                    size_hint_y=None, height=dp(80))
        self.ex_url   = MDTextField(hint_text="Video URL", size_hint_y=None, height=dp(48))

        for w in (self.ex_title, self.ex_desc, self.ex_url):
            content.add_widget(w)
            content.height = sum(child.height + content.spacing for child in content.children)

        self.ex_dialog = MDDialog(
            title="",
            type="custom",
            content_cls=content,
            size_hint=(0.8, None),      
            height=dp(300),            
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda *a: self.ex_dialog.dismiss()),
                MDFlatButton(text="SAVE",   on_release=lambda *a: self.submit_exercise(self.ex_dialog)),
            ],
        )
        self.ex_dialog.open()

    def submit_exercise(self, dialog):
        dialog.dismiss()
        elder = getattr(self, "selected_elder_for_ex", None)
        if not elder:
            toast("Selectează un elder mai întâi.")
            return
        title = self.ex_title.text.strip()
        desc  = self.ex_desc.text.strip()
        url   = self.ex_url.text.strip()
        if not title or not url:
            toast("Titlu și URL necesare.")
            return
        ok = add_exercise_for_elder(elder["id"], title, desc, url)
        toast("Exercițiu adăugat." if ok else "Nu s-a reușit adăugarea.")
        if ok:
            self.load_exercises_for_doctor()

    def view_exercises_screen(self):
        if self.user_role == "caregiver":
            elder_id = get_elder_id_for_caregiver(self.user_id)
        else:
            elder_id = self.user_id

        self.ids.health_manager.current = "view_exercises"

        exs = get_exercises_for_elder(elder_id)
        container = self.ids.exercises_list_elder
        container.clear_widgets()

        if not exs:
            container.add_widget(
                MDLabel(
                    text="No exercises available.",
                    halign="center",
                    size_hint_y=None,
                    height=dp(50),
                )
            )
            return

        for ex_data in exs:
            card = Factory.GridCard(
                text=f"[b]{ex_data['title']}[/b]\n{ex_data['description']}",
                on_release=lambda instance, ed=ex_data: webbrowser.open(ed["video_url"])
            )
            container.add_widget(card)

    def on_magnify_click(self):
        search = self.ids.top_search
        search.width = dp(200)
        search.opacity = 1
        search.focus = True

    def collapse_search(self):
        search = self.ids.top_search
        search.width = 0
        search.opacity = 0
        if hasattr(self, 'search_menu'):
            self.search_menu.dismiss()

    def on_search_text(self, query: str):
        q = query.lower().strip()
        role = self.user_role

        if role == "doctor":
            choices = [
                ("Adăugați Medicamente",      self.add_medication_screen),
                ("Vezi Medicamentele Pacienților",      self.open_view_medications_doctor_screen),
                ("Adaugați Pacienți",               self.create_elder_screen),
                ("Adăugați Îngrijitori",             self.create_caregiver_screen),
                ("Controale Medicale",           self.open_doctor_controls_screen),
                ("Date Medicale",               self.open_doctor_docs_screen),
                ("Fitness",                  self.open_doctor_exercises_screen),
            ]
        elif role == "elder":
            choices = [
                ("Medicamente",        self.view_medications_screen),
                ("Controale Medicale",    self.view_controls_for_elder),
                ("Date Medicale",    self.view_documents_screen),
                ("Fitness",       self.view_exercises_screen),
            ]
        else: 
            choices = [
                ("Medicine",            self.load_elder_medications_for_caregiver),
                ("Medical Controls",    self.view_controls_for_caregiver),
                ("Medical Data",        self.view_documents_screen),
                ("Fitness",           self.view_exercises_screen),
            ]

        matches = []
        for text, cb in choices:
            if q in text.lower():
                matches.append({
                    "text": text,
                    "viewclass": "OneLineListItem",
                    "on_release": lambda t=text, callback=cb: self._on_search_select(t, callback),
                })

        if hasattr(self, "search_menu"):
            self.search_menu.dismiss()
            del self.search_menu

        if matches:
            self.search_menu = MDDropdownMenu(
                caller=self.ids.top_search,
                items=matches,
                width_mult=4,
                max_height=dp(200),
            )
            self.search_menu.open()

    def _on_search_select(self, text, callback):
        self.ids.top_search.text = ""
        self.collapse_search()
        callback()

    def update_user_profile(self):
        new_username = self.ids.account_username.text.strip()
        new_email    = self.ids.account_email.text.strip()
        new_pass     = self.ids.account_password.text
        confirm_pass = self.ids.account_password_confirm.text

        changed = {}
        if new_username and new_username != self.username:
            changed["username"] = new_username
        if new_email and new_email != self.email:
            changed["email"] = new_email

        if new_pass or confirm_pass:
            if new_pass != confirm_pass:
                self.show_popup("Parolele nu se potrivesc.")
                return
            changed["password"] = new_pass

        if not changed:
            self.show_popup("Nu s-au detectat schimbări.")
            return

        send_username = changed.get("username", self.username)
        send_email    = changed.get("email",    self.email)
        send_password = changed.get("password", None)

        success = update_user_profile(
            user_id      = self.user_id,
            new_username = send_username,
            new_email    = send_email,
            new_password = send_password
        )

        if success:
            self.show_popup("Profil modificat cu succes.")
            if "username" in changed:
                self.username = send_username
            if "email" in changed:
                self.email = send_email
            self.ids.account_password.text = ""
            self.ids.account_password_confirm.text = ""
        else:
            self.show_popup("Nu s-a reușit modificarea profilului.")

    def toggle_username_field(self):
        c = self.ids.account_username_container
        c.disabled = not c.disabled
        c.opacity = 1 if not c.disabled else 0

    def toggle_email_field(self):
        c = self.ids.account_email_container
        c.disabled = not c.disabled
        c.opacity = 1 if not c.disabled else 0

    def toggle_password_fields(self):
        c = self.ids.account_password_container
        c.disabled = not c.disabled
        c.opacity = 1 if not c.disabled else 0

    def toggle_manage_username_field(self):
        c = self.ids.username_container
        c.disabled = not c.disabled
        c.opacity = 1 if not c.disabled else 0

    def toggle_manage_email_field(self):
        c = self.ids.email_container
        c.disabled = not c.disabled
        c.opacity = 1 if not c.disabled else 0

    def toggle_manage_password_fields(self):
        c = self.ids.password_container
        c.disabled = not c.disabled
        c.opacity = 1 if not c.disabled else 0

    def open_manage_accounts(self):
        self.ids.health_manager.current = "manage_accounts"
        self.linked_users = []
        self.linked_users += get_elders_by_doctor(self.user_id)
        self.linked_users += get_caregivers_by_doctor(self.user_id)

    def open_manage_user_menu(self):
        items = [{
            "text": u["username"],
            "viewclass": "OneLineListItem",
            "on_release": lambda u=u: self.select_manage_user(u)
        } for u in self.linked_users]

        if hasattr(self, "manage_user_menu"):
            self.manage_user_menu.dismiss()
        self.manage_user_menu = MDDropdownMenu(
            caller=self.ids.user_dropdown,
            items=items,
            width_mult=4
        )
        self.manage_user_menu.open()

    def select_manage_user(self, user):
        self.manage_user_menu.dismiss()
        self.ids.user_dropdown.text = user["username"]
        self.selected_manage_user = user

    def reset_linked_user_password(self):
        pwd = self.ids.new_user_password.text.strip()
        confirm = self.ids.confirm_user_password.text.strip()
        if not pwd or pwd != confirm:
            self.show_popup("Parolele trebuie sa se potrivească și să nu fie null.")
            return

        ok = update_linked_user_password(self.selected_manage_user["id"], pwd)
        if ok:
            self.show_popup(f"Parola pentru {self.selected_manage_user['username']} resetată.")
            self.ids.new_user_password.text = ""
            self.ids.confirm_user_password.text = ""
        else:
            self.show_popup("Nu s-a reușit resetarea parolei.")

    def apply_manage_user_changes(self):
        if not hasattr(self, "selected_manage_user"):
            toast("Nici un user selectat.")
            return
        user = self.selected_manage_user

        new_username = self.ids.new_username.text.strip()
        new_email    = self.ids.new_email.text.strip()
        new_pass     = self.ids.new_user_password.text
        confirm_pass = self.ids.confirm_user_password.text

        if new_pass or confirm_pass:
            if new_pass != confirm_pass:
                toast("Parolele nu se potrivesc.")
                return

            from database import update_linked_user_password
            ok_pw = update_linked_user_password(user["id"], new_pass)
            if ok_pw:
                toast("Parolă schimbată.")
            else:
                toast("Nu s-a reușit schimbarea parolei.")
        else:
            ok_pw = True 

        if new_username or new_email:
            from database import update_linked_user_profile
            un = new_username if new_username else None
            em = new_email    if new_email    else None
            ok_profile = update_linked_user_profile(
                user_id      = user["id"],
                new_username = un,
                new_email    = em
            )
            if ok_profile:
                toast("Profil schimbat.")
            else:
                toast("Nu s-a reușit schimbarea profilului.")
        else:
            ok_profile = True

        if ok_pw and ok_profile:
            self.ids.new_username.text = ""
            self.ids.new_email.text    = ""
            self.ids.new_user_password.text        = ""
            self.ids.confirm_user_password.text    = ""
            for cid in ("username_container", "email_container", "password_container"):
                c = self.ids[cid]
                c.disabled = True
                c.opacity  = 0

    def save_any_user_update(self):
        if not hasattr(self, "selected_user_for_edit") or not self.selected_user_for_edit:
            toast("Niciun utilizator selectat.")
            return

        selected = self.selected_user_for_edit
        username = self.ids.username_field.text.strip()
        email = self.ids.email_field.text.strip()
        password = self.ids.password_field.text.strip()

        try:
            update_user_profile(
                user_id=selected["id"],
                new_username=username,
                new_email=email,
                new_password=password if password else None
            )
            toast("Datele au fost actualizate.")
        except Exception as e:
            print("Eroare reală:", e)
            toast("Eroare reală la salvare.")



    def modify_accounts_screen(self):
        self.ids.select_user_dropdown.text = ""
        self.ids.username_field.text = ""
        self.ids.email_field.text = ""
        self.ids.password_field.text = ""

        self.ids.health_manager.current = "edit_any_account"

    def open_all_users_dropdown(self):
        users = get_all_users()
        self.all_users_list = users
        menu_items = []

        for user in users:
            menu_items.append({
                "text": f"{user['username']} ({user['role']})",
                "viewclass": "OneLineListItem",
                "height": dp(48),
                "on_release": partial(self.select_user_for_edit, user)
            })

        if hasattr(self, "user_select_menu"):
            self.user_select_menu.dismiss()

        self.user_select_menu = MDDropdownMenu(
            caller=self.ids.select_user_dropdown,
            items=menu_items,
            width_mult=4
        )
        self.user_select_menu.open()

    def select_user_for_edit(self, user):
        self.selected_user_for_edit = user
        self.ids.select_user_dropdown.text = user["username"]
        self.ids.username_field.text = user["username"]
        self.ids.email_field.text = user["email"]

    def go_to_view_medications(self):
        self.view_medications_screen()
        self.ids.health_manager.current = "view_medications"

    def delete_selected_user(self):
        if self.selected_user_for_edit:
            user_id = self.selected_user_for_edit["id"]
            role = self.selected_user_for_edit["role"]

            if role == "doctor":
                associated_users = get_users_by_doctor_id(user_id)
                if associated_users:
                    # Construim lista de asociați
                    info = "\n".join([f"{u['username']} ({u['role']})" for u in associated_users])
                    self.show_association_popup(info)
                    return

            if delete_user_by_id(user_id):
                toast("Contul a fost șters.")
                self.open_all_users_dropdown()
                self.ids.username_field.text = ""
                self.ids.email_field.text = ""
                self.ids.select_user_dropdown.text = "Selectează utilizator"
                self.selected_user_for_edit = None
            else:
                toast("Eroare la ștergere cont.")
        else:
            toast("Selectează un utilizator mai întâi.")

    def show_association_popup(self, associated_info):
        if hasattr(self, "dialog") and self.dialog:
            self.dialog.dismiss()

        self.dialog = MDDialog(
            title="Conturi asociate existente",
            text=f"Nu poți șterge acest doctor deoarece are următoarele conturi asociate:\n\n{associated_info}\n\nȘterge-le mai întâi.",
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: self.dialog.dismiss()
                )
            ]
        )
        self.dialog.open()

            

class MainApp(MDApp):

    dialog = None

    def build(self):
        sm = ScreenManager()

        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(DoctorRegisterScreen(name="doctor_register"))
        sm.add_widget(ViewDoctorDocumentsScreen(name="view_doctor_documents"))
        return sm
    
    def close_drawer(self):
        nav_drawer = self.root.get_screen("main").ids.nav_drawer
        nav_drawer.set_state("close")
    
    def show_logout_dialog(self):
        if not self.dialog:
            self.dialog = MDDialog(
                title="Deconectare?",
                text="Ești sigur că dorești să te deconectezi?",
                buttons = [
                    MDFlatButton(
                        text="Anulare",
                        on_release=self.close_dialog
                    ),
                    MDFlatButton(
                        text="Da",
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

    def open_url(self, url: str):
        try:
            utils.open_url(url)
        except Exception as e:
            toast(f"Nu am putut deschide link-ul: {e}")

if __name__ == '__main__':
    MainApp().run()