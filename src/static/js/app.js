const API_BASE = '';
let orders = [];
let currentSagaId = null;
let lastOrdersHash = null; // Track changes to avoid unnecessary updates
let updateDebounceTimer = null; // Debounce rapid updates
let lastSagaStatus = {}; // Track saga status to avoid unnecessary updates
let isRefreshInProgress = false; // Prevent overlapping refreshes

// Initialize the application
document.addEventListener('DOMContentLoaded', function () {
  refreshSystemState();
  refreshOrdersList();
  addLog('info', 'Saga Pattern Demo UI loaded successfully');
});

// Form submission handler
document
  .getElementById('orderForm')
  .addEventListener('submit', async function (e) {
    e.preventDefault();

    const formData = {
      user_id: document.getElementById('userId').value,
      product_id: document.getElementById('productId').value,
      quantity: parseInt(document.getElementById('quantity').value),
      amount: parseFloat(document.getElementById('amount').value),
    };

    await createOrder(formData);
  });

// Create order and execute saga
async function createOrder(orderData) {
  const loading = document.getElementById('loading');
  const result = document.getElementById('orderResult');

  loading.style.display = 'block';
  result.innerHTML = '';

  addLog(
    'info',
    `Creating order for user ${orderData.user_id}, product ${orderData.product_id}`,
  );

  try {
    const response = await fetch(`${API_BASE}/orders`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(orderData),
    });

    const data = await response.json();

    if (response.ok) {
      addLog(
        'success',
        `Order created successfully! Order ID: ${data.order_id}, Saga ID: ${data.saga_id}`,
      );
      displayOrderResult(data);
      currentSagaId = data.saga_id;

      // Start monitoring the saga
      monitorSaga(data.saga_id);

      // Refresh system state after a delay
      setTimeout(refreshSystemState, 2000);
      // Refresh orders list immediately to show new order (force = true, no loading indicator)
      setTimeout(() => refreshOrdersList(true, false), 500);
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

  const stepsHtml = data.steps
    .map(
      step => `
        <div class="step ${step.status.toLowerCase()}">
            <span class="step-icon">${getStepIcon(step.name)}</span>
            <span class="step-name">${formatStepName(step.name)}</span>
            <span class="step-status status-${step.status.toLowerCase()}">${
        step.status
      }</span>
        </div>
    `,
    )
    .join('');

  result.innerHTML = `
        <div class="success-message">
            <h3>🎉 Order Created Successfully!</h3>
            <p><strong>Order ID:</strong> ${data.order_id}</p>
            <p><strong>Saga ID:</strong> ${data.saga_id}</p>
            <p><strong>Status:</strong> <span class="status-indicator status-${data.status.toLowerCase()}">${
    data.status
  }</span></p>
            
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

  // Initialize tracking for this saga
  lastSagaStatus[sagaId] = 'processing';

  const interval = setInterval(async () => {
    attempts++;

    try {
      const response = await fetch(`${API_BASE}/sagas/${sagaId}`);
      const data = await response.json();

      if (response.ok) {
        updateSagaStatus(data);

        const previousStatus = lastSagaStatus[sagaId];
        const currentStatus = data.status;

        // Only refresh orders list when saga actually completes or fails
        // (not during intermediate processing steps)
        if (
          currentStatus !== previousStatus &&
          (currentStatus === 'completed' || currentStatus === 'failed')
        ) {
          clearInterval(interval);
          addLog(
            'info',
            `Saga ${sagaId} finished with status: ${currentStatus}`,
          );
          refreshSystemState();

          // Use debounced refresh to prevent glittering, no loading indicator since saga just finished
          debouncedRefreshOrdersList(500, false, false);

          // Clean up tracking
          delete lastSagaStatus[sagaId];
        } else {
          // Update our tracking but don't refresh orders list
          lastSagaStatus[sagaId] = currentStatus;
        }
      }
    } catch (error) {
      addLog('error', `Error monitoring saga: ${error.message}`);
    }

    if (attempts >= maxAttempts) {
      clearInterval(interval);
      addLog('warning', `Saga monitoring timeout after ${maxAttempts} seconds`);
      // Clean up tracking
      delete lastSagaStatus[sagaId];
    }
  }, 1000);
}

// Update saga status display
function updateSagaStatus(sagaData) {
  const result = document.getElementById('orderResult');
  if (!result.innerHTML.includes(sagaData.id)) return;

  const stepsHtml = sagaData.steps
    .map(
      step => `
        <div class="step ${step.status.toLowerCase()}">
            <span class="step-icon">${getStepIcon(step.name)}</span>
            <span class="step-name">${formatStepName(step.name)}</span>
            <span class="step-status status-${step.status.toLowerCase()}">${
        step.status
      }</span>
        </div>
    `,
    )
    .join('');

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
      .map(
        ([product, quantity]) => `
                <div class="state-item">
                    <span>${product}</span>
                    <span>${quantity} units</span>
                </div>
            `,
      )
      .join('');

    document.getElementById('inventoryState').innerHTML = inventoryHtml;

    // Get balances
    const balanceResponse = await fetch(`${API_BASE}/balances`);
    const balanceData = await balanceResponse.json();

    const balanceHtml = Object.entries(balanceData.balances)
      .map(
        ([user, balance]) => `
                <div class="state-item">
                    <span>${user}</span>
                    <span>$${balance.toFixed(2)}</span>
                </div>
            `,
      )
      .join('');

    document.getElementById('balanceState').innerHTML = balanceHtml;

    // Update form options with current state
    updateFormOptions(inventoryData.inventory, balanceData.balances);
  } catch (error) {
    addLog('error', `Failed to refresh system state: ${error.message}`);
  }
}

// Debounced version of refreshOrdersList to prevent rapid updates
function debouncedRefreshOrdersList(
  delay = 1000,
  force = false,
  showLoading = true,
) {
  if (updateDebounceTimer) {
    clearTimeout(updateDebounceTimer);
  }

  // Don't start another refresh if one is already in progress
  if (isRefreshInProgress && !force) {
    return;
  }

  updateDebounceTimer = setTimeout(() => {
    refreshOrdersList(force, showLoading);
    updateDebounceTimer = null;
  }, delay);
}

// Fetch and display recent orders with smooth transitions
async function refreshOrdersList(force = false, showLoading = true) {
  // Prevent overlapping refreshes
  if (isRefreshInProgress && !force) {
    return;
  }

  isRefreshInProgress = true;
  const ordersList = document.getElementById('ordersList');
  const ordersContainer = document.getElementById('ordersContainer');
  const loadingIndicator = document.getElementById('ordersLoadingIndicator');

  try {
    // Show subtle loading state without replacing content (only if showLoading is true)
    if (!force && showLoading) {
      ordersContainer.classList.add('updating');
      loadingIndicator.classList.add('visible');
    }

    const response = await fetch(`${API_BASE}/orders`);
    const data = await response.json();

    // Create hash of the orders data to check for meaningful changes
    // Only include fields that matter for display and final status
    const ordersHash = JSON.stringify(
      data.map(order => ({
        id: order.id,
        // Only track final status changes (completed/failed), not intermediate processing
        status: order.status === 'processing' ? 'processing' : order.status,
        user_id: order.user_id,
        product_id: order.product_id,
        quantity: order.quantity,
        amount: order.amount,
      })),
    );

    // Only update if data has changed or if forced
    if (force || ordersHash !== lastOrdersHash) {
      lastOrdersHash = ordersHash;

      // Prepare new content
      let newContent;
      if (Array.isArray(data) && data.length > 0) {
        const html = data
          .map(
            order => `
                <div class="order-item">
                    <div><strong>Order ID:</strong> ${order.id}</div>
                    <div><strong>User:</strong> ${order.user_id}</div>
                    <div><strong>Product:</strong> ${order.product_id}</div>
                    <div><strong>Quantity:</strong> ${order.quantity}</div>
                    <div><strong>Amount:</strong> $${order.amount.toFixed(
                      2,
                    )}</div>
                    <div><strong>Status:</strong> <span class="status-indicator status-${order.status.toLowerCase()}">${
              order.status
            }</span></div>
                </div>
            `,
          )
          .join('<hr/>');
        newContent = html;
      } else {
        newContent =
          '<p>No orders created yet. Create an order to see saga transactions here.</p>';
      }

      // Smooth transition: fade out, update content, fade in
      ordersContainer.style.transition = 'opacity 0.2s ease-in-out';
      ordersContainer.style.opacity = '0.4';

      setTimeout(() => {
        ordersList.innerHTML = newContent;
        ordersContainer.style.opacity = '1';
        ordersContainer.classList.remove('updating');
        // Reset transition for normal CSS handling
        setTimeout(() => {
          ordersContainer.style.transition = '';
        }, 200);
      }, 100);
    } else {
      // No changes, just remove loading state
      ordersContainer.classList.remove('updating');
    }
  } catch (error) {
    // Handle error gracefully without jarring content replacement
    const errorMessage = `<p class="error-message">Failed to load orders: ${error.message}</p>`;

    ordersContainer.style.transition = 'opacity 0.2s ease-in-out';
    ordersContainer.style.opacity = '0.4';
    setTimeout(() => {
      ordersList.innerHTML = errorMessage;
      ordersContainer.style.opacity = '1';
      ordersContainer.classList.remove('updating');
      // Reset transition
      setTimeout(() => {
        ordersContainer.style.transition = '';
      }, 200);
    }, 100);
  } finally {
    // Always hide loading indicator and reset refresh state
    setTimeout(() => {
      loadingIndicator.classList.remove('visible');
      isRefreshInProgress = false;
    }, 200);
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
      // Force refresh orders list after reset (immediate update needed, no loading indicator)
      refreshOrdersList(true, false);
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
      fetch(`${API_BASE}/balances`),
    ]);

    const inventoryData = await inventoryResponse.json();
    const balanceData = await balanceResponse.json();

    const scenarios = {
      success: {
        user_id: 'user_1',
        product_id: 'product_1',
        quantity: 2,
        amount: 100.0,
      },
      payment_failure: {
        user_id: 'user_3',
        product_id: 'product_1',
        quantity: 1,
        amount: balanceData.balances['user_3'] + 100, // Ensure payment failure
      },
      shipping_failure: {
        user_id: 'user_3',
        product_id: 'product_1',
        quantity: 1,
        amount: 50.0,
      },
      inventory_failure: {
        user_id: 'user_1',
        product_id: 'product_1',
        quantity: inventoryData.inventory['product_1'] + 10, // Ensure inventory failure
        amount: 10000.0,
      },
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
    // Use debounced refresh for test scenarios, no loading since order creation will show loading
    debouncedRefreshOrdersList(1200, false, false);
  } catch (error) {
    addLog('error', `Failed to run test scenario: ${error.message}`);
  }
}

// Utility functions
function getStepIcon(stepName) {
  const icons = {
    validate_order: '✅',
    reserve_inventory: '📦',
    process_payment: '💳',
    ship_order: '🚚',
  };
  return icons[stepName] || '⚙️';
}

function formatStepName(stepName) {
  return stepName
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
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
