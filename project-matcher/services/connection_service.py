from models.connection import Connection
from models.notification import Notification
from datetime import datetime

class ConnectionService:
    def __init__(self, db, user_service, notification_service):
        self.db = db
        self.user_service = user_service
        self.notification_service = notification_service
        self.connections = {}
        
    def send_connection_request(self, sender_id, receiver_id, message=None):
        if sender_id == receiver_id:
            return False, "Cannot connect with yourself"
            
        # Check if users exist
        sender = self.user_service.get_user_by_id(sender_id)
        receiver = self.user_service.get_user_by_id(receiver_id)
        if not sender or not receiver:
            return False, "User not found"
            
        # Check if connection already exists
        for conn in self.connections.values():
            if ((conn.user_id_1 == sender_id and conn.user_id_2 == receiver_id) or 
                (conn.user_id_1 == receiver_id and conn.user_id_2 == sender_id)):
                if conn.status == Connection.STATUS_PENDING:
                    return False, "Connection request already sent"
                elif conn.status == Connection.STATUS_ACCEPTED:
                    return False, "Connection already exists"
        
        # Create connection
        conn_id = len(self.connections) + 1
        connection = Connection(conn_id, sender_id, receiver_id)
        self.connections[conn_id] = connection
        
        # Create notification for receiver
        notification_content = f"{sender.username} wants to connect with you"
        if message:
            notification_content += f": \"{message}\""
            
        self.notification_service.create_notification(
            receiver_id, 
            sender_id,
            Notification.TYPE_CONNECTION_REQUEST,
            notification_content,
            {"connection_id": conn_id}
        )
        
        return True, conn_id
        
    def accept_connection(self, connection_id, accepting_user_id):
        connection = self.connections.get(connection_id)
        if not connection:
            return False, "Connection not found"
            
        # Verify the accepting user is the receiver
        if connection.user_id_2 != accepting_user_id:
            return False, "Unauthorized action"
            
        if connection.status != Connection.STATUS_PENDING:
            return False, "Connection already processed"
            
        # Update connection status
        connection.status = Connection.STATUS_ACCEPTED
        connection.accepted_at = datetime.now()
        
        # Add users to each other's connections
        sender = self.user_service.get_user_by_id(connection.user_id_1)
        receiver = self.user_service.get_user_by_id(connection.user_id_2)
        
        if sender and receiver:
            sender.connections.append(receiver)
            receiver.connections.append(sender)
            
            # Create notification for the original sender
            notification_content = f"{receiver.username} accepted your connection request"
            self.notification_service.create_notification(
                sender.id,
                receiver.id,
                Notification.TYPE_CONNECTION_ACCEPTED,
                notification_content,
                {"connection_id": connection_id}
            )
            
            return True, connection_id
        
        return False, "User not found"
        
    def decline_connection(self, connection_id, declining_user_id):
        connection = self.connections.get(connection_id)
        if not connection:
            return False, "Connection not found"
        
        if connection.user_id_2 != declining_user_id:
            return False, "Unauthorized action"
            
        if connection.status != Connection.STATUS_PENDING:
            return False, "Connection already processed"
        
        connection.status = Connection.STATUS_DECLINED
        return True, connection_id
        
    def get_user_connections(self, user_id, status=None):
        user_connections = []
        for conn in self.connections.values():
            if conn.user_id_1 == user_id or conn.user_id_2 == user_id:
                if status is None or conn.status == status:
                    user_connections.append(conn)
        return user_connections

    def get_connection_by_id(self, connection_id):
        return self.connections.get(connection_id)
