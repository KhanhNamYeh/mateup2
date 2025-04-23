from flask import Flask, request, render_template, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

# Import services
from services.user_service import UserService
from services.project_service import ProjectService
from services.connection_service import ConnectionService
from services.notification_service import NotificationService
from services.task_service import TaskService
from services.course_service import CourseService

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Set up login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize services
db = {}  # Using an in-memory db for now
user_service = UserService(db)
notification_service = NotificationService(db, user_service)
project_service = ProjectService(db, user_service)
connection_service = ConnectionService(db, user_service, notification_service)
task_service = TaskService(db, user_service, notification_service, project_service)
course_service = CourseService(db, user_service)

# Add current date to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

@login_manager.user_loader
def load_user(user_id):
    return user_service.get_user_by_id(int(user_id))

# Routes for authentication
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Validate input
        if not username or not email or not password:
            flash('All fields are required')
            return redirect(url_for('register'))
            
        # Check if user already exists
        if user_service.get_user_by_email(email):
            flash('Email already registered')
            return redirect(url_for('register'))
            
        # Create new user
        password_hash = generate_password_hash(password)
        user = user_service.create_user(username, email, password_hash)
        
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = user_service.get_user_by_email(email)
        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid email or password')
            return redirect(url_for('login'))
            
        login_user(user)
        return redirect(url_for('register_project'))
        
    return render_template('login.html')

