from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText, MDExtendedFabButton, MDButtonIcon
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivy.uix.screenmanager import SlideTransition
from kivy.clock import Clock
from kivy.properties import ObjectProperty
import time

from utils.storage import load_data, save_data

class HomeScreen(MDScreen):
    destinations_container = ObjectProperty(None)

    def on_enter(self):
        Clock.schedule_once(lambda dt: self.refresh_list(), 0)

    def refresh_list(self):
        container = self.destinations_container
        if not container:
            return
        container.clear_widgets()

        data = load_data()
        time.sleep(.2)
        for dest in data["destinations"]:
            self.add_button(container, text=dest, callback=lambda btn, d=dest: self.open_prompt_screen(d))

        dest_btn = MDButton(
                                MDButtonIcon(
                                    icon="plus",
                                ),
                                MDButtonText(
                                    text="Add Destination",
                                ),
                                style="elevated")
        dest_btn.bind(on_release=self.show_add_dialog)
        # Add button for new destination
        container.add_widget(dest_btn)

    def add_button(self, container, text, callback, extended=False):
        if extended:
            btn = MDExtendedFabButton(MDButtonText(text=text, size_hint_y=None, height=60))
        else:
            btn = MDButton(
                MDButtonText(text=text),
                size_hint_y=None,
                height=60
            )
        btn.bind(on_release=callback)
        container.add_widget(btn)

    def show_add_dialog(self, *args):
        layout = MDBoxLayout(orientation='vertical', spacing=10, padding=10)
        text_input = MDTextField(hint_text="Destination name")
        layout.add_widget(text_input)

        def add_and_close(_):
            name = text_input.text.strip()
            if name:
                data = load_data()
                if name not in data["destinations"]:
                    data["destinations"].append(name)
                    save_data(data)
                popup.dismiss()
                self.refresh_list()

        add_button = MDButton(
                                MDButtonIcon(
                                    icon="plus",
                                ),
                                MDButtonText(
                                    text="Elevated",
                                ),
                                style="elevated")

        add_button.bind(on_release=add_and_close)
        layout.add_widget(add_button)

        popup = MDDialog(
            title="Add Destination",
            content=layout,
            size_hint=(0.8, 0.4)
        )
        popup.open()

    def open_prompt_screen(self, destination):
        prompt_screen = self.manager.get_screen('prompt')
        prompt_screen.set_destination(destination)
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'prompt'