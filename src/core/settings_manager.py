"""Settings persistence manager."""

import json
import os


class SettingsManager:
    """Manages application settings persistence."""
    
    def __init__(self, settings_file):
        self.settings_file = settings_file
    
    def load(self):
        """Load settings from disk."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def save(self, settings):
        """Save settings to disk."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f)
        except Exception:
            pass
