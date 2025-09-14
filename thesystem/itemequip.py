from pathlib import Path
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage
import ujson
import csv
import subprocess
import threading
import cv2
from PIL import Image, ImageTk
import sys
import os
import sys
from thesystem.misc import resource_path

current_dir = os.path.dirname(os.path.abspath(__file__))

project_root = os.path.abspath(os.path.join(current_dir, '../../'))

sys.path.insert(0, project_root)

import thesystem.system

OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / "assets/frame0"
EQUIPMENT_TEMP_FILE = 'Files/Temp Files/Equipment Temp.csv'
INVENTORY_FILE = 'Files/Player Data/Inventory.json'
EQUIPMENT_FILE = 'Files/Player Data/Equipment.json'
STATUS_FILE = 'Files/Player Data/Status.json'
PRESETS_FILE = "Files/Mod/presets.json"

# Utility Functions
def relative_to_assets(path: str) -> Path:
    """Returns the relative path to assets."""
    return ASSETS_PATH / path

def load_ujson(file_path):
    """Loads ujson data from a file."""
    try:
        with open(file_path, 'r') as file:
            return ujson.load(file)
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return {}

def save_ujson(file_path, data):
    """Saves ujson data to a file."""
    try:
        with open(file_path, 'w') as file:
            ujson.dump(data, file, indent=6)
    except Exception as e:
        print(f"Error saving to {file_path}: {e}")

def resolve_buff_name(buff_key):
    """Maps buff/debuff keys to corresponding attribute names."""
    buff_map = {
        "AGIbuff": "AGI", "STRbuff": "STR", "VITbuff": "VIT",
        "INTbuff": "INT", "PERbuff": "PER", "MANbuff": "MAN",
        "AGIdebuff": "AGI", "STRdebuff": "STR", "VITdebuff": "VIT",
        "INTdebuff": "INT", "PERdebuff": "PER", "MANdebuff": "MAN",
    }
    return buff_map.get(buff_key)

def process_item_buffs(item_data, status_data, sign=1):
    """Applies or removes buffs/debuffs to/from the status data."""
    for buff_type in ("buff", "debuff"):
        items = item_data.get(buff_type, {})
        if not isinstance(items, dict):
            # Handle or log error: perhaps skip or try to parse the string into a dict
            continue
        for key, value in items.items():
            attribute = resolve_buff_name(key)
            if attribute:
                status_data["equipment"][0][attribute] += sign * value


# Command to open and handle equipment selection
def handle_selection(val, name, cat, window, dat1, dat2, dat3, dat4, dat5):
    equipment_data = load_ujson(EQUIPMENT_FILE)
    status_data = load_ujson(STATUS_FILE)

    if equipment_data.get(cat):
        current_item = list(equipment_data[cat].keys())[0]
        process_item_buffs(equipment_data[cat][current_item][0], status_data, sign=-1)

    if name != '-':
        new_item_data = {1: dat1, 2: dat2, 3: dat3, 4: dat4, 5: dat5}.get(val)
        if new_item_data is not None:
            equipment_data[cat] = new_item_data
            save_ujson(EQUIPMENT_FILE, equipment_data)

            new_item_name = list(new_item_data.keys())[0]
            process_item_buffs(new_item_data[new_item_name][0], status_data, sign=1)

    save_ujson(STATUS_FILE, status_data)
    subprocess.Popen([sys.executable, resource_path('Anime Version/Equipment/gui.py')])
    window.quit()

    
def equip_item(cat, item_full_data, window):
    # --- Handle Rune Stones and The Orb of Order (No changes here) ---
    if cat.upper() == "RUNE STONE":
        # ... (keep the existing Rune Stone logic)
        rune_name = list(item_full_data.keys())[0]
        skill_list_data = load_ujson("Files/Data/Skill_List.json")
        player_skill_data = load_ujson("Files/Player Data/Skill.json")

        if rune_name in player_skill_data:
            current_lvl = player_skill_data[rune_name][0].get("lvl", 1)
            if str(current_lvl).upper() != "MAX":
                new_lvl = int(current_lvl) + 1
                player_skill_data[rune_name][0]["lvl"] = "MAX" if new_lvl >= 10 else new_lvl
        elif rune_name in skill_list_data:
            import copy
            skill_entry = copy.deepcopy(skill_list_data[rune_name])
            skill_entry[0]["lvl"] = 1
            skill_entry[0]["pl_point"] = 0
            player_skill_data[rune_name] = skill_entry

        save_ujson("Files/Player Data/Skill.json", player_skill_data)
        thesystem.inventory.remove_item(rune_name, 1)

    elif cat.upper() == "ORDER":
        # ... (keep the existing Order logic)
        thesystem.inventory.remove_item("The Orb of Order", 1)
        subprocess.Popen([sys.executable, resource_path("First/The Order/gui.py")])
        window.quit()
        return

    # --- Handle All Standard Equipment (UPDATED LOGIC) ---
    else:
        equipment_data = load_ujson(EQUIPMENT_FILE)
        status_data = load_ujson(STATUS_FILE)
        
        # NEW: Determine the correct equipment slot
        equip_slot = cat
        if cat == "WEAPON":
            if not equipment_data.get("WEAPON 1"): # If WEAPON 1 is empty, use it
                equip_slot = "WEAPON 1"
            elif not equipment_data.get("WEAPON 2"): # Else if WEAPON 2 is empty, use it
                equip_slot = "WEAPON 2"
            else: # If both are full, default to replacing WEAPON 1
                equip_slot = "WEAPON 1"
        
        # Step 1: Unequip the old item from the determined slot
        if equip_slot in equipment_data and equipment_data[equip_slot]:
            old_item_name = list(equipment_data[equip_slot].keys())[0]
            old_item_details = equipment_data[equip_slot][old_item_name][0]
            print(f"Unequipping {old_item_name} from {equip_slot}...")
            process_item_buffs(old_item_details, status_data, sign=-1)

        # Step 2: Equip the new item into the determined slot
        new_item_name = list(item_full_data.keys())[0]
        new_item_details = item_full_data[new_item_name][0]
        print(f"Equipping {new_item_name} into {equip_slot}...")
        
        equipment_data[equip_slot] = item_full_data
        process_item_buffs(new_item_details, status_data, sign=1)
        
        thesystem.inventory.remove_item(new_item_name, 1)

        # Step 3: Save all changes
        save_ujson(EQUIPMENT_FILE, equipment_data)
        save_ujson(STATUS_FILE, status_data)

    # --- Step 4: Close current window and open the next one (No changes here) ---
    theme_data = load_ujson('Files/Player Data/Theme_Check.json')
    tab_son_data = load_ujson("Files/Player Data/Tabs.json")
    theme = theme_data.get("Theme", "default")

    if tab_son_data.get("Inventory") == 'Close':
        subprocess.Popen([sys.executable, resource_path(f'{theme} Version/Equipment/gui.py')])
    else:
         subprocess.Popen([sys.executable, resource_path(f'{theme} Version/Inventory/gui.py')])
    
    window.quit()