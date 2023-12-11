from plyer import notification

# Set the title and message for the notification
title = "emergency Alert"
message = "Patient is critical."

# Display the notification
notification.notify(
    title=title,
    message=message,
    app_name="YourApp",  # Optional, specify the name of your application
    timeout=20,  # Optional, specify how long the notification should be visible (in seconds)
)
