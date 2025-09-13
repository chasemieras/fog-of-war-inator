import os
import json
from datetime import datetime
from tkinter import filedialog, messagebox
import numpy as np
from PIL import Image
from player_window import PlayerWindow

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
                    initialfile=default_filename,
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