@app.route('/register_project')
@login_required
def register_project():
    return render_template('register_project.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Dashboard
@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    user_projects = project_service.get_user_projects(current_user.id)
    user_tasks = task_service.get_user_tasks(current_user.id)
    notifications = notification_service.get_user_notifications(current_user.id, unread_only=True)
    
    return render_template('dashboard.html', 
        projects=user_projects,
        tasks=user_tasks,
        notifications=notifications
    )

# Connections routes
@app.route('/connections')
@login_required
def connections():
    accepted_connections = connection_service.get_user_connections(current_user.id, status='accepted')
    pending_connections = connection_service.get_user_connections(current_user.id, status='pending')
    
    # Get user info for accepted connections
    connection_users = {}
    for connection in accepted_connections:
        other_user_id = connection.user_id_1 if connection.user_id_2 == current_user.id else connection.user_id_2
        other_user = user_service.get_user_by_id(other_user_id)
        if other_user:
            connection_users[connection.id] = other_user
    
    # Get user info for pending connections
    pending_users = {}
    for connection in pending_connections:
        other_user_id = connection.user_id_1 if connection.user_id_2 == current_user.id else connection.user_id_2
        other_user = user_service.get_user_by_id(other_user_id)
        if other_user:
            pending_users[connection.id] = other_user
    
    # Get shared projects for each connection
    shared_projects = {}
    for connection_id, user in connection_users.items():
        other_user_id = user.id
        
        # Get projects where current user is owner and other user is collaborator
        user_owned_projects = project_service.get_user_projects(current_user.id, as_owner=True)
        projects_with_other_user = []
        
        for project in user_owned_projects:
            for collab in project.collaborators:
                if collab.id == other_user_id:
                    projects_with_other_user.append(project)
                    break
        
        # Get projects where other user is owner and current user is collaborator
        other_user_owned_projects = project_service.get_user_projects(other_user_id, as_owner=True)
        for project in other_user_owned_projects:
            for collab in project.collaborators:
                if collab.id == current_user.id:
                    projects_with_other_user.append(project)
                    break
        
        if projects_with_other_user:
            shared_projects[connection_id] = projects_with_other_user
    
    return render_template('connections.html', 
        connections=accepted_connections,
        pending_connections=pending_connections,
        connection_users=connection_users,
        pending_users=pending_users,
        shared_projects=shared_projects
    )

@app.route('/connections/send/<int:user_id>', methods=['POST'])
@login_required
def send_connection_request(user_id):
    success, result = connection_service.send_connection_request(current_user.id, user_id)
    
    if success:
        flash('Connection request sent successfully')
    else:
        flash(result)
        
    return redirect(url_for('users'))

@app.route('/connections/accept/<int:connection_id>', methods=['POST'])
@login_required
def accept_connection(connection_id):
    success, result = connection_service.accept_connection(connection_id, current_user.id)
    
    if success:
        flash('Connection accepted')
        # Redirect to connection detail page to show suggested tasks
        return redirect(url_for('connection_detail', connection_id=connection_id))
    else:
        flash(result)
        
    return redirect(url_for('notifications'))

@app.route('/connections/detail/<int:connection_id>')
@login_required
def connection_detail(connection_id):
    connection = connection_service.get_connection_by_id(connection_id)
    if not connection:
        flash('Connection not found')
        return redirect(url_for('connections'))
    
    # Verify user is part of this connection
    if connection.user_id_1 != current_user.id and connection.user_id_2 != current_user.id:
        flash('You are not authorized to view this connection')
        return redirect(url_for('connections'))
    
    # Get the other user in the connection
    other_user_id = connection.user_id_1 if connection.user_id_2 == current_user.id else connection.user_id_2
    other_user = user_service.get_user_by_id(other_user_id)
    
    # Get suggested tasks based on user skills and projects
    suggested_tasks = task_service.get_suggested_tasks(current_user.id, other_user_id)
    
    return render_template('connection_detail.html', 
                          connection=connection, 
                          other_user=other_user, 
                          suggested_tasks=suggested_tasks)

@app.route('/connections/create-todolist/<int:connection_id>', methods=['POST'])
@login_required
def create_connection_todolist(connection_id):
    connection = connection_service.get_connection_by_id(connection_id)
    if not connection:
        flash('Connection not found')
        return redirect(url_for('connections'))
    
    # Check authorization
    if connection.user_id_1 != current_user.id and connection.user_id_2 != current_user.id:
        flash('You are not authorized for this action')
        return redirect(url_for('connections'))
    
    # Get the other user
    other_user_id = connection.user_id_1 if connection.user_id_2 == current_user.id else connection.user_id_2
    
    # Get selected task IDs from form
    selected_task_ids = request.form.getlist('task_ids')
    custom_tasks = request.form.get('custom_tasks', '').strip().split('\n')
    custom_tasks = [task.strip() for task in custom_tasks if task.strip()]
    
    # Create a collaborative to-do list
    todolist_id = task_service.create_collaborative_todolist(
        current_user.id, 
        other_user_id, 
        selected_task_ids, 
        custom_tasks
    )
    
    flash('To-do list created successfully!')
    return redirect(url_for('view_todolist', todolist_id=todolist_id))

@app.route('/projects/<int:project_id>/create-todolist', methods=['GET', 'POST'])
@login_required
def create_project_todolist(project_id):
    project = project_service.get_project_by_id(project_id)
    if not project:
        flash('Project not found')
        return redirect(url_for('projects'))
        
    # Check if user is owner or collaborator
    if project.owner_id != current_user.id and current_user not in project.collaborators:
        flash('You do not have access to this project')
        return redirect(url_for('projects'))
    
    # Get project collaborators for the form
    project_members = [user_service.get_user_by_id(project.owner_id)]
    for collab in project.collaborators:
        project_members.append(collab)
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description', '')
        collaborator_ids = request.form.getlist('collaborator_ids')
        collaborator_ids = [int(cid) for cid in collaborator_ids if cid]
        
        # Validate selected collaborators are part of the project
        valid_ids = [user.id for user in project_members if user.id != current_user.id]
        for cid in collaborator_ids:
            if cid not in valid_ids:
                flash('Invalid collaborator selected')
                return redirect(url_for('create_project_todolist', project_id=project_id))
        
        # Create to-do list
        todolist_id = task_service.create_project_todolist(
            title,
            description,
            current_user.id,
            project_id,
            collaborator_ids
        )
        
        flash('To-do list created successfully')
        return redirect(url_for('view_todolist', todolist_id=todolist_id))
    
    return render_template('create_project_todolist.html',
                          project=project,
                          project_members=project_members)

@app.route('/todolist/<int:todolist_id>')
@login_required
def view_todolist(todolist_id):
    todolist = task_service.get_todolist_by_id(todolist_id)
    if not todolist:
        flash('To-do list not found')
        return redirect(url_for('todo_list'))
    
    # Check authorization
    if todolist.owner_id != current_user.id and current_user.id not in todolist.collaborator_ids:
        flash('You do not have access to this to-do list')
        return redirect(url_for('todo_list'))
    
    # Get participants
    owner = user_service.get_user_by_id(todolist.owner_id)
    collaborators = [user_service.get_user_by_id(uid) for uid in todolist.collaborator_ids]
    
    # Get all tasks in the to-do list
    todolist_tasks = task_service.get_todolist_tasks(todolist_id)
    
    return render_template('view_todolist.html',
                          todolist=todolist,
                          owner=owner,
                          collaborators=collaborators,
                          tasks=todolist_tasks)

@app.route('/todolist/<int:todolist_id>/add-task', methods=['POST'])
@login_required
def add_task_to_todolist(todolist_id):
    todolist = task_service.get_todolist_by_id(todolist_id)
    if not todolist:
        flash('To-do list not found')
        return redirect(url_for('todo_list'))
    
    # Check authorization
    if todolist.owner_id != current_user.id and current_user.id not in todolist.collaborator_ids:
        flash('You are not authorized to add tasks to this to-do list')
        return redirect(url_for('todo_list'))
    
    title = request.form.get('title')
    description = request.form.get('description', '')
    assignee_id = int(request.form.get('assignee_id'))
    
    # Verify assignee is either owner or collaborator
    valid_assignees = [todolist.owner_id] + todolist.collaborator_ids
    if assignee_id not in valid_assignees:
        flash('Invalid task assignee')
        return redirect(url_for('view_todolist', todolist_id=todolist_id))
    
    # Create the task
    task_id = len(task_service.tasks) + 1
    new_task = task_service.create_task(
        title,
        description,
        None,  # No project
        assignee_id,
        current_user.id
    )
    
    if new_task[0]:  # If task creation successful
        task_id = new_task[1]
        # Add task to todolist
        todolist.add_task(task_id)
        todolist.updated_at = datetime.now()
        flash('Task added successfully')
    else:
        flash(f'Error adding task: {new_task[1]}')
        
    return redirect(url_for('view_todolist', todolist_id=todolist_id))

@app.route('/connections/decline/<int:connection_id>', methods=['POST'])
@login_required
def decline_connection(connection_id):
    success, result = connection_service.decline_connection(connection_id, current_user.id)
    
    if success:
        flash('Connection declined')
    else:
        flash(result)
        
    return redirect(url_for('notifications'))

# Notification routes
@app.route('/notifications')
@login_required
def notifications():
    user_notifications = notification_service.get_user_notifications(current_user.id)
    return render_template('notifications.html', notifications=user_notifications)

@app.route('/notifications/mark_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    success, result = notification_service.mark_notification_as_read(notification_id, current_user.id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': success, 'message': result if not success else 'Marked as read'})
    
    return redirect(url_for('notifications'))

