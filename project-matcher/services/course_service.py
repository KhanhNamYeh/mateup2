from models.course import Course

class CourseService:
    def __init__(self, db, user_service):
        self.db = db
        self.user_service = user_service
        self.courses = {}
        
        # Seed some sample courses
        self._seed_sample_courses()
        
    def create_course(self, title, description, instructor_id, price, category, duration=None):
        instructor = self.user_service.get_user_by_id(instructor_id)
        if not instructor:
            return False, "Instructor not found"
            
        course_id = len(self.courses) + 1
        course = Course(course_id, title, description, instructor_id, price, category, duration)
        
        self.courses[course_id] = course
        return True, course_id
        
    def get_course_by_id(self, course_id):
        return self.courses.get(course_id)
        
    def get_courses_by_category(self, category):
        return [course for course in self.courses.values() if course.category == category]
        
    def get_recommended_courses_for_project(self, project):
        """Get courses that are relevant to the project based on title, description, or skills"""
        if not project:
            return []
            
        # Extract keywords from project
        project_keywords = set()
        if project.title:
            project_keywords.update(self._extract_keywords(project.title))
        if project.description:
            project_keywords.update(self._extract_keywords(project.description))
        if project.required_skills:
            project_keywords.update([skill.lower() for skill in project.required_skills])
            
        # Filter and score courses based on relevance
        scored_courses = []
        
        for course in self.courses.values():
            course_keywords = set()
            course_keywords.update(self._extract_keywords(course.title))
            course_keywords.update(self._extract_keywords(course.description))
            course_keywords.add(course.category.lower())
            
            # Calculate relevance score (intersection of keywords)
            common_keywords = project_keywords.intersection(course_keywords)
            if common_keywords:
                relevance_score = len(common_keywords) / len(project_keywords) * 100 if project_keywords else 0
                scored_courses.append((course, relevance_score))
                
        # Sort by relevance and return top matches
        scored_courses.sort(key=lambda x: x[1], reverse=True)
        return scored_courses[:6]  # Return top 6 matches
    
    def search_courses(self, query):
        """Search courses by title, description, or category"""
        if not query:
            return []
            
        query_keywords = self._extract_keywords(query)
        
        results = []
        for course in self.courses.values():
            course_text = f"{course.title} {course.description} {course.category}".lower()
            if any(keyword in course_text for keyword in query_keywords):
                results.append(course)
                
        return results
        
    def _extract_keywords(self, text):
        """Extract meaningful keywords from text"""
        if not text:
            return set()
            
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
        
        return set(keywords)
        
    def _seed_sample_courses(self):
        """Add some sample courses for demonstration"""
        courses_data = [
            {
                "title": "Web Development Fundamentals", 
                "description": "Learn the basics of HTML, CSS, and JavaScript to build responsive websites from scratch.",
                "instructor_id": 1, 
                "price": 49.99, 
                "category": "Web Development",
                "duration": 10,
                "video": "nu_pCVPKzTk",  # YouTube video ID
                "thumbnail": "web_dev.jpg",
                "rating": 4.5,
                "students": 1245
            },
            {
                "title": "Python for Data Science", 
                "description": "Master Python programming and essential libraries for data analysis and visualization.",
                "instructor_id": 1, 
                "price": 59.99, 
                "category": "Data Science",
                "duration": 12,
                "video": "LHBE6Q9XlzI",  # YouTube video ID
                "thumbnail": "python_ds.jpg",
                "rating": 4.7,
                "students": 3210
            },
            {
                "title": "UI/UX Design Principles", 
                "description": "Create beautiful user interfaces and seamless user experiences using modern design tools.",
                "instructor_id": 2, 
                "price": 69.99, 
                "category": "Design",
                "duration": 8,
                "video": "c9Wg6Cb_YlU",  # YouTube video ID
                "thumbnail": "uiux.jpg",
                "rating": 4.8,
                "students": 2187
            },
            {
                "title": "Mobile App Development with React Native", 
                "description": "Build cross-platform mobile applications using React Native framework.",
                "instructor_id": 2, 
                "price": 79.99, 
                "category": "Mobile Development",
                "duration": 15,
                "video": "obH0Po_RdWk",  # YouTube video ID
                "thumbnail": "react_native.jpg",
                "rating": 4.6,
                "students": 1876
            },
            {
                "title": "Machine Learning Fundamentals", 
                "description": "Introduction to machine learning algorithms and practical implementation using Python.",
                "instructor_id": 1, 
                "price": 89.99, 
                "category": "Data Science",
                "duration": 18,
                "video": "7eh4d6sabA0",  # YouTube video ID
                "thumbnail": "ml.jpg",
                "rating": 4.9,
                "students": 4567
            },
            {
                "title": "DevOps and CI/CD Pipelines", 
                "description": "Learn modern DevOps practices and how to set up continuous integration pipelines.",
                "instructor_id": 2, 
                "price": 74.99, 
                "category": "DevOps",
                "duration": 14,
                "video": "j5Zsa_eOXeY",  # YouTube video ID
                "thumbnail": "devops.jpg",
                "rating": 4.5,
                "students": 1342
            },
            {
                "title": "Full Stack JavaScript Development", 
                "description": "Master both frontend and backend development using JavaScript and popular frameworks.",
                "instructor_id": 1, 
                "price": 84.99, 
                "category": "Web Development",
                "duration": 20,
                "video": "nu_pCVPKzTk",  # YouTube video ID
                "thumbnail": "fullstack_js.jpg",
                "rating": 4.7,
                "students": 2876
            },
            {
                "title": "Blockchain and Cryptocurrency Development", 
                "description": "Understanding blockchain technology and building decentralized applications.",
                "instructor_id": 2, 
                "price": 99.99, 
                "category": "Blockchain",
                "duration": 16,
                "video": "SSo_EIwHSd4",  # YouTube video ID
                "thumbnail": "blockchain.jpg",
                "rating": 4.4,
                "students": 965
            }
        ]
        
        course_id = 1
        for data in courses_data:
            course = Course(
                course_id, 
                data["title"], 
                data["description"], 
                data["instructor_id"], 
                data["price"], 
                data["category"], 
                data["duration"]
            )
            course.video_url = data["video"]
            course.thumbnail_url = data["thumbnail"]
            course.rating = data["rating"]
            course.student_count = data["students"]
            
            self.courses[course_id] = course
            course_id += 1
