import re
from kivymd.uix.label import MDLabel
from kivymd.uix.pickers import MDDockedDatePicker
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp

from utils.storage import load_data, save_data
from datetime import datetime
from dotenv import load_dotenv
import os

#Local imports
from google_directions import get_directions_via_waypoints
import itinerary_generator as ig

class PromptScreen(Screen):
    # On Enter is called when the screen is entered
    def on_enter(self, *args):
        load_dotenv()
        self.google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")

        return super().on_enter(*args)
    
    def set_destination(self, destination):
        self.destination = destination
        self.ids.destination_label.text = f"What do you want to do in {destination}?"
        self.ids.prompt_input.text = ""
        self.ids.output_box.clear_widgets()
        data = load_data()

        #If the destination already has a plan, load it into the label for directions
        self.ids.output_box.add_widget(
            MDLabel(
                text = data["plans"][destination]["prompt"] if destination in data["plans"] else "",
                font_size=14,
                size_hint_y=None,
                height=40
            )
        )

    def submit_prompt(self):
        prompt_text = self.ids.prompt_input.text.strip()
        if not prompt_text:
            self._display_message("Prompt is empty.")
            return

        self._display_message("Fetching directions...")
        
        #Hook for llm responses!
        def fetch(dt):
            data = load_data()
            try:
                # Get the itinerary
                itinerary = ig.build_itinerary(
                    self.destination,
                    prompt_text,
                    limit=10
                )
                #output itinerary to file
                with open("itinerary.txt", "w") as f:
                    f.write(itinerary["output"])

                #take in itinerary and get steps
                steps = itinerary["output"].split("\n")

                data["plans"][self.destination] = {
                    "destination": self.destination,
                    "prompt": prompt_text,
                    "steps": steps
                }

                self.ids.output_box.clear_widgets()

                for step in data["plans"][self.destination]["steps"]:
                    self._add_step(step)

                # save updated data
                save_data(data)

            except Exception as e:
                self._display_message(f"Error: {e}")

        # schedule on next frame
        Clock.schedule_once(fetch, 0)

    def _add_step(self, step):
        lbl = MDLabel(
            text=step,
            font_size=14,
            size_hint_y=None,
            height=40
        )
        self.ids.output_box.add_widget(lbl)

    def _display_message(self, msg):
        self.ids.output_box.clear_widgets()

        lbl = MDLabel(
            text=msg,
            font_size=14,
            size_hint_y=None,
            height=40
        )
        self.ids.output_box.add_widget(lbl)
        
    def show_date_picker(self, field):
        if not field.focus:
            return

        picker = MDDockedDatePicker(mode='range')
        was_confirmed = {"value": False}

        def on_ok(instance):
            was_confirmed["value"] = True

            try:
                print("selected date:", instance.selected_date)
                # Attempt to grab the selected string from the visible text input
                # selected_text = instance.children[0].text  # this points to the inner MDTextField
                
                # selected_date = datetime.strptime(selected_text, "%m/%d/%Y").date()
                # field.text = selected_date.strftime("%m/%d/%Y")
            except Exception as e:
                print(f"Failed to parse selected date: {e}")
                print(instance.children)

        def on_dismiss(instance):
            if not was_confirmed["value"]:
                print("User dismissed without selecting a date.")

        picker.bind(on_ok=on_ok)
        picker.bind(on_dismiss=on_dismiss)

        picker.pos = [
            field.center_x - picker.width / 2,
            field.y - (picker.height + dp(32)),
        ]

        picker.open()

