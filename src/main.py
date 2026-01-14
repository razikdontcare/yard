"""Yard - Yet Another yt-dlp downloader.

A modern video/audio downloader with queue management and clean UI.
"""

import flet as ft
import threading
import webbrowser

# Core imports
from core.constants import (
    APP_VERSION, SETTINGS_FILE, QUEUE_FILE, UPDATE_CHECK_FILE, LOCK_FILE,
    BG, BG_SUBTLE, BORDER, ACCENT, GREEN, RED, YELLOW, TEXT, TEXT_SEC, TEXT_DIM, DEFAULT_FOLDER
)
from core.settings_manager import SettingsManager
from core.queue_manager import QueueManager
from core.downloader import Downloader
from core.update_checker import UpdateChecker

# UI imports
from ui.components import (
    create_url_input, create_paste_button, create_add_queue_button,
    create_download_button, create_progress_bar, create_status_text,
    create_queue_count_text, create_open_folder_button, create_log_area,
    create_audio_checkbox, create_playlist_checkbox, create_compat_checkbox,
    create_quality_dropdown, create_format_dropdown, create_folder_display,
    create_folder_button, create_queue_item, create_info_button,
    create_shortcuts_info, create_update_banner, create_cookies_file_display,
    create_cookies_button, create_clear_cookies_button, create_custom_args_input
)
from ui.dialogs import create_about_dialog

# Utils imports
from utils.helpers import open_folder, acquire_lock, release_lock
from utils.notifications import show_notification


