# DNN Model Optimization Web Application - Interface Documentation

## 1. System Workflow Diagram

```
                          ┌─────────────────────┐
                          │       USER          │
                          │  Upload + Configure │
                          └──────────┬──────────┘
                                     │
                     ┌───────────────┼───────────────┐
                     │               │               │
                     ▼               ▼               ▼
              ┌───────────┐   ┌───────────┐   ┌───────────┐
              │  Pruning  │   │Quantization│   │    CRD    │
              │  (0-99%)  │   │  (INT8)   │   │(Distill.) │
              └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    │
                         ┌──────────▼──────────┐
                         │  Model Optimization │
                         │      Pipeline       │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
              ┌──────────┐    ┌──────────┐    ┌──────────┐
              │   Load   │───>│ Optimize │───>│   Save   │
              │  Model   │    │  Model   │    │  Result  │
              └──────────┘    └──────────┘    └──────────┘
                                                     │
                         ┌───────────────────────────┘
                         │
                         ▼
                ┌─────────────────┐
                │  Display Results│
                │  + Download     │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ Auto Cleanup    │
                │ (On Refresh)    │
                └─────────────────┘
```

**Workflow Summary:**
1. User uploads model architecture (.py), weights (.pth), enters class name & parameters (JSON)
2. User selects optimization technique: Pruning / Quantization / CRD
3. For CRD: User also provides student model details and training script
4. Frontend sends POST request with all files and parameters
5. Backend loads model dynamically using provided class name and parameters
6. Applies selected optimization technique (pruning/quantization/distillation)
7. Saves optimized model and generates summary (for pruning)
8. Returns metrics (size reduction, processing time) and download link
9. User downloads optimized model or views architecture
10. Automatic cleanup removes temporary files on page refresh or server restart
---

## 2. How the Interface Was Built (Detailed Description)

### 2.1 Technology Stack

The web application interface was built using a modern full-stack approach with the following technologies:

**Backend Framework:**
- **Django 4.2.25**: A high-level Python web framework that handles routing, request processing, security, and server-side logic
- **Python 3.8.10**: Programming language for backend logic

**Frontend Technologies:**
- **HTML5**: Semantic markup for structure
- **CSS3**: Custom styling with gradients, animations, and responsive design
- **JavaScript (Vanilla)**: Client-side interactions, AJAX requests, and dynamic content updates

**Deep Learning:**
- **PyTorch**: Framework for loading and running neural network models
- **TorchVision**: Image preprocessing and transformations
- **PIL (Pillow)**: Image validation and handling

**Additional Libraries:**
- **Django CSRF Protection**: Security middleware for preventing cross-site request forgery
- **FileSystemStorage**: Secure file upload handling

### 2.2 Architecture Pattern

The application follows the **Model-View-Template (MVT)** pattern, which is Django's adaptation of MVC:

**Models (utils.py):**
- `ModelManager` class manages the lifecycle of DNN models
- Handles model loading, caching, and inference
- Manages image preprocessing and result post-processing

**Views (views.py):**
- `Home()`: Renders the main classification interface
- `classify_image()`: API endpoint that processes image classification requests
- `model_status_page()`: Renders the model status dashboard
- `get_model_status()`: API endpoint that returns model information

**Templates (HTML):**
- `base.html`: Master template with navigation and common elements
- `home.html`: Classification interface with form and results
- `model_status.html`: Model performance metrics dashboard

### 2.3 Development Process

#### Phase 1: Backend Setup
1. **Project Initialization:**
   - Created Django project structure with `manage.py`
   - Configured `settings.py` with database (SQLite), media files, and installed apps
   - Set up URL routing in `urls.py`

2. **Security Configuration:**
   - Enabled CSRF protection middleware
   - Configured file upload limits (10MB max)
   - Implemented path traversal prevention
   - Added magic byte validation for uploaded files

3. **Model Management System:**
   - Created `ModelManager` class to encapsulate model operations
   - Implemented lazy loading (models loaded on first use)
   - Added device detection (CPU/GPU) for optimal performance
   - Implemented model caching to avoid repeated disk I/O

#### Phase 2: API Endpoints
1. **Classification Endpoint (`/api/classify/`):**
   - POST method only for security
   - Multi-layer validation:
     - File size validation (max 10MB)
     - Extension whitelist (jpg, jpeg, png, bmp, gif)
     - Magic byte verification
     - Format spoofing detection
   - Filename sanitization with regex
   - Timestamp-based unique naming
   - Automatic cleanup after classification

