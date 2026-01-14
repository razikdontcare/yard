"""System notification utilities."""


def show_notification(title, message):
    """
    Show system notification.
    
    Args:
        title: Notification title
        message: Notification message
    """
    try:
        from plyer import notification
        notification.notify(
            title=title,
            message=message,
            app_name="Yard",
            timeout=5
        )
    except Exception:
        pass  # Notification not available
