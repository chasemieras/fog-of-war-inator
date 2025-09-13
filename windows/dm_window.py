import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import numpy as np
from PIL import Image, ImageTk

from utils.save_utils import manual_save
from utils.fog_state import save_fog_state

class DMWindow:
    """Generates the DM Window"""

    def __init__(self, fog_app):
        self.fog_app = fog_app
        try:
            self.window = ctk.CTkToplevel(fog_app.root)
            self.window.title("DM View - Fog of War")

            self.window.geometry("800x600")
            self.window.configure(bg='black')

            # Add escape key binding to exit fullscreen
            self.window.bind('<Escape>', self.toggle_fullscreen)
            self.window.bind('<F11>', self.toggle_fullscreen)

            # Bind Ctrl+S for manual save
            self.window.bind('<Control-s>', manual_save)

            self.window.bind('<Control-z>', lambda e: self.fog_app.undo())
            self.window.bind('<Control-y>', lambda e: self.fog_app.redo())

            self.window.bind('<F1>', self.show_help)

            # Bind window close event to auto-save
            self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

            # Focus the window
            self.window.focus_set()

            # Create canvas that fills the entire screen
            self.canvas = tk.Canvas(
                self.window, bg="black", highlightthickness=0)
            self.canvas.pack(fill="both", expand=True)

            # Bind click events
            self.canvas.bind("<Button-1>", self.on_click)
            self.canvas.bind("<B1-Motion>", self.on_drag)

            # Variables for smooth dragging (removed since we're handling it differently)
            self.last_drag_time = 0

            # Scale factor for image display
            self.scale_factor = 1.0
            self.display_width = 0
            self.display_height = 0
            self.x_offset = 0
            self.y_offset = 0
            self.dm_photo = None

            self.window.after(500, self.update_display)

        except Exception as e:
            print(f"Error creating DM window: {e}")
            raise

    def show_help(self, event=None):
        """Shows the help popup"""
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

    def on_closing(self):
        """Handle window closing - auto-save before closing"""
        save_fog_state(self, auto_save=True)
        self.fog_app.dm_window = None
        self.window.destroy()

    def toggle_fullscreen(self, event=None):
        """Enters fullscreen mode"""
        is_fullscreen = self.window.attributes('-fullscreen')
        self.window.attributes('-fullscreen', not is_fullscreen)
        if is_fullscreen:
            self.window.geometry("800x600")
        self.window.after(100, self.update_display)

    def on_click(self, event):
        """Handles clicking on the DM side"""
        if self.fog_app.map_image is not None:
            image_x = event.x - self.x_offset
            image_y = event.y - self.y_offset

            x = int(image_x / self.scale_factor)
            y = int(image_y / self.scale_factor)

            x = max(0, min(x, self.fog_app.map_image.shape[1] - 1))
            y = max(0, min(y, self.fog_app.map_image.shape[0] - 1))

            self.fog_app.reveal_area(x, y, force_update=True)

    def on_drag(self, event):
        """Does basically on click but when dragging"""
        if self.fog_app.map_image is not None:
            image_x = event.x - self.x_offset
            image_y = event.y - self.y_offset

            x = int(image_x / self.scale_factor)
            y = int(image_y / self.scale_factor)

            x = max(0, min(x, self.fog_app.map_image.shape[1] - 1))
            y = max(0, min(y, self.fog_app.map_image.shape[0] - 1))

            self.fog_app.reveal_area(x, y, force_update=False)

    def update_display(self):
        """Updates the DM display"""
        if self.fog_app.map_image is None:
            return

        try:
            self.window.update_idletasks()

            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = 800
                canvas_height = 600

            img_height, img_width = self.fog_app.map_image.shape[:2]
            scale_x = canvas_width / img_width
            scale_y = canvas_height / img_height

            self.scale_factor = min(scale_x, scale_y)

            self.display_width = int(img_width * self.scale_factor)
            self.display_height = int(img_height * self.scale_factor)

            self.x_offset = (canvas_width - self.display_width) // 2
            self.y_offset = (canvas_height - self.display_height) // 2

            try:
                dm_image = self.fog_app.map_image.copy()
                fog_overlay = np.full_like(dm_image, 64, dtype=np.uint8)

                fog_alpha = (
                    255 - self.fog_app.fog_mask).astype(np.float32) / 255.0
                fog_alpha = fog_alpha[:, :, np.newaxis]

                dm_image = dm_image.astype(np.float32)
                fog_overlay = fog_overlay.astype(np.float32)

                dm_image = (dm_image * (1 - fog_alpha * 0.7) +
                            fog_overlay * fog_alpha * 0.7).astype(np.uint8)

                dm_pil = Image.fromarray(dm_image)
                dm_pil_resized = dm_pil.resize(
                    (self.display_width, self.display_height), Image.LANCZOS)
                self.dm_photo = ImageTk.PhotoImage(dm_pil_resized)

                self.canvas.delete("all")
                self.canvas.create_image(
                    self.x_offset, self.y_offset, anchor="nw", image=self.dm_photo)

            except Exception as e:
                self.canvas.delete("all")
                self.canvas.create_text(canvas_width//2, canvas_height//2,
                                        text="Error loading map", fill="white")

        except Exception as e:
            print(f"Error in update_display: {e}")

