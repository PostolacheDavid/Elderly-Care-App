from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

class MainScreen(MDScreen):
    pass

class MainApp(MDApp):
    def build(self):
        return MainScreen()
    
    def on_menu_click(self):
        print("Menu button clicked!")
    
    def on_magnify_click(self):
        print("Magnify button clicked!")

if __name__ == '__main__':
    MainApp().run()