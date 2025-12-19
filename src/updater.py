import requests
import os
import sys
import tempfile
import subprocess
from packaging import version
from typing import Optional, Callable, Tuple

GITHUB_REPO = "razikdontcare/yard"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

class Updater:
    def __init__(self, current_version: str):
        self.current_version = current_version
        self.latest_version = None
        self.download_url = None
        self.release_notes = None
        self.temp_file = None
        
    def check_for_updates(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check if a new version is available.
        
        Returns:
            Tuple of (update_available, latest_version, release_notes)
        """
        try:
            response = requests.get(GITHUB_API_URL, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Get version from tag (e.g., "v1.0.2" -> "1.0.2")
            tag_name = data.get("tag_name", "")
            self.latest_version = tag_name.lstrip("v")
            self.release_notes = data.get("body", "No release notes available.")
            
            # Find the .exe asset
            assets = data.get("assets", [])
            for asset in assets:
                if asset["name"].endswith(".exe"):
                    self.download_url = asset["browser_download_url"]
                    break
            
            # Compare versions
            if self.download_url and version.parse(self.latest_version) > version.parse(self.current_version):
                return True, self.latest_version, self.release_notes
            
            return False, self.latest_version, None
            
        except requests.RequestException as e:
            print(f"Update check failed: {e}")
            return False, None, None
        except Exception as e:
            print(f"Unexpected error during update check: {e}")
            return False, None, None
    
    def download_update(self, progress_callback: Optional[Callable[[int, int, float], None]] = None) -> Optional[str]:
        """
        Download the update file.
        
        Args:
            progress_callback: Function called with (downloaded_bytes, total_bytes, speed_mbps)
        
        Returns:
            Path to downloaded file, or None if failed
        """
        if not self.download_url:
            return None
        
        try:
            # Create temp file
            temp_dir = tempfile.gettempdir()
            self.temp_file = os.path.join(temp_dir, f"yard_update_{self.latest_version}.exe")
            
            # Download with progress tracking
            response = requests.get(self.download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            chunk_size = 8192
            
            import time
            start_time = time.time()
            last_update_time = start_time
            last_downloaded = 0
            
            with open(self.temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Call progress callback
                        if progress_callback:
                            current_time = time.time()
                            time_diff = current_time - last_update_time
                            
                            # Update every 0.1 seconds
                            if time_diff >= 0.1:
                                bytes_diff = downloaded_size - last_downloaded
                                speed_mbps = (bytes_diff / time_diff) / (1024 * 1024)
                                
                                progress_callback(downloaded_size, total_size, speed_mbps)
                                
                                last_update_time = current_time
                                last_downloaded = downloaded_size
            
            # Final progress callback
            if progress_callback:
                progress_callback(total_size, total_size, 0)
            
            return self.temp_file
            
        except Exception as e:
            print(f"Download failed: {e}")
            if self.temp_file and os.path.exists(self.temp_file):
                try:
                    os.remove(self.temp_file)
                except:
                    pass
            return None
    
    def install_update(self, downloaded_file: str) -> bool:
        """
        Install the update and restart the application.
        
        Args:
            downloaded_file: Path to the downloaded update file
        
        Returns:
            True if installation started successfully
        """
        try:
            # Get current executable path
            if getattr(sys, 'frozen', False):
                current_exe = sys.executable
            else:
                # Development mode - don't actually update
                print("Running in development mode - skipping update installation")
                return False
            
            # Get file size of downloaded update for verification
            import os
            download_size = os.path.getsize(downloaded_file)
            
            # Create batch script for Windows
            batch_script = os.path.join(tempfile.gettempdir(), "yard_updater.bat")
            
            # Create backup filename
            backup_exe = current_exe + ".backup"
            
            batch_content = f"""@echo off
echo Yard Updater
echo.

echo [1/4] Waiting for Yard to close...
timeout /t 3 /nobreak > nul

:wait_loop
tasklist /FI "IMAGENAME eq yard.exe" 2>NUL | find /I /N "yard.exe">NUL
if "%ERRORLEVEL%"=="0" (
    timeout /t 1 /nobreak > nul
    goto wait_loop
)

echo [2/4] Extra wait for file handles to release...
timeout /t 3 /nobreak > nul

echo [3/4] Creating backup...
if exist "{backup_exe}" del /F /Q "{backup_exe}"
copy /Y "{current_exe}" "{backup_exe}" > nul 2>&1

echo [4/4] Installing update...
timeout /t 1 /nobreak > nul
del /F /Q "{current_exe}" 2>nul
timeout /t 1 /nobreak > nul
copy /Y "{downloaded_file}" "{current_exe}" > nul 2>&1

if not exist "{current_exe}" (
    echo ERROR: Failed to install update!
    echo Restoring backup...
    copy /Y "{backup_exe}" "{current_exe}" > nul 2>&1
    echo.
    echo Press any key to exit...
    pause > nul
    goto cleanup
)

echo.
echo ========================================
echo  UPDATE SUCCESSFUL!
echo ========================================
echo.
echo Yard has been updated successfully.
echo Please launch Yard again to use the new version.
echo.
echo This window will close in 5 seconds...
timeout /t 5

:cleanup
if exist "{backup_exe}" del /F /Q "{backup_exe}" 2>nul
if exist "{downloaded_file}" del /F /Q "{downloaded_file}" 2>nul
del "%~f0"
"""
            
            with open(batch_script, 'w') as f:
                f.write(batch_content)
            
            # Launch the batch script with visible window
            subprocess.Popen(['cmd', '/c', batch_script])
            
            return True
            
        except Exception as e:
            print(f"Installation failed: {e}")
            return False
    
    def cleanup(self):
        """Clean up temporary files."""
        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
            except:
                pass
