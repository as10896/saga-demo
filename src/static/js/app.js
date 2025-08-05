const API_BASE = '';
let orders = [];
let currentSagaId = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    refreshSystemState();
    refreshOrdersList();
    addLog('info', 'Saga Pattern Demo UI loaded successfully');
});

// Form submission handler
document.getElementById('orderForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = {
        user_id: document.getElementById('userId').value,
        product_id: document.getElementById('productId').value,
        quantity: parseInt(document.getElementById('quantity').value),
        amount: parseFloat(document.getElementById('amount').value)
    };

    await createOrder(formData);
});

// Create order and execute saga
async function createOrder(orderData) {
    const loading = document.getElementById('loading');
    const result = document.getElementById('orderResult');
    
    loading.style.display = 'block';
    result.innerHTML = '';
    
    addLog('info', `Creating order for user ${orderData.user_id}, product ${orderData.product_id}`);
    
    try {
        const response = await fetch(`${API_BASE}/orders`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(orderData)
        });

        const data = await response.json();
        
        if (response.ok) {
            addLog('success', `Order created successfully! Order ID: ${data.order_id}, Saga ID: ${data.saga_id}`);
            displayOrderResult(data);
            currentSagaId = data.saga_id;
            
            // Start monitoring the saga
            monitorSaga(data.saga_id);
            
            // Refresh system state after a delay
            setTimeout(refreshSystemState, 2000);
            // Refresh orders list after a delay
            setTimeout(refreshOrdersList, 1000);
        } else {
            addLog('error', `Failed to create order: ${data.detail}`);
            displayError(data.detail);
        }
            } catch (error) {
            addLog('error', `Network error: ${error.message}`);
            displayError('Network error. Please check the server connection.');
        } finally {
        loading.style.display = 'none';
    }
}

// Display order creation result
function displayOrderResult(data) {
    const result = document.getElementById('orderResult');
    
    const stepsHtml = data.steps.map(step => `
        <div class="step ${step.status.toLowerCase()}">
            <span class="step-icon">${getStepIcon(step.name)}</span>
            <span class="step-name">${formatStepName(step.name)}</span>
            <span class="step-status status-${step.status.toLowerCase()}">${step.status}</span>
        </div>
    `).join('');

    result.innerHTML = `
        <div class="success-message">
            <h3>🎉 Order Created Successfully!</h3>
            <p><strong>Order ID:</strong> ${data.order_id}</p>
            <p><strong>Saga ID:</strong> ${data.saga_id}</p>
            <p><strong>Status:</strong> <span class="status-indicator status-${data.status.toLowerCase()}">${data.status}</span></p>
            
            <h4>Saga Steps:</h4>
            <div class="saga-steps">
                ${stepsHtml}
            </div>
        </div>
    `;
}

// Display error message
function displayError(message) {
    const result = document.getElementById('orderResult');
    result.innerHTML = `
        <div class="error-message">
            <h3>❌ Error</h3>
            <p>${message}</p>
        </div>
    `;
}

// Monitor saga progress
async function monitorSaga(sagaId) {
    let attempts = 0;
    const maxAttempts = 30; // 30 seconds max
    
    const interval = setInterval(async () => {
        attempts++;
        
        try {
            const response = await fetch(`${API_BASE}/sagas/${sagaId}`);
            const data = await response.json();
            
            if (response.ok) {
                updateSagaStatus(data);
                
                if (data.status === 'completed' || data.status === 'failed') {
                    clearInterval(interval);
                    addLog('info', `Saga ${sagaId} finished with status: ${data.status}`);
                    refreshSystemState();
                }
            }
        } catch (error) {
            addLog('error', `Error monitoring saga: ${error.message}`);
        }
        
        if (attempts >= maxAttempts) {
            clearInterval(interval);
            addLog('warning', `Saga monitoring timeout after ${maxAttempts} seconds`);
        }
    }, 1000);
}

// Update saga status display
function updateSagaStatus(sagaData) {
    const result = document.getElementById('orderResult');
    if (!result.innerHTML.includes(sagaData.id)) return;
    
    const stepsHtml = sagaData.steps.map(step => `
        <div class="step ${step.status.toLowerCase()}">
            <span class="step-icon">${getStepIcon(step.name)}</span>
            <span class="step-name">${formatStepName(step.name)}</span>
            <span class="step-status status-${step.status.toLowerCase()}">${step.status}</span>
        </div>
    `).join('');

    const statusSection = result.querySelector('.success-message');
    if (statusSection) {
        const statusElement = statusSection.querySelector('.status-indicator');
        if (statusElement) {
            statusElement.className = `status-indicator status-${sagaData.status.toLowerCase()}`;
            statusElement.textContent = sagaData.status;
        }
        
        const stepsSection = statusSection.querySelector('.saga-steps');
        if (stepsSection) {
            stepsSection.innerHTML = stepsHtml;
        }
    }
}

// Refresh system state
async function refreshSystemState() {
    try {
        // Get inventory
        const inventoryResponse = await fetch(`${API_BASE}/inventory`);
        const inventoryData = await inventoryResponse.json();
        
        const inventoryHtml = Object.entries(inventoryData.inventory)
            .map(([product, quantity]) => `
                <div class="state-item">
                    <span>${product}</span>
                    <span>${quantity} units</span>
                </div>
            `).join('');
        
        document.getElementById('inventoryState').innerHTML = inventoryHtml;
        
        // Get balances
        const balanceResponse = await fetch(`${API_BASE}/balances`);
        const balanceData = await balanceResponse.json();
        
        const balanceHtml = Object.entries(balanceData.balances)
            .map(([user, balance]) => `
                <div class="state-item">
                    <span>${user}</span>
                    <span>$${balance.toFixed(2)}</span>
                </div>
            `).join('');
        
        document.getElementById('balanceState').innerHTML = balanceHtml;
        
        // Update form options with current state
        updateFormOptions(inventoryData.inventory, balanceData.balances);
        
    } catch (error) {
        addLog('error', `Failed to refresh system state: ${error.message}`);
    }
}

