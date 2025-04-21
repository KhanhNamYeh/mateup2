# Project Matcher

## Overview
Project Matcher is a web application designed to help users find similar projects based on their input. Users can register their project details, including the type of project, country, name, their idea, and what they are looking for in a partner. The application then provides a list of similar projects that match their criteria.

## Features
- User-friendly registration form for project details.
- Matching algorithm to find similar projects.
- Clean and responsive frontend design.
- Easy navigation between pages.

## Technologies Used
- Python
- Flask (for backend)
- HTML/CSS (for frontend)
- JavaScript (for client-side functionality)

## Project Structure
```
project-matcher
├── app.py                # Main application file
├── requirements.txt      # Project dependencies
├── static                # Static files (CSS, JS)
│   ├── css
│   │   └── style.css     # Styles for the application
│   └── js
│       └── main.js       # JavaScript for client-side functionality
├── templates             # HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Homepage
│   ├── register.html     # Registration form
│   └── results.html      # Results page
├── models                # Data models
│   ├── __init__.py       # Initialize models package
│   └── project.py        # Project model definition
├── services              # Business logic services
│   ├── __init__.py       # Initialize services package
│   └── matching_service.py # Logic for matching projects
├── .gitignore            # Git ignore file
└── README.md             # Project documentation
```

## Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```
   cd project-matcher
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
1. Run the application:
   ```
   python app.py
   ```
2. Open your web browser and go to `http://127.0.0.1:5000` to access the application.
3. Navigate to the registration page to submit your project details and view similar projects.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.