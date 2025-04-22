from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from models.project import Project
from services.data_service import DataService
import os
import functools

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management
data_service = DataService()  # Initialize data service

# Login required decorator
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page')
            return redirect(url_for('login_page'))
        return view(*args, **kwargs)
    return wrapped_view

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = data_service.authenticate_user(email, password)
        if not user:
            flash('Invalid email or password')
            return render_template('login.html')
        
        # Set session
        session['user_id'] = user['id']
        session['user_email'] = user['email']
        session['user_name'] = user['name']
        
        flash('Login successful')
        return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validation
        if data_service.get_user_by_email(email):
            flash('Email already registered')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match')
            return render_template('register.html')
        
        # Create user
        user = data_service.create_user(name, email, password)
        if not user:
            flash('Registration failed')
            return render_template('register.html')
        
        # Set session
        session['user_id'] = user['id']
        session['user_email'] = user['email']
        session['user_name'] = user['name']
        
        flash('Registration successful')
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/register-project', methods=['GET', 'POST'])
@login_required
def register_project():
    if request.method == 'POST':
        kind = request.form['kind']
        country = request.form['country']
        name = request.form['name']
        idea = request.form['idea']
        partner = request.form['partner']
        
        # Create project
        project = data_service.create_project(
            owner_id=session['user_id'],
            name=name,
            kind=kind,
            country=country,
            idea=idea,
            partner=partner
        )
        
        if not project:
            flash('Failed to create project')
            return render_template('register_project.html')
        
        # Find similar projects
        similar_projects = data_service.find_similar_projects(project)
        
        return render_template('results.html', projects=similar_projects)
    
    categories = data_service.get_categories()
    countries = data_service.get_countries()
    
    return render_template(
        'register_project.html', 
        categories=categories,
        countries=countries
    )

@app.route('/results')
def results():
    # This route would typically be accessed with parameters
    # For now, redirect to the register page if accessed directly
    return redirect(url_for('register_project'))

@app.route('/register-user', methods=['POST'])
def register_user():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validation
        if data_service.get_user_by_email(email):
            flash('Email already registered')
            return redirect(url_for('index'))
        
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('index'))
        
        # Create user
        user = data_service.create_user(name, email, password)
        if not user:
            flash('Registration failed')
            return redirect(url_for('index'))
        
        # Set session
        session['user_id'] = user['id']
        session['user_email'] = user['email']
        session['user_name'] = user['name']
        
        flash('Registration successful')
        return redirect(request.referrer or url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out')
    return redirect(url_for('index'))

@app.route('/save-project', methods=['POST'])
@login_required
def save_project():
    data = request.json
    project_id = data.get('project_id')
    user_id = session['user_id']
    
    success = data_service.save_project_for_user(user_id, project_id)
    
    if success:
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'Project already saved or not found'})

@app.route('/send-connection', methods=['POST'])
@login_required
def send_connection():
    project_id = request.form['project_id']
    message = request.form['message']
    user_id = session['user_id']
    
    connection = data_service.create_connection(user_id, project_id, message)
    
    if connection:
        flash('Connection request sent successfully!')
    else:
        flash('Failed to send connection request')
    
    return redirect(request.referrer or url_for('index'))

@app.route('/my-projects')
@login_required
def my_projects():
    user_id = session['user_id']
    user_projects = data_service.get_projects_by_user(user_id)
    saved_projects = data_service.get_saved_projects_by_user(user_id)
    
    return render_template(
        'my_projects.html', 
        projects=user_projects, 
        saved_projects=saved_projects
    )

@app.route('/my-connections')
@login_required
def my_connections():
    user_id = session['user_id']
    connections = data_service.get_connections_by_user(user_id)
    
    # Enrich connection data
    for conn in connections:
        conn['from_user'] = data_service.get_user_by_id(conn['from_user_id'])
        conn['to_user'] = data_service.get_user_by_id(conn['to_user_id'])
        conn['project'] = data_service.get_project_by_id(conn['to_project_id'])
    
    return render_template('my_connections.html', connections=connections)

@app.route('/update-connection/<int:connection_id>', methods=['POST'])
@login_required
def update_connection(connection_id):
    action = request.form.get('action')
    
    if action not in ('accept', 'reject'):
        flash('Invalid action')
        return redirect(url_for('my_connections'))
    
    status = 'accepted' if action == 'accept' else 'rejected'
    success = data_service.update_connection_status(connection_id, status)
    
    if success:
        flash(f'Connection request {status}')
    else:
        flash('Failed to update connection status')
    
    return redirect(url_for('my_connections'))

@app.route('/notifications')
@login_required
def notifications():
    user_id = session['user_id']
    notifications = data_service.get_notifications_for_user(user_id)
    
    return render_template('notifications.html', notifications=notifications)

@app.route('/api/notifications')
@login_required
def api_notifications():
    user_id = session['user_id']
    notifications = data_service.get_notifications_for_user(user_id)
    
    return jsonify({
        "count": len(notifications),
        "notifications": notifications[:5]  # Return top 5 notifications
    })

@app.route('/delete-connection/<int:connection_id>', methods=['POST'])
@login_required
def delete_connection(connection_id):
    user_id = session['user_id']
    success = data_service.delete_connection(connection_id, user_id)
    
    if success:
        flash('Connection request deleted')
    else:
        flash('Failed to delete connection request')
    
    return redirect(url_for('my_connections'))

@app.route('/view-project/<int:project_id>')
def view_project(project_id):
    project = data_service.get_project_by_id(project_id)
    
    if not project:
        flash('Project not found')
        return redirect(url_for('index'))
    
    owner = data_service.get_user_by_id(project['owner_id'])
    
    # Check if current user is logged in
    can_connect = False
    has_connection = False
    connection_status = None
    
    if session.get('user_id'):
        user_id = session['user_id']
        # Can't connect to own project
        can_connect = project['owner_id'] != user_id
        
        # Check for existing connection
        connection = data_service.get_connection_by_project_and_user(project_id, user_id)
        if connection:
            has_connection = True
            connection_status = connection['status']
    
    return render_template(
        'view_project.html',
        project=project,
        owner=owner,
        can_connect=can_connect,
        has_connection=has_connection,
        connection_status=connection_status
    )
if __name__ == '__main__':
    app.run(debug=True)