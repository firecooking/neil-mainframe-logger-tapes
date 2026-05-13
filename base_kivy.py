from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ListProperty, StringProperty, BooleanProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.colorpicker import ColorPicker
from kivy.core.window import Window
from kivy.clock import Clock
import json
import datetime
import os

class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior, RecycleBoxLayout):
    pass

class AlterItem(RecycleDataViewBehavior, BoxLayout):
    name = StringProperty()
    birthday = StringProperty()
    pronouns = StringProperty()
    bio = StringProperty()
    selected = BooleanProperty(False)
    index = 0

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        self.name = data.get('name', '')
        self.birthday = data.get('birthday', '')
        self.pronouns = data.get('pronouns', '')
        self.bio = data.get('bio', '')
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.parent.select_with_touch(self.index, touch)
        return super().on_touch_down(touch)

class FrontItem(RecycleDataViewBehavior, BoxLayout):
    alter_name = StringProperty()
    timestamp = StringProperty()
    selected = BooleanProperty(False)
    index = 0

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        self.alter_name = data.get('alter_name', '')
        self.timestamp = data.get('timestamp', '')
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.parent.select_with_touch(self.index, touch)
        return super().on_touch_down(touch)

class MainWidget(BoxLayout):
    alters_data = ListProperty()
    front_data = ListProperty()
    bg_color = ListProperty([0.8, 0.8, 0.8, 1])
    fg_color = ListProperty([0, 0, 0, 1])
    entry_bg_color = ListProperty([1, 1, 1, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Use Clock to ensure App.get_running_app() is available
        Clock.schedule_once(self.delayed_init)

    def delayed_init(self, dt):
        self.load_settings()
        self.load_entries_auto()

    def get_settings_file(self):
        app = App.get_running_app()
        if app:
            return os.path.join(app.user_data_dir, "settings.json")
        return "settings.json"

    def get_data_file(self):
        app = App.get_running_app()
        if app:
            return os.path.join(app.user_data_dir, "data.json")
        return "data.json"

    def load_settings(self):
        settings_file = self.get_settings_file()
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                bg_hex = settings.get("bg_color", "#CACACA")
                fg_hex = settings.get("fg_color", "#000000")
                entry_hex = settings.get("entry_bg_color", "#ffffff")
                self.bg_color = self.hex_to_rgba(bg_hex)
                self.fg_color = self.hex_to_rgba(fg_hex)
                self.entry_bg_color = self.hex_to_rgba(entry_hex)
            except Exception as e:
                print(f"Failed to load settings: {e}")

    def hex_to_rgba(self, hex_color):
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            return [int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4)] + [1]
        return [0.8, 0.8, 0.8, 1]

    def save_settings(self):
        settings_file = self.get_settings_file()
        settings = {
            "bg_color": self.rgba_to_hex(self.bg_color),
            "fg_color": self.rgba_to_hex(self.fg_color),
            "entry_bg_color": self.rgba_to_hex(self.entry_bg_color)
        }
        try:
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def rgba_to_hex(self, rgba):
        return '#{:02x}{:02x}{:02x}'.format(int(rgba[0]*255), int(rgba[1]*255), int(rgba[2]*255))

    def load_entries_auto(self):
        data_file = self.get_data_file()
        if os.path.exists(data_file):
            try:
                with open(data_file, "r", encoding="utf-8") as file:
                    data = json.load(file)
                alters = data.get("alters", [])
                front = data.get("front", [])
                self.alters_data = [{'name': a.get('Name', ''), 'birthday': a.get('Birthday', ''),
                                     'pronouns': a.get('Pronouns', ''), 'bio': a.get('Bio', '')} for a in alters]
                self.front_data = [{'alter_name': f.get('Alter Name', ''), 'timestamp': f.get('Timestamp', '')} for f in front]
            except Exception as e:
                print(f"Failed to load data: {e}")

    def save_entries_auto(self):
        data_file = self.get_data_file()
        data = {
            "alters": [{'Name': d.get('name', ''), 'Birthday': d.get('birthday', ''),
                        'Pronouns': d.get('pronouns', ''), 'Bio': d.get('bio', '')} for d in self.alters_data],
            "front": [{'Alter Name': d.get('alter_name', ''), 'Timestamp': d.get('timestamp', '')} for d in self.front_data]
        }
        try:
            os.makedirs(os.path.dirname(data_file), exist_ok=True)
            with open(data_file, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save data: {e}")

    def add_entry(self):
        name = self.ids.name_input.text.strip()
        if name:
            self.alters_data.append({
                'name': name, 'birthday': self.ids.birthday_input.text,
                'pronouns': self.ids.pronouns_input.text, 'bio': self.ids.bio_input.text
            })
            self.clear_inputs()
            self.save_entries_auto()
        else:
            Popup(title='Error', content=Label(text='Name is required'), size_hint=(0.5, 0.5)).open()

    def clear_inputs(self):
        self.ids.name_input.text = self.ids.birthday_input.text = ''
        self.ids.pronouns_input.text = self.ids.bio_input.text = ''

    def get_selected_index(self, rv_id):
        rv = self.ids.get(rv_id)
        if rv and rv.layout_manager:
            selected = rv.layout_manager.selected_nodes
            return selected[0] if selected else None
        return None

    def remove_entry(self):
        index = self.get_selected_index('alters_rv')
        if index is not None:
            del self.alters_data[index]
            self.save_entries_auto()
        else:
            Popup(title='Warning', content=Label(text='No entry selected'), size_hint=(0.5, 0.5)).open()

    def load_selected(self):
        index = self.get_selected_index('alters_rv')
        if index is not None:
            alter = self.alters_data[index]
            self.ids.name_input.text = alter['name']
            self.ids.birthday_input.text = alter['birthday']
            self.ids.pronouns_input.text = alter['pronouns']
            self.ids.bio_input.text = alter['bio']
            self.editing_index = index
        else:
            Popup(title='Warning', content=Label(text='No alter selected'), size_hint=(0.5, 0.5)).open()

    def update_entry(self):
        if hasattr(self, 'editing_index'):
            name = self.ids.name_input.text.strip()
            if name:
                self.alters_data[self.editing_index] = {
                    'name': name, 'birthday': self.ids.birthday_input.text,
                    'pronouns': self.ids.pronouns_input.text, 'bio': self.ids.bio_input.text
                }
                self.clear_inputs()
                delattr(self, 'editing_index')
                self.save_entries_auto()
            else:
                Popup(title='Error', content=Label(text='Name is required'), size_hint=(0.5, 0.5)).open()
        else:
            Popup(title='Warning', content=Label(text='No alter loaded for editing'), size_hint=(0.5, 0.5)).open()

    def add_to_front(self):
        index = self.get_selected_index('alters_rv')
        if index is not None:
            name = self.alters_data[index].get('name', '')
            self.front_data.append({'alter_name': name, 'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
            self.save_entries_auto()
        else:
            Popup(title='Warning', content=Label(text='No alter selected'), size_hint=(0.5, 0.5)).open()

    def remove_from_front(self):
        index = self.get_selected_index('front_rv')
        if index is not None:
            del self.front_data[index]
            self.save_entries_auto()
        else:
            Popup(title='Warning', content=Label(text='No front entry selected'), size_hint=(0.5, 0.5)).open()

    def save_entries(self):
        self.save_entries_auto()
        Popup(title='Saved', content=Label(text=f'Saved to {self.get_data_file()}'), size_hint=(0.5, 0.5)).open()

    def load_entries(self):
        self.load_entries_auto()
        Popup(title='Loaded', content=Label(text='Data reloaded from file'), size_hint=(0.5, 0.5)).open()

    def choose_colors(self):
        content = BoxLayout(orientation='vertical')
        cp = ColorPicker()
        content.add_widget(cp)
        btns = BoxLayout(size_hint_y=0.2)
        b_bg = Button(text='Set BG'); b_fg = Button(text='Set Text'); b_en = Button(text='Set Entry'); b_cl = Button(text='Close')
        b_bg.bind(on_press=lambda x: [setattr(self, 'bg_color', cp.color), self.save_settings()])
        b_fg.bind(on_press=lambda x: [setattr(self, 'fg_color', cp.color), self.save_settings()])
        b_en.bind(on_press=lambda x: [setattr(self, 'entry_bg_color', cp.color), self.save_settings()])
        b_cl.bind(on_press=lambda x: p.dismiss())
        for b in [b_bg, b_fg, b_en, b_cl]: btns.add_widget(b)
        content.add_widget(btns)
        p = Popup(title='Colors', content=content, size_hint=(0.9, 0.9)); p.open()

    def reset_colors(self):
        self.bg_color = [0.8, 0.8, 0.8, 1]; self.fg_color = [0, 0, 0, 1]; self.entry_bg_color = [1, 1, 1, 1]
        self.save_settings()

    def show_about(self):
        Popup(title='About', content=Label(text='System Log by firecooking\nko-fi.com/firecooking'), size_hint=(0.6, 0.4)).open()

class SystemLoggerApp(App):
    def build(self):
        Window.softinput_mode = 'below_target'
        Window.bind(on_keyboard=self.on_key)
        self.title = "System Logger - by firecooking"
        return Builder.load_file(os.path.join(os.path.dirname(__file__), 'base_kivy.kv'))

    def on_key(self, window, key, *args):
        if key == 27: # Back button
            return True
        return False

if __name__ == "__main__":
    SystemLoggerApp().run()