2. **Status Endpoint (`/api/model-status/`):**
   - GET method to retrieve model information
   - Returns file sizes, existence status, and performance metrics
   - Includes batch performance data for different batch sizes

#### Phase 3: Frontend Interface Development
1. **Base Template Design:**
   - Responsive navigation bar with gradient styling
   - Hamburger menu for mobile devices
   - Sidebar navigation with smooth transitions
   - Consistent color scheme (purple gradient theme)

2. **Home Page (Classification Interface):**
   - Two-column responsive layout
   - Left column: Form with model selection and image upload
   - Right column: Dynamic results display
   - File upload with custom styled button
   - Real-time image preview
   - Form validation before submission

3. **Model Status Dashboard:**
   - Grid layout with model cards
   - Status indicators (Available/Not Found)
   - Performance metrics table showing:
     - Batch sizes (1, 8, 32, 64)
     - Inference times
     - Throughput values
   - Responsive design that adapts to screen size

#### Phase 4: JavaScript Interactivity
1. **AJAX Implementation:**
   - Asynchronous form submission without page reload
   - CSRF token extraction and inclusion
   - Loading states during API calls
   - Error handling and user feedback

2. **Dynamic Content Updates:**
   - Real-time image preview on file selection
   - Results rendered dynamically from JSON response
   - Table population for performance metrics
   - Status badge color changes based on model availability

3. **User Experience Enhancements:**
   - Smooth animations and transitions
   - Hover effects on interactive elements
   - Loading spinners during processing
   - Clear error messages

#### Phase 5: Styling and Responsiveness
1. **CSS Organization:**
   - Centralized styles in `styles.css`
   - Component-based styling approach
   - CSS Grid and Flexbox for layouts
   - Media queries for mobile responsiveness

2. **Visual Design:**
   - Purple gradient theme for modern appearance
   - Card-based layout for content organization
   - Icon usage (emojis) for visual appeal
   - Box shadows for depth perception

3. **Responsive Breakpoints:**
   - Desktop: Full two-column layout
   - Tablet (≤768px): Adjusted grid columns
   - Mobile (≤480px): Single column stacked layout

### 2.4 Security Measures Implemented

1. **Input Validation:**
   - File size limits
   - Extension whitelist
   - Magic byte verification
   - MIME type checking

2. **Path Security:**
   - Filename sanitization (removes special characters)
   - Path traversal prevention
   - Resolved path verification

3. **CSRF Protection:**
   - Token generation on page load
   - Token inclusion in AJAX requests
   - Server-side verification

4. **File Cleanup:**
   - Automatic deletion after classification
   - Cleanup function for old uploads
   - Error handling to prevent file leaks

---

## 3. Component Description

### 3.1 Backend Components

#### Component 1: ModelManager Class (`utils.py`)

**Purpose:** Central management system for deep neural network models

**Attributes:**
- `models` (dict): Cache of loaded PyTorch models
- `model_dir` (Path): Directory path to stored model files
- `device` (torch.device): Computation device (CPU/GPU)

**Methods:**

1. **`__init__()`**
   - Initializes empty model cache
   - Sets model directory path (`app/dnn_models/`)
   - Detects and sets device (CPU or CUDA GPU)

2. **`load_model(model_name)`**
   - Loads TorchScript model from disk
   - Uses `torch.jit.load()` for optimized models
   - Sets model to evaluation mode
   - Caches model for future use
   - Returns loaded model or raises exception

3. **`preprocess_image(image_path)`**
   - Opens image using PIL
   - Converts to RGB format (handles grayscale/RGBA)
   - Applies transformations:
     - Resize to 32×32 (CIFAR-10 input size)
     - Convert to PyTorch tensor
     - Normalize with ImageNet statistics
   - Adds batch dimension
   - Moves tensor to device (CPU/GPU)
   - Returns preprocessed tensor

4. **`classify_image(image_path, model_name)`**
   - Orchestrates the classification process
   - Loads appropriate model
   - Preprocesses input image
   - Runs inference with timing
   - Applies softmax for probabilities
   - Extracts prediction and confidence
   - Maps class ID to class name
   - Returns comprehensive result dictionary

5. **`_get_class_names()`**
   - Returns list of CIFAR-10 class names
   - Maps numeric predictions to human-readable labels

