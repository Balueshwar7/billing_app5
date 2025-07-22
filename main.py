import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton

from printer import print_bill
from db import save_bill_to_db, get_menu_items, add_menu_item_to_db  # ✅ From DB

KV = '''
<MainScreen>:
    orientation: 'vertical'

    ScrollView:
        size_hint_y: 0.35
        GridLayout:
            id: menu_grid
            cols: 2
            size_hint_y: None
            height: self.minimum_height

    Label:
        id: bill_area
        text: "No items selected."
        font_size: 18
        size_hint_y: 0.25
        text_size: self.width, None
        halign: 'left'
        valign: 'top'

    BoxLayout:
        size_hint_y: 0.1
        spacing: 10

        Button:
            text: "Delete Selected Item"
            on_press: root.delete_selected_menu_item()

        Button:
            text: "Delete Last Item"
            on_press: root.delete_last_item()

        Button:
            text: "Clear Bill"
            on_press: root.clear_bill()

    BoxLayout:
        size_hint_y: 0.15
        spacing: 10

        TextInput:
            id: new_item_name
            hint_text: "New item name"
            multiline: False

        TextInput:
            id: new_item_price
            hint_text: "Price"
            multiline: False
            input_filter: "float"

        Button:
            text: "Add New Item"
            size_hint_x: 0.3
            on_press: root.add_new_menu_item()

    Button:
        text: "Print & Save Bill"
        size_hint_y: 0.15
        font_size: 24
        on_press: root.print_and_save()
'''

class MainScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bill_items = []
        self.menu = get_menu_items()  # ✅ Load menu from DB
        self.selected_toggle = None
        self.selected_item = None
        self.build_menu()

    def build_menu(self):
        self.ids.menu_grid.clear_widgets()
        self.selected_toggle = None
        self.selected_item = None
        for item in self.menu:
            toggle = ToggleButton(
                text=f"{item['name']} - ₹{item['price']}",
                group="menu_items",
                size_hint_y=None,
                height=60,
                allow_no_selection=True,
            )
            toggle.bind(on_press=lambda btn, i=item: self.on_toggle_select(btn, i))
            toggle.bind(on_release=lambda btn, i=item: self.add_item(i) if btn.state == 'down' else None)
            self.ids.menu_grid.add_widget(toggle)

    def on_toggle_select(self, toggle_btn, item):
        if toggle_btn.state == 'down':
            self.selected_toggle = toggle_btn
            self.selected_item = item
        else:
            self.selected_toggle = None
            self.selected_item = None

    def delete_selected_menu_item(self):
        if not self.selected_item:
            self.show_popup("No menu item selected to delete!")
            return
        name = self.selected_item['name']
        self.menu.remove(self.selected_item)
        self.build_menu()
        self.show_popup(f"Deleted menu item: {name}")
        self.selected_toggle = None
        self.selected_item = None

    def add_item(self, item):
        self.bill_items.append({"name": item["name"], "qty": 1, "price": item["price"]})
        self.update_bill_area()

    def delete_last_item(self):
        if self.bill_items:
            self.bill_items.pop()
            self.update_bill_area()
        else:
            self.show_popup("No items to delete!")

    def clear_bill(self):
        self.bill_items = []
        self.update_bill_area()

    def update_bill_area(self):
        if not self.bill_items:
            self.ids.bill_area.text = "No items selected."
            return

        text = ""
        for item in self.bill_items:
            text += f"{item['name']} - ₹{item['price']}\n"
        self.ids.bill_area.text = text

    def print_and_save(self):
        if not self.bill_items:
            self.ids.bill_area.text = "No items selected!\n"
            return

        total = sum(i["price"] * i["qty"] for i in self.bill_items)
        bill_text = "Food Truck Bill\n\n"
        for item in self.bill_items:
            bill_text += f"{item['name']} x{item['qty']} = ₹{item['qty'] * item['price']}\n"
        bill_text += f"\nTotal = ₹{total}\n\nThank you!\n"

        print_bill(bill_text)
        save_bill_to_db(self.bill_items, total)  # ✅ Save to MySQL
        self.ids.bill_area.text = "✅ Bill Printed & Saved (MySQL)!\n"
        self.bill_items = []

    def add_new_menu_item(self):
        name = self.ids.new_item_name.text.strip()
        price_text = self.ids.new_item_price.text.strip()

        if not name or not price_text:
            self.show_popup("Please enter both name and price.")
            return

        try:
            price = float(price_text)
        except ValueError:
            self.show_popup("Price must be a number.")
            return

        # Add to DB and refresh UI
        add_menu_item_to_db(name, price)        # ✅ Save to DB
        self.menu = get_menu_items()            # ✅ Reload from DB
        self.build_menu()                       # ✅ Refresh UI
        self.ids.new_item_name.text = ""
        self.ids.new_item_price.text = ""

    def show_popup(self, message):
        popup = Popup(title='Info',
                      content=Label(text=message),
                      size_hint=(None, None), size=(300, 200))
        popup.open()

class FoodTruckApp(App):
    def build(self):
        Builder.load_string(KV)
        return MainScreen()

if __name__ == "__main__":
    FoodTruckApp().run()
