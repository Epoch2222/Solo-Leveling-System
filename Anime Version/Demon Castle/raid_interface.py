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
import math

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
        self.enemy_sprites_path = self.assets_path / "enemies"

        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("Enemy.Horizontal.TProgressbar", foreground='#8B0000', background='#8B0000', troughcolor='#400000', bordercolor="#111", lightcolor="#111", darkcolor="#111")
        style.configure("Player.Horizontal.TProgressbar", foreground='#00FFFF', background='#00FFFF', troughcolor='#004040', bordercolor="#111", lightcolor="#111", darkcolor="#111")
        style.configure("Stagger.Horizontal.TProgressbar", foreground='#FFD700', background='#FFD700', troughcolor='#4A4100', bordercolor="#111", lightcolor="#111", darkcolor="#111")

        self.exercises = {
            'easy': ['Jumping Jacks', 'Wall Sit', 'Crunches'], 
            'medium': ['Squats', 'Push-ups', 'Plank'], 
            'hard': ['Pull-ups', 'Burpees', 'V-Ups']
        }
        
        # Enhanced boss descriptions
        self.bosses = {
            'Orc Warlord': {
                'description': 'A massive brute with incredible strength but slow movements',
                'weakness': 'AGI',
                'special': 'Ground Slam - Deals heavy damage and stuns'
            },
            'Lich King': {
                'description': 'An undead sorcerer who drains your energy',
                'weakness': 'VIT',
                'special': 'Life Drain - Steals health and applies fatigue'
            },
            'Fire Drake': {
                'description': 'A flying beast that breathes scorching flames',
                'weakness': 'STR',
                'special': 'Fire Breath - Deals damage over time'
            },
            'Demon Knight': {
                'description': 'A heavily armored warrior with dark powers',
                'weakness': 'STR',
                'special': 'Dark Shield - Blocks next attack completely'
            }
        }
        
        self.current_floor = 0
        self.damage_indicator_labels = []
        self.particle_effects = []
        self.combo_counter = 0
        self.combo_multiplier = 1.0
        self.special_charge = 0
        self.special_ready = False

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
        
        # Enemy sprite display
        self.enemy_canvas = tk.Canvas(self.enemy_frame, width=250, height=150, bg=transparent_color, highlightthickness=0)
        self.enemy_canvas.pack(pady=10)
        self.enemy_sprite = None
        self.enemy_sprite_frames = []
        self.current_sprite_frame = 0
        self.sprite_animation_direction = 1
        
        self.title_label = tk.Label(self.enemy_frame, text="", font=("Impact", 30), fg="#8B0000", bg=transparent_color)
        self.title_label.pack()
        
        self.boss_description = tk.Label(self.enemy_frame, text="", font=("Arial", 10), fg="#CCCCCC", 
                                        bg=transparent_color, wraplength=400, justify=tk.CENTER)
        self.boss_description.pack(pady=(0, 10))
        
        self.enemy_health_label = tk.Label(self.enemy_frame, text="", font=("Arial", 12, "bold"), fg="white", bg=transparent_color)
        self.enemy_health_label.pack(pady=(5,0))
        
        self.enemy_health_bar = ttk.Progressbar(self.enemy_frame, style="Enemy.Horizontal.TProgressbar", 
                                               orient="horizontal", length=400, mode="determinate")
        self.enemy_health_bar.pack()
        
        self.stagger_bar = ttk.Progressbar(self.enemy_frame, style="Stagger.Horizontal.TProgressbar", 
                                          orient="horizontal", length=300, mode="determinate")
        self.stagger_bar.pack(pady=5)
        
        # Combo counter
        self.combo_frame = tk.Frame(self.enemy_frame, bg=transparent_color)
        self.combo_frame.pack(pady=5)
        self.combo_label = tk.Label(self.combo_frame, text="COMBO: 0", font=("Impact", 16), 
                                   fg="#FFD700", bg=transparent_color)
        self.combo_label.pack(side=tk.LEFT)
        self.combo_multiplier_label = tk.Label(self.combo_frame, text="x1.0", font=("Impact", 14), 
                                             fg="#00FF00", bg=transparent_color)
        self.combo_multiplier_label.pack(side=tk.LEFT, padx=(10, 0))

        # The moves_frame will now live in the main content area and be centered
        self.moves_frame_container = tk.Frame(self.main_content_frame)
        self.moves_frame_container.pack(fill=tk.BOTH, expand=True)
        self.moves_frame = tk.Frame(self.moves_frame_container) # The actual frame for cards
        self.move_cards = []
        self._create_move_cards()

        # --- Widgets for the Sidebar (Right) ---
        # A frame for player stats at the top of the sidebar
        self.player_stats_frame = tk.Frame(self.sidebar_frame, bg=transparent_color)
        self.player_stats_frame.pack(side=tk.TOP, pady=(10, 20))
        
        # Player level and stats
        self.player_level_label = tk.Label(self.player_stats_frame, text="Lv. 1", font=("Arial", 14, "bold"), 
                                          fg="#00FFFF", bg=transparent_color)
        self.player_level_label.pack(pady=(0, 5))
        
        self.player_stats_text = tk.Label(self.player_stats_frame, text="STR: 5\nAGI: 5\nVIT: 5", 
                                         font=("Arial", 10), fg="white", bg=transparent_color, justify=tk.LEFT)
        self.player_stats_text.pack(pady=(0, 10))
        
        self.player_health_label = tk.Label(self.player_stats_frame, text="", font=("Arial", 12, "bold"), 
                                           fg="white", bg=transparent_color)
        self.player_health_label.pack(pady=(10, 0))
        
        self.player_health_bar = ttk.Progressbar(self.player_stats_frame, style="Player.Horizontal.TProgressbar", 
                                                orient="horizontal", length=200, mode="determinate")
        self.player_health_bar.pack()
        
        # Special attack meter
        self.special_frame = tk.Frame(self.sidebar_frame, bg=transparent_color)
        self.special_frame.pack(fill=tk.X, pady=(20, 10))
        
        self.special_label = tk.Label(self.special_frame, text="SPECIAL", font=("Arial", 10, "bold"), 
                                     fg="#FF00FF", bg=transparent_color)
        self.special_label.pack()
        
        self.special_bar = ttk.Progressbar(self.special_frame, style="Player.Horizontal.TProgressbar", 
                                          orient="horizontal", length=200, mode="determinate")
        self.special_bar.pack(pady=(5, 0))
        
        self.special_button = tk.Button(self.special_frame, text="ULTIMATE READY!", font=("Arial", 10, "bold"), 
                                       bg="#FF00FF", fg="white", state=tk.DISABLED, command=self.use_special_attack)
        self.special_button.pack(pady=(5, 0))

        # A frame for status text in the middle of the sidebar
        self.status_frame = tk.Frame(self.sidebar_frame, bg=transparent_color)
        self.status_frame.pack(fill=tk.Y, expand=True, pady=20)
        
        self.status_label = tk.Label(self.status_frame, text="Choose your attack...", 
                                    font=("Helvetica", 16, "italic"), fg="white", wraplength=200, bg=transparent_color)
        self.status_label.pack(pady=20)
        
        self.timer_label = tk.Label(self.status_frame, text="", font=("Impact", 48), fg="#FFD700", bg=transparent_color)
        self.timer_label.pack(pady=10)

        # A frame for action buttons at the bottom of the sidebar
        self.complete_move_button = tk.Button(self.main_content_frame, text="Complete Move", font=("Helvetica", 14, "bold"), 
                                             bg="#1E5627", fg="white", relief=tk.FLAT, command=self.complete_move, width=20, height=2)
        
        self.return_button = tk.Button(self.main_content_frame, text="Return to Tower", font=("Helvetica", 14, "bold"), 
                                      bg="#561E1E", fg="white", relief=tk.FLAT, command=self.end_raid_callback, width=20, height=2)
        
        # Apply transparency to all frames and labels
        for widget in self.winfo_children():
            self._set_transparent_bg(widget)

    def _set_transparent_bg(self, parent_widget):
        parent_widget.config(bg="#0E0A41")
        for child in parent_widget.winfo_children():
            if isinstance(child, (tk.Label, tk.Frame, tk.Canvas)):
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
            
            # Card header with type indicator
            card_header = tk.Frame(card, bg="#333", height=20)
            card_header.pack(fill=tk.X)
            card_header.pack_propagate(False)
            
            card_type = tk.Label(card_header, text="", font=("Helvetica", 8, "bold"), fg="white", bg="#333")
            card_type.pack(side=tk.LEFT, padx=5)
            
            card_cooldown = tk.Label(card_header, text="", font=("Helvetica", 8), fg="#FF5555", bg="#333")
            card_cooldown.pack(side=tk.RIGHT, padx=5)
            
            icon_label = tk.Label(card, text="", font=("Helvetica", 10, "bold"), fg="white", bg="#222", compound=tk.TOP)
            icon_label.pack(padx=10, pady=5, expand=True)
            
            card_data = {
                'frame': card, 
                'icon_label': icon_label, 
                'icon': None, 
                'move_index': i,
                'type_label': card_type,
                'cooldown_label': card_cooldown,
                'cooldown': 0
            }
            self.move_cards.append(card_data)

            def on_enter(event, c=card):
                if c.is_enabled:
                    c.config(bg="#333")
                    for child in c.winfo_children():
                        if isinstance(child, tk.Frame):
                            child.config(bg="#444")
                        else:
                            child.config(bg="#333")
            
            def on_leave(event, c=card):
                if 'selected' not in c.tk.call('bindtags', c):
                    c.config(bg="#222")
                    for child in c.winfo_children():
                        if isinstance(child, tk.Frame):
                            child.config(bg="#333")
                        else:
                            child.config(bg="#222")

            def on_click(event, index=i, c=card):
                if c.is_enabled and self.move_cards[index]['cooldown'] == 0:
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
            type_label = card_data['type_label']
            cooldown_label = card_data['cooldown_label']
            
            # Handle cooldown display
            if card_data['cooldown'] > 0:
                cooldown_label.config(text=f"{card_data['cooldown']}")
                card.is_enabled = False
                card.config(bg="#111", relief=tk.FLAT, cursor="")
                icon_label.config(text="", image="", bg="#111")
                type_label.config(text="ON COOLDOWN", fg="#FF5555")
                card.icon = None
                continue
            elif disable or not hasattr(self, 'available_moves') or not self.available_moves:
                card.is_enabled = False
                card.config(bg="#111", relief=tk.FLAT, cursor="")
                icon_label.config(text="", image="", bg="#111")
                type_label.config(text="", fg="white")
                card.icon = None
            else:
                card.is_enabled = True
                move = self.available_moves[i]
                icon_name = move['name'].lower().replace(' ', '_') + ".png"
                
                # Determine move type and color
                move_type = "STR"
                type_color = "#FF5555"
                if any(x in move['name'].lower() for x in ['jacks', 'sit', 'plank']):
                    move_type = "VIT"
                    type_color = "#5555FF"
                elif any(x in move['name'].lower() for x in ['crunches', 'squats', 'burpees']):
                    move_type = "AGI"
                    type_color = "#55FF55"
                
                try:
                    img = Image.open(self.icons_path / icon_name).resize((64, 64), Image.Resampling.LANCZOS)
                    card_data['icon'] = ImageTk.PhotoImage(img)
                except FileNotFoundError:
                    print(f"Warning: Icon '{icon_name}' not found.")
                    card_data['icon'] = None
                
                icon_label.config(text=f"{move['name']}\n({move['reps']} reps)", image=card_data['icon'], bg="#222")
                type_label.config(text=move_type, fg=type_color)
                card.config(bg="#222", relief=tk.RAISED, cursor="hand2")
                tags = list(card.bindtags())
                if 'selected' in tags:
                    tags.remove('selected')
                    card.bindtags(tuple(tags))

    def load_enemy_sprite(self, boss_name):
        """Load and animate enemy sprite"""
        self.enemy_sprite_frames = []
        boss_key = boss_name.lower().replace(' ', '_').replace('a_', '').replace('an_', '')
        
        try:
            # Try to load multiple frames for animation
            frame_files = sorted([f for f in os.listdir(self.enemy_sprites_path) if f.startswith(boss_key)])
            for frame_file in frame_files:
                img = Image.open(self.enemy_sprites_path / frame_file).resize((250, 200), Image.Resampling.LANCZOS)
                self.enemy_sprite_frames.append(ImageTk.PhotoImage(img))
        except (FileNotFoundError, OSError):
            # Fallback to a single frame if animation not available
            try:
                img = Image.open(self.enemy_sprites_path / f"{boss_key}.png").resize((250, 200), Image.Resampling.LANCZOS)
                self.enemy_sprite_frames.append(ImageTk.PhotoImage(img))
            except (FileNotFoundError, OSError):
                # If no sprite available, create a placeholder
                self.enemy_canvas.create_text(150, 100, text=boss_name, font=("Impact", 20), fill="red")
                return
        
        # Start animation
        self.animate_enemy_sprite()
    
    def animate_enemy_sprite(self):
        """Animate the enemy sprite"""
        if not self.enemy_sprite_frames or not self.winfo_exists():
            return
            
        self.enemy_canvas.delete("all")
        self.enemy_sprite = self.enemy_canvas.create_image(
            150, 100, image=self.enemy_sprite_frames[self.current_sprite_frame]
        )
        
        # Update frame for next animation
        self.current_sprite_frame = (self.current_sprite_frame + 1) % len(self.enemy_sprite_frames)
        
        # Schedule next animation frame
        self.after(200, self.animate_enemy_sprite)
    
    def create_particle_effect(self, x, y, color, count=10, size=5, speed=2):
        """Create particle effects for attacks"""
        particles = []
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            velocity = random.uniform(0.5, speed)
            dx = math.cos(angle) * velocity
            dy = math.sin(angle) * velocity
            life = random.randint(20, 40)
            particle = self.enemy_canvas.create_oval(
                x-size, y-size, x+size, y+size,
                fill=color, outline=""
            )
            particles.append({
                'id': particle,
                'dx': dx,
                'dy': dy,
                'life': life,
                'size': size
            })
        
        self.particle_effects.extend(particles)
        self.animate_particles()
    
    def animate_particles(self):
        """Animate all active particles"""
        if not self.winfo_exists():
            return
            
        to_remove = []
        for i, particle in enumerate(self.particle_effects):
            particle['life'] -= 1
            if particle['life'] <= 0:
                self.enemy_canvas.delete(particle['id'])
                to_remove.append(i)
            else:
                self.enemy_canvas.move(particle['id'], particle['dx'], particle['dy'])
                # Fade out as life decreases
                alpha = particle['life'] / 40
                color = self.enemy_canvas.itemcget(particle['id'], "fill")
                self.enemy_canvas.itemconfig(particle['id'], fill=color)
        
        # Remove dead particles
        for i in sorted(to_remove, reverse=True):
            self.particle_effects.pop(i)
        
        # Continue animation if particles remain
        if self.particle_effects:
            self.after(30, self.animate_particles)

    def show_damage_indicator(self, value, is_player, is_critical=False):
        color = "#00FF00" if is_player else "#FF4500"
        if is_critical:
            color = "#FFFF00"  # Yellow for critical hits
            
        x_pos = 0.35 if is_player else 0.65
        y_pos = 0.8 if is_player else 0.25
        
        damage_label = tk.Label(self, text=str(value), font=("Impact", 28), fg=color, bg="#0E0A41")
        damage_label.place(relx=x_pos, rely=y_pos, anchor=tk.CENTER)
        
        self.damage_indicator_labels.append(damage_label)
        self._fade_out_label(damage_label, 1.5)
        
        # Create particle effect for damage
        if not is_player:  # Enemy taking damage
            self.create_particle_effect(150, 100, color, count=15, size=3, speed=3)

    def _fade_out_label(self, label, duration_seconds):
        start_time = time.time()
        def update_fade():
            elapsed = time.time() - start_time
            if elapsed >= duration_seconds or not label.winfo_exists():
                if label in self.damage_indicator_labels:
                    self.damage_indicator_labels.remove(label)
                label.destroy()
                return
            
            # Move upward and fade out
            y = label.winfo_y() - 2
            label.place(y=y)
            
            # Calculate opacity
            opacity = 1.0 - (elapsed / duration_seconds)
            if opacity < 0:
                opacity = 0
                
            # Apply fading (if supported by platform)
            try:
                label.config(fg=self._adjust_alpha(label.cget("fg"), opacity))
            except:
                pass
            
            self.after(20, update_fade)
        update_fade()
        
    def _adjust_alpha(self, color, alpha):
        """Adjust color alpha (simplified implementation)"""
        if color.startswith("#"):
            # For hex colors, we can't easily adjust alpha in tkinter
            # So we'll just return the original color
            return color
        return color
        
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
        # Get equipment stats from the loaded data
        equipment = stats.get("equipment", [{}])[0] 
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
            # Select a random boss from our enhanced boss list
            boss_name = random.choice(list(self.bosses.keys()))
            self.current_boss = boss_name
        
        self.affliction = None
        if self.current_boss == "Archdemon of Ruin":
            self.affliction = "timer_burn"
        elif self.current_boss == "Lich King":
            self.affliction = "fatigue"

        base_hp = 50 + (floor_num * 15) + round(pow(floor_num, 1.2))
        self.enemy_max_health = base_hp + (player["level"] * 10)
        self.enemy_health = self.enemy_max_health
        
        # Player stats now include equipment bonuses
        self.player_str = player.get("str", 0) + equipment.get("STR", 0)
        self.player_agi = player.get("agi", 0) + equipment.get("AGI", 0)
        self.player_vit = player.get("vit", 0) + equipment.get("VIT", 0)
        self.player_level = player.get("level", 1)

        self.player_max_health = 75 + (self.player_vit * 5)
        self.player_health = self.player_max_health
        self.stagger_value = 0

        self.stagger_threshold = self.enemy_max_health * 2 - (self.player_str * 10)
        self.is_staggered = False

        if self.boss_mechanic == "execute_phase":
            self.boss_phase = 1
            self.enemy_max_health *= 2
            self.enemy_health = self.enemy_max_health
            
        if 50 <= floor_num <= 74:
            self.hazard = "unstable_ground"
            
        # Initialize combo system
        self.combo_counter = 0
        self.combo_multiplier = 1.0
        self.special_charge = 0
        self.special_ready = False

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
        
        # Show boss description
        boss_info = self.bosses.get(self.current_boss, {})
        description = boss_info.get('description', 'A formidable foe stands before you.')
        weakness = boss_info.get('weakness', 'None')
        special = boss_info.get('special', 'Unknown ability')
        
        self.boss_description.config(text=f"{description}\nWeakness: {weakness}\nSpecial: {special}")
        
        self.status_label.config(text=f"You face {self.current_boss}! Choose your attack.")
        self.return_button.pack_forget()
        self.complete_move_button.pack_forget()
        self.timer_label.config(text="")
        
        # Load enemy sprite
        self.load_enemy_sprite(self.current_boss)
        
        # Update player stats display
        self.player_level_label.config(text=f"Lv. {self.player_level}")
        self.player_stats_text.config(text=f"STR: {self.player_str}\nAGI: {self.player_agi}\nVIT: {self.player_vit}")
        
        self.start_new_player_turn()

    def select_move(self, move_index):
        self.chosen_move = self.available_moves[move_index]
        self._update_card_ui(disable=True) 
        
        selected_card = self.move_cards[move_index]['frame']
        selected_card.config(bg="#00FFFF", relief=tk.SUNKEN)
        for child in selected_card.winfo_children():
            if isinstance(child, tk.Frame):
                child.config(bg="#00AAAA")
            else:
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
            # Calculate base damage
            base_damage = round(self.chosen_move['reps'] * 1.5)
            
            # Apply stat bonus based on move type
            if any(x in self.chosen_move['name'].lower() for x in ['jacks', 'sit', 'plank']):
                base_damage += self.player_vit * 1.2  # VIT-based moves
            elif any(x in self.chosen_move['name'].lower() for x in ['crunches', 'squats', 'burpees']):
                base_damage += self.player_agi * 1.2  # AGI-based moves
            else:
                base_damage += self.player_str * 1.5  # STR-based moves (default)
            
            # Apply combo multiplier
            damage = round(base_damage * self.combo_multiplier)
            is_critical = self.combo_multiplier >= 1.5
            
            if self.is_staggered: 
                damage = round(damage * 1.5)
                is_critical = True
                
            self.enemy_health -= damage
            self.stagger_value += damage
            
            # Update combo
            self.combo_counter += 1
            self.combo_multiplier = min(2.0, 1.0 + (self.combo_counter * 0.1))
            
            # Charge special meter
            self.special_charge = min(100, self.special_charge + damage / 5)
            if self.special_charge >= 100 and not self.special_ready:
                self.special_ready = True
                self.special_button.config(state=tk.NORMAL, bg="#FF00FF", text="ULTIMATE READY!")
            
            self.show_damage_indicator(damage, is_player=False, is_critical=is_critical)
            
            if hasattr(self, 'is_defending') and self.is_defending:
                self.status_label.config(text="Your attack glances off its armor!")
                self.is_defending = False
            else:
                self.status_label.config(text=f"A direct hit! You dealt {damage} damage!")
                
            # Put move on cooldown
            move_type = "STR"
            if any(x in self.chosen_move['name'].lower() for x in ['jacks', 'sit', 'plank']):
                move_type = "VIT"
            elif any(x in self.chosen_move['name'].lower() for x in ['crunches', 'squats', 'burpees']):
                move_type = "AGI"
                
            # Set cooldown based on move type
            for i, move in enumerate(self.available_moves):
                if move['name'] == self.chosen_move['name']:
                    self.move_cards[i]['cooldown'] = 2  # 2 turn cooldown
        else:
            self.status_label.config(text="You ran out of time and failed the exercise!")
            # Reset combo on failure
            self.combo_counter = 0
            self.combo_multiplier = 1.0

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

    def use_special_attack(self):
        if not self.special_ready:
            return
            
        self.special_ready = False
        self.special_charge = 0
        self.special_button.config(state=tk.DISABLED, bg="#555", text="Charging...")
        
        # Special attack does massive damage based on player level and stats
        special_damage = round((self.player_str + self.player_agi + self.player_vit) * 3 + self.player_level * 5)
        self.enemy_health -= special_damage
        self.stagger_value += special_damage * 2
        
        # Flashy effect
        self.create_particle_effect(150, 100, "#FF00FF", count=30, size=8, speed=5)
        self.show_damage_indicator(special_damage, is_player=False, is_critical=True)
        self.status_label.config(text=f"ULTIMATE ATTACK! {special_damage} damage!")
        
        # Screen shake for emphasis
        self.screen_shake(intensity=10, duration_ms=500)
        
        self.update_ui(disable_buttons=True)
        
        if self.enemy_health <= 0:
            self.after(1000, self.victory)
            return
            
        # Continue with enemy turn after a delay
        threading.Timer(2.0, self.enemy_turn).start()

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
        
        # Reset combo when player is hit
        self.combo_counter = 0
        self.combo_multiplier = 1.0

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
            
        # Reduce cooldowns
        for card in self.move_cards:
            if card['cooldown'] > 0:
                card['cooldown'] -= 1
                
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
        
        # Apply combo bonus to XP
        xp_bonus = 1.0 + (self.combo_counter * 0.05)
        base_xp = round(base_xp * xp_bonus)
        
        coin_gain = 10000 if "Boss" in self.current_boss else 200
        player["XP"] += base_xp
        player["coins"] += coin_gain
        player["fatigue"] += 5
        save_player_stats(stats)
        leveled_up, _ = thesystem.system.get_fin_xp()
        msg = f"V I C T O R Y\n+{base_xp} XP | +{coin_gain} Coins"
        if self.combo_counter > 5:
            msg += f"\n{self.combo_counter} Hit Combo!"
        if leveled_up: msg += "\nLEVEL UP!"
        self.status_label.config(text=msg)
        self.moves_frame_container.pack_forget()
        self.return_button.pack(pady=20)
        self.battle_is_over = True
        
        # Victory particle effect
        self.create_particle_effect(150, 100, "#00FF00", count=50, size=6, speed=3)
        
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
        
        # Update combo display
        self.combo_label.config(text=f"COMBO: {self.combo_counter}")
        self.combo_multiplier_label.config(text=f"x{self.combo_multiplier:.1f}")
        
        # Update special meter
        self._animate_progress_bar(self.special_bar, self.special_charge)

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