from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import tkinter as tk
from pyopengltk import OpenGLFrame
from OpenGL.GLUT import glutInit
from math import sin, cos, pi
import random

def draw_cube(size=1.0):
    half = size / 2
    glBegin(GL_QUADS)
    # Front
    glVertex3f(-half, -half, half)
    glVertex3f( half, -half, half)
    glVertex3f( half,  half, half)
    glVertex3f(-half,  half, half)
    # Back
    glVertex3f(-half, -half, -half)
    glVertex3f(-half,  half, -half)
    glVertex3f( half,  half, -half)
    glVertex3f( half, -half, -half)
    # Left
    glVertex3f(-half, -half, -half)
    glVertex3f(-half, -half,  half)
    glVertex3f(-half,  half,  half)
    glVertex3f(-half,  half, -half)
    # Right
    glVertex3f(half, -half, -half)
    glVertex3f(half,  half, -half)
    glVertex3f(half,  half,  half)
    glVertex3f(half, -half,  half)
    # Top
    glVertex3f(-half, half, -half)
    glVertex3f(-half, half,  half)
    glVertex3f( half, half,  half)
    glVertex3f( half, half, -half)
    # Bottom
    glVertex3f(-half, -half, -half)
    glVertex3f( half, -half, -half)
    glVertex3f( half, -half,  half)
    glVertex3f(-half, -half,  half)
    glEnd()


def draw_cylinder(radius=1.0, height=2.0, slices=32):
    # Cylinder walls
    glBegin(GL_QUAD_STRIP)
    for i in range(slices+1):
        theta = 2 * pi * i / slices
        x = radius * cos(theta)
        z = radius * sin(theta)
        glVertex3f(x, 0, z)
        glVertex3f(x, height, z)
    glEnd()

    # Top cap
    glBegin(GL_TRIANGLE_FAN)
    glVertex3f(0, height, 0)
    for i in range(slices+1):
        theta = 2 * pi * i / slices
        x = radius * cos(theta)
        z = radius * sin(theta)
        glVertex3f(x, height, z)
    glEnd()

    # Bottom cap
    glBegin(GL_TRIANGLE_FAN)
    glVertex3f(0, 0, 0)
    for i in range(slices+1):
        theta = 2 * pi * i / slices
        x = radius * cos(theta)
        z = radius * sin(theta)
        glVertex3f(x, 0, z)
    glEnd()

def draw_building_block(size=1.0, window_size=0.15, window_spacing=0.2, highlight=False):
    half = size / 2
    
    # NEW: Choose color based on highlight state
    if highlight:
        wall_color = (0.9, 0.8, 0.2)  # Bright yellow/gold for highlight
        side_wall_color = (0.8, 0.7, 0.1)
    else:
        wall_color = (0.2, 0.2, 0.25) # Original dark "scorched" color
        side_wall_color = (0.15, 0.15, 0.2)

    # Loop through each face of the cube
    for face in ['front', 'back', 'left', 'right']:
        glBegin(GL_QUADS)
        if face == 'front' or face == 'back':
            glColor3fv(wall_color)
        else: # left or right
            glColor3fv(side_wall_color)
        
        # Vertex definitions are the same as before...
        if face == 'front':
            glVertex3f(-half, -half, half); glVertex3f(half, -half, half)
            glVertex3f(half, half, half); glVertex3f(-half, half, half)
        elif face == 'back':
            glVertex3f(-half, -half, -half); glVertex3f(-half, half, -half)
            glVertex3f(half, half, -half); glVertex3f(half, -half, -half)
        elif face == 'left':
            glVertex3f(-half, -half, -half); glVertex3f(-half, -half, half)
            glVertex3f(-half, half, half); glVertex3f(-half, half, -half)
        elif face == 'right':
            glVertex3f(half, -half, -half); glVertex3f(half, half, -half)
            glVertex3f(half, half, half); glVertex3f(half, -half, half)
        glEnd()

        # Window drawing logic is the same...
        glColor3f(0.1, 0.1, 0.15) # Dark windows
        y = -half + window_spacing
        while y <= half - window_spacing:
            x = -half + window_spacing
            while x <= half - window_spacing:
                w_half = window_size / 2
                glBegin(GL_QUADS)
                # ... (rest of window drawing code is unchanged)
                if face == 'front':
                    glVertex3f(x - w_half, y - w_half, half + 0.01); glVertex3f(x + w_half, y - w_half, half + 0.01)
                    glVertex3f(x + w_half, y + w_half, half + 0.01); glVertex3f(x - w_half, y + w_half, half + 0.01)
                elif face == 'back':
                    glVertex3f(x - w_half, y - w_half, -half - 0.01); glVertex3f(x + w_half, y - w_half, -half - 0.01)
                    glVertex3f(x + w_half, y + w_half, -half - 0.01); glVertex3f(x - w_half, y + w_half, -half - 0.01)
                elif face == 'left':
                    glVertex3f(-half - 0.01, y - w_half, x - w_half); glVertex3f(-half - 0.01, y + w_half, x - w_half)
                    glVertex3f(-half - 0.01, y + w_half, x + w_half); glVertex3f(-half - 0.01, y - w_half, x + w_half)
                elif face == 'right':
                    glVertex3f(half + 0.01, y - w_half, x - w_half); glVertex3f(half + 0.01, y + w_half, x - w_half)
                    glVertex3f(half + 0.01, y + w_half, x + w_half); glVertex3f(half + 0.01, y - w_half, x + w_half)
                glEnd()
                x += window_spacing
            y += window_spacing

    # Top and bottom cap drawing is also the same...
    glColor3f(0.1, 0.1, 0.1)
    glBegin(GL_QUADS)
    glVertex3f(-half, half, -half); glVertex3f(-half, half, half)
    glVertex3f(half, half, half); glVertex3f(half, half, -half)
    glVertex3f(-half, -half, -half); glVertex3f(half, -half, -half)
    glVertex3f(half, -half, half); glVertex3f(-half, -half, half)
    glEnd()


