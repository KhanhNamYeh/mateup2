from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, username, email, password_hash):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.skills = []
        self.projects = []
        self.connections = []
        self.notifications = []
        self.tasks = []

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'skills': self.skills,
            'projects': [project.id for project in self.projects],
            'connections': [conn.id for conn in self.connections],
            'notifications': [notif.id for notif in self.notifications],
            'tasks': [task.id for task in self.tasks]
        }