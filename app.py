"""Creates a program to handle fog of war for TTRPGs with save/load functionality"""
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import queue
import customtkinter as ctk
import numpy as np
from PIL import Image

from windows.dm_window import DMWindow
from windows.player_window import PlayerWindow

# Fog methods
from utils.fog_utils import reset_fog, clear_fog

# Save/load methods
from utils.save_utils import (
    get_fog_save_path, #todo find where this is used
    save_fog_state, 
    load_fog_state,
    load_fog_from_path, #todo find where this is used
    auto_load_fog_state,
    manual_save, #todo find where this is used
    update_status
)

# Undo/redo methods
from utils.undo_redo_utils import undo, redo

class FogOfWar:
    """The main popup that you load maps with"""
    def __init__(self):
        # Initialize the main application
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Create the main control window
        self.root = ctk.CTk()
        self.root.title("Fog of War - Control Panel")
        self.root.geometry("400x500")

        self.root.bind('<F1>', self.show_help)

        # Variables
        self.map_image = None
        self.fog_mask = None
        self.dm_window = None
        self.player_window = None
        self.reveal_radius = 70
        self.update_queue = queue.Queue()
        self.last_update_time = 0
        self.update_interval = 0.017  # ~60 FPS (1/60 seconds)
        self.undo_stack = []
        self.redo_stack = []

        # Save/Load variables
        self.current_map_path = None
        self.current_save_path = None
        self.auto_save_enabled = True

        # Create UI
        self.create_ui()

        # Start the update thread
        self.update_thread = threading.Thread(
            target=self.update_windows, daemon=True)
        self.update_thread.start()

    def show_help(self, event=None):
        """Shows the helper menu"""

        messagebox.showinfo("Fog of War - Controls",
                            "Keyboard Shortcuts:\n\n"
                            "Ctrl + S  : Save fog state\n"
                            "Ctrl + Z  : Undo last action\n"
                            "Ctrl + Y  : Redo last undone action\n"
                            "F11       : Toggle fullscreen\n"
                            "Esc       : Exit fullscreen\n"
                            "F1        : Show this help\n\n"
                            "Mouse:\n"
                            "Left Click      : Reveal fog\n"
                            "Click + Drag    : Reveal multiple areas")

    def push_undo(self):
        """Modifies the undo/redo stacks"""
        if self.fog_mask is not None:
            self.undo_stack.append(self.fog_mask.copy())
            self.redo_stack.clear()

    def create_ui(self):
        """Generates the UI for the first window"""

        # Title
        title_label = ctk.CTkLabel(self.root, text="Fog of War Controller",
                                   font=ctk.CTkFont(size=20, weight="bold"))
        title_label.pack(pady=20)

        title_label = ctk.CTkLabel(self.root, text="Press F1 for controls",
                                   font=ctk.CTkFont(size=15, weight="bold"))
        title_label.pack()

        # Load map button
        load_btn = ctk.CTkButton(self.root, text="Load Map Image",
                                 command=self.load_map, width=200)
        load_btn.pack(pady=10)

        # Save/Load buttons
        save_load_frame = ctk.CTkFrame(self.root)
        save_load_frame.pack(pady=10)

        save_btn = ctk.CTkButton(save_load_frame, text="Save Fog State",
                                 command=lambda: save_fog_state(self), width=120)
        save_btn.pack(side="left", padx=5)

        load_btn = ctk.CTkButton(save_load_frame, text="Load Fog State",
                                 command=lambda: load_fog_state(self), width=120)
        load_btn.pack(side="left", padx=5)

        # Reveal radius slider
        radius_label = ctk.CTkLabel(self.root, text="Reveal Size:")
        radius_label.pack(pady=(20, 5))

        self.radius_slider = ctk.CTkSlider(self.root, from_=20, to=200,
                                           number_of_steps=180)
        self.radius_slider.set(self.reveal_radius)
        self.radius_slider.pack(pady=5)

        # Radius value label
        self.radius_value = ctk.CTkLabel(
            self.root, text=f"{self.reveal_radius}x{self.reveal_radius} pixels")
        self.radius_value.pack(pady=5)

        # Update radius value display
        self.radius_slider.configure(command=self.update_radius)

        # Control buttons
        button_frame = ctk.CTkFrame(self.root)
        button_frame.pack(pady=20)

        dm_btn = ctk.CTkButton(button_frame, text="Open DM View",
                               command=self.open_dm_window, width=120)
        dm_btn.pack(side="left", padx=5)

        player_btn = ctk.CTkButton(button_frame, text="Open Player View",
                                   command=self.open_player_window, width=120)
        player_btn.pack(side="left", padx=5)

        # Reset and clear buttons
        control_frame = ctk.CTkFrame(self.root)
        control_frame.pack(pady=10)

        reset_btn = ctk.CTkButton(control_frame, text="Reset Fog",
                                  command=lambda: reset_fog(self), width=120)
        reset_btn.pack(side="left", padx=5)

        clear_btn = ctk.CTkButton(control_frame, text="Clear All Fog",
                                  command=lambda: clear_fog(self), width=120)
        clear_btn.pack(side="left", padx=5)

        # Status label
        self.status_label = ctk.CTkLabel(self.root, text="Ready",
                                         font=ctk.CTkFont(size=10))
        self.status_label.pack(pady=(10, 0))

    def update_radius(self, value):
        """Updates the radius of what will be removed"""
        self.reveal_radius = int(value)
        self.radius_value.configure(text=f"{int(value)}x{int(value)} pixels")

    def load_map(self):
        """Loads a map for the tool"""
        file_path = filedialog.askopenfilename(
            title="Select Map Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.gif")]
        )

        if file_path:
            try:
                # Load the image using PIL (already in RGB format)
                pil_image = Image.open(file_path).convert('RGB')
                self.map_image = np.array(pil_image)
                self.current_map_path = file_path

                # Create initial fog mask (all black)
                self.fog_mask = np.zeros(
                    (self.map_image.shape[0], self.map_image.shape[1]), dtype=np.uint8)

                # Try to auto-load associated fog state
                auto_load_fog_state(self)

                messagebox.showinfo("Success", "Map loaded successfully!")
                update_status(self, "Map loaded successfully")

                # Update windows if they're open
                self.update_queue.put("update_all")

            except Exception as e:
                messagebox.showerror(
                    "Error", f"Failed to load image: {str(e)}")
                update_status(self, "Failed to load map")

    def update_windows(self):
        """Updates the windows"""
        while True:
            try:
                message = self.update_queue.get(timeout=0.1)
                if message == "update_all":
                    while not self.update_queue.empty():
                        try:
                            self.update_queue.get_nowait()
                        except queue.Empty:
                            break

                    try:
                        if self.dm_window and hasattr(self.dm_window, 'window'):
                            if self.dm_window.window.winfo_exists():
                                self.dm_window.window.after_idle(
                                    self.dm_window.update_display)
                    except tk.TclError:
                        self.dm_window = None
                    except Exception as e:
                        print(f"Error updating DM window: {e}")

                    try:
                        if self.player_window and hasattr(self.player_window, 'window'):
                            if self.player_window.window.winfo_exists():
                                self.player_window.window.after_idle(
                                    self.player_window.update_display)
                    except tk.TclError:
                        self.player_window = None
                    except Exception as e:
                        print(f"Error updating player window: {e}")

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in update_windows: {e}")
                continue

    def open_dm_window(self):
            """Opens the DM window"""
            if self.map_image is None:
                messagebox.showwarning("Warning", "Please load a map first!")
                return

            try:
                if self.dm_window is None or not self.dm_window.window.winfo_exists():
                    self.dm_window = DMWindow(self)
                    self.dm_window.window.after(200, self.dm_window.update_display)
                else:
                    self.dm_window.window.lift()
            except Exception as e:
                messagebox.showerror(
                    "Error", f"Failed to open DM window: {str(e)}")

    def open_player_window(self):
        """Opens the player window"""
        if self.map_image is None:
            messagebox.showwarning("Warning", "Please load a map first!")
            return

        try:
            if self.player_window is None or not self.player_window.window.winfo_exists():
                self.player_window = PlayerWindow(self)
                self.player_window.window.after(
                    200, self.player_window.update_display)
            else:
                self.player_window.window.lift()
        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to open player window: {str(e)}")
    
    def run(self):
        """Runs the main loop"""
        self.root.mainloop()

if __name__ == "__main__":
    app = FogOfWar()
    app.run()
