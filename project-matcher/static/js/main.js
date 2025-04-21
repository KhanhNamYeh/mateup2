document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.getElementById('register-form');
    
    registerForm.addEventListener('submit', function(event) {
        event.preventDefault();
        
        const kind = document.getElementById('kind').value;
        const country = document.getElementById('country').value;
        const name = document.getElementById('name').value;
        const idea = document.getElementById('idea').value;
        const partner = document.getElementById('partner').value;

        if (kind && country && name && idea && partner) {
            const formData = {
                kind: kind,
                country: country,
                name: name,
                idea: idea,
                partner: partner
            };

            fetch('/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                window.location.href = '/results';
            })
            .catch(error => {
                console.error('Error:', error);
            });
        } else {
            alert('Please fill in all fields.');
        }
    });
});