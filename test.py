import kivy

kivy.require('1.9.1')

from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder

Builder.load_string('''
<PaintWindow>:
    orientation: 'vertical'

<CPopup>:
    title: 'Pick a Color'
    size_hint: 1.0, 0.9
    id: cpopup

    BoxLayout:
        orientation: 'vertical'

        ColorPicker:
            size_hint: 1.0, 1.0

        Button:
            text: 'OK'
            size_hint: 1.0, 0.2
            on_press: root.dismiss()
''')


class PaintWindow(BoxLayout):
    pass


class CPopup(Popup):
    def on_press_dismiss(self, *args):
        self.dismiss()
        return False


class PixPaint(App):
    def build(self):
        pw = PaintWindow()
        popup = CPopup()
        popup.open()
        return pw


if __name__ == '__main__':
    PixPaint().run()
