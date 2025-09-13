
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
                save_path = get_fog_save_path()
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
                update_status(self, "Auto-saved fog state")
            else:
                messagebox.showinfo(
                    "Success", f"Fog state saved to {save_path}")
                update_status(self, "Fog state saved successfully")

            return True

        except Exception as e:
            error_msg = f"Failed to save fog state: {str(e)}"
            if not auto_save:
                messagebox.showerror("Error", error_msg)
            update_status(self, "Failed to save fog state")
            return False
