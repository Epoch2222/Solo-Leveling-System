from pathlib import Path
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage
from tkinter import Button, PhotoImage, Toplevel, Canvas, Label
from thesystem.misc import resource_path # Use the existing resource_path function for robustness
from PIL import Image, ImageTk
import ujson
import subprocess
import threading
import thesystem.system
import csv
import os
import sys
from thesystem.misc import resource_path


INVENTORY_FILE = 'Files/Player Data/Inventory.json'

def remove_item(item_name: str, quantity: int):
    """Removes a specified quantity of an item from the inventory."""
    if not os.path.exists(INVENTORY_FILE):
        print(f"Error: Inventory file not found at {INVENTORY_FILE}")
        return

    with open(INVENTORY_FILE, 'r') as file:
        inventory_data = ujson.load(file)

    if item_name in inventory_data:
        # Decrease quantity
        inventory_data[item_name][0]['qty'] -= quantity
        
        # If quantity is zero or less, remove the item completely
        if inventory_data[item_name][0]['qty'] <= 0:
            del inventory_data[item_name]
            print(f"Removed all stacks of {item_name} from inventory.")
        else:
            print(f"Removed {quantity} of {item_name}. Remaining: {inventory_data[item_name][0]['qty']}.")

    else:
        print(f"Error: Tried to remove {item_name}, but it was not found in inventory.")

    with open(INVENTORY_FILE, 'w') as file:
        ujson.dump(inventory_data, file, indent=6)

def inventory_name_cut(name: str, max_len=20) -> str:
    """Truncates a string to a specified length, adding '...' if truncated."""
    if len(name) > max_len:
        return name[:max_len-3] + "..."
    return name
# In file: thesystem/inventory.py

# --- MODIFIED: FUNCTION TO GET AND RESIZE IMAGES ---
def get_item_button_image(item_name: str, max_width: int, max_height: int) -> PhotoImage:
    """
    Finds an image for an item, resizes it to fit the given dimensions,
    and falls back to a default image to prevent crashes.
    """
    safe_filename = "".join(c for c in item_name if c.isalnum() or c in (' ', '_')).rstrip()
    image_path = resource_path(os.path.join('Files', 'Mod', 'default', 'icons', f'{safe_filename}.png'))

    if not os.path.exists(image_path):
        image_path = resource_path(os.path.join('Files', 'Mod', 'default', 'icons', 'default_item.png'))

    if not os.path.exists(image_path):
        print(f"!!! WARNING: Default inventory image not found at {image_path}. Please create 'default_item.png'.")
        return None
    
    # Open image with PIL and resize it while maintaining aspect ratio
    with Image.open(image_path) as img:
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)