# Add API endpoint for notification count
@app.route('/api/notifications/unread/count')
@login_required
def get_unread_notification_count():
    notifications = notification_service.get_user_notifications(current_user.id, unread_only=True)
    return jsonify({'count': len(notifications)})

# Project routes
@app.route('/projects')
@login_required
def projects():
    user_projects = project_service.get_user_projects(current_user.id)
    return render_template('projects.html', projects=user_projects)

@app.route('/projects/new', methods=['GET', 'POST'])
@login_required
def create_project():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        required_skills = request.form.get('required_skills', '').split(',')
        required_skills = [skill.strip() for skill in required_skills if skill.strip()]
        
        success, project_id = project_service.create_project(
            title, description, current_user.id, required_skills
        )
        
        if success:
            flash('Project created successfully')
            project = project_service.get_project_by_id(project_id)
            
            # Find similar projects
            similar_projects = project_service.get_similar_projects(project, current_user.id)
            
            if similar_projects:
                # Store similar projects in session for the similar_projects route
                session['similar_projects'] = [(p[0].id, p[1]) for p in similar_projects]
                return redirect(url_for('similar_projects', project_id=project_id))
            else:
                return redirect(url_for('project_detail', project_id=project_id))
        else:
            flash(project_id)  # Error message
            
    return render_template('create_project.html')

@app.route('/projects/<int:project_id>/similar')
@login_required
def similar_projects(project_id):
    project = project_service.get_project_by_id(project_id)
    if not project:
        flash('Project not found')
        return redirect(url_for('projects'))
        
    # Verify the user is the project owner
    if project.owner_id != current_user.id:
        flash('Unauthorized access')
        return redirect(url_for('projects'))
        
    # Get similar projects from session
    similar_project_ids = session.get('similar_projects', [])
    
    # Clear from session after retrieval
    if 'similar_projects' in session:
        del session['similar_projects']
    
    similar_projects_data = []
    for proj_id, similarity in similar_project_ids:
        similar_project = project_service.get_project_by_id(proj_id)
        if similar_project:
            owner = user_service.get_user_by_id(similar_project.owner_id)
            # Check if connection already exists or requested
            connection_status = "none"
            for conn in connection_service.connections.values():
                if ((conn.user_id_1 == current_user.id and conn.user_id_2 == owner.id) or
                    (conn.user_id_2 == current_user.id and conn.user_id_1 == owner.id)):
                    connection_status = conn.status
                    break
                    
            similar_projects_data.append({
                'project': similar_project,
                'similarity': round(similarity, 1),
                'owner': owner,
                'connection_status': connection_status
            })
    
    return render_template('similar_projects.html', 
        project=project,
        similar_projects=similar_projects_data
    )

