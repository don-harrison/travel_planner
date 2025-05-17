from kivy.uix.screenmanager import Screen
from kivy_garden.mapview import MapView  # You need to install this
from kivy.properties import ListProperty
from utils.storage import load_data, save_data
from kivymd.uix.label import MDLabel

class MapScreen(Screen):
    waypoints = ListProperty([])

    def on_enter(self):
        self.load_map()

    def load_map(self):
        data = load_data()
        self.steps = data["plans"][self.destination]["steps"]
        
        
        if not self.waypoints:
            self.ids.route_label.text = "No waypoints provided."
            return

        self.ids.route_label.text = f"Trip from {self.waypoints[0]} to {self.waypoints[-1]}"
        url = self.generate_google_maps_url(self.waypoints)
        self.ids.webview.url = url

    def generate_google_maps_url(self, waypoints):
        # Build a Google Maps directions URL
        base_url = "https://www.google.com/maps/dir/"
        route_path = "/".join(waypoints)
        return base_url + route_path.replace(" ", "+")
    
    def set_destination(self, destination):
        self.destination = destination