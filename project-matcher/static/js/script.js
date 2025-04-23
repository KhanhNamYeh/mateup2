document.addEventListener('DOMContentLoaded', function() {
    // Handle flash messages - fade out after 5 seconds
    const flashMessages = document.querySelectorAll('.flash-message');
    if (flashMessages.length > 0) {
        setTimeout(() => {
            flashMessages.forEach(message => {
                message.style.opacity = '0';
                setTimeout(() => {
                    message.style.display = 'none';
                }, 500);
            });
        }, 5000);
    }

    // Update notification badge count
    function updateNotificationCount() {
        fetch('/api/notifications/unread/count')
            .then(response => response.json())
            .then(data => {
                const badgeElement = document.getElementById('notification-count');
                if (badgeElement) {
                    if (data.count > 0) {
                        badgeElement.textContent = data.count;
                        badgeElement.style.display = 'flex';
                    } else {
                        badgeElement.style.display = 'none';
                    }
                }
            })
            .catch(error => console.error('Error fetching notification count:', error));
    }

    // If user is logged in, check for notifications periodically
    const notificationBadge = document.getElementById('notification-count');
    if (notificationBadge) {
        updateNotificationCount();
        // Check for new notifications every minute
        setInterval(updateNotificationCount, 60000);
    }
});
