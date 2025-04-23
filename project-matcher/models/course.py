from datetime import datetime

class Course:
    def __init__(self, id, title, description, instructor_id, price, category, duration=None):
        self.id = id
        self.title = title
        self.description = description
        self.instructor_id = instructor_id
        self.price = price
        self.category = category
        self.duration = duration  # in hours
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.video_url = None
        self.thumbnail_url = None
        self.rating = 0
        self.student_count = 0
        
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'instructor_id': self.instructor_id,
            'price': self.price,
            'category': self.category,
            'duration': self.duration,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'video_url': self.video_url,
            'thumbnail_url': self.thumbnail_url,
            'rating': self.rating,
            'student_count': self.student_count
        }