def main(page: ft.Page):
    """Main application entry point."""
    # Configure page
    page.title = "Yard"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 900
    page.window.height = 680
    page.window.min_width = 800
    page.window.min_height = 600
    page.window.resizable = True
    page.window.maximizable = True
    page.padding = 0
    page.bgcolor = BG
    
    # Initialize managers
    settings_mgr = SettingsManager(SETTINGS_FILE)
    queue_mgr = QueueManager(QUEUE_FILE)
    
    # Application state
    class State:
        downloading = False
        last_download_path = None
        queue = []
        settings_visible = True  # Settings panel visibility
    
    state = State()
    
    def toggle_settings():
        """Toggle settings panel visibility."""
        state.settings_visible = not state.settings_visible
        settings_panel_wrapper.visible = state.settings_visible
        divider.visible = state.settings_visible
        page.update()
    
    def manual_update_check(e):
        """Manually check for updates (bypasses cache)."""
        def do_check():
            if hasattr(manual_update_check, 'checker_func'):
                manual_update_check.checker_func(force=True)
        threading.Thread(target=do_check, daemon=True).start()


    
    # Create UI components
    url_input = create_url_input(lambda e: start_download())
    paste_btn = create_paste_button(lambda e: on_paste())
    add_queue_btn = create_add_queue_button(lambda e: on_add_to_queue())
    dl_btn = create_download_button(lambda e: on_download())
    
    progress = create_progress_bar()
    status = create_status_text()
    queue_count = create_queue_count_text()
    open_folder_btn = create_open_folder_button(
        lambda e: open_folder(state.last_download_path or folder_path.value)
    )
    
    log_area = create_log_area()
    info_btn = create_info_button(lambda e: create_about_dialog(page, APP_VERSION))
    
    audio_cb = create_audio_checkbox(lambda e: on_audio_change())
    playlist_cb = create_playlist_checkbox()
    compat_cb = create_compat_checkbox()
    
    quality_dd = create_quality_dropdown()
    format_dd = create_format_dropdown()
    
    folder_path = ft.TextField(value=DEFAULT_FOLDER, visible=False)
    folder_display = create_folder_display(DEFAULT_FOLDER)
    
    # Advanced settings
    cookies_path = ft.TextField(value="", visible=False)
    cookies_display = create_cookies_file_display()
    custom_args_input = create_custom_args_input()
    
    picker = ft.FilePicker(on_result=lambda e: on_folder(e))
    page.overlay.append(picker)
    
    cookies_picker = ft.FilePicker(on_result=lambda e: on_cookies_file(e))
    page.overlay.append(cookies_picker)
    
    folder_btn = create_folder_button(lambda _: picker.get_directory_path())
    cookies_btn = create_cookies_button(lambda _: cookies_picker.pick_files(
        allowed_extensions=["txt"],
        dialog_title="Select cookies.txt file"
    ))
    clear_cookies_btn = create_clear_cookies_button(lambda e: clear_cookies())

    
    # Helper functions
    def log(msg):
        """Add message to log area."""
        log_area.value = (log_area.value or "") + f"{msg}\n"
        page.update()
    
    def set_status(text, color=TEXT_SEC):
        """Update status text."""
        status.value = text
        status.color = color
        page.update()
    
    def update_queue_display():
        """Update queue UI."""
        queue_count.value = f"Queue: {len(state.queue)}"
        queue_count.visible = len(state.queue) > 0
        
        queue_list.controls.clear()
        for i, item in enumerate(state.queue):
            url = item['url'] if isinstance(item, dict) else item
            settings = item.get('settings', {}) if isinstance(item, dict) else {}
            
            queue_list.controls.append(
                create_queue_item(i, url, settings, lambda e, idx=i: remove_from_queue(idx))
            )
        
        queue_section.visible = len(state.queue) > 0
        page.update()
    
    def remove_from_queue(index):
        """Remove item from queue."""
        if 0 <= index < len(state.queue):
            state.queue.pop(index)
            queue_mgr.save(state.queue)
            update_queue_display()
            set_status(f"Removed from queue ({len(state.queue)} remaining)", TEXT_SEC)
    
    def clear_queue(e):
        """Clear all queue items."""
        state.queue.clear()
        queue_mgr.clear()
        update_queue_display()
        set_status("Queue cleared", TEXT_SEC)
    
    # Download callbacks
    def progress_hook(d):
        """Handle download progress updates."""
        if d['status'] == 'downloading':
            try:
                pct = d.get('_percent_str', '0%').replace('%', '').strip()
                progress.value = float(pct) / 100
                
                speed = d.get('_speed_str', '').strip()
                eta = d.get('_eta_str', '').strip()
                
                msg = f"{d.get('_percent_str', '').strip()}"
                if speed:
                    msg += f" · {speed}"
                if eta:
                    msg += f" · {eta}"
                set_status(msg, TEXT)
            except Exception:
                pass
        elif d['status'] == 'finished':
            progress.value = 1
            set_status("Download complete, processing...", TEXT_SEC)
            if compat_cb.value:
                log("Download finished, converting to constant framerate...")
            else:
                log("Download finished, merging formats...")
    
    def postprocessor_hook(d):
        """Handle post-processing updates."""
        if d['status'] == 'started':
            postprocessor_name = d.get('postprocessor', 'Unknown')
            log(f"Post-processing: {postprocessor_name}")
            set_status("Converting to editor-compatible format...", TEXT_SEC)
        elif d['status'] == 'processing':
            info = d.get('info_dict', {})
            filename = info.get('filepath', 'video')
            if filename:
                import os
                basename = os.path.basename(filename)
                log(f"Re-encoding: {basename[:50]}...")
                set_status("Re-encoding video (VFR → CFR)...", TEXT_SEC)
        elif d['status'] == 'finished':
            log("✓ Post-processing complete")
            set_status("Video optimized for editing", GREEN)
    
    # Initialize downloader
    downloader = Downloader(progress_hook, postprocessor_hook, log)
    
    def do_download(url, audio, quality, fmt, playlist, compat, path):
        """Execute download in background thread."""
        state.downloading = True
        state.last_download_path = path
        
        # Get advanced settings
        cookies = cookies_path.value if cookies_path.value else None
        custom_args = custom_args_input.value if custom_args_input.value.strip() else None
        
        result = downloader.download(url, audio, quality, fmt, playlist, compat, path, 
                                     cookies, custom_args)
        
        if result['success']:
            progress.color = GREEN
            title = result['title']
            set_status(f"✓ {title[:40]}...", GREEN)
            open_folder_btn.visible = True
            show_notification("Download Complete", f"{title[:50]}")
            save_current_settings()
        elif result['error'] == 'Cancelled':
            progress.color = YELLOW
            set_status("Cancelled", YELLOW)
        else:
            progress.color = RED
            set_status("Failed", RED)
        
        state.downloading = False
        
        # Process queue
        if state.queue:
            next_item = state.queue.pop(0)
            queue_mgr.save(state.queue)
            update_queue_display()
            
            if isinstance(next_item, dict):
                url_input.value = next_item['url']
                settings = next_item.get('settings', {})
                apply_item_settings(settings)
            else:
                url_input.value = next_item
            
            page.update()
            start_download()
        else:
            dl_btn.text = "Download"
            dl_btn.icon = ft.Icons.DOWNLOAD
            dl_btn.bgcolor = ACCENT
            queue_mgr.clear()
            page.update()

    
    def apply_item_settings(settings):
        """Apply settings from queue item."""
        audio_cb.value = settings.get('audio', False)
        quality_dd.value = settings.get('quality', 'Best')
        format_dd.value = settings.get('format', 'MP4' if not settings.get('audio') else 'MP3')
        playlist_cb.value = settings.get('playlist', False)
        compat_cb.value = settings.get('compat', True)
        if settings.get('folder'):
            folder_path.value = settings['folder']
    
    def start_download():
        """Start download process."""
        url = url_input.value.strip()
        if not url:
            set_status("Enter a URL", YELLOW)
            return
        
        if state.downloading:
            downloader.cancel()
            set_status("Cancelling...", YELLOW)
            return
        
        progress.value = 0
        progress.color = ACCENT
        open_folder_btn.visible = False
        set_status("Starting...", TEXT_SEC)
        
        dl_btn.text = "Cancel"
        dl_btn.icon = ft.Icons.CLOSE
        dl_btn.bgcolor = RED
        
        url_input.value = ""
        page.update()
        
        threading.Thread(
            target=do_download,
            args=(url, audio_cb.value, quality_dd.value, format_dd.value,
                  playlist_cb.value, compat_cb.value, folder_path.value),
            daemon=True
        ).start()
    
    def on_download():
        """Handle download button click."""
        start_download()
    
    def on_paste():
        """Paste from clipboard."""
        try:
            import pyperclip
            clip = pyperclip.paste()
            if clip:
                url_input.value = clip
                page.update()
        except Exception:
            pass
    
    def on_add_to_queue():
        """Add URL to queue."""
        url = url_input.value.strip()
        if url and url.startswith('http'):
            # Check duplicates
            existing_urls = [
                item['url'] if isinstance(item, dict) else item
                for item in state.queue
            ]
            if url in existing_urls:
                log("⚠ Duplicate URL - Already in queue")
                set_status("Duplicate URL detected", YELLOW)
                page.update()
                return
            
            queue_item = {
                'url': url,
                'settings': {
                    'audio': audio_cb.value,
                    'quality': quality_dd.value,
                    'format': format_dd.value,
                    'playlist': playlist_cb.value,
                    'compat': compat_cb.value,
                    'folder': folder_path.value
                }
            }
            
            state.queue.append(queue_item)
            queue_mgr.save(state.queue)
            update_queue_display()
            url_input.value = ""
            set_status(f"Added to queue ({len(state.queue)} pending)", ACCENT)
            page.update()
            
            # Auto-start if not downloading
            if not state.downloading:
                start_download()
    
    def on_audio_change():
        """Handle audio checkbox change."""
        if audio_cb.value:
            format_dd.options = [
                ft.dropdown.Option("MP3"),
                ft.dropdown.Option("M4A"),
                ft.dropdown.Option("WAV")
            ]
            format_dd.value = "MP3"
            quality_dd.disabled = True
        else:
            format_dd.options = [
                ft.dropdown.Option("MP4"),
                ft.dropdown.Option("MKV"),
                ft.dropdown.Option("WEBM")
            ]
            format_dd.value = "MP4"
            quality_dd.disabled = False
        page.update()
    
    def on_folder(e):
        """Handle folder selection."""
        if e.path:
            folder_path.value = e.path
            folder_display.value = e.path
            page.update()
    
    def on_cookies_file(e):
        """Handle cookies file selection."""
        if e.files and len(e.files) > 0:
            cookies_path.value = e.files[0].path
            cookies_display.value = os.path.basename(e.files[0].path)
            log(f"Cookies file selected: {os.path.basename(e.files[0].path)}")
            page.update()
    
    def clear_cookies():
        """Clear cookies file selection."""
        cookies_path.value = ""
        cookies_display.value = "No cookies file"
        log("Cookies file cleared")
        page.update()

    
    def save_current_settings():
        """Save current settings to disk."""
        settings = {
            'audio_only': audio_cb.value,
            'playlist': playlist_cb.value,
            'compat': compat_cb.value,
            'quality': quality_dd.value,
            'format': format_dd.value,
            'folder': folder_path.value,
            'cookies_file': cookies_path.value,
            'custom_args': custom_args_input.value,
        }
        settings_mgr.save(settings)
    
    def apply_saved_settings(settings):
        """Apply loaded settings to UI."""
        import os
        if settings.get('audio_only'):
            audio_cb.value = True
            format_dd.options = [
                ft.dropdown.Option("MP3"),
                ft.dropdown.Option("M4A"),
                ft.dropdown.Option("WAV")
            ]
            format_dd.value = settings.get('format', 'MP3')
            quality_dd.disabled = True
        else:
            format_dd.value = settings.get('format', 'MP4')
        
        if settings.get('playlist'):
            playlist_cb.value = True
        
        if settings.get('compat') is not None:
            compat_cb.value = settings.get('compat', True)
        
        if settings.get('quality'):
            quality_dd.value = settings.get('quality')
        
        if settings.get('folder') and os.path.exists(settings.get('folder')):
            folder_path.value = settings['folder']
            folder_display.value = settings['folder']
        
        # Advanced settings
        if settings.get('cookies_file') and os.path.exists(settings.get('cookies_file')):
            cookies_path.value = settings['cookies_file']
            cookies_display.value = os.path.basename(settings['cookies_file'])
        
        if settings.get('custom_args'):
            custom_args_input.value = settings['custom_args']

    
    # Build UI layout
    left_panel = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text("Yard", size=24, weight=ft.FontWeight.BOLD, color=TEXT),
                    ft.Text("Video Downloader", size=12, color=TEXT_SEC),
                ], spacing=2),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.SYSTEM_UPDATE,
                    icon_color=TEXT_DIM,
                    tooltip="Check for Updates",
                    on_click=manual_update_check,
                ),
                ft.IconButton(
                    icon=ft.Icons.SETTINGS,
                    icon_color=TEXT_DIM,
                    tooltip="Toggle Settings",
                    on_click=lambda e: toggle_settings(),
                ),
                info_btn,
            ]),
            ft.Container(height=20),
            ft.Row([url_input, paste_btn, add_queue_btn, dl_btn], spacing=8),
            ft.Container(height=16),
            progress,
            ft.Container(height=8),
            ft.Row([status, ft.Container(expand=True), queue_count, open_folder_btn]),
            ft.Container(height=20),
            ft.Text("Log", size=12, color=TEXT_SEC),
            ft.Container(height=6),
            log_area,
        ]),
        padding=28,
        expand=True,
    )
    
    queue_list = ft.Column([], spacing=0)
    
    queue_section = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("Download Queue", size=14, weight=ft.FontWeight.W_600, color=TEXT),
                ft.Container(expand=True),
                ft.TextButton(
                    "Clear all",
                    style=ft.ButtonStyle(color=RED),
                    on_click=clear_queue
                ),
            ]),
            ft.Container(height=8),
            queue_list,
        ]),
        bgcolor=BG_SUBTLE,
        border_radius=6,
        padding=16,
        margin=ft.margin.only(left=28, right=28, bottom=16),
        visible=False,
    )
    
    right_panel = ft.Container(
        content=ft.Column([
            ft.Text("Settings", size=16, weight=ft.FontWeight.W_600, color=TEXT),
            ft.Container(height=20),
            audio_cb,
            ft.Container(height=2),
            playlist_cb,
            ft.Container(height=2),
            compat_cb,
            ft.Container(height=20),
            quality_dd,
            ft.Container(height=12),
            format_dd,
            ft.Container(height=20),
            ft.Row([folder_display, folder_btn], spacing=8),
            ft.Container(height=20),
            # Advanced settings
            ft.Text("Advanced", size=14, weight=ft.FontWeight.W_600, color=TEXT),
            ft.Container(height=12),
            ft.Row([cookies_display, cookies_btn, clear_cookies_btn], spacing=4),
            ft.Container(height=8),
            custom_args_input,
            ft.Container(height=4),
            ft.Text(
                "ℹ️ Custom args override default settings",
                size=9,
                color=TEXT_DIM,
                italic=True
            ),
            create_shortcuts_info(),
        ], scroll=ft.ScrollMode.AUTO, spacing=0),
        bgcolor=BG_SUBTLE,
        padding=ft.padding.only(left=24, top=24, right=10, bottom=24),
        expand=3, 
    )
    
    # Create named references for toggle functionality
    divider = ft.VerticalDivider(width=1, color=BORDER)
    settings_panel_wrapper = right_panel
    
    # Add main layout
    page.add(
        ft.Row([
            ft.Column([
                left_panel,
                queue_section,
            ], expand=7, spacing=0),  
            divider,
            settings_panel_wrapper,
        ], expand=True, spacing=0)
    )
    
    # Update checker
    def check_updates(force=False):
        """Check for updates in background."""
        if force:
            log("Forcing update check...")
        else:
            log("Checking for updates...")
        
        checker = UpdateChecker(APP_VERSION, UPDATE_CHECK_FILE, "razikdontcare", "yard")
        update = checker.check(force=force)
        
        if update:
            log(f"Current version: {APP_VERSION}")
            log(f"Latest version: {update['version']}")
            log(f"✨ Update available: v{update['version']}")
            
            def open_release_page(e):
                webbrowser.open(update['url'])
            
            banner = create_update_banner(update['version'], open_release_page)
            
            # Remove existing banner if any
            for control in page.controls[:]:
                if isinstance(control, ft.Container) and hasattr(control, 'content'):
                    if isinstance(control.content, ft.Row):
                        for item in control.content.controls:
                            if isinstance(item, ft.Icon) and item.name == ft.Icons.UPDATE:
                                page.controls.remove(control)
                                break
            
            page.controls.insert(0, banner)
            page.update()
            
            if force:
                set_status(f"Update available: v{update['version']}", ACCENT)
        else:
            log("You're using the latest version")
            if force:
                set_status("No updates available", TEXT_SEC)
    
    # Store reference for manual check button
    manual_update_check.checker_func = check_updates

    
    threading.Thread(target=check_updates, daemon=True).start()
    
    # Load saved settings
    saved = settings_mgr.load()
    if saved:
        apply_saved_settings(saved)
        page.update()
    
    # Lock file handling
    def on_window_close(e):
        """Cleanup on exit."""
        try:
            release_lock(LOCK_FILE)
            if not state.queue:
                queue_mgr.clear()
        except Exception:
            pass
    
    page.on_disconnect = on_window_close
    
    # Acquire lock
    if not acquire_lock(LOCK_FILE):
        log("⚠ Another instance of Yard is already running")
        set_status("Warning: Multiple instances detected", YELLOW)
        page.update()
    
    # Load queue
    state.queue = queue_mgr.load()
    if state.queue:
        update_queue_display()
        log(f"📋 Restored {len(state.queue)} queued items")
    
    # Auto-paste on startup
    try:
        import pyperclip
        import os
        clip = pyperclip.paste()
        if clip and clip.startswith("http"):
            url_input.value = clip
            page.update()
    except Exception:
        pass


if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
