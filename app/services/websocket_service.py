import logging
import json
import asyncio
from typing import Dict, List, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect
from uuid import UUID

from app.db.models.notification import Notification
from app.schemas.notification import NotificationResponse, WebSocketNotification, WebSocketMessage

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for real-time notifications"""
    
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # Store connection metadata
        self.connection_info: Dict[WebSocket, Dict] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept new WebSocket connection"""
        await websocket.accept()
        
        # Initialize user connections set if not exists
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        # Add connection
        self.active_connections[user_id].add(websocket)
        self.connection_info[websocket] = {
            'user_id': user_id,
            'connected_at': asyncio.get_event_loop().time()
        }
        
        logger.info(f"WebSocket connected for user {user_id}. Total connections: {self.get_connection_count()}")
        
        # Send welcome message
        await self.send_personal_message({
            'type': 'connection_established',
            'data': {
                'message': 'Connected to notification service',
                'user_id': user_id
            }
        }, websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.connection_info:
            user_id = self.connection_info[websocket]['user_id']
            
            # Remove from user connections
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                
                # Clean up empty user sets
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            # Remove connection info
            del self.connection_info[websocket]
            
            logger.info(f"WebSocket disconnected for user {user_id}. Total connections: {self.get_connection_count()}")
    
    async def send_personal_message(self, message: Dict, websocket: WebSocket):
        """Send message to specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send personal message: {str(e)}")
            self.disconnect(websocket)
    
    async def send_message_to_user(self, message: Dict, user_id: int):
        """Send message to all connections for a specific user"""
        if user_id not in self.active_connections:
            logger.debug(f"No active connections for user {user_id}")
            return
        
        # Get all connections for user (copy to avoid modification during iteration)
        user_connections = list(self.active_connections[user_id])
        
        # Send to all user connections
        disconnected_connections = []
        for connection in user_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {str(e)}")
                disconnected_connections.append(connection)
        
        # Clean up failed connections
        for connection in disconnected_connections:
            self.disconnect(connection)
    
    async def broadcast_message(self, message: Dict):
        """Broadcast message to all connected users"""
        all_connections = []
        for user_connections in self.active_connections.values():
            all_connections.extend(user_connections)
        
        disconnected_connections = []
        for connection in all_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to broadcast message: {str(e)}")
                disconnected_connections.append(connection)
        
        # Clean up failed connections
        for connection in disconnected_connections:
            self.disconnect(connection)
    
    def get_user_connection_count(self, user_id: int) -> int:
        """Get number of connections for a specific user"""
        return len(self.active_connections.get(user_id, set()))
    
    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return sum(len(connections) for connections in self.active_connections.values())
    
    def get_connected_users(self) -> List[int]:
        """Get list of users with active connections"""
        return list(self.active_connections.keys())
    
    def is_user_connected(self, user_id: int) -> bool:
        """Check if user has any active connections"""
        return user_id in self.active_connections and bool(self.active_connections[user_id])

class WebSocketService:
    """Service for managing real-time WebSocket notifications"""
    
    def __init__(self):
        self.manager = ConnectionManager()
    
    async def connect_user(self, websocket: WebSocket, user_id: int):
        """Connect a user's WebSocket"""
        await self.manager.connect(websocket, user_id)
    
    def disconnect_user(self, websocket: WebSocket):
        """Disconnect a user's WebSocket"""
        self.manager.disconnect(websocket)
    
    async def send_notification_to_user(self, user_id: int, notification: Notification):
        """Send notification to a specific user via WebSocket"""
        try:
            # Convert notification to response format
            notification_data = NotificationResponse(
                id=notification.id,
                event_type=notification.event_type,
                recipient_user_id=notification.recipient_user_id,
                recipient_type=notification.recipient_type,
                title=notification.title,
                message=notification.message,
                event_metadata=notification.event_metadata,
                email_sent=notification.email_sent,
                email_sent_at=notification.email_sent_at,
                email_error=notification.email_error,
                twitter_posted=notification.twitter_posted,
                twitter_posted_at=notification.twitter_posted_at,
                twitter_error=notification.twitter_error,
                twitter_post_id=notification.twitter_post_id,
                read_at=notification.read_at,
                created_at=notification.created_at,
                updated_at=notification.updated_at
            )
            
            # Create WebSocket message
            ws_message = {
                'type': 'notification',
                'data': notification_data.dict()
            }
            
            await self.manager.send_message_to_user(ws_message, user_id)
            logger.info(f"Sent notification {notification.id} via WebSocket to user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to send WebSocket notification to user {user_id}: {str(e)}")
    
    async def send_notification_update(self, user_id: int, notification_id: UUID, update_data: Dict):
        """Send notification update (e.g., marked as read) to user"""
        try:
            message = {
                'type': 'notification_update',
                'data': {
                    'notification_id': str(notification_id),
                    'updates': update_data
                }
            }
            
            await self.manager.send_message_to_user(message, user_id)
            logger.info(f"Sent notification update for {notification_id} to user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to send notification update to user {user_id}: {str(e)}")
    
    async def send_system_message(self, user_id: int, message: str, message_type: str = "info"):
        """Send system message to user"""
        try:
            ws_message = {
                'type': 'system_message',
                'data': {
                    'message': message,
                    'message_type': message_type,
                    'timestamp': asyncio.get_event_loop().time()
                }
            }
            
            await self.manager.send_message_to_user(ws_message, user_id)
            
        except Exception as e:
            logger.error(f"Failed to send system message to user {user_id}: {str(e)}")
    
    async def broadcast_system_announcement(self, message: str, announcement_type: str = "info"):
        """Broadcast system announcement to all connected users"""
        try:
            ws_message = {
                'type': 'system_announcement',
                'data': {
                    'message': message,
                    'announcement_type': announcement_type,
                    'timestamp': asyncio.get_event_loop().time()
                }
            }
            
            await self.manager.broadcast_message(ws_message)
            logger.info(f"Broadcasted system announcement: {message}")
            
        except Exception as e:
            logger.error(f"Failed to broadcast system announcement: {str(e)}")
    
    async def send_unread_count_update(self, user_id: int, unread_count: int):
        """Send updated unread notification count to user"""
        try:
            message = {
                'type': 'unread_count_update',
                'data': {
                    'unread_count': unread_count
                }
            }
            
            await self.manager.send_message_to_user(message, user_id)
            
        except Exception as e:
            logger.error(f"Failed to send unread count update to user {user_id}: {str(e)}")
    
    async def handle_client_message(self, websocket: WebSocket, message: Dict):
        """Handle incoming message from client"""
        try:
            message_type = message.get('type')
            data = message.get('data', {})
            
            if message_type == 'ping':
                # Respond to ping with pong
                await self.manager.send_personal_message({
                    'type': 'pong',
                    'data': {'timestamp': asyncio.get_event_loop().time()}
                }, websocket)
                
            elif message_type == 'mark_notification_read':
                # Handle marking notification as read
                notification_id = data.get('notification_id')
                if notification_id:
                    # This would trigger the notification service to update the database
                    # and send updates to other connected clients
                    pass
                    
            elif message_type == 'request_unread_count':
                # Handle request for current unread count
                user_id = self.manager.connection_info.get(websocket, {}).get('user_id')
                if user_id:
                    # This would query the database for current unread count
                    # and send it back via send_unread_count_update
                    pass
            
        except Exception as e:
            logger.error(f"Error handling client message: {str(e)}")
    
    def get_connection_stats(self) -> Dict:
        """Get WebSocket connection statistics"""
        return {
            'total_connections': self.manager.get_connection_count(),
            'connected_users': len(self.manager.get_connected_users()),
            'users_online': self.manager.get_connected_users()
        }
    
    def is_user_online(self, user_id: int) -> bool:
        """Check if user is currently connected"""
        return self.manager.is_user_connected(user_id)

# Global WebSocket service instance
websocket_service = WebSocketService() 