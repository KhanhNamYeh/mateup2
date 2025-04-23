from models.task import Task
from models.notification import Notification
from models.todolist import ToDoList
from datetime import datetime

class TaskService:
    def __init__(self, db, user_service, notification_service, project_service):
        self.db = db
        self.user_service = user_service
        self.notification_service = notification_service
        self.project_service = project_service
        self.tasks = {}
        self.todolists = {}
        
    def create_task(self, title, description, project_id, assignee_id, assigner_id, due_date=None):
        # Verify users and project exist
        assignee = self.user_service.get_user_by_id(assignee_id)
        assigner = self.user_service.get_user_by_id(assigner_id)
        project = self.project_service.get_project_by_id(project_id)
        
        if not assignee or not assigner or not project:
            return False, "User or project not found"
        
        # Check if assigner is project owner or collaborator
        if project.owner_id != assigner_id and assigner not in project.collaborators:
            return False, "Unauthorized action"
        
        task_id = len(self.tasks) + 1
        task = Task(task_id, title, description, project_id, assignee_id, assigner_id)
        
        if due_date:
            task.due_date = due_date
            
        self.tasks[task_id] = task
        project.tasks.append(task)
        assignee.tasks.append(task)
        
        # Send notification to assignee
        notification_content = f"New task assigned to you: {title}"
        self.notification_service.create_notification(
            assignee_id,
            assigner_id,
            Notification.TYPE_TASK_ASSIGNMENT,
            notification_content,
            {"task_id": task_id}
        )
        
        return True, task_id
    
    def update_task_status(self, task_id, user_id, new_status):
        task = self.tasks.get(task_id)
        if not task:
            return False, "Task not found"
            
        # Verify user is assignee or assigner
        if task.assignee_id != user_id and task.assigner_id != user_id:
            return False, "Unauthorized action"
            
        valid_statuses = [
            Task.STATUS_PENDING,
            Task.STATUS_ACCEPTED,
            Task.STATUS_IN_PROGRESS,
            Task.STATUS_COMPLETED,
            Task.STATUS_REJECTED
        ]
        
        if new_status not in valid_statuses:
            return False, "Invalid status"
            
        task.status = new_status
        task.updated_at = datetime.now()
        
        return True, task_id
    
    def get_user_tasks(self, user_id, status=None, as_assignee=True):
        user = self.user_service.get_user_by_id(user_id)
        if not user:
            return []
            
        if as_assignee:
            tasks = [t for t in self.tasks.values() if t.assignee_id == user_id]
        else:
            tasks = [t for t in self.tasks.values() if t.assigner_id == user_id]
            
        if status:
            tasks = [t for t in tasks if t.status == status]
            
        return tasks
    
    def get_project_tasks(self, project_id, status=None):
        project = self.project_service.get_project_by_id(project_id)
        if not project:
            return []
            
        tasks = [t for t in self.tasks.values() if t.project_id == project_id]
        
        if status:
            tasks = [t for t in tasks if t.status == status]
            
        return tasks

    def get_suggested_tasks(self, user_id_1, user_id_2):
        """Generate suggested tasks for collaboration between two users"""
        user1 = self.user_service.get_user_by_id(user_id_1)
        user2 = self.user_service.get_user_by_id(user_id_2)
        
        if not user1 or not user2:
            return []
            
        suggested_tasks = []
        
        # Add some default collaborative tasks
        suggested_tasks.append({
            'id': 'default_1',
            'title': 'Schedule an introductory meeting',
            'description': 'Get to know each other and discuss potential collaboration.',
            'type': 'default'
        })
        
        suggested_tasks.append({
            'id': 'default_2',
            'title': 'Share your portfolio/previous work',
            'description': 'Exchange examples of past projects to understand each other\'s experience.',
            'type': 'default'
        })
        
        suggested_tasks.append({
            'id': 'default_3',
            'title': 'Identify common interests',
            'description': 'List areas where your skills and interests align.',
            'type': 'default'
        })
        
        # Add tasks based on user skills
        if user1.skills and user2.skills:
            # Find complementary skills
            user1_skills = set(user1.skills)
            user2_skills = set(user2.skills)
            
            # Skills that user2 has but user1 doesn't
            complementary_skills = user2_skills - user1_skills
            
            if complementary_skills:
                for skill in list(complementary_skills)[:2]:  # Limit to 2 skills
                    suggested_tasks.append({
                        'id': f'skill_{skill}',
                        'title': f'Learn about {skill}',
                        'description': f'Ask your connection about their experience with {skill}.',
                        'type': 'skill'
                    })
        
        # Add project-based tasks
        user1_projects = self.project_service.get_user_projects(user_id_1)
        user2_projects = self.project_service.get_user_projects(user_id_2)
        
        # Suggest collaborating on user1's projects
        if user1_projects:
            for project in user1_projects[:2]:  # Limit to 2 projects
                suggested_tasks.append({
                    'id': f'project_{project.id}',
                    'title': f'Discuss collaboration on project: {project.title}',
                    'description': f'Explore potential roles for {user2.username} in this project.',
                    'type': 'project',
                    'project_id': project.id
                })
                
        # Suggest collaborating on user2's projects
        if user2_projects:
            for project in user2_projects[:2]:  # Limit to 2 projects
                suggested_tasks.append({
                    'id': f'project_{project.id}_collab',
                    'title': f'Explore joining project: {project.title}',
                    'description': f'Discuss with {user2.username} how you might contribute to this project.',
                    'type': 'project',
                    'project_id': project.id
                })
        
        return suggested_tasks
        
    def create_collaborative_todolist(self, creator_id, collaborator_id, selected_task_ids, custom_tasks):
        """Create a collaborative to-do list between two users"""
        creator = self.user_service.get_user_by_id(creator_id)
        collaborator = self.user_service.get_user_by_id(collaborator_id)
        
        if not creator or not collaborator:
            return None
            
        # Create the to-do list
        todolist_id = len(self.todolists) + 1
        todolist_title = f"Collaboration: {creator.username} & {collaborator.username}"
        
        todolist = ToDoList(todolist_id, todolist_title, creator_id)
        todolist.add_collaborator(collaborator_id)
        
        # Create tasks for selected suggestions
        suggested_tasks = self.get_suggested_tasks(creator_id, collaborator_id)
        
        # Dictionary to map suggestion IDs to their data
        suggestion_map = {task['id']: task for task in suggested_tasks}
        
        # Create tasks from selected suggestions
        for task_id in selected_task_ids:
            if task_id in suggestion_map:
                suggestion = suggestion_map[task_id]
                
                task_title = suggestion['title']
                task_description = suggestion['description']
                
                # If it's a project task, attach it to the project
                project_id = suggestion.get('project_id', None)
                
                new_task_id = len(self.tasks) + 1
                new_task = Task(
                    new_task_id,
                    task_title,
                    task_description,
                    project_id,
                    collaborator_id,  # Assign to collaborator
                    creator_id
                )
                
                self.tasks[new_task_id] = new_task
                todolist.add_task(new_task_id)
        
        # Create tasks from custom task list
        for task_text in custom_tasks:
            if task_text:
                new_task_id = len(self.tasks) + 1
                new_task = Task(
                    new_task_id,
                    task_text,  # Use the text as title
                    "",  # No description
                    None,  # No project
                    collaborator_id,  # Assign to collaborator
                    creator_id
                )
                
                self.tasks[new_task_id] = new_task
                todolist.add_task(new_task_id)
        
        # Store the to-do list
        self.todolists[todolist_id] = todolist
        
        # Send notification to collaborator
        notification_content = f"{creator.username} created a collaborative to-do list with you"
        self.notification_service.create_notification(
            collaborator_id,
            creator_id,
            self.notification_service.notification_types.TYPE_TASK_ASSIGNMENT,  # Use notification_types from the model
            notification_content,
            {"todolist_id": todolist_id}
        )
        
        return todolist_id

    def create_project_todolist(self, title, description, creator_id, project_id, collaborator_ids):
        """Create a to-do list for a specific project"""
        creator = self.user_service.get_user_by_id(creator_id)
        project = self.project_service.get_project_by_id(project_id)
        
        if not creator or not project:
            return None
            
        # Create the to-do list
        todolist_id = len(self.todolists) + 1
        todolist = ToDoList(todolist_id, title, creator_id)
        
        # Add collaborators
        for collab_id in collaborator_ids:
            collaborator = self.user_service.get_user_by_id(collab_id)
            if collaborator:
                todolist.add_collaborator(collab_id)
                
                # Send notification to collaborator
                notification_content = f"{creator.username} added you to a to-do list for {project.title}"
                self.notification_service.create_notification(
                    collab_id,
                    creator_id,
                    self.notification_service.notification_types.TYPE_TASK_ASSIGNMENT,
                    notification_content,
                    {"todolist_id": todolist_id}
                )
        
        # Store the to-do list
        self.todolists[todolist_id] = todolist
        
        return todolist_id

    def get_todolist_by_id(self, todolist_id):
        """Get a to-do list by its ID"""
        return self.todolists.get(todolist_id)
        
    def get_todolist_tasks(self, todolist_id):
        """Get all tasks in a to-do list"""
        todolist = self.get_todolist_by_id(todolist_id)
        if not todolist:
            return []
            
        tasks = []
        for task_id in todolist.task_ids:
            task = self.tasks.get(task_id)
            if task:
                tasks.append(task)
                
        return tasks
        
    def get_user_todolists(self, user_id):
        """Get all to-do lists a user is part of"""
        user_todolists = []
        
        for todolist in self.todolists.values():
            if todolist.owner_id == user_id or user_id in todolist.collaborator_ids:
                user_todolists.append(todolist)
                
        return user_todolists

    def get_project_todolists(self, project_id):
        """Get all to-do lists associated with a project"""
        project_todolists = []
        
        # Check if project exists
        project = self.project_service.get_project_by_id(project_id)
        if not project:
            return []
        
        # First, find all tasks associated with this project
        project_tasks = self.get_project_tasks(project_id)
        project_task_ids = [task.id for task in project_tasks]
        
        # Find to-do lists containing any of these tasks
        for todolist in self.todolists.values():
            # Check if any tasks in this to-do list are from the project
            if any(task_id in project_task_ids for task_id in todolist.task_ids):
                project_todolists.append(todolist)
                continue
                
            # Also add to-do lists created by project owner or collaborators
            if todolist.owner_id == project.owner_id or todolist.owner_id in [c.id for c in project.collaborators]:
                project_todolists.append(todolist)
        
        return project_todolists
