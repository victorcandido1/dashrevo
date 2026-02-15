// Main application JavaScript

// Global app state
const AppState = {
    dataLoaded: false,
    currentFilters: {},
    activeTab: 'dashboard'
};

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    checkDataStatus();
});

// Check if data is loaded
async function checkDataStatus() {
    try {
        const response = await fetch('/api/data/status');
        const data = await response.json();
        AppState.dataLoaded = data.loaded;
        
        const statusEl = document.getElementById('data-status');
        if (statusEl) {
            if (data.loaded) {
                statusEl.textContent = `✓ ${data.filtered_records.toLocaleString()} registros`;
                statusEl.className = 'text-sm bg-green-600 px-3 py-1 rounded';
            } else {
                statusEl.textContent = 'No data loaded';
                statusEl.className = 'text-sm bg-blue-700 px-3 py-1 rounded';
            }
        }
    } catch (error) {
        console.error('Error checking data status:', error);
    }
}

// Export for use in other scripts
window.AppState = AppState;
window.checkDataStatus = checkDataStatus;


