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

// Add these functions
function showAllowanceModal() {
    document.getElementById('allowanceModal').style.display = 'block';
}

function hideAllowanceModal() {
    document.getElementById('allowanceModal').style.display = 'none';
}

function showEarningsModal() {
    document.getElementById('earningsModal').style.display = 'block';
}

function hideEarningsModal() {
    document.getElementById('earningsModal').style.display = 'none';
}

// Close modals when clicking outside
window.onclick = function(event) {
    if (event.target.className === 'modal') {
        event.target.style.display = 'none';
    }
} 