// Flash message auto-dismiss
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 3000);
    });
});

// Form validation
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(e) {
        const emailInputs = form.querySelectorAll('input[type="email"]');
        const passwordInput = form.querySelector('input[type="password"]');
        
        emailInputs.forEach(input => {
            if (!input.value.includes('@')) {
                e.preventDefault();
                alert('Please enter a valid email address');
            }
        });
        
        if (passwordInput && passwordInput.value.length < 6) {
            e.preventDefault();
            alert('Password must be at least 6 characters long');
        }
    });
}); 