import json
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class DataService:
    def __init__(self, data_file='data/db.json'):
        self.data_file = data_file
        self.data = self.load_data()
    
    def load_data(self):
        """Load data from JSON file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            else:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
                # Return default empty data structure
                return {
                    "users": [],
                    "projects": [],
                    "connections": [],
                    "categories": [
                        "Tech", "Art", "Education", "Healthcare", "Food",
                        "Business", "Entertainment", "Social", "Environment", "Sports"
                    ],
                    "countries": [
                        "USA", "Canada", "UK", "Germany", "France", "Italy",
                        "Japan", "Australia", "Brazil", "India"
                    ]
                }
        except Exception as e:
            print(f"Error loading data: {e}")
            return {
                "users": [],
                "projects": [],
                "connections": [],
                "categories": [],
                "countries": []
            }
    
    def save_data(self):
        """Save data to JSON file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False
    
    # User methods
    def get_users(self):
        """Get all users"""
        return self.data.get("users", [])
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        for user in self.data.get("users", []):
            if user["id"] == user_id:
                return user
        return None
    
    def get_user_by_email(self, email):
        """Get user by email"""
        for user in self.data.get("users", []):
            if user["email"] == email:
                return user
        return None
    
    def create_user(self, name, email, password):
        """Create a new user"""
        # Check if email already exists
        if self.get_user_by_email(email):
            return None
        
        # Generate new user ID
        user_id = 1
        if self.data.get("users"):
            user_id = max(user["id"] for user in self.data["users"]) + 1
        
        # Create user object
        new_user = {
            "id": user_id,
            "name": name,
            "email": email,
            "password_hash": generate_password_hash(password),
            "created_at": datetime.utcnow().isoformat(),
            "projects": [],
            "saved_projects": [],
            "connections": []
        }
        
        # Add user to data and save
        self.data.setdefault("users", []).append(new_user)
        self.save_data()
        
        return new_user
    
    def authenticate_user(self, email, password):
        """Authenticate user with email and password"""
        user = self.get_user_by_email(email)
        if user and check_password_hash(user["password_hash"], password):
            return user
        return None
    
    def update_user(self, user_id, **kwargs):
        """Update user details"""
        user = self.get_user_by_id(user_id)
        if user:
            for key, value in kwargs.items():
                if key in user and key != "id":
                    user[key] = value
            self.save_data()
            return user
        return None
    
    # Project methods
    def get_projects(self):
        """Get all projects"""
        return self.data.get("projects", [])
    
    def get_project_by_id(self, project_id):
        """Get project by ID"""
        for project in self.data.get("projects", []):
            if project["id"] == project_id:
                return project
        return None
    
    def get_projects_by_user(self, user_id):
        """Get all projects owned by a user"""
        return [p for p in self.data.get("projects", []) if p["owner_id"] == user_id]
    
    def get_saved_projects_by_user(self, user_id):
        """Get all projects saved by a user"""
        user = self.get_user_by_id(user_id)
        if user and "saved_projects" in user:
            saved_projects = []
            for project_id in user["saved_projects"]:
                project = self.get_project_by_id(project_id)
                if project:
                    saved_projects.append(project)
            return saved_projects
        return []
    
    def create_project(self, owner_id, name, kind, country, idea, partner):
        """Create a new project"""
        # Generate new project ID
        project_id = 1
        if self.data.get("projects"):
            project_id = max(project["id"] for project in self.data["projects"]) + 1
        
        # Create project object
        new_project = {
            "id": project_id,
            "owner_id": owner_id,
            "name": name,
            "kind": kind,
            "country": country,
            "idea": idea,
            "partner": partner,
            "created_at": datetime.utcnow().isoformat(),
            "status": "active"
        }
        
        # Add project to data and save
        self.data.setdefault("projects", []).append(new_project)
        
        # Add project to user's projects list
        user = self.get_user_by_id(owner_id)
        if user:
            user.setdefault("projects", []).append(project_id)
        
        self.save_data()
        return new_project
    
    def save_project_for_user(self, user_id, project_id):
        """Save a project for a user"""
        user = self.get_user_by_id(user_id)
        project = self.get_project_by_id(project_id)
        
        if user and project:
            if "saved_projects" not in user:
                user["saved_projects"] = []
            
            if project_id not in user["saved_projects"]:
                user["saved_projects"].append(project_id)
                self.save_data()
                return True
        
        return False
    
    # Connection methods
    def get_connections(self):
        """Get all connections"""
        return self.data.get("connections", [])
    
    def get_connection_by_id(self, connection_id):
        """Get connection by ID"""
        for connection in self.data.get("connections", []):
            if connection["id"] == connection_id:
                return connection
        return None
    
    def get_connections_by_user(self, user_id, status=None):
        """Get connections by user ID and optionally filtered by status"""
        connections = [
            c for c in self.data.get("connections", []) 
            if c["from_user_id"] == user_id or c["to_user_id"] == user_id
        ]
        
        if status:
            connections = [c for c in connections if c["status"] == status]
        
        return connections
    
    def create_connection(self, from_user_id, to_project_id, message):
        """Create a new connection request"""
        # Get the project's owner ID
        project = self.get_project_by_id(to_project_id)
        if not project:
            return None
        
        to_user_id = project["owner_id"]
        
        # Generate new connection ID
        connection_id = 1
        if self.data.get("connections"):
            connection_id = max(conn["id"] for conn in self.data["connections"]) + 1
        
        # Create connection object
        now = datetime.utcnow().isoformat()
        new_connection = {
            "id": connection_id,
            "from_user_id": from_user_id,
            "to_project_id": to_project_id,
            "to_user_id": to_user_id,
            "message": message,
            "status": "pending",
            "created_at": now,
            "updated_at": now
        }
        
        # Add connection to data and save
        self.data.setdefault("connections", []).append(new_connection)
        
        # Add connection to users' connections list
        from_user = self.get_user_by_id(from_user_id)
        to_user = self.get_user_by_id(to_user_id)
        
        if from_user:
            from_user.setdefault("connections", []).append(
                {"connection_id": connection_id, "status": "pending"}
            )
        
        if to_user:
            to_user.setdefault("connections", []).append(
                {"connection_id": connection_id, "status": "pending"}
            )
        
        self.save_data()
        return new_connection
    
    def update_connection_status(self, connection_id, new_status):
        """Update connection status (accepted/rejected)"""
        if new_status not in ("accepted", "rejected"):
            return False
        
        connection = self.get_connection_by_id(connection_id)
        if connection:
            connection["status"] = new_status
            connection["updated_at"] = datetime.utcnow().isoformat()
            
            # Update status in users' connection lists
            from_user = self.get_user_by_id(connection["from_user_id"])
            to_user = self.get_user_by_id(connection["to_user_id"])
            
            if from_user:
                for conn in from_user.get("connections", []):
                    if conn.get("connection_id") == connection_id:
                        conn["status"] = new_status
            
            if to_user:
                for conn in to_user.get("connections", []):
                    if conn.get("connection_id") == connection_id:
                        conn["status"] = new_status
            
            self.save_data()
            return True
        
        return False
    
    # Category and Country methods
    def get_categories(self):
        """Get all project categories"""
        return self.data.get("categories", [])
    
    def get_countries(self):
        """Get all countries"""
        return self.data.get("countries", [])
    
    def add_category(self, category):
        """Add a new category"""
        categories = self.data.setdefault("categories", [])
        if category not in categories:
            categories.append(category)
            self.save_data()
            return True
        return False
    
    def add_country(self, country):
        """Add a new country"""
        countries = self.data.setdefault("countries", [])
        if country not in countries:
            countries.append(country)
            self.save_data()
            return True
        return False
    
    # Project matching
    def find_similar_projects(self, project_data):
        """Find similar projects based on input data"""
        from services.matching_service import calculate_similarity
        
        matching_projects = []
        all_projects = self.get_projects()
        
        for project in all_projects:
            # Skip if the project is owned by the current user
            if "owner_id" in project_data and project["owner_id"] == project_data["owner_id"]:
                continue
                
            similarity = calculate_similarity(project_data, project)
            project_copy = project.copy()
            project_copy["match_percentage"] = similarity
            matching_projects.append(project_copy)
        
        # Sort by similarity score
        matching_projects.sort(key=lambda x: x["match_percentage"], reverse=True)
        
        # Return top 5 matches
        return matching_projects[:5]