@app.route('/projects/connect/<int:owner_id>/<int:project_id>', methods=['POST'])
@login_required
def connect_with_project_owner(owner_id, project_id):
    if owner_id == current_user.id:
        flash('You cannot connect with yourself')
        return redirect(url_for('similar_projects', project_id=project_id))
    
    # Get project for the message
    project = project_service.get_project_by_id(project_id)
    if not project:
        flash('Project not found')
        return redirect(url_for('projects'))
    
    # Send connection request
    success, result = connection_service.send_connection_request(
        current_user.id, 
        owner_id, 
        f"Interested in collaboration on similar project: {project.title}"
    )
    
    if success:
        flash('Connection request sent successfully')
    else:
        flash(result)
        
    return redirect(url_for('similar_projects', project_id=project_id))

@app.route('/projects/<int:project_id>')
@login_required
def project_detail(project_id):
    project = project_service.get_project_by_id(project_id)
    if not project:
        flash('Project not found')
        return redirect(url_for('projects'))
        
    # Check if user is owner or collaborator
    if project.owner_id != current_user.id and current_user not in project.collaborators:
        flash('You do not have access to this project')
        return redirect(url_for('projects'))
    
    # Get the owner user object
    owner = user_service.get_user_by_id(project.owner_id)
    
    # Get to-do lists for this project instead of tasks
    todo_lists = task_service.get_project_todolists(project_id)
    
    # Calculate progress for each to-do list
    todolist_progress = {}
    for todolist in todo_lists:
        todolist_tasks = task_service.get_todolist_tasks(todolist.id)
        if todolist_tasks:
            completed_tasks = sum(1 for task in todolist_tasks if task.status == 'completed')
            progress = round((completed_tasks / len(todolist_tasks)) * 100) if todolist_tasks else 0
            todolist_progress[todolist.id] = progress
    
    return render_template('project_detail.html', 
                           project=project, 
                           owner=owner,
                           todo_lists=todo_lists,
                           todolist_progress=todolist_progress)

@app.route('/projects/<int:project_id>/add_collaborator', methods=['GET', 'POST'])
@login_required
def add_collaborator_form(project_id):
    project = project_service.get_project_by_id(project_id)
    if not project:
        flash('Project not found')
        return redirect(url_for('projects'))
        
    # Only the owner can add collaborators
    if project.owner_id != current_user.id:
        flash('Only the project owner can add collaborators')
        return redirect(url_for('project_detail', project_id=project_id))
        
    if request.method == 'POST':
        user_id = request.form.get('user_id', type=int)
        if user_id:
            success, message = project_service.add_collaborator(project_id, user_id, current_user.id)
            if success:
                flash('Team member added successfully')
                return redirect(url_for('project_detail', project_id=project_id))
            else:
                flash(message)
                
    # Get all users except current user and existing collaborators
    all_users = user_service.get_all_users()
    collaborator_ids = [c.id for c in project.collaborators]
    available_users = [u for u in all_users if u.id != current_user.id and u.id not in collaborator_ids]
    
    return render_template('add_collaborator.html', project=project, available_users=available_users)

@app.route('/projects/<int:project_id>/todolists')
@login_required
def project_todolist(project_id):
    project = project_service.get_project_by_id(project_id)
    if not project:
        flash('Project not found')
        return redirect(url_for('projects'))
        
    # Check if user is owner or collaborator
    if project.owner_id != current_user.id and current_user not in project.collaborators:
        flash('You do not have access to this project')
        return redirect(url_for('projects'))
    
    # Get to-do lists related to this project
    project_todolists = task_service.get_project_todolists(project_id)
    
    # Calculate progress for each to-do list
    todolist_progress = {}
    for todolist in project_todolists:
        todolist_tasks = task_service.get_todolist_tasks(todolist.id)
        if todolist_tasks:
            completed_tasks = sum(1 for task in todolist_tasks if task.status == 'completed')
            progress = round((completed_tasks / len(todolist_tasks)) * 100) if todolist_tasks else 0
            todolist_progress[todolist.id] = progress
    
    # Get collaborators for each to-do list
    todolist_collaborators = {}
    for todolist in project_todolists:
        collaborators = []
        for collab_id in todolist.collaborator_ids:
            user = user_service.get_user_by_id(collab_id)
            if user:
                collaborators.append(user)
        todolist_collaborators[todolist.id] = collaborators
    
    return render_template('project_todolists.html',
                          project=project,
                          todolists=project_todolists,
                          todolist_progress=todolist_progress,
                          todolist_collaborators=todolist_collaborators)

