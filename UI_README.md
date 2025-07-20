# Saga Pattern Demo - Interactive UI

A beautiful, interactive web interface for exploring and understanding the Saga Pattern implementation.

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

### Running the Application

1. **Install dependencies:**
   ```bash
   uv sync --frozen
   ```

2. **Start the application:**
   ```bash
   uv run main.py
   ```

3. **Open your browser:**
   The UI will be available at `http://localhost:8000`

## 🎯 Features

### 📝 Order Creation
- **Interactive Form**: Create orders with different users, products, quantities, and amounts
- **Real-time Validation**: Form validation with helpful error messages
- **Live Status Updates**: See saga execution progress in real-time

### 🧪 Test Scenarios
Four pre-configured test scenarios to demonstrate different saga behaviors:

1. **✅ Success Scenario**: Valid order with sufficient funds and inventory
2. **💳 Payment Failure**: Order with insufficient funds - triggers compensation
3. **🚚 Shipping Failure**: Order for user_3 - shipping fails, payment refunded
4. **📦 Inventory Failure**: Order with insufficient inventory

### 📊 System Monitoring
- **Real-time Inventory**: Current stock levels for all products
- **User Balances**: Live balance tracking for all users
- **Saga Status**: Detailed step-by-step saga execution tracking

### 📋 Activity Logs
- **Comprehensive Logging**: All actions and events are logged with timestamps
- **Color-coded Messages**: Different colors for info, success, error, and warning messages
- **Scrollable History**: View complete transaction history

## 🎨 UI Components

### Educational Content
- **Saga Pattern Explanation**: Clear overview of how the pattern works
- **Step-by-step Process**: Visual representation of the saga workflow
- **Compensation Logic**: Explanation of automatic rollback mechanisms

### Interactive Elements
- **Form Controls**: Dropdown menus for users and products with current state
- **Status Indicators**: Color-coded status badges for different states
- **Progress Tracking**: Visual step-by-step progress indicators
- **Real-time Updates**: Live updates without page refresh

## 🔧 Technical Details

### Architecture
- **Jinja2 Templates**: Server-side templating for dynamic content
- **Separated CSS/JS**: External files for better maintainability
- **RESTful API Integration**: Communicates with FastAPI backend
- **Responsive Design**: Works on desktop and mobile devices
- **Modern UI**: Clean, intuitive interface with smooth animations

### API Integration
- **Order Creation**: POST requests to `/orders` endpoint
- **Saga Monitoring**: GET requests to `/sagas/{id}` endpoint
- **System State**: GET requests to `/inventory` and `/balances` endpoints
- **Static Files**: CSS served from `/static/css/styles.css`, JS from `/static/js/app.js`
- **Templates**: HTML served using Jinja2 templates from `/templates/index.html`
- **Error Handling**: Comprehensive error handling and user feedback

### Browser Compatibility
- **Modern Browsers**: Chrome, Firefox, Safari, Edge
- **ES6 Features**: Uses modern JavaScript features
- **CSS Grid/Flexbox**: Modern layout techniques

## 🎓 Learning Path

### For Beginners
1. Start with the educational content at the top
2. Try the "Success Scenario" to see normal flow
3. Experiment with the "Payment Failure" scenario
4. Observe how compensation works automatically

### For Developers
1. Create custom orders with different parameters
2. Monitor the real-time saga execution
3. Check the activity logs for detailed information
4. Observe system state changes after transactions

### For Architects
1. Study the saga workflow visualization
2. Understand the compensation mechanisms
3. Analyze the distributed transaction patterns
4. Consider how this applies to microservices

## 🐛 Troubleshooting

### Common Issues

**UI doesn't load:**
- Make sure the application is running: `uv run main.py`
- Check that `templates/index.html` exists
- Verify that the `static/js/app.js` and `static/css/styles.css` files exist

**API connection errors:**
- Verify the application is running: `uv run main.py`
- Check browser console for any JavaScript errors
- Ensure all dependencies are installed: `uv sync --frozen`

**Port conflicts:**
- If port 8000 is busy, modify the port in `main.py` (uvicorn.run call)

### Debug Mode
Open browser developer tools (F12) to see:
- Network requests to the API
- JavaScript console logs
- Real-time saga monitoring data

## 🎨 Customization

### Styling
- Modify CSS in the `static/css/styles.css` file
- Color scheme can be adjusted in the CSS variables
- Responsive breakpoints can be modified for different screen sizes

### Functionality
- Add new test scenarios in the `static/js/app.js` file
- Modify API endpoints in the JavaScript code
- Add new UI components as needed

### Integration
- The UI can be easily integrated with other saga implementations
- API endpoints can be modified to work with different backends
- The monitoring system can be extended for production use

## 📚 Next Steps

After exploring the UI:

1. **Read the Code**: Examine the Python saga implementation
2. **Study the Flowcharts**: Review `saga_flowchart.md` for detailed diagrams
3. **Experiment**: Try different failure scenarios
4. **Extend**: Add new saga steps or services
5. **Deploy**: Consider deploying to a cloud platform

The UI provides an excellent foundation for understanding and demonstrating the Saga Pattern in action! 