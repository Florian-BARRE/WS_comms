# WS_comms - English Documentation

The websocket module has been developed symmetrically between the server side and the client side. We will therefore see how to instantiate the server and a client. As for other functionalities, they have the same name and are used in the same way on both sides.

## General Functioning

There are two main objects: **Server** and **Client**. They are built in the same way. Each has a route manager that handles sending and receiving data on associated routes. Route managers, in turn, use two essential objects: **Sender** and **Receiver**. These objects facilitate message reception through a configurable queue system, as well as message sending.

## Initialization

Only the instantiation of objects differs between **Server** and **Client**. Here’s an example for each:

```python
# Client Instantiation
ws_client = WSclient(logger=..., host="192.168.0.100", port=8080)

# Server Instantiation
ws_server = WServer(logger=..., host="0.0.0.0", port=8080)
```

> Routine Configuration
> 

Once the websocket client/server is started, it is no longer possible to call functions or execute code. This is why the `add_background_task` method exists. It allows adding, before launching the server, all the routines/functions that should run in parallel with the server or the client. The function passed as a parameter must be **asynchronous**! Their execution relies on pseudo-parallelism, as it uses the asynchronous execution of the **Asyncio** library.

> Startup
> 

The **Server** or **Client** starts via the `run()` method.

```python
# Start Client
ws_client.run()

# Start Server
ws_server.run()
```

## RouteManager

> Initialization
> 

Once our websocket object is created, we will add routes to it, which it will connect to or serve. Each route must be associated with a manager composed of a **Sender** and a **Receiver**. Here’s an example of creating a **RouteManager** and associating it with a sample route:

```python
# For the client
# Create the route manager (we provide the client name to the sender to sign the sent messages with this name)
ws_route_example_manager = WSclientRouteManager(WSreceiver(), WSender("Client"))
# Associate the manager with a path (a route), using the previously defined ws_client instance
ws_client.add_route_handler("/route_example", ws_route_example_manager)

# For the server
# Create the route manager (we provide the server name to the sender to sign the sent messages with this name)
ws_route_example_manager = WServerRouteManager(WSreceiver(), WSender("Server"))
# Associate the manager with a path (a route), using the previously defined ws_server instance
ws_server.add_route_handler("/route_example", ws_route_example_manager)
```

> Sending Messages
> 

To send a message using our **RouteManager**, we will use the `sender` attribute, which is an instance of the **Sender** object. See the documentation for this object to use it easily.

One of the features offered by the **Sender**, when on the server side, is the ability to target specific clients for message sending. This function requires providing the **Sender** with the clients to target. The **RouteManager** has a function that allows targeting based on the client’s connection name: **`get_client`**. 

This method takes the client’s name as input and returns the **WebSocket connections** associated with that username. There may be multiple if multiple clients use the same name. If no client name is found, the function returns an empty list.

Example:

```python
ws_client1 = route_manager.get_client("<target client name 1>")
ws_client2 = route_manager.get_client("<target client name 2>")

# Send a message to 1 client
await route_manager.sender.send(
    WSmsg(sender="the server", msg="message server -> client", data={"data": "any data", 1: "other data"}),
    clients=ws_client1
)

# Send a message to 2 clients
await route_manager.sender.send(
    WSmsg(sender="the server", msg="message server -> [client1, client2]", data={"data": "any data", 1: "other data"}),
    clients=[ws_client1, ws_client2]
)
```

> Reading Messages
> 

To read messages using our **RouteManager**, we will use the `receiver` attribute, which is an instance of the **Receiver** object. See the documentation for this object to use it easily.

---

## Receiver

We will now detail the functionalities of the **Receiver**. This object manages the reception of messages received on the WebSocket route being listened to.

The **Receiver** supports **queue-based** operation, allowing all received messages to be stacked until they are read (dequeued). If the queue is not used, it will always return the last received message, meaning that any messages received in between will be lost.

The option **`keep_memory`** is also available, ensuring that the last element remains in the queue or memory. This means that even if the queue is emptied because all messages were read, you can still retrieve the last value without it being deleted.

By default, `use_queue` and `keep_memory` are **False**.

> How to Read Received Messages?
> 

The `get()` method allows reading received messages while respecting the parameters defined when creating the object (use of queue or not, persistence of elements).

```python
message = await route_manager.receiver.get()
```

→ **Asynchronous function**, it must be called with `await`!

> How to Get Queue Size?
> 

The `get_queue_size()` method allows knowing the number of messages in the queue waiting to be read.

```python
queue_size = route_manager.receiver.get_queue_size()
```

→ **Synchronous function**, do not call with `await`!

---

## Sender

The **Sender** only requires a name to function. This name is used to sign messages, allowing the identification of the message source on the WebSocket route.

Example:

