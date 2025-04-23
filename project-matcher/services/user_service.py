from models.user import User

class UserService:
    def __init__(self, db):
        self.db = db
        self.users = {}  # In-memory store for development purposes
        
    def create_user(self, username, email, password_hash):
        user_id = len(self.users) + 1
        user = User(user_id, username, email, password_hash)
        self.users[user_id] = user
        return user
    
    def get_user_by_id(self, user_id):
        return self.users.get(user_id)
    
    def get_user_by_email(self, email):
        for user in self.users.values():
            if user.email == email:
                return user
        return None
    
    def add_skill(self, user_id, skill):
        user = self.get_user_by_id(user_id)
        if user and skill not in user.skills:
            user.skills.append(skill)
            return True
        return False
    
    def get_all_users(self):
        return list(self.users.values())