# --- NEW: FUNCTION TO OPEN THE ITEM DETAILS GUI ---
def open_item_details(item_data: dict, main_window):
    """
    Writes the item data to a temporary file and launches the detailed item GUI.
    """
    temp_file_path = resource_path('Files/Temp Files/Inventory temp.csv')
    item_details_script_path = resource_path('Anime Version/Item Data/gui.py')

    # Write the clicked item's data to the temp file for the other script to read
    with open(temp_file_path, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        # Format: [Item Name, Quantity, Type]
        writer.writerow([
            item_data.get('name', 'Unknown'),
            item_data.get('qty', 1),
            'Item' # Specify that this is a player-owned item
        ])
    
    # Launch the item details GUI script
    subprocess.Popen([sys.executable, item_details_script_path])
    
    # Close the current inventory window
    main_window.destroy()



def show_item_details_popup(item_data: dict, window):
    """Creates a Toplevel window to display detailed item information."""
    popup = Toplevel(window)
    popup.overrideredirect(True)
    popup.attributes("-topmost", True)
    popup.configure(bg="#1E1E1E")
    
    # Position the popup nicely next to the main window
    x = window.winfo_x() + window.winfo_width()
    y = window.winfo_y() + 100
    popup.geometry(f"250x200+{x}+{y}")
    
    # Display item data
    Label(popup, text=item_data.get('name', ''), bg="#1E1E1E", fg="#50ABFF", font=("Montserrat Bold", 14)).pack(pady=5)
    Label(popup, text=f"Category: {item_data.get('cat', '')}", bg="#1E1E1E", fg="white", font=("Montserrat Medium", 10)).pack(pady=2, anchor='w', padx=10)
    Label(popup, text=f"Rank: {item_data.get('rank', '')}", bg="#1E1E1E", fg="white", font=("Montserrat Medium", 10)).pack(pady=2, anchor='w', padx=10)
    Label(popup, text=f"Quantity: {item_data.get('qty', '')}", bg="#1E1E1E", fg="white", font=("Montserrat Medium", 10)).pack(pady=2, anchor='w', padx=10)
    Label(popup, text=f"Buff: {item_data.get('buff', 'None')}", bg="#1E1E1E", fg="lightgreen", font=("Montserrat Regular", 9)).pack(pady=2, anchor='w', padx=10)
    Label(popup, text=f"Debuff: {item_data.get('debuff', 'None')}", bg="#1E1E1E", fg="coral", font=("Montserrat Regular", 9)).pack(pady=2, anchor='w', padx=10)
    Label(popup, text=item_data.get('desc', ''), bg="#1E1E1E", fg="white", font=("Montserrat Regular", 9), wraplength=230, justify='left').pack(pady=5, padx=10)

    Button(popup, text="Close", command=popup.destroy, bg="#444444", fg="white").pack(pady=10)

# --- CORE FUNCTION (ENHANCED) ---

# --- MODIFIED: CORE ITEM CREATION FUNCTION ---
def create_inventory_item(canvas, window, item_data, x, y, button_images_ref, item_images_ref, bg_image_path):
    """
    Creates the visual elements for an inventory item. The button command now
    launches your detailed GUI instead of the simple popup.
    """
    name = item_data.get("name", "Unknown Item")
    qty = item_data.get("qty", 1)
    category = item_data.get("cat", "Misc")
    
    bg_photo = PhotoImage(file=bg_image_path)
    button_images_ref.append(bg_photo) 
    bg_widget = canvas.create_image(x + 35, y + 35, image=bg_photo)
    
    # Get the correctly sized 70x70 icon for the main inventory grid
    item_photo = get_item_button_image(name, 70, 70)
    if item_photo:
        item_images_ref.append(item_photo)
    
    item_button = Button(
        window,
        image=item_photo,
        borderwidth=0,
        highlightthickness=0,
        # This command now calls the function to open your detailed GUI
        command=lambda d=item_data: open_item_details(d, window),
        relief="flat",
        bg="#2E2E2E",
        activebackground="#4F4F4F"
    )
    
    qty_text = canvas.create_text(
        x + 65, y + 65, text=f"x{qty}", fill="#FFFFFF",
        font=("Montserrat Bold", 10 * -1), anchor="se"
    )

    return {
        "widgets": {
            "background": bg_widget,
            "button": item_button,
            "qty_text": qty_text
        },
        "category": category.strip().capitalize()
    }



def ex_close(win):
    with open("Files/Player Data/Tabs.json",'r') as tab_son:
        tab_son_data=ujson.load(tab_son)

    with open("Files/Player Data/Tabs.json",'w') as fin_tab_son:
        tab_son_data["Inventory"]='Close'
        ujson.dump(tab_son_data,fin_tab_son,indent=4)
    subprocess.Popen([sys.executable, resource_path('Files/Mod/default/sfx_close.py')])
    thesystem.system.animate_window_close(win, win.winfo_height(), win.winfo_width(), step=40, delay=1)

def inventory_item_data(name,rank,category,t,r,s,window):
    try:
        if name!='-' and rank!='-' and category!='-':
            fout=open('Files/Temp Files/Inventory temp.csv', 'w', newline='')
            fw=csv.writer(fout)
            rec=[name]
            fw.writerow(rec)
            fout.close()

            with open('Files/Player Data/Theme_Check.json', 'r') as themefile:
                theme_data=ujson.load(themefile)
                theme=theme_data["Theme"]
            subprocess.Popen([sys.executable, resource_path(f'{theme} Version/Item Data/gui.py')])
    
    except:
        print()

def selling_item(name,window,val):
    with open("Files/Player Data/Status.json", 'r') as read_status_file:
        read_status_file_data=ujson.load(read_status_file)

    with open("Files/Player Data/Inventory.json", 'r') as fin_inv_fson:
        fin_inv_data=ujson.load(fin_inv_fson)

        fin_qt=fin_inv_data[name][0]["qty"]
        fin_inv_data[name][0]["qty"]=fin_qt-1
        closing=False   
        if fin_inv_data[name][0]["qty"]==0:
            del fin_inv_data[name]
            closing=True

    
    
    with open("Files/Player Data/Skill.json", 'r') as f:
        skill_data = ujson.load(f)

    addition = 0
    if thesystem.system.skill_use("Negotiation", (0), False) and ("Negotiation" in skill_data):
        lvl = skill_data["Negotiation"][0]["lvl"]
        if isinstance(lvl, str):
            lvl = 10

        percentile = 0.015 * lvl
        addition = abs(val) * percentile


    with open("Files/Player Data/Inventory.json", 'w') as finaladdon_inv:
        ujson.dump(fin_inv_data, finaladdon_inv, indent=6)

    with open("Files/Player Data/Status.json", 'w') as write_status_file:
        read_status_file_data["status"][0]['coins']+=int(val+addition)
        ujson.dump(read_status_file_data, write_status_file, indent=4)

    with open('Files/Player Data/Theme_Check.json', 'r') as themefile:
        theme_data=ujson.load(themefile)
        theme=theme_data["Theme"]

    if closing==True:
        subprocess.Popen([sys.executable, resource_path(f'{theme} Version/Inventory/gui.py')])

        window.quit()

    else:
        subprocess.Popen([sys.executable, resource_path(f'{theme} Version/Item Data/gui.py')])

        window.quit()
