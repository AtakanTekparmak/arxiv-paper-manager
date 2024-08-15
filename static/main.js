document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search');
    searchInput.addEventListener('search', function() {
        if (this.value === '') {
            window.location.href = '/';
        }
    });
});