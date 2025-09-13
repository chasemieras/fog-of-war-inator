from utils.save_utils import update_status

def undo(self, event=None):
        """Undoes the last done action"""
        if self.undo_stack:
            self.redo_stack.append(self.fog_mask.copy())
            self.fog_mask = self.undo_stack.pop()
            self.update_queue.put("update_all")
            update_status(self, "Undo applied")
        else:
            update_status(self, "Nothing to undo")

def redo(self):
        """Redoes the undo action"""
        if self.redo_stack:
            self.undo_stack.append(self.fog_mask.copy())
            self.fog_mask = self.redo_stack.pop()
            self.update_queue.put("update_all")
            update_status("self, Redo applied")
        else:
            update_status(self, "Nothing to redo")
