// orders/static/orders/js/main.js

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('OrderHub loaded successfully!');
    
    // Auto-dismiss alerts after 5 seconds
    autoDismissAlerts();
    
    // Add hover effects to cards
    addCardHoverEffects();
    
    // Initialize any tooltips
    initTooltips();
});

/**
 * Auto-dismiss alert messages after 5 seconds
 */
function autoDismissAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const closeButton = alert.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            } else {
                alert.style.transition = 'opacity 0.5s';
                alert.style.opacity = '0';
                setTimeout(function() {
                    alert.style.display = 'none';
                }, 500);
            }
        }, 5000);
    });
}

/**
 * Add hover effects to stat cards
 */
function addCardHoverEffects() {
    const cards = document.querySelectorAll('.stat-card, .card');
    cards.forEach(function(card) {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-3px)';
            this.style.transition = 'transform 0.3s ease';
            this.style.boxShadow = '0 4px 15px rgba(0,0,0,0.12)';
        });
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '';
        });
    });
}

/**
 * Initialize Bootstrap tooltips
 */
function initTooltips() {
    // If Bootstrap is loaded and tooltips are available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

/**
 * Format currency in Ugandan Shillings
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-UG', {
        style: 'currency',
        currency: 'UGX',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

/**
 * Get status badge color
 */
function getStatusColor(status) {
    const statusMap = {
        'pending': 'warning',
        'confirmed': 'primary',
        'preparing': 'info',
        'ready': 'success',
        'delivering': 'warning',
        'delivered': 'success',
        'cancelled': 'danger',
        'available': 'success',
        'busy': 'warning',
        'offline': 'secondary'
    };
    return statusMap[status] || 'secondary';
}

/**
 * Search filter function for tables
 */
function filterTable(inputId, tableId) {
    const input = document.getElementById(inputId);
    if (!input) return;
    
    input.addEventListener('keyup', function() {
        const filter = this.value.toLowerCase();
        const table = document.getElementById(tableId);
        if (!table) return;
        
        const rows = table.getElementsByTagName('tr');
        for (let i = 1; i < rows.length; i++) {
            let found = false;
            const cells = rows[i].getElementsByTagName('td');
            for (let j = 0; j < cells.length; j++) {
                const text = cells[j].textContent || cells[j].innerText;
                if (text.toLowerCase().indexOf(filter) > -1) {
                    found = true;
                    break;
                }
            }
            rows[i].style.display = found ? '' : 'none';
        }
    });
}

/**
 * Confirm deletion with a modal
 */
function confirmDelete(message, callback) {
    if (confirm(message || 'Are you sure you want to delete this item?')) {
        if (typeof callback === 'function') {
            callback();
        }
        return true;
    }
    return false;
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('en-UG', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Show a toast notification
 */
function showToast(message, type) {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        // Create container if it doesn't exist
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.style.position = 'fixed';
        container.style.top = '20px';
        container.style.right = '20px';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type || 'primary'} border-0 show`;
    toast.role = 'alert';
    toast.style.minWidth = '250px';
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    document.getElementById('toast-container').appendChild(toast);
    
    setTimeout(function() {
        toast.remove();
    }, 5000);
}