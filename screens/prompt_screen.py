import re
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivy.uix.label import Label
from kivymd.uix.pickers import MDDockedDatePicker
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp
from threading import Thread
from kivymd.uix.snackbar import (
    MDSnackbar, MDSnackbarSupportingText, MDSnackbarText
)
from kivy.uix.screenmanager import SlideTransition

from utils.storage import load_data, save_data
from datetime import datetime
from dotenv import load_dotenv
import os
from kivymd.uix.pickers import MDModalDatePicker
from datetime import date, timedelta  # This gives you the 'date' type

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
        steps = data["plans"].get(destination, {}).get("steps", [])

        day_title = ""
        entries = []

        def add_day_section(day_title, entries):
            print(entries)
            # Add elevated button as day header
            self.ids.output_box.add_widget(
                MDButton(
                    MDButtonText(text=day_title),
                    style="elevated",
                    size_hint_y=None,
                    height=dp(40),
                )
            )

            # Add time + description per entry
            for time, desc in entries:
                row = MDBoxLayout(
                    orientation="horizontal",
                    spacing=dp(10),
                    size_hint_y=None,
                    height=dp(36),
                    padding=(dp(10), 0),
                )

                time_button = MDButton(
                    MDButtonText(text=time),
                    style="text",
                    size_hint=(None, None),
                    height=dp(30),
                    width=dp(80),
                )

                desc_label = MDLabel(
                    text=desc
                )

                row.add_widget(time_button)
                row.add_widget(desc_label)
                self.ids.output_box.add_widget(row)

        entry_pattern = re.compile(r"\*\s+\*\*(.+?)\*\*\s*(.*)")

        for step in steps:
            step = step.strip()
            if step.startswith("**Day"):
                if day_title:
                    add_day_section(day_title, entries)
                day_title = step.strip("*").strip()
                entries = []
            elif step.startswith("*"):
                match = entry_pattern.match(step)
                if match:
                    entries.append((match.group(1).strip(), match.group(2).strip()))

        if day_title and entries:
            add_day_section(day_title, entries)

    def open_google_maps_screen(self, destination):
        map_screen = self.manager.get_screen('map')
        map_screen.set_destination(destination)
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'map'


    def clear_itinerary(self):
        self.ids.output_box.clear_widgets()
        data = load_data()
        data["plans"][self.destination]["steps"] = ""
        save_data(data)

    def submit_prompt(self):
        prompt_text = self.ids.prompt_input.text.strip()
        origin = self.ids.origin_input.text.strip()
        
        #WARNING: Might cause issues if the self is shared between instances on different destination pages
        self.origin = origin

        data = load_data()
        data["plans"][self.destination]["origin"] = origin

        if not prompt_text:
            self._display_message("Prompt is empty.")
            return

        self._display_message("Fetching Itinerary…")

        # Start the heavy work in a daemon thread:
        Thread(
            target=self._fetch_itinerary,
            args=(prompt_text,),
            daemon=True
        ).start()

    def _fetch_itinerary(self, prompt_text):
        try:
            data = load_data()

            state = ig.State(
                destination=self.destination,
                prompt=prompt_text,
                origin = self.origin,
                date_start = str(self.date_start),
                date_end = str(self.date_end),
                interests=prompt_text,
                limit=10,
                itinerary="",
                improved_itinerary="",
                final_itinerary=""
            )

            itinerary = ig.generate_improved_itinerary(state)

            steps = itinerary.split("\n")

            data["plans"][self.destination] = {
                "destination": self.destination,
                "prompt": prompt_text,
                "steps": steps
            }
            
            save_data(data)

            # Schedule the UI update back on the main thread
            Clock.schedule_once(lambda dt: self._on_itinerary_ready(), 0)

        except Exception as e:
            Clock.schedule_once(lambda dt, error=e: self._display_message(f"Error: {error}"), 0)

    def _on_itinerary_ready(self):
        self.update_steps()

    def update_steps(self):
        data = load_data()
        self.ids.output_box.clear_widgets()

        for step in data["plans"][self.destination]["steps"]:
            self._add_step(step)

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

    def on_ok(self, instance_date_picker):
            self.ids.date_field.text = str(instance_date_picker.min_date) + "-" + str(instance_date_picker.max_date)
            data = load_data()
            data["plans"][self.destination]["date_start"] = instance_date_picker.min_date
            data["plans"][self.destination]["date_end"] = instance_date_picker.max_date
            self.date_start = instance_date_picker.min_date
            self.date_end = instance_date_picker.max_date
            
            MDSnackbar(
                MDSnackbarText(
                    text="Selected dates is:"
                ),
                MDSnackbarSupportingText(
                    text="\n".join(str(date) for date in instance_date_picker.get_date()),
                    padding=[0, 0, 0, dp(12)],
                ),
                y=dp(124),
                pos_hint={"center_x": 0.5},
                size_hint_x=0.5,
                padding=[0, 0, "8dp", "8dp"],
            ).open()
            
    def on_date_focus(self, instance, focused):
        if focused:  # Only when the user clicks into the field
            self.show_modal_date_picker()

    def show_modal_date_picker(self, *args):
        today = date.today()
        future_date = today + timedelta(days=4)

        date_dialog = MDModalDatePicker(
            mode="range",
            min_date=today,
            max_date=future_date
        )
        
        date_dialog.bind(on_ok=self.on_ok)
        date_dialog.open()


    # def show_date_picker(self, field):
    #     if not field.focus:
    #         return

    #     picker = MDDockedDatePicker(mode='range')
    #     was_confirmed = {"value": False}

    #     def on_ok(instance):
    #         was_confirmed["value"] = True

    #         try:
    #             print("selected date:", instance.get_date())
    #             # Attempt to grab the selected string from the visible text input
    #             # selected_text = instance.children[0].text  # this points to the inner MDTextField
                
    #             # selected_date = datetime.strptime(selected_text, "%m/%d/%Y").date()
    #             # field.text = selected_date.strftime("%m/%d/%Y")
    #         except Exception as e:
    #             print(f"Failed to parse selected date: {e}")
    #             print(instance.children)

    #     def on_dismiss(instance):
    #         print("selected date:", instance.get_date())

    #         if not was_confirmed["value"]:
    #             print("User dismissed without selecting a date.")

    #     picker.bind(on_ok=on_ok)
    #     picker.bind(on_dismiss=on_dismiss)

    #     picker.pos = [
    #         field.center_x - picker.width / 2,
    #         field.y - (picker.height + dp(32)),
    #     ]

    #     picker.open()