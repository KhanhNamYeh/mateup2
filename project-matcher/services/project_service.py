from models.project import Project

class ProjectService:
    def __init__(self, db, user_service):
        self.db = db
        self.user_service = user_service
        self.projects = {}
        
    def create_project(self, title, description, owner_id, required_skills=None):
        owner = self.user_service.get_user_by_id(owner_id)
        if not owner:
            return False, "User not found"
            
        project_id = len(self.projects) + 1
        project = Project(project_id, title, description, owner_id, required_skills)
        
        self.projects[project_id] = project
        owner.projects.append(project)
        
        return True, project_id
    
    def get_project_by_id(self, project_id):
        return self.projects.get(project_id)
    
    def add_collaborator(self, project_id, user_id, added_by_id):
        project = self.get_project_by_id(project_id)
        user = self.user_service.get_user_by_id(user_id)
        
        if not project or not user:
            return False, "Project or user not found"
            
        # Check if the person adding is the owner
        if project.owner_id != added_by_id:
            return False, "Only project owner can add collaborators"
            
        # Check if user is already a collaborator
        if user in project.collaborators:
            return False, "User is already a collaborator"
            
        project.collaborators.append(user)
        user.projects.append(project)
        
        return True, project_id
    
    def get_user_projects(self, user_id, as_owner=False):
        """
        Get projects associated with a user
        If as_owner is True, returns only projects where user is the owner
        Otherwise, returns all projects where user is either owner or collaborator
        """
        user = self.user_service.get_user_by_id(user_id)
        if not user:
            return []
            
        if as_owner:
            return [p for p in self.projects.values() if p.owner_id == user_id]
        else:
            return user.projects

    def get_similar_projects(self, project, exclude_owner_id=None):
        """
        Find projects similar to the given project based on title, description, and skills
        Returns a list of tuples (project, similarity_score)
        """
        similar_projects = []
        all_projects = list(self.projects.values())
        
        # If no other projects exist yet, return empty list
        if len(all_projects) <= 1:
            return []
            
        # Filter out owner's projects if exclude_owner_id is provided
        if exclude_owner_id:
            all_projects = [p for p in all_projects if p.id != project.id and p.owner_id != exclude_owner_id]
        else:
            all_projects = [p for p in all_projects if p.id != project.id]
        
        if not all_projects:  # No other projects to compare
            return []
        
        # Simple similarity calculation approach (no external libraries)
        project_keywords = set(self._extract_keywords(project.title + " " + project.description))
        project_skills = set(skill.lower() for skill in project.required_skills)
        
        for other_project in all_projects:
            other_keywords = set(self._extract_keywords(other_project.title + " " + other_project.description))
            other_skills = set(skill.lower() for skill in other_project.required_skills)
            
            # Calculate similarity score components
            keyword_similarity = self._calculate_similarity(project_keywords, other_keywords)
            skill_similarity = self._calculate_similarity(project_skills, other_skills)
            
            # Combined similarity score (weighted average)
            # 60% keywords, 40% skills (if skills exist)
            if project_skills and other_skills:
                similarity_score = (keyword_similarity * 0.6) + (skill_similarity * 0.4)
            else:
                similarity_score = keyword_similarity
            
            # Only include projects with at least 10% similarity
            if similarity_score >= 10:
                similar_projects.append((other_project, similarity_score))
        
        # Sort by similarity score (highest first)
        similar_projects.sort(key=lambda x: x[1], reverse=True)
        
        # Return top 5 similar projects
        return similar_projects[:5]

    def _extract_keywords(self, text):
        """Extract meaningful keywords from text"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation
        import string
        for char in string.punctuation:
            text = text.replace(char, ' ')
        
        # Split into words
        words = text.split()
        
        # Filter out common words (simple stopwords)
        stopwords = {'a', 'an', 'the', 'and', 'or', 'but', 'if', 'in', 'of', 'on', 'to', 'with', 'is', 'it', 'for', 'as'}
        keywords = [word for word in words if word not in stopwords and len(word) > 2]
        
        return keywords

    def _calculate_similarity(self, set1, set2):
        """Calculate Jaccard similarity between two sets (expressed as percentage)"""
        if not set1 or not set2:
            return 0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        if union == 0:
            return 0
        
        similarity = (intersection / union) * 100
        return round(similarity, 1)
