import components.component_utils as component_utils
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText, MDExtendedFabButton, MDButtonIcon
from kivymd.uix.textfield import MDTextField

from kivymd.uix.dialog import (
    MDDialog,
    MDDialogHeadlineText,
    MDDialogSupportingText,
    MDDialogContentContainer,
    MDDialogButtonContainer,
    MDDialogIcon
)
from components.button import DestinationButton
from kivy.lang import Builder
from kivymd.uix.divider import MDDivider
from kivymd.uix.list import MDListItem, MDListItemLeadingIcon, MDListItemSupportingText
from kivymd.uix.label import MDLabel
from kivymd.uix.widget import Widget
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
            MDButtonIcon(icon="plus"),
            MDButtonText(text="Add Destination"),
            style="elevated"
        )
        dest_btn.bind(on_release=self.show_add_dialog)
        container.add_widget(dest_btn)
        container.do_layout()  # ensures layout & pos updates
    
    def add_button(self, container, text, callback, extended=False):
        btn = component_utils.add_tonal(text)
        btn.bind(on_release=callback)
        container.add_widget(btn)

    def show_add_dialog(self, *args):
        text_input = MDTextField(
            hint_text="Destination name",
            mode="outlined"
        )

        def add_and_close(_):
            name = text_input.text.strip()
            if name:
                data = load_data()
                if name not in data["destinations"]:
                    data["destinations"].append(name)
                    data["plans"][name] = {"destination": name,
                    "prompt": None,
                    "steps": None,
                    "date_start": None,
                    "date_end": None}
                    save_data(data)
                dialog.dismiss()
                self.refresh_list()

        dialog = MDDialog(
            MDDialogIcon(icon="plus"),
            MDDialogHeadlineText(text="Add a Destination"),
            MDDialogContentContainer(
                text_input,
                orientation="vertical"
            ),
            MDDialogButtonContainer(
                Widget(),  # Spacer
                MDButton(
                    MDButtonText(text="Cancel"),
                    style="text",
                    on_release=lambda _: dialog.dismiss()
                ),
                MDButton(
                    MDButtonIcon(icon="plus"),
                    MDButtonText(text="Add"),
                    on_release=add_and_close
                ),
                spacing="8dp",
            ),
        )

        dialog.open()

    def open_prompt_screen(self, destination):
        prompt_screen = self.manager.get_screen('prompt')
        prompt_screen.set_destination(destination)
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'prompt'