6. **`get_model_info(model_name)`**
   - Checks if model file exists
   - Calculates file size in MB
   - Returns model metadata including:
     - Existence status
     - Loaded status
     - File size
     - Performance metrics (batch-specific)
     - CIFAR-10 test accuracy

**Singleton Pattern:**
- Module exports `model_manager` instance
- Ensures single model cache across application
- Reduces memory usage and load times

---

#### Component 2: View Functions (`views.py`)

##### View 1: `Home(request)`
**Type:** Page Renderer
**HTTP Method:** GET
**Decorators:** `@ensure_csrf_cookie`

**Functionality:**
- Renders the main classification page
- Ensures CSRF token is set in cookies
- Returns `home.html` template

---

##### View 2: `classify_image(request)`
**Type:** API Endpoint
**HTTP Method:** POST
**URL:** `/api/classify/`

**Request Processing:**
1. **Method Validation:**
   - Accepts only POST requests
   - Returns 405 error for other methods

2. **Input Validation:**
   - **Model Selection:** Validates model name (heavy/light)
   - **File Presence:** Checks if image file uploaded
   - **File Size:** Enforces 10MB limit
   - **File Extension:** Whitelist validation
   - **Magic Bytes:** Verifies actual file format
   - **Format Spoofing:** Checks extension matches content

3. **Security Processing:**
   - Sanitizes filename with regex
   - Removes path components
   - Adds timestamp prefix
   - Generates unique filename
   - Verifies no path traversal

4. **Classification:**
   - Saves file temporarily
   - Calls `model_manager.classify_image()`
   - Retrieves prediction results

5. **Cleanup:**
   - Deletes uploaded file
   - Handles cleanup errors gracefully

6. **Response:**
   - Success: 200 with classification results
   - Client Error: 400 with error message
   - Server Error: 500 with error details

**Response Format (Success):**
```json
{
  "success": true,
  "prediction": "cat",
  "confidence": 94.52,
  "model_used": "heavy",
  "class_id": 3,
  "inference_time": 21.57,
  "total_time": 45.32,
  "filename": "24-10-2025_my_image.jpg"
}
```

---

##### View 3: `model_status_page(request)`
**Type:** Page Renderer
**HTTP Method:** GET
**Decorators:** `@ensure_csrf_cookie`

**Functionality:**
- Renders model status dashboard
- Returns `model_status.html` template

---

##### View 4: `get_model_status(request)`
**Type:** API Endpoint
**HTTP Method:** GET
**URL:** `/api/model-status/`

**Functionality:**
- Retrieves information for both models
- Calls `model_manager.get_model_info()` for each
- Aggregates data
- Returns JSON response

**Response Format:**
```json
{
  "success": true,
  "models": {
    "heavy": {
      "exists": true,
      "loaded": false,
      "name": "Heavy",
      "size_mb": 178.32,
      "batch_metrics": [
        {"batch_size": 1, "inference_time": 21.57, "throughput": 46.4},
        {"batch_size": 8, "inference_time": 26.11, "throughput": 306.4},
        {"batch_size": 32, "inference_time": 56.92, "throughput": 562.1},
        {"batch_size": 64, "inference_time": 106.90, "throughput": 598.6}
      ],
      "cifar10_accuracy": 94.26
    },
    "light": { /* similar structure */ }
  },
  "device": "cpu"
}
```

---

##### View 5: `cleanup_old_uploads(max_age_seconds=3600)`
**Type:** Utility Function
**Parameters:** `max_age_seconds` - Files older than this are deleted

**Functionality:**
- Iterates through upload directory
- Checks file modification time
- Deletes files older than threshold
- Prevents storage bloat
- Handles deletion errors gracefully

---

### 3.2 Frontend Components

#### Component 3: Base Template (`base.html`)

**Structure:**
```
<!DOCTYPE html>
├── <head>
│   ├── Meta tags (charset, viewport)
│   ├── Title block
│   ├── CSS: styles.css
│   └── CSRF token meta
│
└── <body>
    ├── Navigation Bar
    │   ├── Menu button (hamburger)
    │   └── App title
    │
    ├── Sidebar Menu
    │   ├── Home link
    │   └── Model Status link
    │
    ├── Main Content Block
    │   └── {% block content %}
    │
    └── JavaScript
        ├── Menu toggle function
        └── Sidebar click handler
```

**Key Features:**
1. **Responsive Navigation:**
   - Fixed position app bar
   - Gradient background
   - Hamburger menu icon

2. **Sidebar:**
   - Slides in from left
   - Overlay closes on click outside
   - Smooth transition animations

