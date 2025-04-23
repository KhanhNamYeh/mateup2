from datetime import datetime

class Task:
    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_REJECTED = "rejected"
    
    def __init__(self, id, title, description, project_id, assignee_id, assigner_id):
        self.id = id
        self.title = title
        self.description = description
        self.project_id = project_id
        self.assignee_id = assignee_id
        self.assigner_id = assigner_id
        self.status = self.STATUS_PENDING
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.due_date = None

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'project_id': self.project_id,
            'assignee_id': self.assignee_id,
            'assigner_id': self.assigner_id,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'due_date': self.due_date.isoformat() if self.due_date else None
        }
