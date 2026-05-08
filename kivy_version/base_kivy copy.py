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
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.colorpicker import ColorPicker
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
        self.name = data['name']
        self.birthday = data['birthday']
        self.pronouns = data['pronouns']
        self.bio = data['bio']
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
        self.alter_name = data['alter_name']
        self.timestamp = data['timestamp']
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.parent.select_with_touch(self.index, touch)
        return super().on_touch_down(touch)

class MainWidget(BoxLayout):
    alters_data = ListProperty()
    front_data = ListProperty()
    bg_color = ListProperty([0.8, 0.8, 0.8, 1])  # Default gray
    fg_color = ListProperty([0, 0, 0, 1])  # Black
    entry_bg_color = ListProperty([1, 1, 1, 1])  # White

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.load_settings()
        self.load_entries_auto()

    def get_settings_file(self):
        return os.path.join(os.path.dirname(__file__), "settings.json")

    def get_data_file(self):
        return os.path.join(os.path.dirname(__file__), "data.json")

    def load_settings(self):
        settings_file = self.get_settings_file()
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                # Convert hex to rgba
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
        return [int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4)] + [1]

    def save_settings(self):
        settings_file = self.get_settings_file()
        settings = {
            "bg_color": self.rgba_to_hex(self.bg_color),
            "fg_color": self.rgba_to_hex(self.fg_color),
            "entry_bg_color": self.rgba_to_hex(self.entry_bg_color)
        }
        try:
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def rgba_to_hex(self, rgba):
        return '#{:02x}{:02x}{:02x}'.format(int(rgba[0]*255), int(rgba[1]*255), int(rgba[2]*255))

    def load_entries_auto(self):
        self.alters_data = []
        self.front_data = []
        data_file = self.get_data_file()
        if os.path.exists(data_file):
            try:
                with open(data_file, "r", encoding="utf-8") as file:
                    data = json.load(file)
                alters = data.get("alters", [])
                front = data.get("front", [])
                self.alters_data = [
                    {
                        'name': a.get('Name', ''),
                        'birthday': a.get('Birthday', ''),
                        'pronouns': a.get('Pronouns', ''),
                        'bio': a.get('Bio', ''),
                    }
                    for a in alters
                ]
                self.front_data = [
                    {
                        'alter_name': f.get('Alter Name', ''),
                        'timestamp': f.get('Timestamp', ''),
                    }
                    for f in front
                ]
            except Exception as e:
                print(f"Failed to load data: {e}")

    def save_entries_auto(self):
        data_file = self.get_data_file()
        alters = [
            {
                'Name': d.get('name', ''),
                'Birthday': d.get('birthday', ''),
                'Pronouns': d.get('pronouns', ''),
                'Bio': d.get('bio', ''),
            }
            for d in self.alters_data
        ]
        front = [
            {
                'Alter Name': d.get('alter_name', ''),
                'Timestamp': d.get('timestamp', ''),
            }
            for d in self.front_data
        ]
        data = {"alters": alters, "front": front}
        try:
            with open(data_file, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save data: {e}")

    def add_entry(self):
        name = self.ids.name_input.text
        birthday = self.ids.birthday_input.text
        pronouns = self.ids.pronouns_input.text
        bio = self.ids.bio_input.text
        if name:
            self.alters_data.append({'name': name, 'birthday': birthday, 'pronouns': pronouns, 'bio': bio})
            if hasattr(self, 'editing_index'):
                delattr(self, 'editing_index')
            self.clear_inputs()
            self.save_entries_auto()
            self.ids.alters_rv.refresh_from_data()
        else:
            popup = Popup(title='Error', content=Label(text='Name is required'), size_hint=(0.5, 0.5))
            popup.open()

    def clear_inputs(self):
        self.ids.name_input.text = ''
        self.ids.birthday_input.text = ''
        self.ids.pronouns_input.text = ''
        self.ids.bio_input.text = ''

    def get_selected_index(self, rv_id):
        rv = self.ids.get(rv_id)
        if rv is None:
            return None
        lm = getattr(rv, 'layout_manager', None)
        if lm is None:
            return None
        selected = getattr(lm, 'selected_nodes', [])
        return selected[0] if selected else None

    def clear_selection(self, rv_id):
        rv = self.ids.get(rv_id)
        if rv is None:
            return
        lm = getattr(rv, 'layout_manager', None)
        if lm is None:
            return
        selected = getattr(lm, 'selected_nodes', None)
        if selected is not None:
            selected.clear()

    def remove_entry(self):
        index = self.get_selected_index('alters_rv')
        if index is not None:
            if 0 <= index < len(self.alters_data):
                del self.alters_data[index]
            self.clear_selection('alters_rv')
            if hasattr(self, 'editing_index'):
                delattr(self, 'editing_index')
            self.save_entries_auto()
            self.ids.alters_rv.refresh_from_data()
        else:
            popup = Popup(title='Warning', content=Label(text='No entry selected'), size_hint=(0.5, 0.5))
            popup.open()

    def load_selected(self):
        index = self.get_selected_index('alters_rv')
        if index is not None and 0 <= index < len(self.alters_data):
            alter = self.alters_data[index]
            self.ids.name_input.text = alter.get('name', '')
            self.ids.birthday_input.text = alter.get('birthday', '')
            self.ids.pronouns_input.text = alter.get('pronouns', '')
            self.ids.bio_input.text = alter.get('bio', '')
            self.editing_index = index
        else:
            popup = Popup(title='Warning', content=Label(text='No alter selected'), size_hint=(0.5, 0.5))
            popup.open()

    def update_entry(self):
        if hasattr(self, 'editing_index'):
            name = self.ids.name_input.text
            birthday = self.ids.birthday_input.text
            pronouns = self.ids.pronouns_input.text
            bio = self.ids.bio_input.text
            if name:
                self.alters_data[self.editing_index] = {'name': name, 'birthday': birthday, 'pronouns': pronouns, 'bio': bio}
                self.clear_inputs()
                delattr(self, 'editing_index')
                self.save_entries_auto()
                self.ids.alters_rv.refresh_from_data()
            else:
                popup = Popup(title='Error', content=Label(text='Name is required'), size_hint=(0.5, 0.5))
                popup.open()
        else:
            popup = Popup(title='Warning', content=Label(text='No alter loaded for editing'), size_hint=(0.5, 0.5))
            popup.open()

    def add_to_front(self):
        index = self.get_selected_index('alters_rv')
        if index is not None and 0 <= index < len(self.alters_data):
            alter_name = self.alters_data[index].get('name', '')
            if alter_name:
                timestamp = datetime.datetime.now().isoformat()
                self.front_data.append({'alter_name': alter_name, 'timestamp': timestamp})
                self.save_entries_auto()
                self.ids.front_rv.refresh_from_data()
            else:
                popup = Popup(title='Warning', content=Label(text='Selected alter has no name'), size_hint=(0.5, 0.5))
                popup.open()
        else:
            popup = Popup(title='Warning', content=Label(text='No alter selected'), size_hint=(0.5, 0.5))
            popup.open()

    def remove_from_front(self):
        index = self.get_selected_index('front_rv')
        if index is not None and 0 <= index < len(self.front_data):
            del self.front_data[index]
            self.clear_selection('front_rv')
            self.save_entries_auto()
            self.ids.front_rv.refresh_from_data()
        else:
            popup = Popup(title='Warning', content=Label(text='No front entry selected'), size_hint=(0.5, 0.5))
            popup.open()

    def save_entries(self):
        # Simple save to data.json for now
        self.save_entries_auto()
        popup = Popup(title='Saved', content=Label(text='Entries saved to data.json'), size_hint=(0.5, 0.5))
        popup.open()

    def load_entries(self):
        # For now, just reload from data.json
        self.load_entries_auto()
        self.ids.alters_rv.refresh_from_data()
        self.ids.front_rv.refresh_from_data()
        popup = Popup(title='Loaded', content=Label(text=f'Loaded {len(self.alters_data)} alters and {len(self.front_data)} front entries'), size_hint=(0.5, 0.5))
        popup.open()

    def choose_colors(self):
        # Open color picker popup
        content = BoxLayout(orientation='vertical')
        color_picker = ColorPicker()
        content.add_widget(color_picker)
        buttons = BoxLayout(size_hint_y=0.2)
        btn_bg = Button(text='Set Background')
        btn_fg = Button(text='Set Text')
        btn_entry = Button(text='Set Entry BG')
        btn_reset = Button(text='Reset')
        btn_close = Button(text='Close')
        buttons.add_widget(btn_bg)
        buttons.add_widget(btn_fg)
        buttons.add_widget(btn_entry)
        buttons.add_widget(btn_reset)
        buttons.add_widget(btn_close)
        content.add_widget(buttons)
        
        popup = Popup(title='Choose Colors', content=content, size_hint=(0.8, 0.8))
        
        def set_bg(instance):
            self.bg_color = color_picker.color
            self.save_settings()
        def set_fg(instance):
            self.fg_color = color_picker.color
            self.save_settings()
        def set_entry(instance):
            self.entry_bg_color = color_picker.color
            self.save_settings()
        def reset_colors(instance):
            self.bg_color = [0.8, 0.8, 0.8, 1]
            self.fg_color = [0, 0, 0, 1]
            self.entry_bg_color = [1, 1, 1, 1]
            self.save_settings()
        def close_popup(instance):
            popup.dismiss()
        
        btn_bg.bind(on_press=set_bg)
        btn_fg.bind(on_press=set_fg)
        btn_entry.bind(on_press=set_entry)
        btn_reset.bind(on_press=reset_colors)
        btn_close.bind(on_press=close_popup)
        
        popup.open()

    def reset_colors(self):
        self.bg_color = [0.8, 0.8, 0.8, 1]
        self.fg_color = [0, 0, 0, 1]
        self.entry_bg_color = [1, 1, 1, 1]
        self.save_settings()

    def show_about(self):
        popup = Popup(title='About', content=Label(text='System Log by firecooking\nBuy me a coffee at https://ko-fi.com/firecooking'), size_hint=(0.6, 0.4))
        popup.open()

class SystemLoggerApp(App):
    def build(self):
        self.title = "System Logger - by firecooking"
        kv_path = os.path.join(os.path.dirname(__file__), 'base_kivy.kv')
        return Builder.load_file(kv_path)

if __name__ == "__main__":
    SystemLoggerApp().run()