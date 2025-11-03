document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing Socket.IO connection...');
    
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);
    
    // Connection event handlers
    socket.on('connect', function() {
        console.log('✅ Socket.IO connected successfully!');
        showFlashMessage('bg-green-500', 'Connected to server');
    });
    
    socket.on('disconnect', function() {
        console.log('❌ Socket.IO disconnected');
        showFlashMessage('bg-red-500', 'Disconnected from server');
    });
    
    socket.on('connect_error', function(error) {
        console.error('❌ Socket.IO connection error:', error);
        showFlashMessage('bg-red-500', 'Connection error');
    });

    // Debug: Listen to ALL events
    socket.onAny(function(eventName, ...args) {
        console.log('🔔 Received event:', eventName, args);
    });

    // Order and trading event handlers
    socket.on('master_contract_download', function(data) {
        console.log('📥 Master Contract Download:', data);
        showFlashMessage('bg-blue-500', `Master Contract: ${data.message}`);
    });

    socket.on('cancel_order_event', function(data) {
        console.log('🚫 Cancel Order Event:', data);
        showFlashMessage('bg-yellow-500', `Cancel Order ID: ${data.orderid}`);
    });

    socket.on('modify_order_event', function(data) {
        console.log('✏️ Modify Order Event:', data);
        showFlashMessage('bg-blue-500', `ModifyOrder - Order ID: ${data.orderid}`);
    });

    socket.on('close_position', function(data) {
        console.log('📊 Close Position Event:', data);
        showFlashMessage('bg-purple-500', `Message: ${data.message}`);
    });

    socket.on('order_event', function(data) {
        console.log('📈 Order Event:', data);
        var bgColorClass = data.action.toUpperCase() === 'BUY' ? 'bg-green-500' : 'bg-red-500';
        showFlashMessage(bgColorClass, `${data.action.toUpperCase()} Order Placed for Symbol: ${data.symbol}, Order ID: ${data.orderid}`);
    });

    function showFlashMessage(bgColorClass, message) {
        console.log(`💬 Flash message (${bgColorClass}): ${message}`);
        
        // Create flash message container if it doesn't exist
        let container = document.getElementById('flash-message-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'flash-message-container';
            container.className = 'fixed top-4 right-4 z-50 space-y-2';
            document.body.appendChild(container);
        }
        
        // Create flash message element
        const flashDiv = document.createElement('div');
        flashDiv.className = `${bgColorClass} text-white px-6 py-3 rounded-lg shadow-lg flex items-center space-x-3 animate-slide-in`;
        flashDiv.innerHTML = `
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
            </svg>
            <span class="font-medium">${message}</span>
        `;
        
        container.appendChild(flashDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            flashDiv.style.opacity = '0';
            flashDiv.style.transform = 'translateX(100%)';
            flashDiv.style.transition = 'all 0.3s ease-out';
            setTimeout(() => flashDiv.remove(), 300);
        }, 5000);
    }
});

// Functions for mobile menu toggle
function toggleMobileMenu() {
    var menu = document.getElementById('mobile-menu');
    menu.classList.remove('-translate-x-full');
    document.querySelector('button[onclick="toggleMobileMenu()"]').style.display = 'none';
}

function closeMobileMenu() {
    var menu = document.getElementById('mobile-menu');
    menu.classList.add('-translate-x-full');
    document.querySelector('button[onclick="toggleMobileMenu()"]').style.display = 'block';
}
