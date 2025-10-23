import os
import torch
from django.conf import settings
from pathlib import Path


class ModelManager:
    def __init__(self):
        self.models = {}
        self.model_dir = Path(settings.BASE_DIR) / 'app' / 'dnn_models'
        # self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.device = torch.device('cpu')
        
    def load_model(self, model_name):
        if model_name in self.models:
            return self.models[model_name]

        model_file = f"{model_name}.pt"
        model_path = self.model_dir / model_file
        
        try:
            # light_model = torch.jit.load("quantized89.pt")
            # heavy_model = torch.jit.load("bt94.pt")
            # Load the model
            model = torch.jit.load(model_path, map_location=self.device)
            model.eval()  # Set to evaluation mode
            
            # Cache the model
            self.models[model_name] = model
            
            return model
            
        except Exception as e:
            raise Exception(f"Error loading model {model_name}: {str(e)}")
    
    def preprocess_image(self, image_path):
        from PIL import Image
        from torchvision import transforms
        
        transform = transforms.Compose([
            transforms.Resize((32, 32)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                std=[0.229, 0.224, 0.225])
        ])
        
        image = Image.open(image_path).convert('RGB')
        image_tensor = transform(image).unsqueeze(0)  # Add batch dimension
        
        return image_tensor.to(self.device)
    
    def classify_image(self, image_path, model_name):
        import time
        
        try:
            # Start timing
            start_time = time.time()
            
            model = self.load_model(model_name)
            image_tensor = self.preprocess_image(image_path)
            
            # Time inference only
            inference_start = time.time()
            
            # Perform inference
            with torch.no_grad():
                output = model(image_tensor)
                if isinstance(output, tuple):
                    output = output[1]
            
            inference_time = time.time() - inference_start

            # Process output - MODIFY THIS based on your model
            # Example for classification models:
            probabilities = torch.nn.functional.softmax(output, dim=1)
            confidence, predicted = torch.max(probabilities, 1)
            
            # Example class names - REPLACE with your actual classes
            class_names = self._get_class_names()
            
            prediction = class_names[predicted.item()] if predicted.item() < len(class_names) else f"Class {predicted.item()}"
            confidence_score = confidence.item() * 100
            
            # Calculate total time
            total_time = time.time() - start_time
            
            return {
                'success': True,
                'prediction': prediction,
                'confidence': round(confidence_score, 2),
                'model_used': model_name,
                'class_id': predicted.item(),
                'inference_time': round(inference_time * 1000, 2),  # milliseconds
                'total_time': round(total_time * 1000, 2)  # milliseconds
            }
            
        except FileNotFoundError as e:
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Classification error: {str(e)}"
            }
    
    def _get_class_names(self):
        return ['airplane', 'automobile', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck']
    
    def get_model_info(self, model_name):
        """
        Get information about a model
        
        Args:
            model_name (str): 'heavy' or 'light'
            
        Returns:
            dict: Model information
        """
        model_file = f"{model_name}.pt"
        model_path = self.model_dir / model_file
        
        if not model_path.exists():
            model_file = f"{model_name}.pth"
            model_path = self.model_dir / model_file
        
        if model_path.exists():
            file_size = os.path.getsize(model_path)
            return {
                'exists': True,
                'path': str(model_path),
                'size_mb': round(file_size / (1024 * 1024), 2),
                'device': str(self.device)
            }
        else:
            return {
                'exists': False,
                'path': str(model_path),
                'error': 'Model file not found'
            }


# Global instance
model_manager = ModelManager()
