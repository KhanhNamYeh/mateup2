class Project:
    def __init__(self, id, title, description, owner_id, required_skills=None):
        self.id = id
        self.title = title
        self.description = description
        self.owner_id = owner_id
        self.required_skills = required_skills or []
        self.collaborators = []
        self.tasks = []

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'owner_id': self.owner_id,
            'required_skills': self.required_skills,
            'collaborators': [collab.id for collab in self.collaborators],
            'tasks': [task.id for task in self.tasks]
        }