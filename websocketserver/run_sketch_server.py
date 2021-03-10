import logging
import json
from typing import Any, Callable, Dict, Set
import asyncio
import websockets

# Dict mapping path id -> serialized representation of that path
PATHS: Dict[str, str] = {}

# Set keeping track of connected users
USERS: Set[websockets.WebSocketClientProtocol] = set()

"""
SERIALIZATION
"""
def serialize_paths() -> str:
    """ Serialize paths to send to clients """
    paths = {
        'type': 'paths',
        'paths': PATHS,
    }
    return json.dumps(paths)

def serialize_users() -> str:
    """ Serialize users to send to clients.
        Currently unused, but could be used to show clients who is currently connected.
    """
    users = {
        'type': 'users',
        'count': len(USERS)
    }
    return json.dumps(users)

"""
CLIENT NOTIFICATION: to synchronize updated state across clients
"""
async def notify_paths() -> None:
    """ Notifies each connected client of the current paths """
    if USERS:
        message = serialize_paths()
        await asyncio.wait([user.send(message) for user in USERS])

async def notify_paths() -> None:
    """ Notifies each connected client of the current users """
    if USERS:
        message = serialize_paths()
        await asyncio.wait([user.send(message) for user in USERS])

"""
CONNECTION HANDLERS: for when a client is connected/disconnected
"""
async def register(websocket) -> None:
    print(f'Adding user {websocket}: {type(websocket)}')
    USERS.add(websocket)

async def unregister(websocket) -> None:
    USERS.remove(websocket)

"""
ACTION HANDLERS: to run whenever a client sends an action
"""
async def add_path(data: Dict) -> None:
    """ Action handler for when a new path is created """
    path_id = data.get('pathID')
    path = data.get('pathData')
    if path_id is not None and path is not None:
        PATHS[path_id] = path
    await notify_paths()

async def update_path(data: Dict) -> None:
    """ Action handler to update an existing path """
    path_id = data.get('pathID')
    path = data.get('pathData')
    if path_id is not None and path is not None:
        PATHS[path_id] = path
    await notify_paths()

async def delete_path(data: Dict) -> None:
    """ Action handler to delete a path """
    path_id = data.get('pathID')
    if path_id is not None:
        PATHS.pop(path_id, None)
    await notify_paths()

# Dict mapping action id -> function to run for that action
actions: Dict[str, Callable[[Dict], Any]] = {
    'createPath': add_path,
    'updatePath': update_path,
    'deletePath': delete_path,
}

"""
SERVER LOOP
"""
# TODO: Instead, send each path on initial load and after that each create/update/delete sends each client
# a message to only change the single changed path
async def sketch_server_loop(websocket, path) -> None:
    """ Main logic loop for sketch server """
    await register(websocket)
    try:
        await websocket.send(serialize_paths())
        async for message in websocket:
            data = json.loads(message)
            action = data.get('action')
            handle_action = actions.get(action)
            if handle_action:
                handle_action(data)
                await notify_state()
            else:
                logging.error(f'Invalid action {action}')
    finally:
        await unregister(websocket)

def run_server() -> None:
    #Start server
    start_server = websockets.serve(sketch_server_loop, 'localhost', 12345)
    asyncio.get_event_loop().run_until_complete(start_server)

    # Continue running until stopped manually
    asyncio.get_event_loop().run_forever()

if __name__ == '__main__':
    run_server()
