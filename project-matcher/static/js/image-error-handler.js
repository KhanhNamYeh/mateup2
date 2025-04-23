/**
 * Function to handle course image loading errors
 * Replaces broken images with placeholder images that show the course title
 */
document.addEventListener('DOMContentLoaded', function() {
    // Find all course thumbnail images
    const courseImages = document.querySelectorAll('.course-thumbnail img');
    
    // Add error handling to each image
    courseImages.forEach(img => {
        img.onerror = function() {
            // Clear the error handler to prevent loops
            this.onerror = null;
            
            // Get course title from alt text
            const courseTitle = this.alt || 'Course';
            
            // Create a URL-safe version of the title
            const encodedTitle = encodeURIComponent(courseTitle);
            
            // Set a placeholder image with the course title
            this.src = `https://via.placeholder.com/300x300?text=${encodedTitle}`;
        };
    });
});
