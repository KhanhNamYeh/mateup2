from datetime import datetime

class Notification:
    TYPE_CONNECTION_REQUEST = "connection_request"
    TYPE_TASK_ASSIGNMENT = "task_assignment"
    TYPE_CONNECTION_ACCEPTED = "connection_accepted"
    
    def __init__(self, id, user_id, sender_id, notification_type, content, data=None):
        self.id = id
        self.user_id = user_id
        self.sender_id = sender_id
        self.notification_type = notification_type
        self.content = content
        self.data = data or {}
        self.created_at = datetime.now()
        self.is_read = False

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'sender_id': self.sender_id,
            'type': self.notification_type,
            'content': self.content,
            'data': self.data,
            'created_at': self.created_at.isoformat(),
            'is_read': self.is_read
        }