// Fetch and display recent orders
async function refreshOrdersList() {
    const ordersList = document.getElementById('ordersList');
    ordersList.innerHTML = '<p>Loading...</p>';
    try {
        const response = await fetch(`${API_BASE}/orders`);
        const data = await response.json();
        if (Array.isArray(data) && data.length > 0) {
            const html = data.map(order => `
                <div class="order-item">
                    <div><strong>Order ID:</strong> ${order.id}</div>
                    <div><strong>User:</strong> ${order.user_id}</div>
                    <div><strong>Product:</strong> ${order.product_id}</div>
                    <div><strong>Quantity:</strong> ${order.quantity}</div>
                    <div><strong>Amount:</strong> $${order.amount.toFixed(2)}</div>
                    <div><strong>Status:</strong> <span class="status-indicator status-${order.status.toLowerCase()}">${order.status}</span></div>
                </div>
            `).join('<hr/>');
            ordersList.innerHTML = html;
        } else {
            ordersList.innerHTML = '<p>No orders created yet. Create an order to see saga transactions here.</p>';
        }
    } catch (error) {
        ordersList.innerHTML = `<p class="error-message">Failed to load orders: ${error.message}</p>`;
    }
}

// Reset demo data to initial state
async function resetDemoData() {
    addLog('info', 'Resetting demo data to initial state...');
    try {
        const response = await fetch(`${API_BASE}/reset`, { method: 'POST' });
        const data = await response.json();
        if (response.ok) {
            addLog('success', data.message || 'Demo data reset.');
            refreshSystemState();
            document.getElementById('orderResult').innerHTML = '';
            refreshOrdersList();
        } else {
            addLog('error', data.message || 'Failed to reset demo data.');
        }
    } catch (error) {
        addLog('error', `Network error: ${error.message}`);
    }
}

// Test scenarios
async function runTestScenario(scenario) {
    // Get current system state to use real values
    try {
        const [inventoryResponse, balanceResponse] = await Promise.all([
            fetch(`${API_BASE}/inventory`),
            fetch(`${API_BASE}/balances`)
        ]);
        
        const inventoryData = await inventoryResponse.json();
        const balanceData = await balanceResponse.json();
        
        const scenarios = {
            success: {
                user_id: 'user_1',
                product_id: 'product_1',
                quantity: 2,
                amount: 100.0
            },
            payment_failure: {
                user_id: 'user_3',
                product_id: 'product_1',
                quantity: 1,
                amount: balanceData.balances['user_3'] + 100 // Ensure payment failure
            },
            shipping_failure: {
                user_id: 'user_3',
                product_id: 'product_1',
                quantity: 1,
                amount: 50.0
            },
            inventory_failure: {
                user_id: 'user_1',
                product_id: 'product_1',
                quantity: inventoryData.inventory['product_1'] + 10, // Ensure inventory failure
                amount: 10000.0
            }
        };

        const data = scenarios[scenario];
        
        // Fill the form
        document.getElementById('userId').value = data.user_id;
        document.getElementById('productId').value = data.product_id;
        document.getElementById('quantity').value = data.quantity;
        document.getElementById('amount').value = data.amount;
        
        addLog('info', `Running ${scenario} test scenario`);
        
        // Submit the form
        document.getElementById('orderForm').dispatchEvent(new Event('submit'));
        // Refresh orders list after a delay
        setTimeout(refreshOrdersList, 1000);
        
    } catch (error) {
        addLog('error', `Failed to run test scenario: ${error.message}`);
    }
}

// Utility functions
function getStepIcon(stepName) {
    const icons = {
        'validate_order': '✅',
        'reserve_inventory': '📦',
        'process_payment': '💳',
        'ship_order': '🚚'
    };
    return icons[stepName] || '⚙️';
}

function formatStepName(stepName) {
    return stepName.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
}

function addLog(type, message) {
    const logs = document.getElementById('logs');
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${type}`;
    logEntry.textContent = `[${timestamp}] ${message}`;
    logs.appendChild(logEntry);
    logs.scrollTop = logs.scrollHeight;
}

function clearLogs() {
    document.getElementById('logs').innerHTML = '';
    addLog('info', 'Logs cleared');
}

// Update form options with current system state
function updateFormOptions(inventory, balances) {
    // Update user dropdown
    const userSelect = document.getElementById('userId');
    const currentUserId = userSelect.value; // Remember current selection
    
    userSelect.innerHTML = '<option value="">Select a user</option>';
    Object.entries(balances).forEach(([userId, balance]) => {
        const option = document.createElement('option');
        option.value = userId;
        option.textContent = `${userId} ($${balance.toFixed(2)} balance)`;
        userSelect.appendChild(option);
    });
    
    // Restore current selection if it still exists
    if (currentUserId && balances.hasOwnProperty(currentUserId)) {
        userSelect.value = currentUserId;
    }
    
    // Update product dropdown
    const productSelect = document.getElementById('productId');
    const currentProductId = productSelect.value; // Remember current selection
    
    productSelect.innerHTML = '<option value="">Select a product</option>';
    Object.entries(inventory).forEach(([productId, quantity]) => {
        const option = document.createElement('option');
        option.value = productId;
        option.textContent = `${productId} (${quantity} units available)`;
        productSelect.appendChild(option);
    });
    
    // Restore current selection if it still exists
    if (currentProductId && inventory.hasOwnProperty(currentProductId)) {
        productSelect.value = currentProductId;
    }
} 