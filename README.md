# Reduced DNN Model - Image Classification Web App

A secure Django web application for image classification using Deep Neural Network models (Heavy and Light versions).

## 🚀 Features

- **Image Upload & Classification** - Upload images and classify using DNN models
- **Model Selection** - Choose between Heavy or Light model
- **Real-time Results** - View predictions, confidence scores, and processing time
- **Responsive Design** - Side-by-side layout on desktop, stacked on mobile
- **Secure** - Comprehensive security measures including CSRF protection, file validation, and automatic cleanup

## 📋 Prerequisites

- Python 3.8+
- PyTorch
- Django 4.2+
- Pillow (PIL)

## ⚙️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/omor-niloy/Reduced-DNN-Model-WebAPP.git
   cd Reduced-DNN-Model-WebAPP/ReducedDNNModelWebApp
   ```

2. **Create and activate virtual environment** (optional but recommended)
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install django pillow torch torchvision
   ```

4. **Add your model files**
   - Place your PyTorch models in `app/dnn_models/`:
     - `heavy.pt` 
     - `light.pt`

5. **Configure model processing**
   - Edit `app/utils.py`:
     - Update `preprocess_image()` to match your model's preprocessing
     - Update `_get_class_names()` with your actual class labels

## 🏃 Running the Application

```bash
python3 manage.py runserver
```

Open your browser and navigate to: `http://localhost:8000`

## 🎯 Usage

1. Select a model (Heavy or Light)
2. Upload an image (JPG, JPEG, PNG, BMP, GIF)
3. Click "Classify"
4. View results including:
   - Predicted class
   - Confidence score
   - Inference time
   - Total processing time

## 📁 Project Structure

```
ReducedDNNModelWebApp/
├── app/
│   ├── dnn_models/          # Place your .pt model files here
│   ├── static/app/css/     # CSS styles
│   ├── templates/          # HTML templates
│   ├── utils.py           # Model loading and inference
│   ├── views.py           # API endpoints
│   └── urls.py            # URL routing
├── media/uploads/          # Temporary image uploads (auto-cleaned)
├── manage.py
└── ReducedDNNModelWebApp/
    └── settings.py        # Django settings
```

## 🔧 Configuration

### Model Settings (`app/utils.py`)

**Preprocessing** - Adjust image preprocessing to match your model:
```python
def preprocess_image(self, image_path):
    transform = transforms.Compose([
        transforms.Resize((32, 32)),  # Your model's input size
        transforms.ToTensor(),
        transforms.Normalize(mean=[...], std=[...])  # Your normalization
    ])
```

**Class Labels** - Define your model's output classes:
```python
def _get_class_names(self):
    return ['class_1', 'class_2', 'class_3', ...]
```

### Security Settings (`settings.py`)

- **Max file size**: 10MB (configurable in `FILE_UPLOAD_MAX_MEMORY_SIZE`)
- **Max dimensions**: 4096x4096 pixels
- **Allowed formats**: JPG, JPEG, PNG, BMP, GIF

## 🔒 Security Features

- ✅ **CSRF Protection** - Prevents cross-site request forgery attacks
- ✅ **File Validation** - Magic byte verification, format matching
- ✅ **Size Limits** - File size and dimension constraints
- ✅ **Path Traversal Protection** - Sanitized filenames
- ✅ **Automatic Cleanup** - Files deleted after processing
- ✅ **No Database** - Stateless application, no data persistence

## 🛠️ API Endpoints

### POST `/api/classify/`
Classify an uploaded image

**Request:**
- `image`: Image file
- `model`: "heavy" or "light"

**Response:**
```json
{
  "success": true,
  "prediction": "class_name",
  "confidence": 95.67,
  "model_used": "heavy",
  "class_id": 3,
  "inference_time": 45.32,
  "total_time": 123.45,
  "filename": "uploaded_image.jpg"
}
```

### GET `/api/model-status/`
Check if models are available

**Response:**
```json
{
  "success": true,
  "models": {
    "heavy": {"exists": true, "size_mb": 102.45},
    "light": {"exists": true, "size_mb": 25.67}
  },
  "device": "cuda"
}
```

## 🧪 Testing

Access the model status:
```bash
curl http://localhost:8000/api/model-status/
```

Test classification:
```bash
curl -X POST http://localhost:8000/api/classify/ \
  -F "image=@test.jpg" \
  -F "model=heavy" \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN"
```

## 📝 Important Notes

1. **Models are cached** - First load takes time, subsequent requests are faster
2. **Memory Management** - Uploaded files are automatically deleted after processing
3. **No Database** - Application is stateless, no user data is stored

## 🚧 Troubleshooting

**"Model file not found"**
- Ensure models are in `app/dnn_models/` with correct names
- Check file extensions (`.pt` or `.pth`)

**"CSRF token missing"**
- Clear browser cookies and refresh
- Ensure JavaScript is enabled

**"File too large"**
- Maximum file size is 10MB
- Adjust `FILE_UPLOAD_MAX_MEMORY_SIZE` in settings.py if needed

**"Invalid image format"**
- Ensure file is a valid image
- File content must match extension

## 📄 License

This project is open source and available under the MIT License.

## 👤 Author

**Omor Niloy**
- GitHub: [@omor-niloy](https://github.com/omor-niloy)

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

---

**Version:** 1.0  
**Last Updated:** October 24, 2025
