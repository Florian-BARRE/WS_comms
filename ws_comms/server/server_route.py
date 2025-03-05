# ====== Imports ======
# Standard Library Imports
import aiohttp

# Third-party library imports
from loggerplusplus import Logger

# Internal project imports
from ws_comms.receiver import WSreceiver
from ws_comms.sender import WSender


# ====== Class Part ======
class WServerRouteManager:
    """
    this class is used to manage a route. It is used to handle new connections and to manage the clients list.
    It is also composed by a receiver and a sender, which can be used to manage the messages (send or receive).
    * Its routine has to be given at the route creation.
    """

    def __init__(
            self,
            receiver: WSreceiver,
            sender: WSender,
            only_unique_client_name: bool = False,
            logger: Logger = Logger(identifier="WServerRouteManager", follow_logger_manager_rules=True)
    ) -> None:
        self.logger: Logger = logger
        self.receiver: WSreceiver = receiver
        self.sender: WSender = sender
        self.only_unique_client_name: bool = only_unique_client_name

        # Clients set format:
        # {
        #   "client_name": [client_ws_connection, ...]
        # }
        self.clients: dict[str:list[aiohttp.web_ws.WebSocketResponse]] = {}
        self.logger.info(f"Initialized with only_unique_client_name: {self.only_unique_client_name}")

    def add_client(
            self,
            request: aiohttp.web_request.Request,
            client: aiohttp.web_ws.WebSocketResponse,
    ) -> str:
        """
        Add a new client in the router handler list.
        :param request:
        :param client:
        :return:
        """
        # Use get URL value instead
        client_name = request.query.get("sender")

        # Check source validity
        if client_name is None:
            self.logger.error("New client does not have a sender value in url parameter. CONNECTION REFUSED.")
            raise ValueError(
                "New client does not have a sender value in url parameter. CONNECTION REFUSED."
            )

        if self.only_unique_client_name:
            # Check if the client name already exists
            if self.clients.get(client_name, None) is not None:
                self.logger.error(f"Client with name [{client_name}] already exists. CONNECTION REFUSED.")
                raise ValueError(
                    f"Client with name [{client_name}] already exists. CONNECTION REFUSED."
                )

        # Check if the client name already exists, if not create empty list
        if self.clients.get(client_name, None) is None:
            self.clients[client_name] = []

        # Add the new client associated to the source value
        self.clients[client_name].append(client)

        self.logger.debug(f"New client added: {client_name}")
        return client_name

    def get_client(self, name: str) -> list[aiohttp.web_ws.WebSocketResponse]:
        """
        Get a client by its source value (its name).
        :param name:
        :return: list of clients associated to the source name
        """
        if self.clients.get(name) is None:
            self.logger.warning(f"Client with source [{name}] does not exist.")

        clients: list[aiohttp.web_ws.WebSocketResponse] = self.clients.get(name, [])
        self.logger.debug(f"Clients found with name [{name}]: {len({clients})}")
        return clients

    def get_all_clients(self):
        # Concatenate all clients in a list
        return [item for sublist in list(self.clients.values()) for item in sublist]

    def remove_client(self, name: str, client: aiohttp.web_ws.WebSocketResponse) -> None:
        """
        Remove a client from the router handler dict.
        :param name:
        :param client:
        :return:
        """
        if self.clients.get(name, None) is None:
            self.logger.warning(f"Client with source [{name}] does not exist.")
            return

        if client in self.clients[name]:
            self.clients[name].remove(client)
            self.logger.info(f"Client removed: {name}")
        else:
            self.logger.warning(f"Client not found in the list: {name}, it should be already removed.")

    async def close_all_connections(self):
        """
        Close all active WebSocket connections.
        """
        # Loop through all clients and close each WebSocket connection
        for client_name, client in self.get_all_clients():
            if not client.closed:
                await client.close()
            self.logger.info(f"Closed connection for {client_name}")
        self.clients.clear()

    async def routine(
            self, request: aiohttp.web_request.Request
    ) -> aiohttp.web_ws.WebSocketResponse | None:
        """
        Routine to handle new connections.
        * It supports multiple clients / new connections / disconnections.
        :param request:
        :return:
        """
        client = aiohttp.web.WebSocketResponse()
        await client.prepare(request)

        client_name = self.add_client(request, client)
        self.logger.info(f"New client connected: {client_name}")

        self.sender.update_clients(self.get_all_clients())
        try:
            async for msg in client:
                await self.receiver.routine(msg)

        except Exception as error:
            self.logger.error(f"Error during connection handling: {error}")

        finally:
            del self.clients[client_name]

            self.sender.update_clients(self.get_all_clients())
            self.logger.info(f"Client disconnected [{client_name}]")

        return client
