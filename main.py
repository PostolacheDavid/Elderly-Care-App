from plyer import filechooser
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from database import check_user
from database import submit_doctor_request, get_pending_doctors, approve_doctor, create_linked_user, get_elders_by_doctor, add_elder_medication, get_medications_for_elder, get_elder_id_for_caregiver, delete_elder_medication, get_medications_with_id_for_elder, add_medical_control, get_controls_for_elder, delete_medical_control, add_elder_document, get_documents_for_elder, get_document_data, delete_elder_document
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

class ElderControlItem(MDBoxLayout):
    # These must match the KV rule’s usage of root.name, root.goal, etc.
    name = StringProperty()
    goal = StringProperty()
    details = StringProperty()
    scheduled_at = StringProperty()

class DoctorControlItem(MDBoxLayout):
    # These must match exactly what you later pass in from Python
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
        self.dialog = None  # va fi setat din exterior
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
    user_id = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.elders_list = []

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
            title="Photo Preview",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="CLOSE",
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
        if self.user_role == "doctor":
            self.ids.health_manager.current = "doctor_health"
        elif self.user_role == "elder":
            self.ids.health_manager.current = "elder_health"
        elif self.user_role == "caregiver":
            self.ids.health_manager.current = "caregiver_health"
            self.elder_id = get_elder_id_for_caregiver(self.user_id)
            print("Elder ID asociat caregiverului:", self.elder_id)
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
            self.show_popup("All elder fields are required.")
            return

        if password != confirm_pass:
            self.show_popup("Elder passwords do not match.")
            return

        success = create_linked_user(full_name, email, password, "elder", self.user_id)

        if success:
            self.show_popup("Elder account created successfully.")
        else:
            self.show_popup("Failed to create elder account.")

    def submit_caregiver(self):
        full_name = self.ids.caregiver_full_name.text.strip()
        email = self.ids.caregiver_email.text.strip()
        password = self.ids.caregiver_password.text.strip()
        confirm_pass = self.ids.caregiver_confirm_password.text.strip()
        elder_username = self.selected_elder_username

        if not all([full_name, email, password, confirm_pass, elder_username]):
            self.show_popup("All caregiver fields are required.")
            return

        if password != confirm_pass:
            self.show_popup("Caregiver passwords do not match.")
            return

        elder = next((e for e in self.elders_list if e["username"] == elder_username), None)

        if not elder:
            self.show_popup("Selected elder not found.")
            return

        success = create_linked_user(full_name, email, password, "caregiver", self.user_id, elder["id"])

        if success:
            self.show_popup("Caregiver account created successfully.")
        else:
            self.show_popup("Failed to create caregiver account.")

    def show_popup(self, message):
        dialog = MDDialog(
            title="Notice",
            text=message,
            buttons=[MDFlatButton(text="OK", on_release=lambda x: dialog.dismiss())]
        )
        dialog.open()

    def open_elder_menu(self):
        """Open or refresh the elder selection dropdown menu."""
        # 1. Get the list of elders for the current doctor (user_id should be available)
        doctor_id = self.user_id  # assuming user_id is stored in this attribute
        self.elders_list = get_elders_by_doctor(doctor_id)  # fetch list of elder dicts

        # 2. Build menu items for each elder username
        menu_items = []
        for elder in self.elders_list:
            menu_items.append({
                "text": elder["username"],            # display elder's username
                "viewclass": "OneLineListItem",       # use a simple list item view
                # When this item is clicked, call a selection handler with this elder
                "on_release": lambda x=elder: self.select_elder(x)
            })

        # 3. If a dropdown menu already exists, dismiss it to refresh items
        if hasattr(self, "elder_menu"):
            self.elder_menu.dismiss()

        # 4. Create a new dropdown menu for the current elder list and open it
        self.elder_menu = MDDropdownMenu(
            caller=self.ids.elder_field,   # the UI element that triggers the dropdown
            items=menu_items,
            width_mult=4                   # width of the dropdown menu
        )
        self.elder_menu.open()

    def select_elder(self, elder):
        """Handle selection of an elder from the dropdown."""
        # 5. Update the text field to show the selected elder’s username
        self.ids.elder_field.text = elder["username"]
        # Save the selected elder’s username for later (submit_caregiver can use this)
        self.selected_elder_username = elder["username"]
        # 6. Close the dropdown menu now that an item is selected
        self.elder_menu.dismiss()
        # Optionally, remove focus from the text field to hide keyboard (if any)
        self.ids.elder_field.focus = False

    def set_elder_dropdown(self, text):
        self.ids.elder_dropdown.set_item(text)
        self.elder_menu.dismiss()

    def load_elder_medications_for_caregiver(self):
        # 1. Găsim elder_id asociat caregiver-ului
        elder_id = get_elder_id_for_caregiver(self.user_id)  # trebuie ca self.user_id să fie setat corect la login

        if elder_id is None:
            self.show_alert_dialog("Acest îngrijitor nu are asociat niciun pacient.")
            return

        # 2. Luăm medicamentele elder-ului
        medications = get_medications_for_elder(elder_id)

        # 3. Golim lista actuală
        self.ids.medications_list.clear_widgets()

        # 4. Populăm cu medicamente
        for med in medications:
            label = MDLabel(
                text=f"\n\n{med['denumire_comerciala']} \n {med['forma_farmaceutica']} \n {med['concentratie']} \n {med['frecventa']} \n {med.get('observatii', '')}",
                size_hint_y=None,
                height=dp(40)
            )
            self.ids.medications_list.add_widget(label)

        # 5. Navigăm la ecranul cu medicamente
        self.ids.health_manager.current = "view_medications_care"


    def load_medications(self):
        try:
            with open("meds.json", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Eroare la încărcarea meds.json: {e}")
            return []
        
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
        
        # Trimite referința dialogului în content
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
        
        # Închide meniul doar dacă există
        if hasattr(self, "med_menu"):
            self.med_menu.dismiss()

        # Închide dialogul dacă a fost folosit cu search
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
            # (No need to set size_hint_y/height here because the KV rule already does that.)
            container.add_widget(item)


    def open_elder_menu_for_doctor_view(self):
        print("[DEBUG] open_elder_menu_for_doctor_view() called")

        # 1) Print a message *before* calling the DB helper:
        print(f"[DEBUG] About to call get_elders_by_doctor with doctor_id={self.user_id}")

        try:
            self.elders_list = get_elders_by_doctor(self.user_id)
            # 2) This print will only run if no exception is thrown above:
            print(f"[DEBUG] Elders for doctor_id={self.user_id}: {self.elders_list}")
        except Exception as e:
            # 3) If anything went wrong, we’ll see the error here:
            print(f"[ERROR] get_elders_by_doctor({self.user_id}) raised exception: {e}")
            self.elders_list = []

        # 4) Now build menu_items from whatever self.elders_list contains
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

        # 5) Ensure that doctor_elder_dropdown is a valid ID in this screen:
        self.doctor_elder_menu = MDDropdownMenu(
            caller=self.ids.doctor_elder_dropdown,
            items=menu_items,
            width_mult=4
        )
        self.doctor_elder_menu.open()

    def view_medications_screen(self):
        """
        Called when an Elder taps “Medicine” on their dashboard GridCard.
        This reuses the caregiver’s logic but passes the Elder’s own user_id.
        """
        elder_id = self.user_id
        medications = get_medications_for_elder(elder_id)
        print(f"[DEBUG] view_medications_screen() called for elder_id={elder_id}, meds={medications!r}")

        container = self.ids.medications_list
        container.clear_widgets()

        if not medications:
            # 1) Add the “no meds” label
            container.add_widget(
                MDLabel(
                    text="There is no registered medication.",
                    halign="center",
                    size_hint_y=None,
                    height=dp(50)
                )
            )
            # 2) Now switch to the “view_medications_care” screen and return
            self.ids.health_manager.current = "view_medications_care"
            return

        # 3) If there *are* medications, add them all…
        for med in medications:
            item = MDLabel(
                text=(
                    f"[b]{med['denumire_comerciala']}[/b] – {med['forma_farmaceutica']} "
                    f"({med['concentratie']})\n"
                    f"Frecvență: {med['frecventa']}\n"
                    f"Observații: {med.get('observatii', '')}"
                ),
                markup=True,
                size_hint_y=None,
                height=dp(100),
                padding=(dp(10), dp(10))
            )
            container.add_widget(item)

        # 4) Finally, switch to the “view_medications_care” screen
        self.ids.health_manager.current = "view_medications_care"


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

            # Reîncarcă lista de medicamente pentru elderul selectat
            if self.user_role == "doctor":
                # dacă e doctor, reîncarcă pentru elderul selectat anterior
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
        self.open_elder_menu_for_doctor_view()  # Funcție nouă descrisă mai jos

    def open_elder_menu_med(self):
        """
        Populate and open a dropdown of this doctor’s elders when the
        “Selectează pacientul” field is focused in Add Medication.
        """
        # 1) Fetch the list of elders for the current doctor (self.user_id)
        self.elders_list = get_elders_by_doctor(self.user_id)

        # 2) Build MDDropdownMenu items for each elder
        menu_items = [
            {
                "text": elder["username"],
                "viewclass": "OneLineListItem",
                "on_release": lambda x=elder: self.select_elder_med(x)
            }
            for elder in self.elders_list
        ]

        # 3) If a previous menu exists, dismiss it to refresh
        if hasattr(self, "med_elder_menu"):
            self.med_elder_menu.dismiss()

        # 4) Create and open a new dropdown, anchored to the MDTextField id=med_elder
        self.med_elder_menu = MDDropdownMenu(
            caller=self.ids.med_elder,
            items=menu_items,
            width_mult=4
        )
        self.med_elder_menu.open()
    
    def open_doctor_controls_screen(self):
        self.ids.health_manager.current = "view_controls_doctor"
        # Immediately open the elder‐selection dropdown:
        self.open_elder_menu_for_controls()

    def open_elder_menu_for_controls(self):
        # This is nearly identical to open_elder_menu_for_doctor_view,
        # but we’ll call select_elder_for_controls instead of select_elder_for_doctor_view.
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
        # 1) Dismiss the drop-down
        self.doctor_controls_menu.dismiss()

        # 2) Store this elder so future operations know whom we’re working on:
        self.selected_elder_for_control = elder

        # 3) Copy the username into the text field so it stays visible:
        self.ids.doctor_controls_elder_dropdown.text = elder["username"]

        # 4) Now load and show that elder’s controls:
        self.view_controls_for_doctor(elder["id"])


    def view_controls_for_doctor(self, doctor_id=None):
        """
        doctor_id is the logged-in doctor’s ID (or you can store self.user_id directly).
        We will fetch all controls for the currently selected elder, then add
        one DoctorControlItem per record.
        """
        # 0) Switch to the doctor-controls screen first so its ids exist
        self.ids.health_manager.current = "view_controls_doctor"

        # 1) Determine which elder to show controls for (set in select_elder_for_controls)
        elder_id = self.selected_elder_for_control["id"]

        # 2) Fetch from the database
        controls = get_controls_for_elder(elder_id)
        print(f"[DEBUG] controls for elder_id={elder_id}: {controls!r}")
        #    Each control dict should have: "id", "name", "goal", "details", "scheduled_at"

        # 3) Clear out the existing list
        container = self.ids.controls_list_doctor
        container.clear_widgets()

        # 4) Populate or show “no controls” message
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
                sched_str = str(ctrl["scheduled_at"])  # ensure plain str
                item = Factory.DoctorControlItem(
                    control_id=ctrl["id"],
                    name=ctrl["name"],
                    goal=ctrl["goal"],
                    details=ctrl["details"],
                    scheduled_at=sched_str,
                )
                container.add_widget(item)

        # 5) (Optional) keep the screen on after populating—already set at top


    
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
            # Refresh the list for whichever elder is currently shown:
            # We assume “last_elder_for_controls” was stored on self when view_controls_for_doctor was called.
            try:
                self.view_controls_for_doctor(self.last_elder_for_controls)
            except Exception:
                pass
    
    def submit_control(self, elder_id, doctor_id, name, goal, details, datetime_str):
        """
        Called by the “Save Control” button. `datetime_str` should be "YYYY-MM-DD HH:MM".
        """
        scheduled_at = f"{datetime_str}:00"
        success = add_medical_control(elder_id, doctor_id, name, goal, details, scheduled_at)
        if success:
            toast("Control adăugat cu succes!")
            self.last_elder_for_controls = elder_id
            self.view_controls_for_doctor(elder_id)
        else:
            self.show_popup("Eroare la adăugarea controlului.")

    
    def view_controls_for_elder(self):
        """
        Called when an Elder taps its own “Medical Controls” GridCard.
        Simply fetch that elder’s user_id as elder_id, then list controls read-only.
        """
        elder_id = self.user_id  # because for elder, user_id == their own elder_id
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
            sched_str = str(ctrl["scheduled_at"])   # convert to a Python string
            item = Factory.ElderControlItem(
                name=ctrl["name"],
                goal=ctrl["goal"],
                details=ctrl["details"],
                scheduled_at=sched_str,
            )
            container.add_widget(item)

    def view_controls_for_caregiver(self):
        """
        Called when a Caregiver taps its “Medical Controls” GridCard.
        We find that caregiver’s assigned elder_id, then show that elder’s controls
        in the same 'view_controls_elder' screen that an Elder would see.
        """
        # 1) Look up which elder is assigned to this caregiver
        elder_id = get_elder_id_for_caregiver(self.user_id)
        if elder_id is None:
            self.show_popup("Acest îngrijitor nu are asociat niciun pacient.")
            return

        print(f"[DEBUG] view_controls_for_caregiver() called for elder_id={elder_id}")

        # 2) Switch to the existing 'view_controls_elder' screen
        self.ids.health_manager.current = "view_controls_elder"

        # 3) Fetch the ScrollView container inside that screen
        container = self.ids.elder_controls_list
        container.clear_widgets()

        # 4) Query the database for this elder’s controls
        controls = get_controls_for_elder(elder_id)

        if not controls:
            # 5) If none, show a “no controls” label
            container.add_widget(
                MDLabel(
                    text="Nu există controale medicale înregistrate.",
                    halign="center",
                    size_hint_y=None,
                    height=dp(50),
                )
            )
            return

        # 6) Otherwise, create one ElderControlItem per control
        for ctrl in controls:
            # force scheduled_at into a plain string (e.g. “YYYY-MM-DD HH:MM:SS”)
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
        # Ask the user to pick a file
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
            self.show_popup(f"Failed to read file:\n{e}")
            return

        fname = os.path.basename(path)
        if add_elder_document(self.selected_elder_for_docs["id"], self.user_id, fname, data):
            toast("Document uploaded successfully.")
            # Refresh the list
            self.view_documents_for_doctor(self.selected_elder_for_docs["id"])
        else:
            self.show_popup("Upload failed. Please try again.")

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
                # add delete below filename
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
            title="Delete?",
            text="Remove this document?",
            buttons=[
                MDFlatButton(text="No", on_release=lambda x: d.dismiss()),
                MDFlatButton(text="Yes",
                    on_release=lambda x: self.confirm_delete_doc(d, doc_id))
            ])
        d.open()

    def confirm_delete_doc(self, dialog, doc_id):
        dialog.dismiss()
        if delete_elder_document(doc_id):
            toast("Deleted.")
            self.view_documents_for_doctor(self.selected_elder_for_docs["id"])

    def view_documents_screen(self):
        # shared by elder & caregiver
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
        if not row: return
        fname, data = row
        # Write to temp file and open via default app
        tmp = os.path.join(os.getenv("TEMP"), fname)
        with open(tmp, "wb") as f: f.write(data)
        os.startfile(tmp)


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