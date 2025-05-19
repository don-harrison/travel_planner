from kivymd.uix.screen import MDScreen
from kivy_garden.mapview import MapMarkerPopup, MapView
from kivy.properties import StringProperty
from kivy.clock import Clock
from geopy.geocoders import Nominatim
from kivymd.uix.menu import MDDropdownMenu
import openrouteservice
from kivy_garden.mapview import MapLayer
from kivy.graphics import Color, Line
import os
from dotenv import load_dotenv
from kivy.logger import Logger
import math
from utils.storage import load_data, save_data

load_dotenv()
NAV_API_KEY = os.getenv("NAV_API_KEY")

class RouteLineLayer(MapLayer):
    def __init__(self, points, **kwargs):
        super().__init__(**kwargs)
        self.points = points
        self._redraw_scheduled = False
        self._last_zoom = None
        self._cached_screen_points = []

    def update_points(self, new_points):
        self.points = new_points
        self.redraw()

    def redraw(self, *args):
        mapview = self.parent
        if not mapview or not hasattr(mapview, 'get_window_xy_from'):
            return

        zoom = mapview.zoom
        if zoom == self._last_zoom and self._cached_screen_points:
            self._draw_cached()
            return

        self.canvas.clear()
        screen_points = []
        try:
            for lat, lon in self.points:
                x, y = mapview.get_window_xy_from(lat, lon, zoom)
                screen_points.extend([x, y])
        except Exception as e:
            Logger.debug(f"Map: Error mapping points: {e}")
            return

        if len(screen_points) >= 4:
            self._cached_screen_points = screen_points
            self._last_zoom = zoom
            self._draw_cached()

    def _draw_cached(self):
        with self.canvas:
            Color(0, 0.6, 1, 0.9)
            Line(points=self._cached_screen_points, width=3)

    def reposition(self):
        if not self._redraw_scheduled:
            self._redraw_scheduled = True
            Clock.schedule_once(self._delayed_redraw, 0.1)

    def _delayed_redraw(self, dt):
        self._redraw_scheduled = False
        self.redraw()

class FerryLineLayer(MapLayer):
    def __init__(self, ferry_segments, **kwargs):
        super().__init__(**kwargs)
        self.ferry_segments = ferry_segments

    def redraw(self, *args):
        mapview = self.parent
        if not mapview or not hasattr(mapview, 'get_window_xy_from'):
            return

        self.canvas.clear()
        with self.canvas:
            Color(0.8, 0.2, 0.2, 0.6)
            for segment in self.ferry_segments:
                try:
                    x1, y1 = mapview.get_window_xy_from(segment[0][0], segment[0][1], mapview.zoom)
                    x2, y2 = mapview.get_window_xy_from(segment[1][0], segment[1][1], mapview.zoom)
                    Line(points=[x1, y1, x2, y2], width=2, dash_offset=2, dash_length=10)
                except Exception as e:
                    Logger.debug(f"FerryLine: Error mapping ferry segment: {e}")

    def reposition(self):
        self.redraw()

