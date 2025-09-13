def undo(self, event=None):
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
