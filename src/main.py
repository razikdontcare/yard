import flet as ft
import yt_dlp
import imageio_ffmpeg
import os
import threading
import json
import subprocess
import glob

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), '.yard_settings.json')
APP_VERSION = "1.0.3"

def main(page: ft.Page):
    page.title = "Yard"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 800
    page.window.height = 600
    page.window.resizable = False
    page.window.maximizable = False
    page.padding = 0
    page.bgcolor = "#1c1c1c"

    # --- Colors ---
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

    # --- State ---
    class State:
        is_cancelled = False
        current_filename = None
        downloading = False
        queue = []  # Download queue
        last_download_path = None
    
    state = State()

    # --- Settings Persistence ---
    def load_settings():
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {}

    def save_settings():
        settings = {
            'audio_only': audio_cb.value,
            'playlist': playlist_cb.value,
            'compat': compat_cb.value,
            'quality': quality_dd.value,
            'format': format_dd.value,
            'folder': folder_path.value,
        }
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f)
        except:
            pass

    def apply_settings(settings):
        if settings.get('audio_only'):
            audio_cb.value = True
            format_dd.options = [ft.dropdown.Option("MP3"), ft.dropdown.Option("M4A"), ft.dropdown.Option("WAV")]
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

    # --- Helpers ---
    def log(msg):
        log_area.value = (log_area.value or "") + f"{msg}\n"
        page.update()

    def set_status(text, color=TEXT_SEC):
        status.value = text
        status.color = color
        page.update()

    def show_notification(title, message):
        """Show system notification"""
        try:
            from plyer import notification
            notification.notify(
                title=title,
                message=message,
                app_name="Yard",
                timeout=5
            )
        except:
            pass  # Notification not available



    def open_folder(path=None):
        """Open the download folder in file explorer"""
        folder = path or state.last_download_path or folder_path.value
        if os.path.exists(folder):
            if os.name == 'nt':  # Windows
                subprocess.Popen(['explorer', os.path.normpath(folder)])
            else:
                subprocess.run(['xdg-open', folder])

    def update_queue_display():
        """Update queue list UI"""
        queue_count.value = f"Queue: {len(state.queue)}"
        queue_count.visible = len(state.queue) > 0
        
        # Update queue list
        queue_list.controls.clear()
        for i, url in enumerate(state.queue):
            # Truncate URL for display
            display_url = url[:45] + "..." if len(url) > 48 else url
            queue_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(f"{i+1}.", size=11, color=TEXT_DIM, width=20),
                        ft.Text(display_url, size=11, color=TEXT_SEC, expand=True),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            icon_size=14,
                            icon_color=RED,
                            tooltip="Remove",
                            on_click=lambda e, idx=i: remove_from_queue(idx),
                        ),
                    ], spacing=4),
                    padding=ft.padding.symmetric(vertical=2),
                )
            )
        
        queue_section.visible = len(state.queue) > 0
        page.update()

    def remove_from_queue(index):
        """Remove item from queue by index"""
        if 0 <= index < len(state.queue):
            state.queue.pop(index)
            update_queue_display()
            set_status(f"Removed from queue ({len(state.queue)} remaining)", TEXT_SEC)

    def clear_queue(e):
        """Clear all items from queue"""
        state.queue.clear()
        update_queue_display()
        set_status("Queue cleared", TEXT_SEC)



    # --- Progress Hook ---
    def progress_hook(d):
        if state.is_cancelled:
            raise Exception("Download cancelled by user.")
            
        if d['status'] == 'downloading':
            state.current_filename = d.get('filename')
            try:
                pct = d.get('_percent_str', '0%').replace('%', '').strip()
                progress.value = float(pct) / 100
                
                speed = d.get('_speed_str', '').strip()
                eta = d.get('_eta_str', '').strip()
                
                msg = f"{d.get('_percent_str', '').strip()}"
                if speed: msg += f" · {speed}"
                if eta: msg += f" · {eta}"
                set_status(msg, TEXT)
            except:
                pass
        elif d['status'] == 'finished':
            progress.value = 1
            set_status("Download complete, processing...", TEXT_SEC)
            log("Download finished, converting to constant framerate...")

    # --- Post-Processor Hook ---
    def postprocessor_hook(d):
        """Track post-processing progress"""
        if d['status'] == 'started':
            postprocessor_name = d.get('postprocessor', 'Unknown')
            log(f"Post-processing: {postprocessor_name}")
            set_status("Converting to editor-compatible format...", TEXT_SEC)
        elif d['status'] == 'processing':
            info = d.get('info_dict', {})
            filename = info.get('filepath', 'video')
            if filename:
                basename = os.path.basename(filename)
                log(f"Re-encoding: {basename[:50]}...")
                set_status("Re-encoding video (VFR → CFR)...", TEXT_SEC)
        elif d['status'] == 'finished':
            log("✓ Post-processing complete")
            set_status("Video optimized for editing", GREEN)

    # --- Download Logic ---
    def do_download(url, audio, quality, fmt, playlist, compat, path):
        state.is_cancelled = False
        state.downloading = True
        state.last_download_path = path
        os.makedirs(path, exist_ok=True)

        try:
            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
            log("FFmpeg ready")
            
            if audio:
                fstr = 'bestaudio/best'
            elif quality == "Best":
                fstr = 'bestvideo+bestaudio[ext=m4a]/bestvideo+bestaudio/best'
            else:
                h = quality.replace('p', '')
                fstr = f'bestvideo[height<={h}]+bestaudio[ext=m4a]/bestvideo[height<={h}]+bestaudio/best[height<={h}]'

            opts = {
                'ffmpeg_location': ffmpeg,
                'progress_hooks': [progress_hook],
                'postprocessor_hooks': [postprocessor_hook],
                'outtmpl': '%(title)s.%(ext)s',
                'format': fstr,
                'noplaylist': not playlist,
                'quiet': True,
                'no_warnings': True,
                'paths': {'home': path}
            }
            
            if audio:
                opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': fmt.lower(), 'preferredquality': '192'}]
            else:
                opts['merge_output_format'] = fmt.lower()
                
                # Conditionally add post-processing for compatibility mode
                if compat:
                    log("Compatibility mode enabled - converting to CFR")
                    opts['postprocessors'] = [{
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': fmt.lower(),
                    }]
                    # Note: vsync cfr converts VFR->CFR while preserving original framerate
                    opts['postprocessor_args'] = [
                        '-c:v', 'libx264',           # H.264 codec
                        '-preset', 'medium',          # Encoding speed/quality balance
                        '-crf', '18',                 # High quality
                        '-vsync', 'cfr',              # Convert to constant framerate
                        '-c:a', 'aac',                # AAC audio codec
                        '-b:a', '192k',               # Audio bitrate
                        '-movflags', '+faststart'     # Enable streaming
                    ]
                else:
                    log("Using original format (may contain variable framerate)")

            deno = os.path.join(os.getcwd(), 'src', 'bin', 'deno.exe')
            if os.path.exists(deno):
                subprocess.run([deno, '--version'], capture_output=True, check=False)
                opts['js_runtimes'] = {'deno': {'args': [deno]}}

            log("Downloading...")
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'video')
                log(f"✓ {title[:60]}")
            
            progress.color = GREEN
            set_status(f"✓ {title[:40]}...", GREEN)
            open_folder_btn.visible = True
            
            # System notification
            show_notification("Download Complete", f"{title[:50]}")
            
            # Save settings on successful download
            save_settings()
            
        except Exception as e:
            if "cancelled" in str(e).lower():
                log("Cancelled")
                set_status("Cancelled", YELLOW)
                progress.color = YELLOW
                # Clean up .part files
                try:
                    for part_file in glob.glob(os.path.join(path, '*.part')):
                        os.remove(part_file)
                except:
                    pass
            else:
                log(f"Error: {e}")
                progress.color = RED
                set_status("Failed", RED)
        
        state.downloading = False
        
        # Process queue
        if state.queue:
            next_url = state.queue.pop(0)
            update_queue_display()
            url_input.value = next_url
            page.update()
            start_download()
        else:
            dl_btn.text = "Download"
            dl_btn.icon = ft.Icons.DOWNLOAD
            dl_btn.bgcolor = ACCENT
            page.update()

    def start_download():
        url = url_input.value.strip()
        if not url:
            set_status("Enter a URL", YELLOW)
            return
        
        if state.downloading:
            state.is_cancelled = True
            set_status("Cancelling...", YELLOW)
            return
        
        progress.value = 0
        progress.color = ACCENT
        open_folder_btn.visible = False
        set_status("Starting...", TEXT_SEC)
        
        dl_btn.text = "Cancel"
        dl_btn.icon = ft.Icons.CLOSE
        dl_btn.bgcolor = RED
        page.update()
        
        threading.Thread(
            target=do_download,
            args=(url, audio_cb.value, quality_dd.value, format_dd.value, playlist_cb.value, compat_cb.value, folder_path.value),
            daemon=True
        ).start()

    def on_download(e):
        start_download()

    def on_url_submit(e):
        """Handle Enter key in URL field"""
        start_download()



    def on_paste(e):
        """Paste from clipboard"""
        try:
            import pyperclip
            clip = pyperclip.paste()
            if clip:
                url_input.value = clip
                page.update()
        except:
            pass

    def on_add_to_queue(e):
        """Add current URL to queue"""
        url = url_input.value.strip()
        if url and url.startswith('http'):
            state.queue.append(url)
            update_queue_display()
            url_input.value = ""
            set_status(f"Added to queue ({len(state.queue)} pending)", ACCENT)
            page.update()
            
            # Auto-start queue if nothing is currently downloading
            if not state.downloading:
                start_download()

    def on_audio_change(e):
        if audio_cb.value:
            format_dd.options = [ft.dropdown.Option("MP3"), ft.dropdown.Option("M4A"), ft.dropdown.Option("WAV")]
            format_dd.value = "MP3"
            quality_dd.disabled = True
        else:
            format_dd.options = [ft.dropdown.Option("MP4"), ft.dropdown.Option("MKV"), ft.dropdown.Option("WEBM")]
            format_dd.value = "MP4"
            quality_dd.disabled = False
        page.update()

    def on_folder(e):
        if e.path:
            folder_path.value = e.path
            folder_display.value = e.path
            page.update()

    def show_about(e):
        """Show about dialog"""
        def close_sheet(e):
            about_sheet.open = False
            page.update()
        
        about_sheet = ft.BottomSheet(
            content=ft.Container(
                content=ft.Column([
                    # Header
                    ft.Row([
                        ft.Text("About", size=16, weight=ft.FontWeight.W_600, color=TEXT),
                        ft.Container(expand=True),
                        ft.IconButton(icon=ft.Icons.CLOSE, icon_color=TEXT_SEC, on_click=close_sheet),
                    ]),
                    # App info
                    ft.Text("Yard", size=22, weight=ft.FontWeight.BOLD, color=TEXT),
                    ft.Text(f"Version {APP_VERSION} · Yet Another yt-dlp", size=11, color=TEXT_DIM),
                    ft.Container(height=12),
                    # Two columns
                    ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Text("BUILT WITH", size=9, color=TEXT_DIM, weight=ft.FontWeight.BOLD),
                                ft.Text("Flet · yt-dlp · FFmpeg", size=10, color=TEXT_SEC),
                            ], spacing=4),
                            bgcolor=BG_CONTROL,
                            border_radius=6,
                            padding=10,
                            expand=True,
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Text("AUTHOR", size=9, color=TEXT_DIM, weight=ft.FontWeight.BOLD),
                                ft.Row([
                                    ft.Text("Razik", size=10, color=TEXT),
                                    ft.TextButton(
                                        "GitHub",
                                        style=ft.ButtonStyle(color=ACCENT, padding=0),
                                        on_click=lambda e: page.launch_url("https://github.com/razikdontcare"),
                                    ),
                                ], spacing=4),
                            ], spacing=4),
                            bgcolor=BG_CONTROL,
                            border_radius=6,
                            padding=10,
                            expand=True,
                        ),
                    ], spacing=8),
                    ft.Container(height=8),
                    ft.Text("© 2025 Yard", size=9, color=TEXT_DIM),
                ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=BG_SUBTLE,
                padding=16,
                border_radius=ft.border_radius.only(top_left=12, top_right=12),
            ),
        )
        page.open(about_sheet)

    picker = ft.FilePicker(on_result=on_folder)
    page.overlay.append(picker)

    # ==================== UI ====================

    # --- Left Panel ---
    url_input = ft.TextField(
        hint_text="Paste video URL",
        hint_style=ft.TextStyle(color=TEXT_DIM),
        bgcolor=BG_CONTROL,
        border_color=BORDER,
        focused_border_color=ACCENT,
        border_radius=6,
        text_size=14,
        color=TEXT,
        expand=True,
        content_padding=ft.padding.symmetric(horizontal=14, vertical=12),
        on_submit=on_url_submit,
    )

    paste_btn = ft.IconButton(
        icon=ft.Icons.CONTENT_PASTE,
        icon_color=TEXT_SEC,
        tooltip="Paste",
        on_click=on_paste,
    )

    add_queue_btn = ft.IconButton(
        icon=ft.Icons.ADD_TO_QUEUE,
        icon_color=ACCENT,
        tooltip="Add to queue",
        on_click=on_add_to_queue,
    )

    dl_btn = ft.ElevatedButton(
        text="Download",
        icon=ft.Icons.DOWNLOAD,
        bgcolor=ACCENT,
        color=TEXT,
        height=46,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
        on_click=on_download,
    )



    # Progress
    progress = ft.ProgressBar(value=0, color=ACCENT, bgcolor=BG_CONTROL, height=8)
    status = ft.Text("Ready", size=13, color=TEXT_SEC)
    queue_count = ft.Text("", size=11, color=ACCENT, visible=False)
    
    open_folder_btn = ft.TextButton(
        "Open folder",
        icon=ft.Icons.FOLDER_OPEN,
        style=ft.ButtonStyle(color=ACCENT),
        visible=False,
        on_click=lambda e: open_folder(),
    )



    # Log area
    log_area = ft.TextField(
        multiline=True,
        read_only=True,
        min_lines=4,
        max_lines=4,
        text_size=11,
        color=TEXT_SEC,
        bgcolor=BG_SUBTLE,
        border_color=BORDER,
        border_radius=6,
    )

    info_btn = ft.IconButton(
        icon=ft.Icons.INFO_OUTLINE,
        icon_color=TEXT_DIM,
        tooltip="About",
        on_click=show_about,
    )

    left_panel = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text("Yard", size=24, weight=ft.FontWeight.BOLD, color=TEXT),
                    ft.Text("Video Downloader", size=12, color=TEXT_DIM),
                ], spacing=2),
                ft.Container(expand=True),
                info_btn,
            ]),
            ft.Container(height=20),
            ft.Row([url_input, paste_btn, add_queue_btn, dl_btn], spacing=8),
            ft.Container(height=16),
            progress,
            ft.Container(height=8),
            ft.Row([status, ft.Container(expand=True), queue_count, open_folder_btn]),
            ft.Container(height=20),
            ft.Text("Log", size=12, color=TEXT_DIM),
            ft.Container(height=6),
            log_area,
        ]),
        padding=28,
        expand=True,
    )

    # Queue section (shown when queue has items)
    queue_list = ft.Column([], spacing=0)
    
    queue_section = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("Download Queue", size=14, weight=ft.FontWeight.W_600, color=TEXT),
                ft.Container(expand=True),
                ft.TextButton("Clear all", style=ft.ButtonStyle(color=RED), on_click=clear_queue),
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

    # --- Right Panel ---
    audio_cb = ft.Checkbox(label="Audio only", value=False, fill_color=ACCENT, on_change=on_audio_change)
    playlist_cb = ft.Checkbox(label="Download playlist", value=False, fill_color=ACCENT)
    compat_cb = ft.Checkbox(label="Compatibility mode", value=True, fill_color=ACCENT, tooltip="Convert to constant framerate (CFR) for video editors")

    quality_dd = ft.Dropdown(
        label="Quality",
        value="Best",
        width=140,
        bgcolor=BG_CONTROL,
        border_color=BORDER,
        focused_border_color=ACCENT,
        border_radius=6,
        text_size=13,
        color=TEXT,
        options=[ft.dropdown.Option("Best"), ft.dropdown.Option("1080p"), ft.dropdown.Option("720p"), ft.dropdown.Option("480p")],
    )
    
    format_dd = ft.Dropdown(
        label="Format",
        value="MP4",
        width=140,
        bgcolor=BG_CONTROL,
        border_color=BORDER,
        focused_border_color=ACCENT,
        border_radius=6,
        text_size=13,
        color=TEXT,
        options=[ft.dropdown.Option("MP4"), ft.dropdown.Option("MKV"), ft.dropdown.Option("WEBM")],
    )

    folder_path = ft.TextField(value=os.path.join(os.getcwd(), 'yard'), visible=False)
    folder_display = ft.TextField(
        value=os.path.join(os.getcwd(), 'yard'),
        label="Save to",
        read_only=True,
        bgcolor=BG_CONTROL,
        border_color=BORDER,
        border_radius=6,
        text_size=12,
        color=TEXT_SEC,
        expand=True,
    )
    
    folder_btn = ft.IconButton(
        icon=ft.Icons.FOLDER_OPEN,
        icon_color=ACCENT,
        bgcolor=BG_CONTROL,
        on_click=lambda _: picker.get_directory_path(),
    )

    # Keyboard shortcuts info
    shortcuts_info = ft.Container(
        content=ft.Column([
            ft.Text("Shortcuts", size=12, color=TEXT_DIM),
            ft.Container(height=6),
            ft.Text("Enter → Download", size=11, color=TEXT_DIM),
            ft.Text("Paste → Auto-fills URL", size=11, color=TEXT_DIM),
        ]),
        padding=ft.padding.only(top=20),
    )

    right_panel = ft.Container(
        content=ft.Column([
            ft.Text("Settings", size=16, weight=ft.FontWeight.W_600, color=TEXT),
            ft.Container(height=20),
            audio_cb,
            ft.Container(height=8),
            playlist_cb,
            ft.Container(height=8),
            compat_cb,
            ft.Container(height=20),
            quality_dd,
            ft.Container(height=12),
            format_dd,
            ft.Container(height=20),
            ft.Row([folder_display, folder_btn], spacing=8),
            shortcuts_info,
        ]),
        bgcolor=BG_SUBTLE,
        padding=24,
        width=260,
    )

    # ==================== LAYOUT ====================
    page.add(
        ft.Row([
            ft.Column([
                left_panel,
                queue_section,
            ], expand=True, spacing=0),
            ft.VerticalDivider(width=1, color=BORDER),
            right_panel,
        ], expand=True, spacing=0)
    )

    # Load saved settings
    saved = load_settings()
    if saved:
        apply_settings(saved)
        page.update()

    # Auto-paste on startup
    try:
        import pyperclip
        clip = pyperclip.paste()
        if clip and clip.startswith("http"):
            url_input.value = clip
            page.update()
    except:
        pass

if __name__ == "__main__":
    ft.app(target=main)