```python
sender = WSender("<sender name>")
```

> How to Send a Message?
> 

The `send` function is used to send messages. On the client side, the recipient is directly the server. On the server side, you can choose to whom the message is sent.

When a client connects to the server, it provides its name. At that moment, the server associates the established WebSocket connection with that name. This allows targeting a client using the provided connection name.

- If a **client** is specified as a parameter, the message will only be sent to that client (or a list of clients).
- If **no client** is specified, the **Sender** will send the message to everyone.

Examples:

```python
# Send a message from Client to Server
await route_manager.sender.send(
    WSmsg(sender="a client", msg="message client -> server", data={"data": "any data", 1: "other data"})
    # No need to specify the target, the message will automatically be sent to the Server
)
            
# Send a message from Server to All Clients
await route_manager.sender.send(
    WSmsg(sender="the server", msg="message server -> clients", data={"data": "any data", 1: "other data"})
    # If nothing is specified, the message is sent to all clients
)

# Send a message from Server to a Specific Client
await route_manager.sender.send(
    WSmsg(sender="the server", msg="message server -> client", data={"data": "any data", 1: "other data"}),
    clients=await route_manager.get_client("target client name")  # Send the message only to the client named "target client name" (must use WServerRouteManager object)
)
```

→ **Asynchronous function**, it must be called with `await`!

---

## Message

All messages exchanged between the client and the server are of type **`WSmsg`**, which formalizes the exchanged data.

Format:

```python
{
    "sender": str,
    "msg": str,
    "data": any,
    "ts": int
}
```

- **sender**: The sender’s name.
- **msg**: The message title, allowing identification of how to process it.
- **data**: The message content (any JSON-supported format).
- **ts**: (optional) Timestamp of the sent message.

### Constructors

The **WSmsg** class can be instantiated in several ways, all optimized to make its use easy and intuitive.

- **From a JSON object**:
  
  ```python
  message = WSmsg.from_json(
      {
          "sender": "sender_name",
          "msg": "example",
          "data": [1, 2, 3],
          "ts": int
      }
  )
  ```

- **From a text string (JSON in textual format)**:
  
  ```python
  message = WSmsg.from_str(
      '''
          "sender": str,
          "msg": str,
          "data": [1, 2, 3],
          "ts": int
      '''
  )
  ```

- **From an aiohttp response**:
  
  ```python
  message = WSmsg.from_aiohttp_message(response: aiohttp.WSMessage)
  ```

---

> **Comparison Operations**

The **binary comparison operators `==` and `!=`** have been redefined for this class. They compare each field of the message one by one.

## **Author**

