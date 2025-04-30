import re
from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.clock import Clock
from google_directions import get_directions

# Replace with your actual key
GOOGLE_MAPS_API_KEY = "AIzaSyDBDQNtIZWm858YOpZYHmc4JxRYvWoz6GA"

class PromptScreen(Screen):
    def set_destination(self, destination):
        self.destination = destination
        self.ids.destination_label.text = f"What do you want to do in {destination}?"
        self.ids.prompt_input.text = ""
        self.ids.output_box.clear_widgets()

    def submit_prompt(self):
        prompt_text = self.ids.prompt_input.text.strip()
        if not prompt_text:
            self._display_message("Prompt is empty.")
            return

        self._display_message("Fetching directions...")

        def fetch(dt):
            try:
                # TODO: hook up origin/destination dynamically
                steps = get_directions(
                    GOOGLE_MAPS_API_KEY,
                    origin="Salt Lake City, UT",
                    destination="Moab, UT"
                )

                self.ids.output_box.clear_widgets()
                for idx, (instruction, address) in enumerate(steps, 1):
                    # strip all HTML tags
                    cleaned = re.sub(r"<.*?>", "", instruction)
                    step_text = f"{idx}. {cleaned} @ {address}"
                    lbl = Label(
                        text=step_text,
                        font_size=14,
                        size_hint_y=None,
                        height=40
                    )
                    self.ids.output_box.add_widget(lbl)

            except Exception as e:
                self._display_message(f"Error: {e}")

        # schedule on next frame
        Clock.schedule_once(fetch, 0)

    def _display_message(self, msg):
        self.ids.output_box.clear_widgets()
        lbl = Label(
            text=msg,
            font_size=14,
            size_hint_y=None,
            height=40
        )
        self.ids.output_box.add_widget(lbl)
