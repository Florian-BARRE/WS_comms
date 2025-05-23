# ====== Imports ======
# Standard Library Imports
from aiohttp import web
import asyncio
import inspect
import signal
import time
import sys

# Third-party library imports
from loggerplusplus import Logger

# Internal project imports
from ws_comms.server.server_route import WServerRouteManager


# ====== Class Part ======
class WServer:
    """
    This class is websocket server. It is used to handle multiple routes.
    * This server can handle multiple routes.
    * It can handle multiple connections on the same route.
    * It can send messages to the clients.
    * It can receive messages from the clients.
    * It can  run background tasks in parallel with route listening.
    """

    def __init__(
            self,
            host: str,
            port: int,
            # ping_pong_clients_interval: int = None,
            logger: Logger = Logger(identifier="WServer", follow_logger_manager_rules=True)
    ) -> None:
        self.logger: Logger = logger

        self.__host: str = host
        self.__port: int = port

        # self.__ping_pong_clients_interval = ping_pong_clients_interval

        self._app = web.Application(debug=True)

        # Keep access on the route manager
        self.__route_managers: dict[str:WServerRouteManager] = {}
        # Keep access on the background tasks
        self.__background_tasks: set[asyncio.coroutine] = set()

        # Store all functions to call when the stop signal is received
        self.__shutdown_tasks: list[callable] = []

        self.logger.info(f"Initialized with host: {self.__host}, port: {self.__port}")

    # async def __ping_pong_clients_task(self, interval: int):
    #     while True:
    #         for route, manager in self.__route_managers.items():
    #             for client_name, client_ws_connection in manager.clients.items():
    #                 try:
    #                     await client_ws_connection.ping()
    #                     continue
    #                 except asyncio.TimeoutError:
    #                     self.__logger.log(
    #                         f"Pinging timeout [{client_name}] on route [{route}]. "
    #                         f"The client have been suddenly disconnected.",
    #                         LogLevels.WARNING,
    #                     )
    #                 except websockets.exceptions.ConnectionClosed:
    #                     self.__logger.log(
    #                         f"Connection closed [{client_name}] on route [{route}]. "
    #                         f"The client have been suddenly disconnected.",
    #                         LogLevels.WARNING,
    #                     )
    #                 except Exception as error:
    #                     self.__logger.log(
    #                         f"Error while pinging client [{client_name}] on route [{route}]. "
    #                         f"The client have been suddenly disconnected ({error})",
    #                         LogLevels.WARNING,
    #                     )
    #                 del manager.clients[client_name]
    #         await asyncio.sleep(interval)

    def add_route_handler(self, route: str, route_manager: WServerRouteManager) -> None:
        """
        Add a new route to the server.
            - route is the path of url to bind to the handler.
            - route_manager is an object that manage the connection with the client(s). It manages the client(s)
            list and allows to send and receive messages.
        :param route:
        :param route_manager:
        :return:
        """
        self.logger.info(f"New route handler added [{route}], route url: [ws://{self.__host}:{self.__port}{route}]")
        self.__route_managers[route] = route_manager
        self._app.router.add_get(route, route_manager.routine)

    def add_shutdown_task(self, task: callable) -> None:
        """
        Add a new shutdown task to the server. It is useful to execute task in parallel with the server.
        * The task have to be a coroutine (async function).
        * To create the task we add a key in the app dictionary with the name of the task.
        * The task will be created when the server will start.
        * Format: add_background_task(func, (optional) func_params, (optional) name)
        :param task:
        :return:
        """
        self.logger.debug(f"New shutdown task added [{task.__name__}]")
        self.__shutdown_tasks.append(task)

    async def stop_server(self):
        """
        Stop the server and all the background tasks.
        """
        self.logger.warning("Received exit signal...")

        # Close all the ws connections for all the routes
        self.logger.info("Closing all connections...")
        for route, manager in self.__route_managers.items():
            self.logger.debug(f"Closing all connections for [{route}] route.")
            await manager.close_all_connections()

        # Cancel all background tasks except the current one
        current_task = asyncio.current_task()
        tasks = [t for t in asyncio.all_tasks() if t is not current_task]
        self.logger.info(f"Cancelling {len(tasks)} background tasks...")

        for task in tasks:
            task.cancel()

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for task, result in zip(tasks, results):
            if isinstance(result, Exception) and not isinstance(result, asyncio.CancelledError):
                self.logger.warning(
                    f"Task {task.get_name() if hasattr(task, 'get_name') else str(task)} raised: {result}")

        # Execute shutdown hooks
        self.logger.info("Running shutdown tasks...")
        for shutdown_task in self.__shutdown_tasks:
            try:
                if inspect.iscoroutinefunction(shutdown_task):
                    await shutdown_task()
                else:
                    shutdown_task()
            except Exception as error:
                self.logger.error(
                    f"Error in shutdown task [{getattr(shutdown_task, '__name__', str(shutdown_task))}]: {error}")
            else:
                self.logger.debug(
                    f"Shutdown task [{getattr(shutdown_task, '__name__', str(shutdown_task))}] completed.")

        self.logger.info("Shutdown complete.")

    def add_background_task(
            self, task: callable, *args, name: str = "", **kwargs
    ) -> None:
        """
        Add a new background task to the server. It is useful to execute task in parallel with the server.
        * The task have to be a coroutine (async function).
        * To create the task we add a key in the app dictionary with the name of the task.
        * The task will be created when the server will start.
        * Format: add_background_task(func, (optional) func_params, (optional) name)
        :param task:
        :param args:
        :param name:
        :param kwargs:
        :return:
        """
        name = task.__name__ if name == "" else name

        async def background_task(app):
            task_instance = asyncio.create_task(task(*args, **kwargs))
            app[name] = task_instance
            self.__background_tasks.add(task_instance)

        self.logger.debug(f"New background task added [{name}]")
        self._app.on_startup.append(background_task)

    def run(self) -> None:
        loop = asyncio.get_event_loop()
        asyncio.set_event_loop(loop)  # Activate the loop

        async def handle_exit():
            self.logger.info("WServer stopped by user request.")
            await self.stop_server()
            loop.stop()

        async def wait_for_exit():
            try:
                while True:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                await handle_exit()

        # On Unix systems, we add a signal handler for SIGINT
        if sys.platform not in ["win32", "win64", "win", "windows"]:
            loop.add_signal_handler(signal.SIGINT, lambda: asyncio.create_task(handle_exit()))
        else:
            # On Windows, schedule the wait_for_exit task during application startup
            async def startup(app):
                app['wait_for_exit_task'] = asyncio.create_task(wait_for_exit())

            self._app.on_startup.append(startup)

        try:
            self.logger.info(f"WServer started, url: [ws://{self.__host}:{self.__port}]")
            # Ping pong mode does not work for now, if you want to use it,
            # you have to remove the non-unique client identifier or adapt
            # current function to handle multiple clients with the same name
            # if self.__ping_pong_clients_interval is not None:
            #     self.add_background_task(
            #         self.__ping_pong_clients_task,
            #         interval=self.__ping_pong_clients_interval,
            #     )
            #     self.__logger.log(
            #         f"Ping pong mode activated, interval: [{self.__ping_pong_clients_interval}]",
            #         LogLevels.DEBUG,
            #     )
            web.run_app(self._app, host=self.__host, port=self.__port)
        except KeyboardInterrupt:
            loop.run_until_complete(handle_exit())
        except Exception as error:
            self.logger.error(f"WServer error: ({error}), trying to restart...")
            time.sleep(5)
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
