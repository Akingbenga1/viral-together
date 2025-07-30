import logging
import json
import asyncio
from typing import Dict, List, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Any, Optional
from datetime import datetime
import time
import traceback

from app.db.models.user import User
from app.db.models.notification import Notification
from app.schemas.notification import NotificationResponse, WebSocketNotification, WebSocketMessage

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for real-time notifications"""
    
    def __init__(self):
        # Store active connections per user
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.connection_times: Dict[WebSocket, datetime] = {}
        self.user_activity: Dict[int, datetime] = {}
        logger.info(f"🔌 WEBSOCKET_MANAGER_INIT: Connection manager initialized")
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept WebSocket connection with comprehensive logging"""
        start_time = time.time()
        logger.info(f"🔌 WS_CONNECT_START: New connection request for user {user_id}")
        
        try:
            await websocket.accept()
            connect_time = time.time() - start_time
            
            if user_id not in self.active_connections:
                self.active_connections[user_id] = []
            
            self.active_connections[user_id].append(websocket)
            self.connection_times[websocket] = datetime.utcnow()
            self.user_activity[user_id] = datetime.utcnow()
            
            total_connections = self.get_connection_count()
            user_connections = len(self.active_connections[user_id])
            
            logger.info(f"✅ WS_CONNECT_SUCCESS: user={user_id}, time={connect_time:.3f}s, user_connections={user_connections}, total_connections={total_connections}")
            
            # Send welcome message
            await self._send_connection_welcome(websocket, user_id)
            
        except Exception as e:
            connect_time = time.time() - start_time
            logger.error(f"❌ WS_CONNECT_FAILURE: user={user_id}, time={connect_time:.3f}s")
            logger.error(f"Connection error: {str(e)}")
            logger.error(f"Connection stack trace: {traceback.format_exc()}")
            raise
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        """Remove WebSocket connection with comprehensive logging"""
        logger.info(f"🔌 WS_DISCONNECT_START: Disconnecting user {user_id}")
        
        try:
            if user_id in self.active_connections:
                if websocket in self.active_connections[user_id]:
                    self.active_connections[user_id].remove(websocket)
                    
                    # Calculate connection duration
                    if websocket in self.connection_times:
                        connect_time = self.connection_times[websocket]
                        duration = (datetime.utcnow() - connect_time).total_seconds()
                        del self.connection_times[websocket]
                        logger.debug(f"🔌 WS_CONNECTION_DURATION: user={user_id}, duration={duration:.1f}s")
                    
                    # Remove user entry if no more connections
                    if not self.active_connections[user_id]:
                        del self.active_connections[user_id]
                        logger.debug(f"🔌 WS_USER_OFFLINE: user={user_id} has no more connections")
            
            total_connections = self.get_connection_count()
            user_connections = len(self.active_connections.get(user_id, []))
            
            logger.info(f"✅ WS_DISCONNECT_SUCCESS: user={user_id}, user_connections={user_connections}, total_connections={total_connections}")
            
        except Exception as e:
            logger.error(f"❌ WS_DISCONNECT_ERROR: user={user_id}")
            logger.error(f"Disconnect error: {str(e)}")
            logger.error(f"Disconnect stack trace: {traceback.format_exc()}")

    async def send_personal_message(self, message: WebSocketMessage, user_id: int):
        """Send message to specific user with comprehensive logging"""
        start_time = time.time()
        logger.debug(f"🔌 WS_PERSONAL_START: Sending {message.type} message to user {user_id}")
        
        if user_id not in self.active_connections:
            logger.debug(f"🔌 WS_USER_OFFLINE: No active connections for user {user_id}")
            return
        
        successful_sends = 0
        failed_sends = 0
        
        # Send to all user's connections
        for websocket in self.active_connections[user_id].copy():
            try:
                await websocket.send_text(message.json())
                successful_sends += 1
                
            except Exception as e:
                failed_sends += 1
                logger.warning(f"⚠️ WS_SEND_FAILED: Failed to send to one connection for user {user_id}: {str(e)}")
                # Remove failed connection
                try:
                    self.active_connections[user_id].remove(websocket)
                except ValueError:
                    pass  # Already removed
        
        send_time = time.time() - start_time
        
        if successful_sends > 0:
            logger.debug(f"✅ WS_PERSONAL_SUCCESS: user={user_id}, successful={successful_sends}, failed={failed_sends}, time={send_time:.3f}s")
            # Update user activity
            self.user_activity[user_id] = datetime.utcnow()
        else:
            logger.warning(f"⚠️ WS_PERSONAL_ALL_FAILED: user={user_id}, all {failed_sends} connections failed")

    async def broadcast(self, message: WebSocketMessage):
        """Broadcast message to all connected users with comprehensive logging"""
        start_time = time.time()
        logger.info(f"🔌 WS_BROADCAST_START: Broadcasting {message.type} message to all users")
        
        total_connections = 0
        successful_sends = 0
        failed_sends = 0
        users_reached = 0
        
        for user_id, connections in self.active_connections.items():
            user_successful = 0
            user_failed = 0
            
            for websocket in connections.copy():
                total_connections += 1
                try:
                    await websocket.send_text(message.json())
                    successful_sends += 1
                    user_successful += 1
                    
                except Exception as e:
                    failed_sends += 1
                    user_failed += 1
                    logger.warning(f"⚠️ WS_BROADCAST_FAILED: Failed connection for user {user_id}: {str(e)}")
                    # Remove failed connection
                    try:
                        connections.remove(websocket)
                    except ValueError:
                        pass
            
            if user_successful > 0:
                users_reached += 1
                self.user_activity[user_id] = datetime.utcnow()
        
        broadcast_time = time.time() - start_time
        success_rate = (successful_sends / total_connections * 100) if total_connections > 0 else 0
        
        logger.info(f"✅ WS_BROADCAST_COMPLETE: time={broadcast_time:.3f}s, users_reached={users_reached}, successful={successful_sends}, failed={failed_sends}, success_rate={success_rate:.1f}%")

    async def _send_connection_welcome(self, websocket: WebSocket, user_id: int):
        """Send welcome message to newly connected user"""
        try:
            welcome_message = WebSocketMessage(
                type="system",
                message=f"Connected to notification service",
                data={
                    "user_id": user_id,
                    "connected_at": datetime.utcnow().isoformat(),
                    "server_time": datetime.utcnow().isoformat()
                }
            )
            
            await websocket.send_text(welcome_message.json())
            logger.debug(f"🔌 WS_WELCOME_SENT: Welcome message sent to user {user_id}")
            
        except Exception as e:
            logger.warning(f"⚠️ WS_WELCOME_FAILED: Failed to send welcome to user {user_id}: {str(e)}")

    def get_connection_count(self) -> int:
        """Get total number of active WebSocket connections"""
        return sum(len(connections) for connections in self.active_connections.values())

    def get_user_count(self) -> int:
        """Get number of unique users connected"""
        return len(self.active_connections)

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get comprehensive connection statistics"""
        stats = {
            "total_connections": self.get_connection_count(),
            "unique_users": self.get_user_count(),
            "users_online": list(self.active_connections.keys()),
            "connections_per_user": {
                user_id: len(connections) 
                for user_id, connections in self.active_connections.items()
            }
        }
        
        logger.debug(f"📊 WS_STATS: {stats}")
        return stats

class WebSocketService:
    """Service for managing real-time WebSocket notifications"""
    
    def __init__(self):
        self.manager = ConnectionManager()
        logger.info(f"🔌 WEBSOCKET_SERVICE_INIT: WebSocket service initialized")
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Connect user with logging"""
        await self.manager.connect(websocket, user_id)
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        """Disconnect user with logging"""
        self.manager.disconnect(websocket, user_id)
    
    async def send_notification_to_user(self, notification: Notification, user_id: int):
        """Send notification to specific user with comprehensive logging"""
        start_time = time.time()
        logger.info(f"🔌 WS_NOTIFICATION_START: Sending notification {notification.id} to user {user_id}")
        
        try:
            # Create WebSocket notification
            ws_notification = WebSocketNotification(
                id=notification.id,
                uuid=notification.uuid,
                event_type=notification.event_type,
                title=notification.title,
                message=notification.message,
                event_metadata=notification.event_metadata or {},
                created_at=notification.created_at
            )
            
            message = WebSocketMessage(
                type="notification",
                data=ws_notification.dict()
            )
            
            await self.manager.send_personal_message(message, user_id)
            
            send_time = time.time() - start_time
            logger.info(f"✅ WS_NOTIFICATION_SUCCESS: notification={notification.id}, user={user_id}, time={send_time:.3f}s")
            
        except Exception as e:
            send_time = time.time() - start_time
            logger.error(f"❌ WS_NOTIFICATION_FAILURE: notification={notification.id}, user={user_id}, time={send_time:.3f}s")
            logger.error(f"WebSocket notification error: {str(e)}")
            logger.error(f"WebSocket stack trace: {traceback.format_exc()}")
            raise
    
    async def send_notification_update(self, user_id: int, notification_id: int, update_data: Dict):
        """Send notification update to a specific user"""
        start_time = time.time()
        logger.info(f"🔌 WS_UPDATE_START: Sending update for notification {notification_id} to user {user_id}")
        
        try:
            message = WebSocketMessage(
                type="notification_update",
                data={
                    'notification_id': notification_id,
                    'update_data': update_data
                }
            )
            
            await self.manager.send_personal_message(message, user_id)
            
            update_time = time.time() - start_time
            logger.info(f"✅ WS_UPDATE_SUCCESS: notification={notification_id}, user={user_id}, time={update_time:.3f}s")
            
        except Exception as e:
            update_time = time.time() - start_time
            logger.error(f"❌ WS_UPDATE_FAILURE: notification={notification_id}, user={user_id}, time={update_time:.3f}s")
            logger.error(f"Update error: {str(e)}")
            raise

    async def send_system_message(self, user_id: int, message: str, data: Optional[Dict] = None):
        """Send system message to user with logging"""
        logger.info(f"🔌 WS_SYSTEM_START: Sending system message to user {user_id}")
        
        try:
            ws_message = WebSocketMessage(
                type="system",
                message=message,
                data=data
            )
            
            await self.manager.send_personal_message(ws_message, user_id)
            logger.debug(f"✅ WS_SYSTEM_SUCCESS: message sent to user {user_id}")
            
        except Exception as e:
            logger.error(f"❌ WS_SYSTEM_FAILURE: user={user_id}, error={str(e)}")
            raise

    async def broadcast_system_announcement(self, message: str, data: Optional[Dict] = None):
        """Broadcast system announcement to all users with logging"""
        logger.info(f"🔌 WS_ANNOUNCEMENT_START: Broadcasting system announcement")
        
        try:
            ws_message = WebSocketMessage(
                type="system_announcement",
                message=message,
                data=data
            )
            
            await self.manager.broadcast(ws_message)
            logger.info(f"✅ WS_ANNOUNCEMENT_SUCCESS: System announcement broadcasted")
            
        except Exception as e:
            logger.error(f"❌ WS_ANNOUNCEMENT_FAILURE: error={str(e)}")
            raise

    async def send_unread_count_update(self, user_id: int, unread_count: int):
        """Send unread notification count update with logging"""
        logger.debug(f"🔌 WS_UNREAD_START: Sending unread count {unread_count} to user {user_id}")
        
        try:
            message = WebSocketMessage(
                type="unread_count",
                data={"unread_count": unread_count}
            )
            
            await self.manager.send_personal_message(message, user_id)
            logger.debug(f"✅ WS_UNREAD_SUCCESS: count={unread_count}, user={user_id}")
            
        except Exception as e:
            logger.error(f"❌ WS_UNREAD_FAILURE: user={user_id}, error={str(e)}")

    async def handle_client_message(self, websocket: WebSocket, user_id: int, message_data: str):
        """Handle incoming client message with logging"""
        logger.debug(f"🔌 WS_CLIENT_MESSAGE: Received from user {user_id}")
        
        try:
            data = json.loads(message_data)
            message_type = data.get('type', 'unknown')
            
            logger.debug(f"🔌 WS_MESSAGE_TYPE: {message_type} from user {user_id}")
            
            # Handle different message types
            if message_type == 'ping':
                await self._handle_ping(websocket, user_id)
            elif message_type == 'mark_read':
                await self._handle_mark_read(websocket, user_id, data)
            elif message_type == 'get_unread_count':
                await self._handle_get_unread_count(websocket, user_id)
            else:
                logger.warning(f"⚠️ WS_UNKNOWN_MESSAGE: Unknown message type '{message_type}' from user {user_id}")
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ WS_JSON_ERROR: Invalid JSON from user {user_id}: {str(e)}")
        except Exception as e:
            logger.error(f"❌ WS_MESSAGE_ERROR: Error handling message from user {user_id}: {str(e)}")
            logger.error(f"Message handling stack trace: {traceback.format_exc()}")

    async def _handle_ping(self, websocket: WebSocket, user_id: int):
        """Handle ping message"""
        logger.debug(f"🔌 WS_PING: Ping from user {user_id}")
        
        pong_message = WebSocketMessage(
            type="pong",
            data={"timestamp": datetime.utcnow().isoformat()}
        )
        
        await websocket.send_text(pong_message.json())
        logger.debug(f"🔌 WS_PONG: Pong sent to user {user_id}")

    async def _handle_mark_read(self, websocket: WebSocket, user_id: int, data: Dict):
        """Handle mark as read message"""
        notification_id = data.get('notification_id')
        if notification_id:
            logger.debug(f"🔌 WS_MARK_READ: User {user_id} marking notification {notification_id} as read")
            # Here you would typically update the database
            # For now, just acknowledge
            response = WebSocketMessage(
                type="mark_read_response",
                data={"notification_id": notification_id, "status": "acknowledged"}
            )
            await websocket.send_text(response.json())

    async def _handle_get_unread_count(self, websocket: WebSocket, user_id: int):
        """Handle get unread count message"""
        logger.debug(f"🔌 WS_UNREAD_REQUEST: User {user_id} requesting unread count")
        # Here you would typically query the database
        # For now, return a placeholder
        response = WebSocketMessage(
            type="unread_count",
            data={"unread_count": 0}
        )
        await websocket.send_text(response.json())

    def get_service_stats(self) -> Dict[str, Any]:
        """Get comprehensive service statistics"""
        return self.manager.get_connection_stats()

# Global service instance
websocket_service = WebSocketService() 