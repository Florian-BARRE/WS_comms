# ====== Imports ======
# Standard Library Imports
import aiohttp
import asyncio

# Third-party library imports
from loggerplusplus import Logger

# Internal project imports
from ws_comms.message import WSmsg


class WSender:
    """
    This class is used to send messages to clients.
    Every sent messages are marked with the source value of the sender (this machine name).
    """

    def __init__(
            self,
            name: str,
            logger: Logger = Logger(identifier="WSender", follow_logger_manager_rules=True)
    ) -> None:
        """
        Initialize the sender with its name value.
        This value is used to identify the sender.
        :param name:
        """
        self.logger: Logger = logger
        self.name: str = name
        self.__route_manager_clients: list = []

        self.logger.info(f"Initialized with name: {self.name}")

    def update_clients(
            self,
            clients
    ) -> None:
        if not isinstance(clients, list):
            self.__route_manager_clients: list = [clients]
        else:
            self.__route_manager_clients: list = clients
        self.logger.debug(f"Clients list updated: {self.__route_manager_clients}")

    async def get_clients(self, wait_clients: bool = False) -> list:
        while len(self.__route_manager_clients) == 0 and wait_clients:
            await asyncio.sleep(0.5)
            self.logger.debug("No clients ...")

        return self.__route_manager_clients

    async def send(
            self,
            msg: WSmsg,
            clients=None,
            wait_client: bool = False
    ) -> bool:
        """
        Send a message to one or multiple clients.
        :param msg:
        :param clients:
        :param wait_client:
        :return:
        """
        # Add the source value to the message
        msg.sender = self.name

        # By default send to attributes clients
        if clients is None:
            clients = await self.get_clients(wait_client)

        if clients is None:
            self.logger.warning("Can't send message: no clients found.")
            return False

        if not isinstance(clients, list):
            clients = [clients]

        for client in clients:
            try:
                await client.send_str(msg.prepare())
                self.logger.debug(f"Message sent: {msg}, to client: {client}")

            except Exception as error:
                self.logger.error(f"Error during sending message: {error}")
                return False

        self.logger.info(f"Message sent: {msg}, to {len(clients)} clients.")
        return True