def get_notifications_for_user(self, user_id):
    """Get notifications for a user (connections, etc)"""
    notifications = []
    
    # Get connection requests received by the user
    connections = self.get_connections_by_user(user_id)
    
    for connection in connections:
        # Check if the connection is to the user and is still pending
        if connection["to_user_id"] == user_id and connection["status"] == "pending":
            # Get project and sender info
            sender = self.get_user_by_id(connection["from_user_id"])
            project = self.get_project_by_id(connection["to_project_id"])
            
            if sender and project:
                notifications.append({
                    "id": connection["id"],
                    "type": "connection_request",
                    "sender_name": sender["name"],
                    "sender_id": sender["id"],
                    "project_name": project["name"],
                    "project_id": project["id"],
                    "message": connection["message"],
                    "created_at": connection["created_at"],
                    "read": False,  # Add read status tracking if needed
                    "connection_id": connection["id"]
                })
    
    # Sort notifications by date (newest first)
    notifications.sort(key=lambda x: x["created_at"], reverse=True)
    
    return notifications

def get_project_owner(self, project_id):
    """Get the owner of a project"""
    project = self.get_project_by_id(project_id)
    if project:
        return self.get_user_by_id(project["owner_id"])
    return None

def get_connection_by_project_and_user(self, project_id, user_id):
    """Check if a connection request already exists"""
    for conn in self.data.get("connections", []):
        if conn["to_project_id"] == project_id and conn["from_user_id"] == user_id:
            return conn
    return None

def delete_connection(self, connection_id, user_id):
    """Delete a connection (only allowed if pending and initiated by user)"""
    conn = self.get_connection_by_id(connection_id)
    
    if not conn or conn["from_user_id"] != user_id or conn["status"] != "pending":
        return False
    
    # Remove from connections list
    self.data["connections"] = [c for c in self.data["connections"] if c["id"] != connection_id]
    
    # Remove from users' connections lists
    from_user = self.get_user_by_id(conn["from_user_id"])
    to_user = self.get_user_by_id(conn["to_user_id"])
    
    if from_user and "connections" in from_user:
        from_user["connections"] = [
            c for c in from_user["connections"] 
            if c.get("connection_id") != connection_id
        ]
    
    if to_user and "connections" in to_user:
        to_user["connections"] = [
            c for c in to_user["connections"] 
            if c.get("connection_id") != connection_id
        ]
    
    self.save_data()
    return True