3. **Template Inheritance:**
   - Provides base structure
   - Child templates extend and fill content block

---

#### Component 4: Home Page (`home.html`)

**Layout Structure:**
```
Classification Container
├── Left Column (Form)
│   ├── Card
│   │   └── Form
│   │       ├── Model Selection Dropdown
│   │       ├── File Upload Input
│   │       ├── Image Preview
│   │       └── Classify Button
│   
└── Right Column (Results)
    └── Results Card (hidden initially)
        └── Dynamic Results Content
```

**Form Elements:**

1. **Model Selection Dropdown:**
   - ID: `modelSelect`
   - Options: Heavy Model, Light Model
   - Required field
   - Styled with custom CSS

2. **File Upload Input:**
   - ID: `imageUpload`
   - Accept: `image/*`
   - Custom styled label
   - Displays selected filename
   - Hidden native input

3. **Image Preview:**
   - Container ID: `imagePreviewContainer`
   - Image element ID: `imagePreview`
   - Initially hidden
   - Shows preview after file selection

4. **Submit Button:**
   - Type: `submit`
   - Class: `btn-primary btn-large`
   - Full width
   - Gradient background on hover

**JavaScript Functionality:**

1. **File Selection Handler:**
```javascript
imageUpload.addEventListener('change', function(e) {
  // Update filename display
  // Create FileReader
  // Load image as Data URL
  // Display preview
  // Show preview container
});
```

2. **Form Submission Handler:**
```javascript
classificationForm.addEventListener('submit', function(e) {
  e.preventDefault();
  
  // Create FormData
  // Get CSRF token
  // Show loading state
  // Send AJAX request
  // Handle response
  // Display results or errors
});
```

3. **CSRF Token Extraction:**
```javascript
function getCookie(name) {
  // Parse document.cookies
  // Find matching cookie
  // Return token value
}
```

4. **Results Rendering:**
- Creates HTML elements dynamically
- Displays prediction with class icon
- Shows confidence as percentage
- Shows inference time
- Shows model used
- Color-codes confidence level

**Responsive Behavior:**
- Desktop: Side-by-side columns
- Tablet: Stacked layout
- Mobile: Full-width single column

---

#### Component 5: Model Status Page (`model_status.html`)

**Layout Structure:**
```
Status Container
├── Status Header
│   └── Title: "Model Status"
│
├── Loading Indicator
│   ├── Spinner animation
│   └── Loading text
│
├── Error Banner (hidden)
│   └── Error message display
│
└── Status Content (hidden initially)
    └── Models Grid
        ├── Heavy Model Card
        │   ├── Header (icon + name)
        │   ├── Status Badge
        │   ├── Model Info Section
        │   │   ├── Model Size
        │   │   └── CIFAR-10 Accuracy
        │   └── Performance Table
        │       └── Batch metrics rows
        │
        └── Light Model Card
            └── (same structure)
```

**Model Card Elements:**

1. **Model Header:**
   - Icon emoji (🔥 for heavy, ⚡ for light)
   - Model name
   - Label (High Accuracy / Fast Inference)

2. **Status Badge:**
   - Dynamic class: `.available` or `.unavailable`
   - Text: "✓ Available" or "✗ Not Found"
   - Color-coded (green/orange)

3. **Model Info Section:**
   - Purple gradient background
   - Two info items:
     - Model Size (MB)
     - CIFAR-10 Accuracy (%)

4. **Performance Table:**
   - Table structure:
     - Header: Batch Size | Inference Time | Throughput
     - 4 data rows (batch sizes: 1, 8, 32, 64)
   - Purple gradient header
   - Hover effect on rows
   - Batch size column highlighted

**JavaScript Functionality:**

1. **`fetchModelStatus()`:**
```javascript
function fetchModelStatus() {
  // Show loading indicator
  // Fetch from /api/model-status/
  // Parse JSON response
  // Call updateModelCard() for each model
  // Hide loading, show content
  // Handle errors
}
```

2. **`updateModelCard(modelType, modelInfo)`:**
```javascript
function updateModelCard(modelType, modelInfo) {
  // Get DOM elements by ID
  // Update model name
  // Set status badge
  // Update model size
  // Update accuracy
  // Clear table body
  // Loop through batch_metrics
  // Create table rows dynamically
  // Append to tbody
}
```

3. **`showError(message)`:**
```javascript
function showError(message) {
  // Display error banner
  // Set error text
  // Hide loading
}
```

