"""Creates a program to handle fog of war for TTRPGs with save/load functionality"""
import os
import json
import time
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import queue
import customtkinter as ctk
import numpy as np
from PIL import Image, ImageTk
import cv2


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

        # Bind Ctrl+S for manual save
        self.root.bind('<Control-s>', self.manual_save)
        self.root.bind('<Control-S>', self.manual_save)

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
                                 command=self.save_fog_state, width=120)
        save_btn.pack(side="left", padx=5)

        load_btn = ctk.CTkButton(save_load_frame, text="Load Fog State",
                                 command=self.load_fog_state, width=120)
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
                                  command=self.reset_fog, width=120)
        reset_btn.pack(side="left", padx=5)

        clear_btn = ctk.CTkButton(control_frame, text="Clear All Fog",
                                  command=self.clear_fog, width=120)
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
                self.auto_load_fog_state()

                messagebox.showinfo("Success", "Map loaded successfully!")
                self.update_status("Map loaded successfully")

                # Update windows if they're open
                self.update_queue.put("update_all")

            except Exception as e:
                messagebox.showerror(
                    "Error", f"Failed to load image: {str(e)}")
                self.update_status("Failed to load map")

    def get_fog_save_path(self, map_path=None):
        """Generate a fog save file path based on the map path"""
        if map_path is None:
            map_path = self.current_map_path

        if map_path is None:
            return None

        # Get the directory and filename of the map
        map_dir = os.path.dirname(map_path)
        map_filename = os.path.basename(map_path)
        map_name = os.path.splitext(map_filename)[0]

        # Create fog directory if it doesn't exist
        fog_dir = os.path.join(map_dir, "fog")
        if not os.path.exists(fog_dir):
            os.makedirs(fog_dir)

        # Create fog save path in the fog directory
        return os.path.join(fog_dir, map_name + ".fog")

    def save_fog_state(self, auto_save=False):
        """Save the current fog state"""
        if self.fog_mask is None or self.current_map_path is None:
            if not auto_save:
                messagebox.showwarning(
                    "Warning", "No map or fog data to save!")
            return False

        try:
            if auto_save:
                # Use auto-generated path for auto-save
                save_path = self.get_fog_save_path()
            else:
                # Ask user for save location for manual save
                default_filename = os.path.splitext(
                    os.path.basename(self.current_map_path))[0] + ".fog"
                save_path = filedialog.asksaveasfilename(
                    title="Save Fog State",
                    defaultextension=".fog",
                    filetypes=[("Fog files", "*.fog"), ("All files", "*.*")],
                    initialvalue=default_filename,
                    initialdir=os.path.join(
                        os.path.dirname(self.current_map_path), "fog")
                )

            if not save_path:
                return False

            # Create save data
            save_data = {
                'fog_mask': self.fog_mask.tolist(),  # Convert numpy array to list
                'map_path': self.current_map_path,
                'map_shape': self.map_image.shape,
                'reveal_radius': self.reveal_radius,
                'timestamp': datetime.now().isoformat(),
                'version': '1.0'
            }

            # Save to file
            with open(save_path, 'w') as f:
                json.dump(save_data, f, indent=2)

            self.current_save_path = save_path

            if auto_save:
                self.update_status("Auto-saved fog state")
            else:
                messagebox.showinfo(
                    "Success", f"Fog state saved to {save_path}")
                self.update_status("Fog state saved successfully")

            return True

        except Exception as e:
            error_msg = f"Failed to save fog state: {str(e)}"
            if not auto_save:
                messagebox.showerror("Error", error_msg)
            self.update_status("Failed to save fog state")
            return False

    def load_fog_state(self):
        """Load a fog state from file"""
        # Default to the fog directory if it exists
        initial_dir = None
        if self.current_map_path:
            fog_dir = os.path.join(os.path.dirname(
                self.current_map_path), "fog")
            if os.path.exists(fog_dir):
                initial_dir = fog_dir

        file_path = filedialog.askopenfilename(
            title="Load Fog State",
            filetypes=[("Fog files", "*.fog"), ("All files", "*.*")],
            initialdir=initial_dir
        )

        if file_path:
            self.load_fog_from_path(file_path)

    def load_fog_from_path(self, file_path):
        """Load fog state from a specific file path"""
        try:
            with open(file_path, 'r') as f:
                save_data = json.load(f)

            # Validate save data
            if 'fog_mask' not in save_data or 'map_path' not in save_data:
                messagebox.showerror("Error", "Invalid fog save file!")
                return False

            # Check if the associated map exists
            saved_map_path = save_data['map_path']
            if not os.path.exists(saved_map_path):
                # Ask user to locate the map
                messagebox.showwarning("Warning",
                                       f"Original map not found at {saved_map_path}\n"
                                       "Please locate the map file.")

                new_map_path = filedialog.askopenfilename(
                    title="Locate Map Image",
                    filetypes=[
                        ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.gif")]
                )

                if not new_map_path:
                    return False

                saved_map_path = new_map_path

            # Load the map if it's not already loaded or if it's different
            if self.current_map_path != saved_map_path:
                try:
                    pil_image = Image.open(saved_map_path).convert('RGB')
                    self.map_image = np.array(pil_image)
                    self.current_map_path = saved_map_path
                except Exception as e:
                    messagebox.showerror(
                        "Error", f"Failed to load map: {str(e)}")
                    return False

            # Load fog mask
            self.fog_mask = np.array(save_data['fog_mask'], dtype=np.uint8)

            # Verify dimensions match
            if self.fog_mask.shape != self.map_image.shape[:2]:
                messagebox.showerror(
                    "Error", "Fog mask dimensions don't match map dimensions!")
                return False

            # Load other settings
            if 'reveal_radius' in save_data:
                self.reveal_radius = save_data['reveal_radius']
                self.radius_slider.set(self.reveal_radius)
                self.radius_value.configure(
                    text=f"{self.reveal_radius}x{self.reveal_radius} pixels")

            self.current_save_path = file_path
            messagebox.showinfo("Success", "Fog state loaded successfully!")
            self.update_status("Fog state loaded successfully")

            # Update windows if they're open
            self.update_queue.put("update_all")
            return True

        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to load fog state: {str(e)}")
            self.update_status("Failed to load fog state")
            return False

    def auto_load_fog_state(self):
        """Automatically load fog state if it exists for the current map"""
        if not self.current_map_path:
            return

        # First, try to find exact match in fog directory
        auto_save_path = self.get_fog_save_path()
        if auto_save_path and os.path.exists(auto_save_path):
            try:
                self.load_fog_from_path(auto_save_path)
                self.update_status("Auto-loaded existing fog state")
                return
            except:
                # Continue to search for other matches
                pass

        # If exact match not found, search for similar names in fog directory
        map_dir = os.path.dirname(self.current_map_path)
        fog_dir = os.path.join(map_dir, "fog")

        if not os.path.exists(fog_dir):
            return

        map_filename = os.path.basename(self.current_map_path)
        map_name = os.path.splitext(map_filename)[0].lower()

        # Look for fog files that match the map name (case-insensitive)
        for filename in os.listdir(fog_dir):
            if filename.lower().endswith('.fog'):
                fog_name = os.path.splitext(filename)[0].lower()
                if fog_name == map_name:
                    fog_path = os.path.join(fog_dir, filename)
                    try:
                        self.load_fog_from_path(fog_path)
                        self.update_status(
                            f"Auto-loaded fog state: {filename}")
                        return
                    except:
                        continue

    def manual_save(self, event=None):
        """Handle Ctrl+S manual save"""
        self.save_fog_state(auto_save=False)

    def update_status(self, message):
        """Update the status label"""
        self.status_label.configure(text=message)
        # Clear status after 3 seconds
        self.root.after(
            3000, lambda: self.status_label.configure(text="Ready"))

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

    def reset_fog(self):
        """Resets the fog of the map"""
        if self.fog_mask is not None:
            self.push_undo()
            self.fog_mask = np.zeros_like(self.fog_mask)
            self.update_queue.put("update_all")

    def clear_fog(self):
        """Clears all of the fog"""
        if self.fog_mask is not None:
            self.push_undo()
            self.fog_mask = np.ones_like(self.fog_mask) * 255
            self.update_queue.put("update_all")

    def reveal_area(self, x, y, force_update=False):
        """Removes the fog where clicked"""
        if self.fog_mask is not None:
            self.push_undo()
            mask = np.zeros_like(self.fog_mask)
            half_size = self.reveal_radius // 2

            x1 = max(0, int(x - half_size))
            y1 = max(0, int(y - half_size))
            x2 = min(self.fog_mask.shape[1], int(x + half_size))
            y2 = min(self.fog_mask.shape[0], int(y + half_size))

            cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)

            self.fog_mask = cv2.bitwise_or(self.fog_mask, mask)

            if force_update:
                self.update_queue.put("update_all")
            else:
                current_time = time.time()
                if current_time - self.last_update_time >= self.update_interval:
                    self.update_queue.put("update_all")
                    self.last_update_time = current_time
                elif current_time - self.last_update_time >= 0.01:
                    self.update_queue.put("update_all")
                    self.last_update_time = current_time

    def undo(self):
        """Undoes the last done action"""
        if self.undo_stack:
            self.redo_stack.append(self.fog_mask.copy())
            self.fog_mask = self.undo_stack.pop()
            self.update_queue.put("update_all")
            self.update_status("Undo applied")
        else:
            self.update_status("Nothing to undo")

    def redo(self):
        """Redoes the undo action"""
        if self.redo_stack:
            self.undo_stack.append(self.fog_mask.copy())
            self.fog_mask = self.redo_stack.pop()
            self.update_queue.put("update_all")
            self.update_status("Redo applied")
        else:
            self.update_status("Nothing to redo")

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

    def run(self):
        """Runs the main loop"""
        self.root.mainloop()


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
            self.window.bind('<Control-s>', self.fog_app.manual_save)
            self.window.bind('<Control-S>', self.fog_app.manual_save)

            self.window.bind('<Control-z>', self.fog_app.undo())
            self.window.bind('<Control-y>', self.fog_app.redo())

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
        self.fog_app.save_fog_state(auto_save=True)
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

            # Bind Ctrl+S for manual save
            self.window.bind('<Control-s>', self.fog_app.manual_save)
            self.window.bind('<Control-S>', self.fog_app.manual_save)

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


if __name__ == "__main__":
    app = FogOfWar()
    app.run()
