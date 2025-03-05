# ====== Code Summary ======
# This script sets up a WebSocket client using `ws_comms` with logging
# capabilities from `loggerplusplus`. It defines a background task
# that continuously sends messages to the WebSocket server at 1-second intervals.
# The WebSocket client connects to `localhost:8080` and communicates over the `/test_route`.

# ====== Logger Configuration ======
from loggerplusplus import LoggerManager, LoggerConfig, Logger

LoggerManager.enable_dynamic_config_update = True
LoggerManager.enable_unique_logger_identifier = True

LoggerManager.global_config = LoggerConfig.from_kwargs(
    # Loggers Output
    write_to_file=False,
    # Monitoring
    display_monitoring=False,
    files_monitoring=False,
    # Placement
    filename_lineno_max_width=18,
)
# ====== Standard Library Imports ======
import asyncio

# ====== Internal Project Imports ======
from ws_comms import WSclient, WSclientRouteManager, WSender, WSreceiver, WSmsg


# ====== Background Task Definition ======
async def send_message_to_server(ws_route_manager: WSclientRouteManager, logger: Logger):
    """
    Periodically sends a message to the WebSocket server.

    Args:
        ws_route_manager (WSclientRouteManager): The WebSocket client route manager to send messages through.
        logger (Logger): Logger instance for logging messages.
    """
    while True:
        await ws_route_manager.sender.send(WSmsg(msg="welcome", data="Hello from client"))
        logger.info("Message sent to server")
        await asyncio.sleep(1)


# ====== Main Execution ======
if __name__ == "__main__":
    # Initialize WebSocket client
    ws_client = WSclient(
        host="localhost",
        port=8080,
    )

    # Define WebSocket route
    ws_cmd = WSclientRouteManager(
        receiver=WSreceiver(use_queue=True),
        sender=WSender(name="default_sender")
    )

    ws_client.add_route_handler("/test_route", ws_cmd)

    # Create a logger for background task
    task_logger: Logger = Logger(identifier="send_message_to_server", follow_logger_manager_rules=True)

    # Register background task to send messages periodically
    ws_client.add_background_task(
        send_message_to_server,
        ws_cmd,
        task_logger
    )

    # Start the WebSocket client
    ws_client.run()