4. **Page Load Event:**
```javascript
document.addEventListener('DOMContentLoaded', fetchModelStatus);
```

**CSS Styling (in styles.css):**

1. **Animations:**
   - Spinner rotation (`@keyframes spin`)
   - Card hover effects
   - Row hover effects

2. **Grid Layout:**
   - Auto-fit responsive columns
   - Minimum 350px column width
   - 2rem gap between cards

3. **Color Scheme:**
   - Primary: Purple gradient (#667eea to #764ba2)
   - Success: Green (#48bb78)
   - Warning: Orange (#ed8936)
   - Background: White cards on light gray

4. **Typography:**
   - Headers: Bold, larger size
   - Labels: Semi-transparent white on gradients
   - Values: Bold white

---

#### Component 6: Stylesheet (`styles.css`)

**Organization:**
```css
/* Global Styles */
- Reset and base styles
- Body and typography

/* App Bar Styles */
- Navigation bar
- Menu button
- Hamburger icon

/* Sidebar Menu */
- Position and animation
- Navigation links

/* Container Styles */
- Page containers
- Grid layouts

/* Card Styles */
- Card appearance
- Shadows and borders

/* Form Styles */
- Input fields
- File upload custom styling
- Buttons

/* Model Status Styles */
- Status containers
- Model cards
- Performance tables
- Info sections

/* Responsive Styles */
- Media queries
- Mobile adaptations
```

**Key CSS Features:**

1. **CSS Grid:**
   - Model grid: `repeat(auto-fit, minmax(350px, 1fr))`
   - Responsive without media queries

2. **Flexbox:**
   - Navigation bar alignment
   - Form layouts
   - Card internal structure

3. **Gradients:**
   - Linear gradients for visual appeal
   - Consistent purple theme

4. **Transitions:**
   - 0.3s ease for smooth animations
   - Applied to hover, transform, colors

5. **Media Queries:**
   - `@media (max-width: 768px)`: Tablet
   - `@media (max-width: 480px)`: Mobile
   - Adjusts padding, font sizes, layouts

---

### 3.3 URL Routing Component

**File:** `app/urls.py`

**URL Patterns:**
```python
urlpatterns = [
    path('', views.Home, name='home'),
    path('model-status/', views.model_status_page, name='model_status_page'),
    path('api/classify/', views.classify_image, name='classify_image'),
    path('api/model-status/', views.get_model_status, name='model_status'),
]
```

**Route Mapping:**
1. **`/`** → Home page (classification interface)
2. **`/model-status/`** → Model status dashboard
3. **`/api/classify/`** → Classification API endpoint
4. **`/api/model-status/`** → Model info API endpoint

---

### 3.4 Configuration Component

**File:** `settings.py`

**Key Settings:**

1. **Database:**
   - Engine: SQLite3
   - Location: `db.sqlite3`

2. **Installed Apps:**
   - `django.contrib.contenttypes`
   - `django.contrib.sessions`
   - `django.contrib.messages`
   - `django.contrib.staticfiles`
   - `django.contrib.auth`
   - `app` (custom application)

3. **Middleware:**
   - SecurityMiddleware
   - SessionMiddleware
   - CommonMiddleware
   - CsrfViewMiddleware (CSRF protection)
   - AuthenticationMiddleware
   - MessageMiddleware

4. **Static Files:**
   - URL: `/static/`
   - Directory: `app/static/`

5. **Media Files:**
   - URL: `/media/`
   - Root: `media/`
   - Upload directory: `media/uploads/`

6. **Security:**
   - CSRF protection enabled
   - File upload max size: 10MB
   - Allowed hosts configured

---

## Summary

The DNN Model Web Application interface is built on a solid three-tier architecture:

1. **Backend (Python/Django):** Handles model management, security, and API endpoints
2. **Frontend (HTML/CSS/JavaScript):** Provides interactive user interface with responsive design
3. **Deep Learning (PyTorch):** Powers the actual image classification

The interface follows modern web development best practices:
- ✅ Separation of concerns (MVT pattern)
- ✅ Security-first approach (validation, CSRF, sanitization)
- ✅ Responsive design (mobile-friendly)
- ✅ User experience focus (feedback, animations, clear messaging)
- ✅ Clean code organization (modular, reusable components)
- ✅ Performance optimization (model caching, async requests)

Each component is designed to work independently while integrating seamlessly with others, making the system maintainable, scalable, and user-friendly.
