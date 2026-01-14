"""Queue persistence manager."""

import json
import os


class QueueManager:
    """Manages download queue persistence."""
    
    def __init__(self, queue_file):
        self.queue_file = queue_file
    
    def load(self):
        """Load queue from disk."""
        try:
            if os.path.exists(self.queue_file):
                with open(self.queue_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return []
    
    def save(self, queue):
        """Save queue to disk."""
        try:
            with open(self.queue_file, 'w') as f:
                json.dump(queue, f)
        except Exception:
            pass
    
    def clear(self):
        """Remove queue file."""
        try:
            if os.path.exists(self.queue_file):
                os.remove(self.queue_file)
        except Exception:
            pass
