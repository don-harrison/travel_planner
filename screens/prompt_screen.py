import re
from kivy.uix.screenmanager import Screen
from kivymd.uix.label import MDLabel
from kivy.clock import Clock
from google_directions import get_directions, get_directions_via_waypoints
from utils.storage import load_data, save_data
import models.plan_model as plan_model
from kivymd.uix.pickers import MDDockedDatePicker
from kivy.metrics import dp
from datetime import datetime

# Replace with your actual key
GOOGLE_MAPS_API_KEY = "AIzaSyDBDQNtIZWm858YOpZYHmc4JxRYvWoz6GA"
class PromptScreen(Screen):

    def on_enter(self, *args):
        return super().on_enter(*args)
        
    def set_destination(self, destination):
        self.destination = destination
        self.ids.destination_label.text = f"What do you want to do in {destination}?"
        self.ids.prompt_input.text = ""
        self.ids.output_box.clear_widgets()
        data = load_data()
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
        
        def fetch(dt):
            data = load_data()
            try:
                data["plans"][self.destination] = {
                    "destination": self.destination,
                    "prompt": prompt_text,
                    "steps": []
                }

                # TODO: hook up origin/destination dynamically
                steps = get_directions_via_waypoints(
                    api_key=f"{GOOGLE_MAPS_API_KEY}",
                    origin="New York, NY",
                    waypoints=["Philadelphia, PA", "Baltimore, MD"],
                    destination="Washington, DC",
                    optimize=True  # or False
                )

                self.ids.output_box.clear_widgets()
                data = load_data()
                for idx, (instruction, address) in enumerate(steps, 1):
                    # strip all HTML tags
                    cleaned = re.sub(r"<.*?>", "", instruction)
                    step_text = f"{idx}. {cleaned} @ {address}"
                    lbl = MDLabel(
                        text=step_text,
                        font_size=14,
                        size_hint_y=None,
                        height=40
                    )
                    self.ids.output_box.add_widget(lbl)
                    #append step to the plan
                    data["plans"][data["destinations"].index(self.destination)]["steps"].append({
                        "instruction": cleaned,
                        "address": address
                    })

                self._display_message("Directions fetched successfully.")
                # save updated data
                save_data(data)

            except Exception as e:
                self._display_message(f"Error: {e}")

        # schedule on next frame
        Clock.schedule_once(fetch, 0)
        
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
                # Attempt to grab the selected string from the visible text input
                selected_text = instance.children[0].text  # this points to the inner MDTextField
                
                selected_date = datetime.strptime(selected_text, "%m/%d/%Y").date()
                field.text = selected_date.strftime("%m/%d/%Y")
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

