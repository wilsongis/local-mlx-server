// MLX Server Admin GUI - Minimal JavaScript for polling and controls

// Poll /api/status every 5 seconds and update the UI
let pollInterval = setInterval(async () => {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        // Update status indicator
        const statusEl = document.getElementById('status-indicator');
        if (statusEl) {
            statusEl.className = 'status ' + data.status;
            const statusText = statusEl.querySelector('.status-text');
            if (statusText) {
                statusText.textContent = data.status.toUpperCase();
            }
        }
        
        // Update model info if available
        if (data.model && data.model.name) {
            const modelSection = document.querySelector('.model-card p');
            if (modelSection) {
                modelSection.innerHTML = '<strong>Model:</strong> ' + data.model.name;
            }
        }
        
    } catch (error) {
        console.error('Status poll failed:', error);
        // If polling fails repeatedly, the meta refresh will handle it
    }
}, 5000); // 5 seconds

// Stop polling when page is hidden (optional optimization)
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        clearInterval(pollInterval);
    } else {
        // Restart polling
        pollInterval = setInterval(async () => {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                const statusEl = document.getElementById('status-indicator');
                if (statusEl) {
                    statusEl.className = 'status ' + data.status;
                }
            } catch (e) {
                // Ignore errors when tab is in background
            }
        }, 5000);
    }
});

// Start Server
async function startServer() {
    const btn = document.getElementById('start-btn');
    btn.disabled = true;
    btn.textContent = 'Starting...';
    
    try {
        const response = await fetch('/api/start', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            alert('Server started successfully');
        } else {
            alert('Failed to start server: ' + (data.message || 'Unknown error'));
        }
    } catch (error) {
        alert('Error starting server: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Start Server';
        // Refresh status after a short delay
        setTimeout(() => location.reload(), 2000);
    }
}

// Stop Server
async function stopServer() {
    const btn = document.getElementById('stop-btn');
    btn.disabled = true;
    btn.textContent = 'Stopping...';
    
    try {
        const response = await fetch('/api/stop', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            alert('Server stopped successfully');
        } else {
            alert('Failed to stop server: ' + (data.message || 'Unknown error'));
        }
    } catch (error) {
        alert('Error stopping server: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Stop Server';
        // Refresh status after a short delay
        setTimeout(() => location.reload(), 2000);
    }
}
