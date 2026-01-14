"""Application constants and configuration."""

import os

# Application metadata
APP_VERSION = "1.1.0"

# File paths
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_FILE = os.path.join(SCRIPT_DIR, '.yard_settings.json')
QUEUE_FILE = os.path.join(SCRIPT_DIR, '.yard_queue.json')
UPDATE_CHECK_FILE = os.path.join(SCRIPT_DIR, '.yard_update_check.json')
LOCK_FILE = os.path.join(SCRIPT_DIR, '.yard.lock')

# Color scheme
BG = "#1c1c1c"
BG_SUBTLE = "#252525"
BG_CONTROL = "#333333"
BORDER = "#404040"
ACCENT = "#60a5fa"
GREEN = "#4ade80"
RED = "#f87171"
YELLOW = "#fbbf24"
TEXT = "#ffffff"
TEXT_SEC = "#999999"
TEXT_DIM = "#666666"

# Default folder
DEFAULT_FOLDER = os.path.join(os.path.expanduser("~"), "Downloads", "yard")
