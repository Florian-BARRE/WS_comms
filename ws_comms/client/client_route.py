# ====== Imports ======
# Standard Library Imports
import aiohttp
import asyncio

# Third-party library imports
from loggerplusplus import Logger

# Internal project imports
from ws_comms.receiver import WSreceiver
from ws_comms.sender import WSender


# ====== Class Part ======
class WSclientRouteManager:
    """
    This class is used to manage a route. It is used to manage a route by establishing
    the client-server connection, listening server message, sending message to the server.
    Sending and listening are managed by a receiver and a sender object.
    * Its routine has to be given at the route creation.
    """

    def __init__(
            self,
            receiver: WSreceiver,
            sender: WSender,
            logger: Logger = Logger(identifier="WSclientRouteManager", follow_logger_manager_rules=True)
    ) -> None:
        self.logger: Logger = logger
        self.receiver: WSreceiver = receiver
        self.sender: WSender = sender

        self.__ws: aiohttp.ClientWebSocketResponse | None = None

        self.logger.info(f"Initialized")

    def set_ws(self, ws: aiohttp.ClientWebSocketResponse) -> None:
        self.__ws: aiohttp.ClientWebSocketResponse = ws
        self.sender.update_clients(ws)

    async def get_ws(self, skip_set=False) -> aiohttp.ClientWebSocketResponse | None:
        # Wait until the ws is connected
        while self.__ws is None and not skip_set:
            await asyncio.sleep(0.5)
        return self.__ws

    async def routine(self) -> None:
        """
        Routine to handle a connection on a specific route.
        * It is used to listen to the server messages.
        """
        try:
            async for msg in self.__ws:
                await self.receiver.routine(msg)

        except Exception as error:
            self.logger.error(f"Error during connection handling: {error}")

        finally:
            self.logger.info("Connection closed")