class Map(MDScreen):
    selected_day = StringProperty("Day 1")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.geolocator = Nominatim(user_agent="travel_planner_v2")
        self.location_cache = {}
        self.route_line = None
        self.ferry_line = None
        self.menu = None
        self.markers = []


    def on_kv_post(self, instance):
        mapview = self.ids.mapview
        mapview.map_source = "osm"
        mapview.bind(on_touch_up=self._on_map_touch)

    def _on_map_touch(self, mapview, touch):
        if self.route_line:
            Clock.schedule_once(lambda dt: self.route_line.reposition(), 0.1)
        if self.ferry_line:
            Clock.schedule_once(lambda dt: self.ferry_line.reposition(), 0.1)

    def open_day_menu(self):
        if not self.menu:
            items = [{"text": day, "on_release": lambda x=day: self.select_day(x)} for day in self.waypoint_schedule]
            self.menu = MDDropdownMenu(caller=self.ids.day_button, items=items, width_mult=4)
        self.menu.open()

    def select_day(self, day):
        self.selected_day = day
        self.ids.day_button.text = day
        if self.menu:
            self.menu.dismiss()
        self.clear_map()
        Clock.schedule_once(lambda dt: self.load_map_for_day(day), 0.3)

    def on_pre_enter(self):
        Clock.schedule_once(lambda dt: self.load_map_for_day(self.selected_day), 1)

    def clear_map(self):
        mapview = self.ids.mapview
        for layer in [self.route_line, self.ferry_line]:
            if layer:
                try:
                    if hasattr(mapview, 'remove_layer'):
                        mapview.remove_layer(layer)
                    layer.canvas.clear()
                except Exception:
                    pass
        self.route_line = self.ferry_line = None

        for marker in self.markers:
            try:
                mapview.remove_widget(marker)
            except Exception:
                pass
        self.markers.clear()
        mapview.canvas.ask_update()

    def load_map_for_day(self, day):
        mapview = self.ids.mapview
        self.clear_map()
        waypoints = self.waypoint_schedule.get(day, [])
        if not waypoints:
            self.ids.route_label.text = "No waypoints available."
            return

        self.ids.route_label.text = f"Route: {waypoints[0]} → {waypoints[-1]}"
        points = []
        valid_waypoints = []

        for place in waypoints:
            location = self.get_or_geocode(place)
            if location:
                latlon = (location.latitude, location.longitude)
                points.append(latlon)
                valid_waypoints.append(place)
                marker = MapMarkerPopup(lat=latlon[0], lon=latlon[1], popup_size=("200dp", "100dp"))
                marker.placeholder = place
                mapview.add_widget(marker)
                self.markers.append(marker)

        if points:
            center_lat = sum(p[0] for p in points) / len(points)
            center_lon = sum(p[1] for p in points) / len(points)
            lats = [p[0] for p in points]
            lons = [p[1] for p in points]

            lat_range = max(lats) - min(lats)
            lon_range = max(lons) - min(lons)
            zoom_level = int(max(8, min(15, 13 - max(lat_range, lon_range) * 10)))
            Clock.schedule_once(lambda dt: mapview.center_on(center_lat, center_lon), 1.0)
            mapview.zoom = zoom_level

        if NAV_API_KEY and len(valid_waypoints) >= 2:
            route_points, ferry_segments = self.get_route_polyline(valid_waypoints)
            if route_points:
                self.route_line = RouteLineLayer(points=route_points)
                Clock.schedule_once(lambda dt: mapview.add_layer(self.route_line), 1.5)
            if ferry_segments:
                self.ferry_line = FerryLineLayer(ferry_segments=ferry_segments)
                Clock.schedule_once(lambda dt: mapview.add_layer(self.ferry_line), 1.6)

    def get_or_geocode(self, place):
        if place in self.location_cache:
            return self.location_cache[place]
        try:
            loc = self.geolocator.geocode(place, timeout=5)
            if loc:
                self.location_cache[place] = loc
            return loc
        except Exception as e:
            Logger.error(f"Geocode failed: {e}")
            return None

    def get_route_polyline(self, waypoints):
        client = openrouteservice.Client(key=NAV_API_KEY)
        coords = []
        for place in waypoints:
            loc = self.get_or_geocode(place)
            if loc:
                coords.append([loc.longitude, loc.latitude])
        if len(coords) < 2:
            return [], []

        try:
            route = client.directions(
                coordinates=coords,
                profile='foot-walking',
                format='geojson',
            )
        except Exception as e:
            Logger.warning(f"Routing failed, fallback: {e}")
            return self._create_simple_route(coords), []

        route_coords = route['features'][0]['geometry']['coordinates']
        route_points = [(coord[1], coord[0]) for coord in route_coords]
        ferry_segments = self._detect_ferry_segments(route_points)
        return route_points, ferry_segments

    def _create_simple_route(self, coords):
        if len(coords) < 2:
            return []
        route_points = []
        for i in range(len(coords) - 1):
            start_lon, start_lat = coords[i]
            end_lon, end_lat = coords[i + 1]
            for j in range(10):
                t = j / 9
                lat = start_lat + t * (end_lat - start_lat)
                lon = start_lon + t * (end_lon - start_lon)
                route_points.append((lat, lon))
        return route_points

    def _detect_ferry_segments(self, route_points, threshold_km=1.0):
        """Detect straight long segments that may indicate ferry crossings"""
        ferry_segments = []
        for i in range(len(route_points) - 1):
            lat1, lon1 = route_points[i]
            lat2, lon2 = route_points[i + 1]
            distance = self._haversine(lat1, lon1, lat2, lon2)
            if distance > threshold_km:
                ferry_segments.append(((lat1, lon1), (lat2, lon2)))
        return ferry_segments

    def _haversine(self, lat1, lon1, lat2, lon2):
        R = 6371  # Earth radius in km
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    
    def set_destination(self, destination):
        """Set the destination for the map"""
        self.destination = destination
        data = load_data()
        self.waypoint_schedule = data["plans"][self.destination]["daily_waypoints"]