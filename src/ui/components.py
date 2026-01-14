"""Reusable UI component factory functions."""

import flet as ft
from core.constants import (
    BG_CONTROL, BORDER, ACCENT, TEXT, TEXT_DIM, TEXT_SEC,
    RED, GREEN, YELLOW, BG_SUBTLE
)


def create_url_input(on_submit):
    """Create URL input field."""
    return ft.TextField(
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
        on_submit=on_submit,
    )


def create_paste_button(on_click):
    """Create paste button."""
    return ft.IconButton(
        icon=ft.Icons.CONTENT_PASTE,
        icon_color=TEXT_SEC,
        tooltip="Paste",
        on_click=on_click,
    )


def create_add_queue_button(on_click):
    """Create add to queue button."""
    return ft.IconButton(
        icon=ft.Icons.ADD_TO_QUEUE,
        icon_color=ACCENT,
        tooltip="Add to queue",
        on_click=on_click,
    )


def create_download_button(on_click):
    """Create download button."""
    return ft.ElevatedButton(
        text="Download",
        icon=ft.Icons.DOWNLOAD,
        bgcolor=ACCENT,
        color=TEXT,
        height=46,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
        on_click=on_click,
    )


def create_progress_bar():
    """Create progress bar."""
    return ft.ProgressBar(value=0, color=ACCENT, bgcolor=BG_CONTROL, height=8)


def create_status_text():
    """Create status text."""
    return ft.Text("Ready", size=13, color=TEXT_SEC)


def create_queue_count_text():
    """Create queue count text."""
    return ft.Text("", size=11, color=ACCENT, visible=False)


def create_open_folder_button(on_click):
    """Create open folder button."""
    return ft.TextButton(
        "Open folder",
        icon=ft.Icons.FOLDER_OPEN,
        style=ft.ButtonStyle(color=ACCENT),
        visible=False,
        on_click=on_click,
    )


