"""General utility helper functions."""

import os
import subprocess
import psutil


def open_folder(path):
    """Open the folder in file explorer."""
    if os.path.exists(path):
        if os.name == 'nt':  # Windows
            subprocess.Popen(['explorer', os.path.normpath(path)])
        else:
            subprocess.run(['xdg-open', path])


def acquire_lock(lock_file):
    """
    Create lock file with current PID.
    
    Returns:
        bool: True if lock acquired, False if another instance is running
    """
    try:
        # Check if lock exists
        if os.path.exists(lock_file):
            try:
                with open(lock_file, 'r') as f:
                    old_pid = int(f.read().strip())
                
                # Check if process is still running
                if psutil.pid_exists(old_pid):
                    return False
                else:
                    # Old process is dead, remove stale lock
                    os.remove(lock_file)
            except Exception:
                # Can't read lock file, remove it
                try:
                    os.remove(lock_file)
                except Exception:
                    pass
        
        # Create new lock
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
        return True
    except Exception:
        # Couldn't create lock, but continue anyway
        return True


def release_lock(lock_file):
    """Remove lock file."""
    try:
        if os.path.exists(lock_file):
            os.remove(lock_file)
    except Exception:
        pass