@app.route('/projects/<int:project_id>/courses')
@login_required
def project_courses(project_id):
    project = project_service.get_project_by_id(project_id)
    if not project:
        flash('Project not found')
        return redirect(url_for('projects'))
        
    # Check if user is owner or collaborator
    if project.owner_id != current_user.id and current_user not in project.collaborators:
        flash('You do not have access to this project')
        return redirect(url_for('projects'))
    
    # Get recommended courses based on project
    recommended_courses = course_service.get_recommended_courses_for_project(project)
    
    # Get all categories for filtering
    all_categories = set(course.category for course in course_service.courses.values())
    
    return render_template('project_courses.html',
                          project=project,
                          recommended_courses=recommended_courses,
                          all_categories=all_categories)

@app.route('/courses/<int:course_id>')
@login_required
def course_detail(course_id):
    course = course_service.get_course_by_id(course_id)
    if not course:
        flash('Course not found')
        return redirect(url_for('projects'))
        
    instructor = user_service.get_user_by_id(course.instructor_id)
    
    # Get referrer project_id if coming from a project page
    project_id = request.args.get('project_id')
    project = None
    if project_id:
        try:
            project = project_service.get_project_by_id(int(project_id))
        except:
            pass
    
    return render_template('course_detail.html',
                          course=course,
                          instructor=instructor,
                          project=project)

@app.route('/courses/search')
@login_required
def search_courses():
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    
    if query:
        courses = course_service.search_courses(query)
    elif category:
        courses = course_service.get_courses_by_category(category)
    else:
        courses = list(course_service.courses.values())
    
    all_categories = set(course.category for course in course_service.courses.values())
    
    return render_template('search_courses.html',
                          courses=courses,
                          query=query,
                          selected_category=category,
                          all_categories=all_categories)

# Task routes
@app.route('/tasks')
@login_required
def tasks():
    assigned_tasks = task_service.get_user_tasks(current_user.id, as_assignee=True)
    created_tasks = task_service.get_user_tasks(current_user.id, as_assignee=False)
    
    # Create a dictionary of projects for easy lookup in template
    projects_dict = {}
    for task in assigned_tasks + created_tasks:
        if task.project_id not in projects_dict:
            project = project_service.get_project_by_id(task.project_id)
            if project:
                projects_dict[task.project_id] = project
    
    # Create a dictionary of users for easy lookup in template
    users_dict = {}
    for task in created_tasks:
        if task.assignee_id not in users_dict:
            user = user_service.get_user_by_id(task.assignee_id)
            if user:
                users_dict[task.assignee_id] = {
                    'id': user.id,
                    'username': user.username
                }
    
    return render_template('tasks.html', 
        assigned_tasks=assigned_tasks,
        created_tasks=created_tasks,
        projects_dict=projects_dict,
        users_dict=users_dict
    )

@app.route('/tasks/new/<int:project_id>', methods=['GET', 'POST'])
@login_required
def create_task(project_id):
    project = project_service.get_project_by_id(project_id)
    if not project:
        flash('Project not found')
        return redirect(url_for('projects'))
        
    # Check if user is allowed to create tasks
    if project.owner_id != current_user.id and current_user not in project.collaborators:
        flash('You are not authorized to create tasks for this project')
        return redirect(url_for('project_detail', project_id=project_id))
        
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        assignee_id = int(request.form.get('assignee_id'))
        due_date_str = request.form.get('due_date')
        
        # Parse due date if provided
        due_date = None
        if due_date_str:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
            
        success, result = task_service.create_task(
            title, 
            description, 
            project_id,
            assignee_id,
            current_user.id,
            due_date
        )
        
        if success:
            flash('Task created successfully')
            return redirect(url_for('project_detail', project_id=project_id))
        else:
            flash(result)
            
    # Get potential assignees (project owner + collaborators)
    assignees = [project.owner_id]
    assignees.extend([collaborator.id for collaborator in project.collaborators])
    assignees = [user_service.get_user_by_id(user_id) for user_id in assignees]
    
    return render_template('create_task.html', 
        project=project,
        assignees=assignees
    )