Project created and maintained by **Florian BARRE**.  
For questions or contributions, feel free to contact me.
[My Website](https://florianbarre.fr/) | [My LinkedIn](www.linkedin.com/in/barre-florian) | [My GitHub](https://github.com/Florian-BARRE)
---

---
# WS_comms - Documentation Française

Le module websocket a été développé de manière symétrique entre le côté serveur et le côté client. Nous allons donc voir comment instancier le serveur et un client. Pour ce qui est des autres fonctionnalités, elles portent le même nom et s'utilisent de la même manière des deux côtés.

## Fonctionnement générale

Il existe deux objets principaux : Server et Client. Ils sont construits de manière identique. Chacun possède un gestionnaire de routes permettant de gérer l'envoi et la réception de données sur les routes associées. Les gestionnaires de routes utilisent à leur tour deux objets essentiels : le Sender et le Receiver. Ces objets facilitent la gestion de la réception des messages grâce à un système de files d'attente configurable, ainsi que l'envoi de messages.

## Initialisation

Seule l’instanciation des objets change entre Server et Client. Voici un exemple pour chacun d'entre eux :

```python
# Instanciation Client
ws_client = WSclient(logger=..., host="192.168.0.100", port=8080)

# Instanciation Server
ws_server = WServer(logger=..., host="0.0.0.0", port=8080)
```

> Configuration de routines
> 

Une fois le client / serveur websocket démarré, il n'est plus possible d'appeler de fonction ou d'exécuter du code. C'est pourquoi la méthode `add_background_task` existe. Elle permet d’ajouter, avant le lancement du serveur, toutes les routines / fonctions que l’on souhaite exécuter en parallèle du serveur ou du client. La fonction passée en paramètre doit être asynchrone ! Leur exécution repose sur du pseudo-parallélisme, car elle utilise l'exécution asynchrone de la bibliothèque Asyncio.

> Démarrage
> 

Le démarrage du Server ou Client se fait via la méthode `run()`.

```python
# Démarrage Client
ws_client.run()

# Démarrage Server
ws_server.run()
```

## RouteManager

> Initialisation
> 

Une fois notre objet websocket créé, nous allons lui ajouter des routes auxquelles il va se connecter ou qu'il va servir. Pour chaque route, il faut lui associer un gestionnaire composé d’un Sender et d’un Receiver. Voici un exemple de création d’un RouteManager que l’on associe à une route d’exemple :

```python
# Pour le client
# Création du route manager (on fournit le nom du client au sender afin de signer avec ce nom les messages envoyés)
ws_route_exemple_manager = WSclientRouteManager(WSreceiver(), WSender("Client"))
# On associe le manager à un path (une route), on utilise l'instance de ws_client définit plus haut
ws_client.add_route_handler("/route_exemple", ws_route_exemple_manager)

# Pour le server
# Création du route manager (on fournit le nom du server au sender afin de signer avec ce nom les messages envoyés)
ws_route_exemple_manager = WServerRouteManager(WSreceiver(), WSender("Server"))
# On associe le manager à un path (une route), on utilise l'instance de ws_server définit plus haut
ws_server.add_route_handler("/route_exemple", ws_route_exemple_manager)
```

> Envoyer des messages
> 

Pour envoyer un message à l’aide de notre RouteManager on va utiliser l’attribut `sender` qui est une instance de l’objet Sender. Allez voir la documentation sur cette objet pour s’en servir facilement. Une des possibilité qu’offre le Sender lorsqu’on est du côté Server est la possibilité de cibler l’envoie de notre message. Cette fonction nécessite de fournir au Sender les clients à cibler. le RouteManager possède une fonction permettant de faire cela à partir du nom de connexion du client. C’est la méthode`get_client` qui permet de faire ça. Elle prend en entrée le nom du client et retourne les connexions WebSockets associé à ce pseudo. Il peut en avoir plusieurs si plusieurs clients ont le même nom. Si aucun nom client n’a été trouvé la fonction retourne une liste vide.

Pour envoyer un message à l’aide de notre RouteManager, nous allons utiliser l’attribut `sender`, qui est une instance de l’objet Sender. Consultez la documentation de cet objet pour l’utiliser facilement. Une des fonctionnalités offertes par le Sender, lorsqu’on est du côté serveur, est la possibilité de cibler l’envoi de notre message. Cette fonction nécessite de fournir au Sender les clients à cibler. Le RouteManager possède une fonction permettant de faire cela à partir du nom de connexion du client, c’est la méthode `get_client` . Elle prend en entrée le nom du client et retourne les connexions WebSocket associées à ce pseudo. Il peut y en avoir plusieurs si plusieurs clients utilisent le même nom. Si aucun nom de client n’est trouvé, la fonction retourne une liste vide.

```python
ws_client1 = route_manager.get_client("<nom du client cible 1>")
ws_client2 = route_manager.get_client("<nom du client cible 2>")

# Envoie du message à 1 client
await route_manager.sender.send(
    WSmsg(sender="le server", msg="message server -> client", data={"data": "donnée en tout genre", 1: "d'autres données"})
    clients=ws_client1
)

# Envoie du message à 2 clients
await route_manager.sender.send(
    WSmsg(sender="le server", msg="message server -> [client1, client2]", data={"data": "donnée en tout genre", 1: "d'autres données"})
    clients=[ws_client1, ws_client2]
)
```

> Lire des messages
> 

Pour lire les messages à l’aide de notre RouteManager on va utiliser l’attribut `receiver`qui est une instance de l’objet Receiver. Allez voir la documentation sur cette objet pour s’en servir facilement.

## Receiver

Nous allons détailler les fonctionnalités du Receiver. Cet objet gère la réception des messages reçus sur la route du websocket écoutée. Le Receiver supporte le fonctionnement en queue, permettant d’empiler tous les messages reçus jusqu’à ce qu’on les lise (dépile). Si la queue n’est pas utilisée, on accédera systématiquement au dernier élément reçu, et les messages reçus entre-temps seront donc perdus. L’option `keep_memory` est également disponible, garantissant qu’il reste toujours dans la queue ou en mémoire le dernier élément de la queue. Ainsi, même si la queue est vidée parce que tous les messages ont été lus, on peut récupérer la dernière valeur sans qu’elle soit supprimée.

Exemples : 

```python
sender = WSender("<le nom qu'on veut>")
```

PS: par défaut`use_queue` et `keep_memory` sont à False.

> Comment lire les messages reçus ?
> 

La méthode `get()` permet de lire les messages reçus en respectant les paramètres précisés lors de la définition de notre objet (utilisation d’une queue ou non, persistance des éléments).

```python
message = await route_manager.receiver.get()
```

→ Fonction asynchrone, il faut penser à l’appeler avec un`await`!

> Comment récupérer la taille de la queue ?
> 

La méthode `get_queue_size()` permet de connaître le nombre de messages dans la queue en attente de lecture.

```python
queue_size = route_manager.receiver.get_queue_size()
```

→ Fonction synchrone ne pas appelé avec un`await`!

## Sender

Le Sender nécessite uniquement un nom pour fonctionner. Ce nom est utilisé pour signer les messages, permettant ainsi d’identifier la source des messages sur la route du WebSocket.

Exemples : 

```python
sender = WSender("<nom du sender>")
```

> Comment envoyer un message ?
> 

La fonction `send` permet d’envoyer des messages. Côté client, le destinataire est directement le serveur. Côté serveur, on peut choisir à qui envoyer le message. Lorsqu’un client se connecte au serveur, il lui fournit son nom. À ce moment, le serveur associe la connexion websocket établie à ce nom. Cela permet de cibler le client à qui envoyer le message en utilisant le nom fourni lors de la connexion. Si on spécifie un client en paramètre, le message sera uniquement envoyé à ce client (on peut également fournir une liste de clients). Si aucun client n’est spécifié, le Sender envoie le message à tout le monde.

Voici des exemples d’utilisation : 

```python
# Envoie d'un message d'un Client vers le Server
await route_manager.sender.send(
    WSmsg(sender="un client", msg="message client -> server", data={"data": "donnée en tout genre", 1: "d'autres données"})
    # Pas besoin de spécifier la cible en tant que client le message sera automatiquement envoyé au Server
)
            
# Envoie d'un message du Server vers tous les Clients
await route_manager.sender.send(
    WSmsg(sender="le server", msg="message server -> clients", data={"data": "donnée en tout genre", 1: "d'autres données"})
    # Si on ne spécifie rien, le message est alors envoyé à tous les clients
)

# Envoie d'un message du Server vers un Client
await route_manager.sender.send(
    WSmsg(sender="le server", msg="message server -> client", data={"data": "donnée en tout genre", 1: "d'autres données"})
    clients=await route_manager.get_client("nom du client cible") # On envoie le message uniquement au client nommé "nom du client cible" (attention c'est l'objet WServerRouteManager qu'il faut utiliser)
)
```

→ Fonction asynchrone, il faut penser à l’appeler avec un`await`!

Il est également possible d’ajouter l’option `wait_client` à la fonction `send` cela permet d’attendre qu’au moins 1 client soit connecté avant d’envoyer le message. Par défaut cette option est désactivée. Attention l’instruction est bloquante jusqu’à qu’un client soit connecté !

La fonction `send` retourne un booléen représentant le succès ou non de l’envoie.

La méthode permettant de récupérer les clients en fonction de leur nom est situé dans l’objet `WServerRouteManager` voir documentation sur cette objet pour plus de précision.

## Message

Tous les messages échangés entre le client et le serveur sont du type `WSmsg`, ce qui permet de formaliser les données échangées. Voici leur format :

```python
{
    "sender": str,
    "msg": str,
    "data": any,
    "ts": int
}
```

- sender : contient le nom de l’expéditeur.
- msg : contient l’intitulé du message envoyé, permettant d’utiliser la méthode appropriée pour traiter le message.
- data : représente le cœur du message. C’est ici que l’on place le contenu du message. Tous les types de structures supportés par le format JSON sont autorisés.
- ts : correspond à la date au format timestamp de l’envoi du message. Il est facultatif et peut ne pas être fourni. Il est utilisé pour déboguer ou simplement pour avoir une trace datée du message.

La classe **`WSmsg`** permet de manipuler ces messages en toute simplicité.

> Constructeurs
> 

Cette classe peut être instanciée de plusieurs manières, toutes optimisées pour rendre son utilisation facile et intuitive.

- A partir d’un json
    
    ```python
    message = WSmsg.from_json(
    	{
    	    "sender": "expediteur",
    	    "msg": "exemple",
    	    "data": [1, 2, 3],
    	    "ts": int
    	}
    )
    ```
    
- A partir de texte (json au format textuel)
    
    ```python
    message = WSmsg.from_str(
    	'''
    	    "sender": str,
    	    "msg": str,
    	    "data": [1, 2, 3],
    	    "ts": int
    	'''
    )
    ```
    
- A partir d’une réponse aiohttp
    
    ```python
    message = WSmsg.from_aiohttp_message(response: aiohttp.WSMessage)
    ```

> Opération de comparaison

Les opérateurs binaires de comparaison `==` et `!=` ont été redéfinit pour cette classe ils comparent un à un chaque champs du message.

## Auteur

Projet créé et maintenu par **Florian BARRE**.  
Pour toute question ou contribution, n'hésitez pas à me contacter.
[Mon Site](https://florianbarre.fr/) | [Mon LinkedIn](www.linkedin.com/in/barre-florian) | [Mon GitHub](https://github.com/Florian-BARRE)