class Castle3D(OpenGLFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.angle = 0
        self.particles = []
        self.floors = []
        self.section_status = {}

        self.current_scroll_floor = 1
        self.camera_y = 0.0
        self.target_camera_y = 0.0

        self.setup_tower(100)
        self.init_particles(500)

        self.bind("<KeyPress>", self.on_key_press)
        self.focus_set()
        
        # NEW: Create the HUD Frame and Widgets
        self.hud_frame = tk.Frame(self, bg="#111111")
        self.hud_status_label = tk.Label(self.hud_frame, text="", font=("Helvetica", 16), bg="#111111", fg="white", justify=tk.LEFT)
        self.hud_status_label.pack(pady=5, padx=10)
        
        self.hud_raid_button = tk.Button(self.hud_frame, text="Raid Floor", font=("Helvetica", 14), bg="#900", fg="white", command=self.raid_floor)
        self.hud_raid_button.pack(pady=10, padx=10, fill=tk.X)
        
        # NEW: Update the HUD to its initial state
        self.update_hud()

    def on_key_press(self, event):
        # Simplified: This method now only controls scrolling
        if event.keysym == 'Down':
            self.current_scroll_floor = max(1, self.current_scroll_floor - 1)
        elif event.keysym == 'Up':
            self.current_scroll_floor = min(len(self.floors), self.current_scroll_floor + 1)
        
        # Update the target Y for the camera to move to
        self.target_camera_y = self.floors[self.current_scroll_floor - 1]['y_center']

        # NEW: Update the HUD every time the floor changes
        self.update_hud()

    def update_hud(self):
        floor_num = self.current_scroll_floor
        status_text = self.section_status.get(floor_num, f"Floor {floor_num}: Unknown")
        
        # Update the label's text
        self.hud_status_label.config(text=status_text)
        
        # Conditionally show or hide the raid button
        if "Locked" in status_text:
            self.hud_raid_button.pack(pady=10, padx=10, fill=tk.X) # Show button
        else:
            self.hud_raid_button.pack_forget() # Hide button
            
        # Place the entire HUD frame on the screen
        self.hud_frame.place(x=20, y=20)

    def raid_floor(self):
            floor_num = self.current_scroll_floor
            print(f"ATTEMPTING RAID ON FLOOR {floor_num}!")
            
            # For demonstration, raiding successfully unlocks the floor
            self.section_status[floor_num] = f"Floor {floor_num}: Unlocked"
            
            # Update the HUD to reflect the new status (button will disappear)
            self.update_hud()

    def setup_tower(self, num_floors):
        # NEW: This method procedurally creates the tower data
        current_y = 0
        for i in range(num_floors):
            floor_num = i + 1
            height = 2.5  # Height of each floor
            
            # Taper the building: floors get smaller as they go up
            scale_factor = 1.0 - (i / (num_floors * 1.5))
            width = 8 * scale_factor
            depth = 8 * scale_factor

            self.floors.append({
                'num': floor_num,
                'y_bottom': current_y,
                'y_top': current_y + height,
                'y_center': current_y + height / 2,
                'width': width,
                'depth': depth,
                'height': height
            })
            
            # Set default status, e.g., only the first 3 are unlocked
            self.section_status[floor_num] = f"Floor {floor_num}: {'Unlocked' if i < 3 else 'Locked'}"
            
            current_y += height

    def on_click(self, event):
        # NEW: Advanced picking logic
        if self.camera_mode == 'orbiting':
            # We need the current projection and modelview matrices to use gluProject
            modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
            projection = glGetDoublev(GL_PROJECTION_MATRIX)
            viewport = glGetIntegerv(GL_VIEWPORT)

            click_y = viewport[3] - event.y  # OpenGL Y is bottom-up

            for floor in self.floors:
                # Project the 3D top and bottom of the floor to 2D screen coordinates
                bottom_screen_pos = gluProject(0, floor['y_bottom'], 0, modelview, projection, viewport)
                top_screen_pos = gluProject(0, floor['y_top'], 0, modelview, projection, viewport)

                # Check if the click Y is between the floor's screen Y coordinates
                if bottom_screen_pos[1] < click_y < top_screen_pos[1]:
                    self.focused_section = floor['num']
                    self.camera_mode = 'focused'
                    
                    status_text = self.section_status.get(self.focused_section, "Unknown")
                    self.info_label.config(text=status_text)
                    self.info_label.place(relx=0.5, rely=0.1, anchor=tk.CENTER)
                    return # Exit after finding the clicked floor

        elif self.camera_mode == 'focused':
            self.camera_mode = 'orbiting'
            self.focused_section = None
            self.info_label.place_forget()


    def initgl(self):
        glEnable(GL_DEPTH_TEST)
        glClearColor(0.15, 0.02, 0.02, 1.0) # Slightly more blue background

        # --- FOG SETUP ---
        glEnable(GL_FOG)
        glFogi(GL_FOG_MODE, GL_EXP2)
        glFogfv(GL_FOG_COLOR, (0.3, 0.1, 0.1, 1.0)) # Match background color
        glFogf(GL_FOG_DENSITY, 0.07)
        # --- END FOG SETUP ---

        # Setup projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, 4/3, 0.1, 100.0)

        glMatrixMode(GL_MODELVIEW)


    def init_particles(self, num_particles):
        for _ in range(num_particles):
            particle = {
                'pos': [random.uniform(-15, 15), random.uniform(0, 25), random.uniform(-15, 15)],
                'vel': [random.uniform(-0.01, 0.01), random.uniform(0.01, 0.05), random.uniform(-0.01, 0.01)],
                'life': random.uniform(1, 5)
            }
            self.particles.append(particle)

    def manage_particles(self):
        glPointSize(3.0) # Set the size of the points
        glColor4f(0.8, 0.8, 0.9, 0.7) # Faint white color
        
        glBegin(GL_POINTS)
        for p in self.particles:
            # 1. Update position and life
            p['pos'][0] += p['vel'][0]
            p['pos'][1] += p['vel'][1]
            p['pos'][2] += p['vel'][2]
            p['life'] -= 0.01

            glColor4f(random.uniform(0.8, 1.0), random.uniform(0.2, 0.6), 0.1, 0.8)
            # ...
            if p['life'] <= 0:
                # Reset particles from the ground
                p['pos'] = [random.uniform(-15, 15), 0, random.uniform(-15, 15)]
                p['life'] = random.uniform(1, 5)
            
            # 3. Draw the particle
            glVertex3fv(p['pos')])
        glEnd()



    def redraw(self):
        self.angle += 0.2
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # --- Default Camera: Orbiting Scroll ---
        self.camera_y += (self.target_camera_y - self.camera_y) * 0.1
        
        radius = 15.0
        eyeX = radius * cos(self.angle * pi / 180.0)
        eyeZ = radius * sin(self.angle * pi / 180.0)
        
        gluLookAt(eyeX, self.camera_y, eyeZ, 0, self.camera_y, 0, 0, 1, 0)

        # --- Drawing Logic (Unchanged) ---
        # Ground
        glColor3f(0.1, 0.1, 0.1)
        glBegin(GL_QUADS)
        glVertex3f(-100, -1, -100); glVertex3f(100, -1, -100)
        glVertex3f(100, -1, 100); glVertex3f(-100, -1, 100)
        glEnd()

        self.manage_particles()

        # Procedurally draw all floors with highlighting
        for floor in self.floors:
            is_highlighted = (floor['num'] == self.current_scroll_floor)
            glPushMatrix()
            glTranslatef(0, floor['y_center'], 0)
            glScalef(floor['width'], floor['height'], floor['depth')])
            draw_building_block(size=1.0, window_size=0.15, window_spacing=0.2, highlight=is_highlighted)
            glPopMatrix()










# =======================
# Run inside Tkinter
# =======================
if __name__ == "__main__":
    glutInit()  # Required for GLUT shapes (cube, cylinder, etc.)
    root = tk.Tk()
    root.geometry("800x600")

    castle = Castle3D(root, width=800, height=600)
    castle.pack(fill=tk.BOTH, expand=True)
    castle.animate = 1  # enable auto-redraw

    root.mainloop()
