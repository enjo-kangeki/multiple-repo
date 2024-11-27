import base64
import functions_framework


@functions_framework.cloud_event
def function2(cloud_event):
    """Handle Pub/Sub messages."""
    pubsub_message = base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8")
    print("test")
    print(pubsub_message)
