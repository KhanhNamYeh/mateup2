from datetime import datetime

class Connection:
    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_DECLINED = "declined"
    
    def __init__(self, id, user_id_1, user_id_2):
        self.id = id
        self.user_id_1 = user_id_1
        self.user_id_2 = user_id_2
        self.status = self.STATUS_PENDING
        self.created_at = datetime.now()
        self.accepted_at = None

    def to_dict(self):
        return {
            'id': self.id,
            'user_id_1': self.user_id_1,
            'user_id_2': self.user_id_2,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'accepted_at': self.accepted_at.isoformat() if self.accepted_at else None
        }
