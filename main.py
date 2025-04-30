from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager

from screens.home_screen import HomeScreen
from screens.prompt_screen import PromptScreen

class TravelPlannerApp(App):
    def build(self):
        Builder.load_file("travel.kv")
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(PromptScreen(name="prompt"))
        return sm

if __name__ == "__main__":
    TravelPlannerApp().run()
