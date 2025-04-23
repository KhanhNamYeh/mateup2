from datetime import datetime

class ToDoList:
    def __init__(self, id, title, owner_id):
        self.id = id
        self.title = title
        self.owner_id = owner_id
        self.collaborator_ids = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.task_ids = []
        
    def add_collaborator(self, user_id):
        if user_id not in self.collaborator_ids:
            self.collaborator_ids.append(user_id)
            
    def add_task(self, task_id):
        if task_id not in self.task_ids:
            self.task_ids.append(task_id)
            
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'owner_id': self.owner_id,
            'collaborator_ids': self.collaborator_ids,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'task_ids': self.task_ids
        }
