import tkinter as tk
from tkinter import ttk
import time
import threading
import random
import ujson
from pathlib import Path
import sys
import os
import subprocess
from PIL import Image, ImageTk

# --- (Your existing import paths and helper functions remain the same) ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../'))
sys.path.insert(0, project_root)

import thesystem.system

def load_player_stats():
    try:
        with open("Files/Player Data/Status.json", 'r') as f:
            data = ujson.load(f)
            if "highest_floor" not in data["status"][0]:
                data["status"][0]["highest_floor"] = 0
                save_player_stats(data)
            return data
    except (FileNotFoundError, IndexError):
        default_stats = {
            "status": [
                {"level": 1, "XP": 0, "str": 5, "agi": 5, "vit": 5, "coins": 0, "fatigue": 0, "highest_floor": 0}
            ]
        }
        save_player_stats(default_stats)
        return default_stats

def save_player_stats(data):
    with open("Files/Player Data/Status.json", 'w') as f:
        ujson.dump(data, f, indent=2)

class RaidInterface(tk.Frame):
    def __init__(self, parent, end_raid_callback, transparent_color="#0E0A41"):
        super().__init__(parent)
        self.end_raid_callback = end_raid_callback
        self.parent = parent

        self.assets_path = Path(__file__).parent / "assets" / "raid"
        self.icons_path = self.assets_path / "icons"

        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("Enemy.Horizontal.TProgressbar", foreground='#8B0000', background='#8B0000', troughcolor='#400000', bordercolor="#111", lightcolor="#111", darkcolor="#111")
        style.configure("Player.Horizontal.TProgressbar", foreground='#00FFFF', background='#00FFFF', troughcolor='#004040', bordercolor="#111", lightcolor="#111", darkcolor="#111")
        style.configure("Stagger.Horizontal.TProgressbar", foreground='#FFD700', background='#FFD700', troughcolor='#4A4100', bordercolor="#111", lightcolor="#111", darkcolor="#111")

        self.exercises = {'easy': ['Jumping Jacks', 'Wall Sit', 'Crunches'], 'medium': ['Squats', 'Push-ups', 'Plank'], 'hard': ['Pull-ups', 'Burpees', 'V-Ups']}
        self.bosses = ['an Orc Warlord', 'a Lich King', 'a Fire Drake', 'a Demon Knight']
        self.current_floor = 0
        self.damage_indicator_labels = []

        try:
            bg_image_pil = Image.open(self.assets_path / "background.png")
            self.bg_image = ImageTk.PhotoImage(bg_image_pil)
            self.bg_label = tk.Label(self, image=self.bg_image)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except FileNotFoundError:
            print("Warning: background.png not found. Using solid color.")
            self.configure(bg=transparent_color)

        # ### NEW LAYOUT STRUCTURE ###
        # 1. A sidebar on the right for player info and actions
        self.sidebar_frame = tk.Frame(self)
        self.sidebar_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 20), pady=20)

        # 2. A main content area on the left for the enemy and move cards
        self.main_content_frame = tk.Frame(self)
        self.main_content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20, 10), pady=10)

        # --- Widgets for the Main Content Area (Left) ---
        self.enemy_frame = tk.Frame(self.main_content_frame)
        self.enemy_frame.pack(side=tk.TOP, fill=tk.X, pady=10)
        
        self.title_label = tk.Label(self.enemy_frame, text="", font=("Impact", 30), fg="#8B0000")
        self.title_label.pack()
        self.enemy_health_label = tk.Label(self.enemy_frame, text="", font=("Arial", 12, "bold"), fg="white")
        self.enemy_health_label.pack(pady=(5,0))
        self.enemy_health_bar = ttk.Progressbar(self.enemy_frame, style="Enemy.Horizontal.TProgressbar", orient="horizontal", length=400, mode="determinate")
        self.enemy_health_bar.pack()
        self.stagger_bar = ttk.Progressbar(self.enemy_frame, style="Stagger.Horizontal.TProgressbar", orient="horizontal", length=300, mode="determinate")
        self.stagger_bar.pack(pady=5)

        # The moves_frame will now live in the main content area and be centered
        self.moves_frame_container = tk.Frame(self.main_content_frame)
        self.moves_frame_container.pack(fill=tk.BOTH, expand=True)
        self.moves_frame = tk.Frame(self.moves_frame_container) # The actual frame for cards
        self.move_cards = []
        self._create_move_cards()

        # --- Widgets for the Sidebar (Right) ---
        # A frame for player stats at the top of the sidebar
        self.player_stats_frame = tk.Frame(self.sidebar_frame)
        self.player_stats_frame.pack(side=tk.TOP, pady=(10, 20))
        self.player_health_label = tk.Label(self.player_stats_frame, text="", font=("Arial", 12, "bold"), fg="white")
        self.player_health_label.pack(pady=(10, 0))
        self.player_health_bar = ttk.Progressbar(self.player_stats_frame, style="Player.Horizontal.TProgressbar", orient="horizontal", length=200, mode="determinate")
        self.player_health_bar.pack()

        # A frame for status text in the middle of the sidebar
        self.status_frame = tk.Frame(self.sidebar_frame)
        self.status_frame.pack(fill=tk.Y, expand=True)
        self.status_label = tk.Label(self.status_frame, text="Choose your attack...", font=("Helvetica", 16, "italic"), fg="white", wraplength=200)
        self.status_label.pack(pady=20)
        self.timer_label = tk.Label(self.status_frame, text="", font=("Impact", 48), fg="#FFD700")
        self.timer_label.pack(pady=10)

        # A frame for action buttons at the bottom of the sidebar
        self.button_frame = tk.Frame(self.sidebar_frame)
        self.button_frame.pack(side=tk.BOTTOM, pady=20)
        self.complete_move_button = tk.Button(self.button_frame, text="Complete Move", font=("Helvetica", 14, "bold"), bg="#1E5627", fg="white", relief=tk.FLAT, command=self.complete_move, width=20, height=2)
        self.return_button = tk.Button(self.button_frame, text="Return to Tower", font=("Helvetica", 14), bg="#333", fg="white", relief=tk.FLAT, command=self.end_raid_callback, width=20, height=2)
        
        # Apply transparency to all frames and labels
        for widget in self.winfo_children():
            self._set_transparent_bg(widget)

    def _set_transparent_bg(self, parent_widget):
        parent_widget.config(bg="#0E0A41")
        for child in parent_widget.winfo_children():
            if isinstance(child, (tk.Label, tk.Frame)):
                child.configure(bg="#0E0A41")
            if child.winfo_children():
                self._set_transparent_bg(child)

    def _create_move_cards(self):
        # Place the moves_frame in the center of its container
        self.moves_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        for i in range(3):
            card = tk.Frame(self.moves_frame, bg="#222", relief=tk.RAISED, borderwidth=2, cursor="hand2")
            card.config(width=150, height=150)
            card.pack_propagate(False)
            card.pack(side=tk.LEFT, padx=15)
            card.is_enabled = True 
            
            icon_label = tk.Label(card, text="", font=("Helvetica", 12, "bold"), fg="white", bg="#222", compound=tk.TOP)
            icon_label.pack(padx=10, pady=5, expand=True)
            
            card_data = {'frame': card, 'icon_label': icon_label, 'icon': None, 'move_index': i}
            self.move_cards.append(card_data)

            def on_enter(event, c=card):
                if c.is_enabled:
                    c.config(bg="#333")
                    for child in c.winfo_children():
                        child.config(bg="#333")
            
            def on_leave(event, c=card):
                if 'selected' not in c.tk.call('bindtags', c):
                    c.config(bg="#222")
                    for child in c.winfo_children():
                        child.config(bg="#222")

            def on_click(event, index=i, c=card):
                if c.is_enabled:
                    self.select_move(index)

            card.bind("<Enter>", on_enter)
            card.bind("<Leave>", on_leave)
            card.bind("<Button-1>", on_click)
            icon_label.bind("<Button-1>", on_click)
            
    def _update_card_ui(self, disable=False):
        if not self.winfo_exists(): return

        for i, card_data in enumerate(self.move_cards):
            card = card_data['frame']
            icon_label = card_data['icon_label']
            
            if disable or not hasattr(self, 'available_moves') or not self.available_moves:
                card.is_enabled = False
                card.config(bg="#111", relief=tk.FLAT, cursor="")
                icon_label.config(text="", image="", bg="#111")
                card.icon = None
            else:
                card.is_enabled = True
                move = self.available_moves[i]
                icon_name = move['name'].lower().replace(' ', '_') + ".png"
                try:
                    img = Image.open(self.icons_path / icon_name).resize((64, 64), Image.Resampling.LANCZOS)
                    card_data['icon'] = ImageTk.PhotoImage(img)
                except FileNotFoundError:
                    print(f"Warning: Icon '{icon_name}' not found.")
                    card_data['icon'] = None
                
                icon_label.config(text=f"{move['name']}\n({move['reps']} reps)", image=card_data['icon'], bg="#222")
                card.config(bg="#222", relief=tk.RAISED, cursor="hand2")
                tags = list(card.bindtags())
                if 'selected' in tags:
                    tags.remove('selected')
                    card.bindtags(tuple(tags))

    # --- (All other methods from here on are correct and remain unchanged) ---
    def show_damage_indicator(self, value, is_player):
        color = "#00FF00" if is_player else "#FF4500" 
        x_pos = 0.35 if is_player else 0.65 # Adjusted for new layout
        y_pos = 0.8 if is_player else 0.25
        
        damage_label = tk.Label(self, text=str(value), font=("Impact", 28), fg=color, bg="#0E0A41")
        damage_label.place(relx=x_pos, rely=y_pos, anchor=tk.CENTER)
        
        self.damage_indicator_labels.append(damage_label)
        self._fade_out_label(damage_label, 1.5)

    def _fade_out_label(self, label, duration_seconds):
        start_time = time.time()
        def update_fade():
            elapsed = time.time() - start_time
            if elapsed >= duration_seconds or not label.winfo_exists():
                if label in self.damage_indicator_labels:
                    self.damage_indicator_labels.remove(label)
                label.destroy()
                return
            
            y = label.winfo_y() - 1
            label.place(y=y)
            
            self.after(20, update_fade)
        update_fade()
        
    def screen_shake(self, intensity=5, duration_ms=300):
        main_window = self.winfo_toplevel()
        start_pos_x = main_window.winfo_x()
        start_pos_y = main_window.winfo_y()
        start_time = time.time()

        def shake():
            elapsed = (time.time() - start_time) * 1000
            if elapsed > duration_ms:
                main_window.geometry(f"+{start_pos_x}+{start_pos_y}")
                return

            offset_x = random.randint(-intensity, intensity)
            offset_y = random.randint(-intensity, intensity)
            main_window.geometry(f"+{start_pos_x + offset_x}+{start_pos_y + offset_y}")
            self.after(20, shake)
        shake()

    def _generate_raid_data(self, floor_num):
        self.hazard = None
        self.current_floor = floor_num
        stats = load_player_stats()
        player = stats["status"][0]
        self.battle_is_over = False
        
        self.boss_mechanic = None
        if floor_num == 100:
            self.current_boss = "Final Demon Lord"
            self.boss_mechanic = "execute_phase"
        elif floor_num % 25 == 0:
            self.current_boss = "Archdemon of Ruin"
            self.boss_mechanic = "power_charge"
        elif floor_num % 10 == 0:
            self.current_boss = "Armored Gatekeeper"
            self.boss_mechanic = "defensive_stance"
        else:
            self.current_boss = random.choice(self.bosses)
        
        self.affliction = None
        if self.current_boss == "Archdemon of Ruin":
            self.affliction = "timer_burn"
        elif self.current_boss == "Lich King":
            self.affliction = "fatigue"

        base_hp = 50 + (floor_num * 15) + round(pow(floor_num, 1.2))
        self.enemy_max_health = base_hp + (player["level"] * 10)
        self.enemy_health = self.enemy_max_health
        self.player_str, self.player_agi, self.player_vit = player["str"], player["agi"], player["vit"]
        self.player_max_health = 75 + (self.player_vit * 5)
        self.player_health = self.player_max_health
        self.stagger_value = 0
        self.stagger_threshold = self.enemy_max_health * 0.3
        self.is_staggered = False

        if self.boss_mechanic == "execute_phase":
            self.boss_phase = 1
            self.enemy_max_health *= 2
            self.enemy_health = self.enemy_max_health
            
        if 50 <= floor_num <= 74:
            self.hazard = "unstable_ground"

    def check_for_phase_change(self):
        if self.boss_mechanic == "execute_phase" and self.boss_phase == 1 and self.enemy_health <= self.enemy_max_health / 2:
            self.boss_phase = 2
            self.status_label.config(text="The Demon Lord is ENRAGED! Finish it NOW!")
            self.timer_label.config(text="EXECUTE!")
            self.stop_timer_event = threading.Event()
            threading.Thread(target=self._burn_phase_timer, daemon=True).start()
            self.start_new_player_turn()
            return True
        return False

    def _burn_phase_timer(self):
        for i in range(60, -1, -1):
            if self.stop_timer_event.is_set() or self.enemy_health <= 0: return
            time.sleep(1)
        if self.enemy_health > 0 and not self.battle_is_over:
            self.after(0, self.defeat, "You were overwhelmed by the Demon Lord's power.")

    def _hazard_timer(self):
        while not self.battle_is_over and self.winfo_exists():
            time.sleep(random.randint(15, 25))
            if self.battle_is_over: return
            hazard_damage = round(self.current_floor * 0.5)
            self.player_health -= hazard_damage
            self.after(0, self.show_damage_indicator, hazard_damage, False)
            self.after(0, lambda: self.status_label.config(text=f"The ground shakes! You take {hazard_damage} damage!"))
            self.after(0, self.update_ui)
            if self.player_health <= 0:
                self.after(0, self.defeat, "You succumbed to the hazardous environment.")
                return

    def start(self, floor_num):
        self._generate_raid_data(floor_num)
        if self.hazard == "unstable_ground":
            threading.Thread(target=self._hazard_timer, daemon=True).start()
        self.title_label.config(text=f"{self.current_boss.upper()}")
        self.status_label.config(text=f"You face {self.current_boss}! Choose your attack.")
        self.return_button.pack_forget()
        self.complete_move_button.pack_forget()
        self.timer_label.config(text="")
        self.start_new_player_turn()

    def select_move(self, move_index):
        self.chosen_move = self.available_moves[move_index]
        self._update_card_ui(disable=True) 
        
        selected_card = self.move_cards[move_index]['frame']
        selected_card.config(bg="#00FFFF", relief=tk.SUNKEN)
        for child in selected_card.winfo_children():
            child.config(bg="#00FFFF")
        
        tags = list(selected_card.bindtags())
        tags.insert(1, 'selected')
        selected_card.bindtags(tuple(tags))
        
        self.moves_frame_container.pack_forget()
        self.complete_move_button.pack(pady=20)
        self.stop_timer_event = threading.Event()
        threading.Thread(target=self._action_phase, daemon=True).start()

    def complete_move(self):
        self.stop_timer_event.set()
        self.resolve_turn(success=True)

    def _action_phase(self):
        duration = self.chosen_move['time']
        self.status_label.config(text=f"Perform {self.chosen_move['reps']} {self.chosen_move['name']}!")
        for i in range(duration, -1, -1):
            if self.stop_timer_event.is_set(): return
            if self.winfo_exists(): self.timer_label.config(text=f"{i}")
            time.sleep(1)
        if not self.stop_timer_event.is_set():
            self.after(0, self.resolve_turn, False)
                
    def resolve_turn(self, success):
        self.complete_move_button.pack_forget()
        if self.battle_is_over: return

        if success:
            damage = round(self.chosen_move['reps'] * 1.5) + (self.player_str * 1.5)
            if self.is_staggered: damage = round(damage * 1.5)
            self.enemy_health -= damage
            self.stagger_value += damage
            self.show_damage_indicator(damage, is_player=False)
            if hasattr(self, 'is_defending') and self.is_defending:
                self.status_label.config(text="Your attack glances off its armor!")
                self.is_defending = False
            else:
                self.status_label.config(text=f"A direct hit! You dealt {damage} damage!")
        else:
            self.status_label.config(text="You ran out of time and failed the exercise!")

        self.update_ui(disable_buttons=True)

        if self.enemy_health <= 0:
            self.after(1000, self.victory) 
            return
        
        if self.check_for_phase_change(): return

        if self.stagger_value >= self.stagger_threshold:
            self.is_staggered = True
            self.stagger_value = 0
            self.status_label.config(text="STAGGERED! The enemy is vulnerable!")
            threading.Timer(1.5, self.start_new_player_turn).start()
        else:
            threading.Timer(1.5, self.enemy_turn).start()

    def enemy_turn(self):
        if self.battle_is_over or not self.winfo_exists(): return
        self.player_affliction = None
        if self.is_staggered:
            self.is_staggered = False
            self.status_label.config(text="The enemy recovered its footing!")

        if self.boss_mechanic == "power_charge" and self.enemy_health < self.enemy_max_health / 2:
            self.status_label.config(text="The Archdemon unleashes a devastating blast!")
            enemy_attack_power = (self.current_floor * 18)
            self.boss_mechanic = None
        else:
            enemy_attack_power = (self.current_floor * 12)
        
        player_defense = self.player_vit / 2
        final_damage = max(1, round(enemy_attack_power - player_defense) + random.randint(-3, 3))
        
        self.player_health -= final_damage
        self.show_damage_indicator(final_damage, is_player=True) 
        self.screen_shake()

        self.status_label.config(text=f"The enemy strikes back, dealing {final_damage} damage!")
        self.timer_label.config(text="")
        self.update_ui(disable_buttons=True)

        if self.player_health <= 0:
            threading.Timer(1.5, self.defeat, ["You have been slain."]).start()
        else:
            threading.Timer(1.5, self.start_new_player_turn).start()

    def start_new_player_turn(self):
        if self.battle_is_over or not self.winfo_exists(): return
        self.moves_frame_container.pack(fill=tk.BOTH, expand=True) # Ensure container is visible
        self.status_label.config(text="Choose your next move.")
        all_exercises = self.exercises['easy'] + self.exercises['medium'] + self.exercises['hard']
        self.available_moves = []
        base_reps = random.randint(8, 20)
        base_time = 45
        if hasattr(self, 'player_affliction') and self.player_affliction:
            if self.player_affliction == "fatigue": base_reps = round(base_reps * 1.5)
            elif self.player_affliction == "timer_burn": base_time = 30
        for name in random.sample(all_exercises, 3):
            self.available_moves.append({'name': name, 'reps': base_reps, 'time': base_time})
        
        self.update_ui(disable_buttons=False)

    def victory(self):
        if self.battle_is_over: return
        stats = load_player_stats()
        player = stats["status"][0]
        if self.current_floor > player["highest_floor"]:
            player["highest_floor"] = self.current_floor
        base_xp = 10 + (self.enemy_max_health // 10)
        coin_gain = 5 if "Boss" in self.current_boss else 0
        player["XP"] += base_xp
        player["coins"] += coin_gain
        player["fatigue"] += 5
        save_player_stats(stats)
        leveled_up, _ = thesystem.system.get_fin_xp()
        msg = f"V I C T O R Y\n+{base_xp} XP | +{coin_gain} Coins"
        if leveled_up: msg += "\nLEVEL UP!"
        self.status_label.config(text=msg)
        self.moves_frame_container.pack_forget()
        self.return_button.pack(pady=20)
        self.battle_is_over = True
        
    def defeat(self, message="You have been defeated."):
        if self.battle_is_over: return
        self.battle_is_over = True
        for label in self.damage_indicator_labels: label.destroy()
        main_window = self.winfo_toplevel()
        try:
            subprocess.Popen([sys.executable, 'First/Game Over/gui.py'])
        except FileNotFoundError:
            print("ERROR: 'game_over_screen.py' not found.")
        main_window.destroy()

    def update_ui(self, disable_buttons=False):
        if not self.winfo_exists(): return
        self._animate_progress_bar(self.enemy_health_bar, (self.enemy_health / self.enemy_max_health) * 100)
        self.enemy_health_label.config(text=f"HP: {max(0, round(self.enemy_health))} / {self.enemy_max_health}")
        self._animate_progress_bar(self.player_health_bar, (self.player_health / self.player_max_health) * 100)
        self.player_health_label.config(text=f"HP: {max(0, round(self.player_health))} / {self.player_max_health}")
        self._animate_progress_bar(self.stagger_bar, (self.stagger_value / self.stagger_threshold) * 100 if self.stagger_threshold > 0 else 0)

        self._update_card_ui(disable=disable_buttons)

    def _animate_progress_bar(self, bar, target_value):
        current_value = bar['value']
        step = (target_value - current_value) / 10
        def update_step():
            nonlocal current_value
            if abs(target_value - current_value) < abs(step) or step == 0:
                bar['value'] = target_value
                return
            current_value += step
            bar['value'] = current_value
            self.after(20, update_step)
        update_step()