from kivy.config import Config

# Simulating a standard Android phone (Pixel 5 style)
# 412x915 is a common logical resolution
# We set this BEFORE any other kivy imports to ensure it takes effect
Config.set('graphics', 'width', '412')
Config.set('graphics', 'height', '915')
Config.set('graphics', 'resizable', '0')

from base_kivy import SystemLoggerApp
from kivy.core.window import Window

if __name__ == "__main__":
    # Ensure the window is placed nicely on your monitor
    Window.top = 100
    Window.left = 100
    
    # Run your app
    SystemLoggerApp().run()