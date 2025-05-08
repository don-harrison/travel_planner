from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
from screens.home_screen import HomeScreen
from screens.prompt_screen import PromptScreen
from kivy.config import Config
import ctypes

class TravelPlannerApp(MDApp):
    def build(self):
        ctypes.windll.user32.SetProcessDPIAware()  # for Windows
        Config.set("graphics", "multisamples", "0")
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Orange"
        Builder.load_file("travel.kv")
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(PromptScreen(name="prompt"))
        return sm


if __name__ == "__main__":
    TravelPlannerApp().run()
