document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search');
    searchInput.addEventListener('search', function() {
        if (this.value === '') {
            window.location.href = '/';
        }
    });

    // Toggle button functionality
    const toggleButtons = document.querySelectorAll('.toggle-button');
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const isActive = this.classList.contains('active');
            const filter = this.id.replace('-toggle', '');
            
            if (isActive) {
                // Remove filter
                window.location.href = '/';
            } else {
                // Apply filter
                window.location.href = `/?filter=${filter}`;
            }
            
            // Toggle active state
            toggleButtons.forEach(btn => btn.classList.remove('active'));
            if (!isActive) {
                this.classList.add('active');
            }
        });
    });
});