@app.route('/tasks/<int:task_id>/update', methods=['POST'])
@login_required
def update_task_status(task_id):
    new_status = request.form.get('status')
    success, result = task_service.update_task_status(task_id, current_user.id, new_status)
    
    if success:
        flash('Task status updated')
    else:
        flash(result)
        
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': success, 'message': result if not success else 'Status updated'})
        
    # Get the task to redirect back to proper project
    task = task_service.tasks.get(task_id)
    if task:
        return redirect(url_for('project_detail', project_id=task.project_id))
    return redirect(url_for('tasks'))

@app.route('/tasks/<int:task_id>/update-status', methods=['POST'])
@login_required
def update_task_status_ajax(task_id):
    if not request.is_json:
        return jsonify(success=False, message="Request must be JSON"), 400
        
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status not in ['pending', 'accepted', 'in_progress', 'completed']:
        return jsonify(success=False, message="Invalid status"), 400
        
    success, result = task_service.update_task_status(task_id, current_user.id, new_status)
    
    if success:
        return jsonify(success=True, message="Status updated")
    else:
        return jsonify(success=False, message=result), 400

# User routes
@app.route('/users')
@login_required
def users():
    all_users = user_service.get_all_users()
    # Don't show current user in the list
    all_users = [user for user in all_users if user.id != current_user.id]
    
    # Get existing connections
    user_connections = connection_service.get_user_connections(current_user.id)
    
    # Create a set of user IDs that are already connected or have pending connections
    connected_ids = set()
    for conn in user_connections:
        if conn.user_id_1 == current_user.id:
            connected_ids.add(conn.user_id_2)
        else:
            connected_ids.add(conn.user_id_1)
    
    return render_template('users.html', 
        users=all_users,
        connected_ids=connected_ids
    )

# To-do list routes
@app.route('/todo')
@login_required
def todo_list():
    # User's personal tasks
    user_tasks = task_service.get_user_tasks(current_user.id)
    # User's collaborative to-do lists
    user_todolists = task_service.get_user_todolists(current_user.id)
    
    # Calculate progress for each to-do list
    todolist_progress = {}
    for todolist in user_todolists:
        todolist_tasks = task_service.get_todolist_tasks(todolist.id)
        if todolist_tasks:
            completed_tasks = sum(1 for task in todolist_tasks if task.status == 'completed')
            progress = round((completed_tasks / len(todolist_tasks)) * 100) if todolist_tasks else 0
            todolist_progress[todolist.id] = progress
    
    # Group tasks by status
    pending_tasks = [t for t in user_tasks if t.status == 'pending']
    accepted_tasks = [t for t in user_tasks if t.status == 'accepted']
    in_progress_tasks = [t for t in user_tasks if t.status == 'in_progress']
    completed_tasks = [t for t in user_tasks if t.status == 'completed']
    
    return render_template('todo.html',
        pending_tasks=pending_tasks,
        accepted_tasks=accepted_tasks,
        in_progress_tasks=in_progress_tasks,
        completed_tasks=completed_tasks,
        todolists=user_todolists,
        todolist_progress=todolist_progress)

# Add a route to serve placeholder images when real ones aren't available
@app.route('/static/images/courses/<filename>')
def course_image(filename):
    import os
    from flask import send_from_directory, redirect
    
    # Check if the requested image file exists
    image_path = os.path.join(app.static_folder, 'images', 'courses', filename)
    if os.path.isfile(image_path):
        return send_from_directory(os.path.join(app.static_folder, 'images', 'courses'), filename)
    
    # If not, redirect to a square placeholder image with the course name
    course_name = os.path.splitext(filename)[0].replace('_', ' ').title()
    placeholder_url = f"https://via.placeholder.com/300x300?text={course_name}"
    return redirect(placeholder_url)

# Create missing templates directory if not exists
import os
if not os.path.exists('templates'):
    os.makedirs('templates')
if not os.path.exists('static/css'):
    os.makedirs('static/css')
if not os.path.exists('static/js'):
    os.makedirs('static/js')

if __name__ == '__main__':
    # Create some test users
    user1 = user_service.create_user('test1', 'test1@example.com', generate_password_hash('password'))
    user2 = user_service.create_user('test2', 'test2@example.com', generate_password_hash('password'))
    
    app.run(debug=True)