def create_log_area():
    """Create log text area."""
    return ft.TextField(
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


def create_audio_checkbox(on_change):
    """Create audio only checkbox."""
    return ft.Checkbox(
        label="Audio only",
        value=False,
        fill_color=ACCENT,
        on_change=on_change
    )


def create_playlist_checkbox():
    """Create playlist checkbox."""
    return ft.Checkbox(
        label="Download playlist",
        value=False,
        fill_color=ACCENT
    )


def create_compat_checkbox():
    """Create compatibility mode checkbox."""
    return ft.Checkbox(
        label="Compatibility mode",
        value=True,
        fill_color=ACCENT,
        tooltip="Convert to constant framerate (CFR) for video editors"
    )


def create_quality_dropdown():
    """Create quality dropdown."""
    return ft.Dropdown(
        label="Quality",
        value="Best",
        width=140,
        bgcolor=BG_CONTROL,
        border_color=BORDER,
        focused_border_color=ACCENT,
        border_radius=6,
        text_size=13,
        color=TEXT,
        options=[
            ft.dropdown.Option("Best"),
            ft.dropdown.Option("1080p"),
            ft.dropdown.Option("720p"),
            ft.dropdown.Option("480p")
        ],
    )


def create_format_dropdown():
    """Create format dropdown."""
    return ft.Dropdown(
        label="Format",
        value="MP4",
        width=140,
        bgcolor=BG_CONTROL,
        border_color=BORDER,
        focused_border_color=ACCENT,
        border_radius=6,
        text_size=13,
        color=TEXT,
        options=[
            ft.dropdown.Option("MP4"),
            ft.dropdown.Option("MKV"),
            ft.dropdown.Option("WEBM")
        ],
    )


def create_folder_display(default_folder):
    """Create folder display field."""
    return ft.TextField(
        value=default_folder,
        label="Save to",
        read_only=True,
        bgcolor=BG_CONTROL,
        border_color=BORDER,
        border_radius=6,
        text_size=12,
        color=TEXT_SEC,
        expand=True,
    )


def create_folder_button(on_click):
    """Create folder selection button."""
    return ft.IconButton(
        icon=ft.Icons.FOLDER_OPEN,
        icon_color=ACCENT,
        bgcolor=BG_CONTROL,
        on_click=on_click,
    )


def create_queue_item(index, url, settings, on_remove):
    """Create a queue list item."""
    # Truncate URL for display
    display_url = url[:40] + "..." if len(url) > 43 else url
    
    # Format indicator
    format_icon = "🎵" if settings.get('audio') else "🎬"
    
    return ft.Container(
        content=ft.Row([
            ft.Text(f"{index+1}.", size=11, color=TEXT_DIM, width=20),
            ft.Text(format_icon, size=11, width=20),
            ft.Text(display_url, size=11, color=TEXT_SEC, expand=True),
            ft.IconButton(
                icon=ft.Icons.CLOSE,
                icon_size=14,
                icon_color=RED,
                tooltip="Remove",
                on_click=on_remove,
            ),
        ], spacing=4),
        padding=ft.padding.symmetric(vertical=2),
    )


def create_info_button(on_click):
    """Create info/about button."""
    return ft.IconButton(
        icon=ft.Icons.INFO_OUTLINE,
        icon_color=TEXT_DIM,
        tooltip="About",
        on_click=on_click,
    )


def create_shortcuts_info():
    """Create keyboard shortcuts info."""
    return ft.Container(
        content=ft.Column([
            ft.Text("Shortcuts", size=12, color=TEXT_DIM),
            ft.Container(height=6),
            ft.Text("Enter → Download", size=11, color=TEXT_DIM),
            ft.Text("Paste → Auto-fills URL", size=11, color=TEXT_DIM),
        ]),
        padding=ft.padding.only(top=20),
    )


def create_update_banner(latest_version, on_click):
    """Create update notification banner."""
    return ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.UPDATE, color=ACCENT, size=20),
            ft.Text(
                f"New version {latest_version} available!",
                size=13,
                color=TEXT,
                weight=ft.FontWeight.W_500
            ),
            ft.TextButton(
                "Download Update",
                on_click=on_click,
                style=ft.ButtonStyle(color=ACCENT)
            ),
        ], spacing=12, alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=BG_SUBTLE,
        padding=8,
        border=ft.border.only(bottom=ft.border.BorderSide(1, BORDER)),
    )


def create_cookies_file_display(default_value="No cookies file"):
    """Create cookies file display field."""
    return ft.TextField(
        value=default_value,
        label="Cookies file (optional)",
        read_only=True,
        bgcolor=BG_CONTROL,
        border_color=BORDER,
        border_radius=6,
        text_size=11,
        color=TEXT_SEC,
        expand=True,
        hint_text="Select cookies.txt file",
    )


def create_cookies_button(on_click):
    """Create cookies file selection button."""
    return ft.IconButton(
        icon=ft.Icons.COOKIE,
        icon_color=ACCENT,
        bgcolor=BG_CONTROL,
        tooltip="Select cookies.txt file",
        on_click=on_click,
    )


def create_clear_cookies_button(on_click):
    """Create clear cookies button."""
    return ft.IconButton(
        icon=ft.Icons.CLEAR,
        icon_color=RED,
        icon_size=16,
        tooltip="Clear cookies file",
        on_click=on_click,
    )


def create_custom_args_input():
    """Create custom arguments input field."""
    return ft.TextField(
        label="Custom yt-dlp arguments",
        hint_text="e.g., --geo-bypass --max-downloads 5",
        hint_style=ft.TextStyle(color=TEXT_DIM, size=10),
        bgcolor=BG_CONTROL,
        border_color=BORDER,
        focused_border_color=ACCENT,
        border_radius=6,
        text_size=11,
        color=TEXT,
        multiline=False,
        max_lines=1,
    )

