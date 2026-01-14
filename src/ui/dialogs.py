"""Dialog components."""

import flet as ft
from core.constants import (
    TEXT, TEXT_SEC, TEXT_DIM, BG_SUBTLE, BG_CONTROL, ACCENT
)


def create_about_dialog(page, version):
    """Create and show the about dialog."""
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
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_color=TEXT_SEC,
                        on_click=close_sheet
                    ),
                ]),
                # App info
                ft.Text("Yard", size=22, weight=ft.FontWeight.BOLD, color=TEXT),
                ft.Text(
                    f"Version {version} · Yet Another yt-dlp",
                    size=11,
                    color=TEXT_DIM
                ),
                ft.Container(height=12),
                # Two columns
                ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                "BUILT WITH",
                                size=9,
                                color=TEXT_DIM,
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.Text("Flet · yt-dlp · FFmpeg", size=10, color=TEXT_SEC),
                        ], spacing=4),
                        bgcolor=BG_CONTROL,
                        border_radius=6,
                        padding=10,
                        expand=True,
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                "AUTHOR",
                                size=9,
                                color=TEXT_DIM,
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.Row([
                                ft.Text("Razik", size=10, color=TEXT),
                                ft.TextButton(
                                    "GitHub",
                                    style=ft.ButtonStyle(color=ACCENT, padding=0),
                                    on_click=lambda e: page.launch_url(
                                        "https://github.com/razikdontcare"
                                    ),
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
