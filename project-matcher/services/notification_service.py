from models.notification import Notification

class NotificationService:
    def __init__(self, db, user_service):
        self.db = db
        self.user_service = user_service
        self.notifications = {}
        # Use the constants from the Notification model
        self.notification_types = Notification
        
    def create_notification(self, user_id, sender_id, notification_type, content, data=None):
        # Verify users exist
        user = self.user_service.get_user_by_id(user_id)
        sender = self.user_service.get_user_by_id(sender_id)
        
        if not user or not sender:
            return False, "User not found"
        
        notification_id = len(self.notifications) + 1
        notification = Notification(
            notification_id,
            user_id,
            sender_id,
            notification_type,
            content,
            data
        )
        
        self.notifications[notification_id] = notification
        user.notifications.append(notification)
        
        return True, notification_id
    
    def get_user_notifications(self, user_id, unread_only=False):
        user = self.user_service.get_user_by_id(user_id)
        if not user:
            return []
            
        if unread_only:
            return [n for n in user.notifications if not n.is_read]
        return user.notifications
    
    def mark_notification_as_read(self, notification_id, user_id):
        notification = self.notifications.get(notification_id)
        if not notification:
            return False, "Notification not found"
            
        if notification.user_id != user_id:
            return False, "Unauthorized action"
            
        notification.is_read = True
        return True, notification_id
