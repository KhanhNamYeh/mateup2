def calculate_similarity(user_input, project):
    """Calculate similarity score between user input and existing project"""
    score = 0
    
    # Category match (25%)
    if user_input['kind'].lower() == project['kind'].lower():
        score += 25
    
    # Country match (15%)
    if user_input['country'].lower() == project['country'].lower():
        score += 15
    
    # Idea similarity (35%)
    user_idea_words = set(user_input['idea'].lower().split())
    project_idea_words = set(project['idea'].lower().split())
    if len(user_idea_words) > 0 and len(project_idea_words) > 0:
        common_words = user_idea_words.intersection(project_idea_words)
        idea_similarity = len(common_words) / max(len(user_idea_words), len(project_idea_words))
        score += 35 * idea_similarity
    
    # Partner preferences similarity (25%)
    user_partner_words = set(user_input['partner'].lower().split())
    project_partner_words = set(project['partner'].lower().split())
    if len(user_partner_words) > 0 and len(project_partner_words) > 0:
        common_words = user_partner_words.intersection(project_partner_words)
        partner_similarity = len(common_words) / max(len(user_partner_words), len(project_partner_words))
        score += 25 * partner_similarity
    
    return round(score, 1)  # Round to 1 decimal place

def find_similar_projects(self, project_data):
    """Find similar projects based on input data"""
    from services.matching_service import calculate_similarity
    
    matching_projects = []
    all_projects = self.get_projects()
    
    # Convert Project object to dictionary if needed
    if not isinstance(project_data, dict):
        project_dict = {
            'id': getattr(project_data, 'id', None),
            'kind': project_data.kind,
            'country': project_data.country,
            'name': project_data.name,
            'idea': project_data.idea,
            'partner': project_data.partner,
            'owner_id': getattr(project_data, 'owner_id', None)
        }
        project_data = project_dict
    
    for project in all_projects:
        # Skip if the project is owned by the current user
        if 'owner_id' in project_data and project['owner_id'] == project_data['owner_id']:
            continue
            
        similarity = calculate_similarity(project_data, project)
        project_copy = project.copy()
        project_copy["match_percentage"] = similarity
        matching_projects.append(project_copy)
    
    # Sort by similarity score
    matching_projects.sort(key=lambda x: x["match_percentage"], reverse=True)
    
    # Return top 5 matches
    return matching_projects[:5]

