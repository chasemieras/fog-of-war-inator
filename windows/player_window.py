import customtkinter as ctk

import tkinter as tk
import numpy as np
from PIL import Image, ImageTk

class PlayerWindow:
    """Sets up the player window"""

    def __init__(self, fog_app):
        self.fog_app = fog_app
        try:
            self.window = ctk.CTkToplevel(fog_app.root)
            self.window.title("Player View - Fog of War")

            self.window.geometry("800x600")
            self.window.configure(bg='black')

            # Add escape key binding to exit fullscreen
            self.window.bind('<Escape>', self.toggle_fullscreen)
            self.window.bind('<F11>', self.toggle_fullscreen)

            # Bind window close event to auto-save
            self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

            # Focus the window
            self.window.focus_set()

            # Create canvas that fills the entire screen
            self.canvas = tk.Canvas(
                self.window, bg="black", highlightthickness=0)
            self.canvas.pack(fill="both", expand=True)

            # Scale factor for image display
            self.scale_factor = 1.0
            self.display_width = 0
            self.display_height = 0
            self.x_offset = 0
            self.y_offset = 0
            self.player_photo = None

            self.window.after(500, self.update_display)

        except Exception as e:
            print(f"Error creating player window: {e}")
            raise

    def on_closing(self):
        """Handle window closing - auto-save before closing"""
        self.fog_app.save_fog_state(auto_save=True)
        self.fog_app.player_window = None
        self.window.destroy()

    def toggle_fullscreen(self, event=None):
        """Toggles fullscreen mode"""
        is_fullscreen = self.window.attributes('-fullscreen')
        self.window.attributes('-fullscreen', not is_fullscreen)
        if is_fullscreen:
            self.window.geometry("800x600")
        self.window.after(100, self.update_display)

    def update_display(self):
        """Updates the display based on DM screen"""
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
                fog_alpha = self.fog_app.fog_mask.astype(np.float32) / 255.0
                fog_alpha = fog_alpha[:, :, np.newaxis]

                player_image = (self.fog_app.map_image.astype(
                    np.float32) * fog_alpha).astype(np.uint8)

                player_pil = Image.fromarray(player_image)
                player_pil_resized = player_pil.resize(
                    (self.display_width, self.display_height), Image.LANCZOS)
                self.player_photo = ImageTk.PhotoImage(player_pil_resized)

                self.canvas.delete("all")
                self.canvas.create_image(
                    self.x_offset, self.y_offset, anchor="nw", image=self.player_photo)

            except Exception as e:
                print(f"Error creating player image: {e}")
                self.canvas.delete("all")
                self.canvas.create_text(canvas_width//2, canvas_height//2,
                                        text="Error loading map", fill="white")

        except Exception as e:
            print(f"Error in update_display: {e}")

