from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.properties import ObjectProperty
from kivy.clock import Clock
from utils.storage import load_data, save_data

class HomeScreen(Screen):
    # this will be bound to the GridLayout in KV
    destinations_container = ObjectProperty(None)

    def on_enter(self):
        # defer the actual refresh one frame
        Clock.schedule_once(lambda dt: self.refresh_list(), 0)

    def refresh_list(self):
        container = self.destinations_container
        if not container:
            # still not bound? bail out
            return
        container.clear_widgets()

        data = load_data()
        for dest in data["destinations"]:
            btn = Button(text=dest, size_hint_y=None, height=60)
            btn.bind(on_release=lambda b, d=dest: self.open_prompt_screen(d))
            container.add_widget(btn)

        add_btn = Button(text="+ Add New Destination", size_hint_y=None, height=60)
        add_btn.bind(on_release=self.show_add_dialog)
        container.add_widget(add_btn)

    def show_add_dialog(self, instance):
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        text_input = TextInput(hint_text="Destination name")
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

        add_button = Button(text="Add", size_hint_y=None, height=40)
        add_button.bind(on_release=add_and_close)
        layout.add_widget(add_button)

        popup = Popup(title="Add Destination", content=layout,
                      size_hint=(0.8, 0.4))
        popup.open()

    def open_prompt_screen(self, destination):
        prompt_screen = self.manager.get_screen('prompt')
        prompt_screen.set_destination(destination)
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'prompt'
