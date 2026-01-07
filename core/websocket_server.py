"""
WebSocket Server for Real-time Visualization
Broadcasts simulation state to web frontend.
"""

import asyncio
import websockets
import json
from typing import Set, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VisualizationServer:
    """
    WebSocket server that broadcasts simulation state to connected clients.
    """
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.current_state: Dict = {}
        self.server = None
    
    async def register(self, websocket: websockets.WebSocketServerProtocol):
        """Register a new client."""
        self.clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")
        
        # Send current state to new client
        if self.current_state:
            await websocket.send(json.dumps({
                'type': 'initial_state',
                'data': self.current_state
            }))
    
    async def unregister(self, websocket: websockets.WebSocketServerProtocol):
        """Unregister a client."""
        self.clients.discard(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.clients)}")
    
    async def broadcast_state(self, state: Dict):
        """Broadcast simulation state to all connected clients."""
        self.current_state = state
        
        if not self.clients:
            return
        
        message = json.dumps({
            'type': 'tick_update',
            'data': state
        })
        
        # Send to all clients
        disconnected = set()
        for client in self.clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
        
        # Remove disconnected clients
        self.clients -= disconnected
    
    async def handler(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """Handle WebSocket connection."""
        await self.register(websocket)
        
        try:
            async for message in websocket:
                # Handle client messages if needed
                data = json.loads(message)
                logger.info(f"Received from client: {data}")
                
                # Echo back for testing
                await websocket.send(json.dumps({
                    'type': 'ack',
                    'message': 'Message received'
                }))
        
        except websockets.exceptions.ConnectionClosed:
            pass
        
        finally:
            await self.unregister(websocket)
    
    async def start(self):
        """Start the WebSocket server."""
        self.server = await websockets.serve(
            self.handler,
            self.host,
            self.port
        )
        logger.info(f"🌐 WebSocket server started on ws://{self.host}:{self.port}")
    
    async def stop(self):
        """Stop the WebSocket server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("WebSocket server stopped")


async def test_server():
    """Test the WebSocket server."""
    server = VisualizationServer()
    await server.start()
    
    # Simulate broadcasting
    for i in range(10):
        await asyncio.sleep(1)
        await server.broadcast_state({
            'tick': i,
            'agents': [{'id': f'agent_{j}', 'x': j * 10, 'y': i * 10} for j in range(5)],
            'prices': {'grain': 10 + i, 'iron': 15 + i}
        })
    
    await server.stop()


if __name__ == "__main__":
    asyncio.run(test_server())
