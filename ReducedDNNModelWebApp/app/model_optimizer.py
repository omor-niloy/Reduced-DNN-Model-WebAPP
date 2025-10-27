import os
import sys
import torch
import torch.nn as nn
import torch.nn.utils.prune as prune
import torch_pruning as tp
import time
import importlib.util
from pathlib import Path


class ModelOptimizer:
    """
    Handles model optimization through pruning and quantization
    """
    
    def __init__(self):
        self.device = torch.device('cpu')  # Use CPU for optimization
    
    def load_model(self, model_path, architecture_path=None, class_name=None, init_params=None):
        """
        Load model from weights file and architecture file
        
        Args:
            model_path: Path to .pth file containing state_dict
            architecture_path: Path to .py file containing model class
            class_name: Name of the model class to instantiate
            init_params: Dictionary of initialization parameters for the model class
        """
        try:
            if architecture_path is None:
                # Try loading as complete model
                model = torch.load(model_path, map_location=self.device, weights_only=False)
                return model
            
            # Load architecture from .py file
            spec = importlib.util.spec_from_file_location("model_architecture", architecture_path)
            model_module = importlib.util.module_from_spec(spec)
            sys.modules['model_architecture'] = model_module
            spec.loader.exec_module(model_module)
            
            # Get the specified class
            if class_name is None:
                raise Exception("class_name is required when loading from architecture file")
            
            if not hasattr(model_module, class_name):
                available_classes = [name for name in dir(model_module) if not name.startswith('_')]
                raise Exception(f"Class '{class_name}' not found in architecture file. Available classes: {available_classes}")
            
            model_class = getattr(model_module, class_name)
            
            # Check if it's a valid nn.Module subclass
            if not (isinstance(model_class, type) and issubclass(model_class, nn.Module)):
                raise Exception(f"'{class_name}' is not a valid PyTorch nn.Module class")
            
            print(f"Found model class: {class_name}")
            
            # Instantiate the model with provided parameters
            if init_params is None:
                init_params = {}
            
            try:
                model = model_class(**init_params)
                print(f"✓ Model instantiated with parameters: {init_params}")
            except TypeError as e:
                raise Exception(f"Failed to instantiate {class_name} with parameters {init_params}. Error: {str(e)}")
            
            # Load state dict
            state_dict = torch.load(model_path, map_location=self.device, weights_only=False)
            
            # Handle different state dict formats
            if isinstance(state_dict, dict):
                if 'state_dict' in state_dict:
                    state_dict = state_dict['state_dict']
                elif 'model_state_dict' in state_dict:
                    state_dict = state_dict['model_state_dict']
            
            # Load weights with strict=False to handle minor mismatches
            try:
                model.load_state_dict(state_dict, strict=True)
            except RuntimeError as e:
                print(f"Warning: Strict loading failed. Trying with strict=False. Error: {str(e)}")
                model.load_state_dict(state_dict, strict=False)
            
            model.eval()
            print(f"✓ Model loaded successfully: {model.__class__.__name__}")
            return model
            
        except Exception as e:
            print(f"Model path: {model_path}")
            print(f"Architecture path: {architecture_path}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Failed to load model: {str(e)}")
    
    def save_model(self, model, output_path):
        try:
            # Save only the state_dict (weights)
            torch.save(model.state_dict(), output_path)
            return True
        except Exception as e:
            raise Exception(f"Failed to save model: {str(e)}")
    
    def get_model_size(self, model_path):
        size_bytes = os.path.getsize(model_path)
        size_mb = size_bytes / (1024 * 1024)
        return round(size_mb, 2)
    
    def get_model_architecture(self, model_path, architecture_path):
        """
        Get a text summary of the model architecture using torchinfo summary
        Note: This reads from a pre-generated summary file
        """
        try:
            # The architecture summary is saved as a .txt file alongside the model
            summary_path = model_path.replace('.pth', '_summary.txt').replace('.pt', '_summary.txt')
            
            if os.path.exists(summary_path):
                with open(summary_path, 'r') as f:
                    return f.read()
            else:
                return "Architecture summary not found. It may have been cleaned up."
            
        except Exception as e:
            import traceback
            error_msg = f"Error loading architecture summary:\n{str(e)}\n\n{traceback.format_exc()}"
            print(error_msg)
            return error_msg
    
    def generate_model_summary(self, model):
        """
        Generate a text summary of the model architecture using torchinfo
        """
        try:
            from torchinfo import summary
            import io
            from contextlib import redirect_stdout
            
            model.eval()
            
            # Capture the summary output
            f = io.StringIO()
            with redirect_stdout(f):
                summary(model, input_size=(1, 3, 32, 32), device='cpu')
            
            return f.getvalue()
            
        except Exception as e:
            import traceback
            return f"Error generating architecture summary:\n{str(e)}\n\n{traceback.format_exc()}"
    
    def prune_model(self, model, amount=0.5, importance_metric='l1', global_pruning=True):
        try:
            # Set importance metric
            if importance_metric == "l1":
                imp = tp.importance.MagnitudeImportance(p=1)
            elif importance_metric == "l2":
                imp = tp.importance.MagnitudeImportance(p=2)
            elif importance_metric == "taylor":
                imp = tp.importance.TaylorImportance()
            elif importance_metric == "random":
                imp = tp.importance.RandomImportance()
            else:
                print(f"Unknown importance metric '{importance_metric}', defaulting to 'l1'")
                imp = tp.importance.MagnitudeImportance(p=1)
            
            example_inputs = torch.randn(1, 3, 224, 224).to(self.device)
            
            output_layers = [m for m in model.modules() if isinstance(m, (nn.Linear, nn.Conv2d))]
            if len(output_layers) > 0:
                output_layers = [output_layers[-1]]  # Ignore only last layer
            else:
                output_layers = []
            
            
            # Create pruner
            pruner = tp.pruner.MagnitudePruner(
                model,
                example_inputs,
                importance=imp,
                iterative_steps=1,
                ch_sparsity=amount,
                ignored_layers=output_layers,
                global_pruning=global_pruning,
            )
            pruner.step()
            return model
            
        except Exception as e:
            print(f"Structured pruning failed: {str(e)}")
            print("Falling back to simple magnitude pruning...")
            # Fallback to simple unstructured pruning if torch_pruning fails
            try:
                for name, module in model.named_modules():
                    if isinstance(module, (nn.Conv2d, nn.Linear)):
                        prune.l1_unstructured(module, name='weight', amount=amount)
                        prune.remove(module, 'weight')
                return model
            except Exception as fallback_error:
                raise Exception(f"Pruning failed: {str(fallback_error)}")
    
    def quantize_model(self, model, quantization_type='dynamic'):
        try:
            # Move model to CPU for quantization
            model = model.cpu()
            model.eval()  # Set to evaluation mode
            
            if quantization_type == 'dynamic':
                # Dynamic quantization - quantizes Conv2d and Linear layers to INT8
                # This is the approach from your code
                print("Applying dynamic quantization to Conv2d and Linear layers...")
                quantized_model = torch.ao.quantization.quantize_dynamic(
                    model,
                    {nn.Linear, nn.Conv2d},  # Only quantize these layer types
                    dtype=torch.qint8
                )
                print("✓ Dynamic quantization completed")
            else:
                # Static quantization (requires calibration data)
                print("Applying static quantization...")
                model.qconfig = torch.ao.quantization.get_default_qconfig('x86')
                torch.ao.quantization.prepare(model, inplace=True)
                # Note: In production, you'd run calibration data through the model here
                quantized_model = torch.ao.quantization.convert(model, inplace=False)
                print("✓ Static quantization completed")
            
            return quantized_model
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise Exception(f"Quantization failed: {str(e)}")
    
    def crd_distillation(self, teacher_model, architecture_path, student_class_name, student_init_params, training_script_path):
        """
        Apply CRD (Contrastive Representation Distillation)
        
        Args:
            teacher_model: The loaded teacher model (from weights file)
            architecture_path: Path to .py file with model classes
            student_class_name: Name of the student model class
            student_init_params: Dict of parameters to initialize student
            training_script_path: Path to .py file with dataset and training code
        """
        try:
            print(f"Starting CRD distillation...")
            print(f"Teacher model: {teacher_model.__class__.__name__}")
            print(f"Student class: {student_class_name}")
            print(f"Student params: {student_init_params}")
            
            # Load architecture module
            spec = importlib.util.spec_from_file_location("model_architecture", architecture_path)
            model_module = importlib.util.module_from_spec(spec)
            sys.modules['model_architecture'] = model_module
            spec.loader.exec_module(model_module)
            
            # Get student model class
            if not hasattr(model_module, student_class_name):
                available = [name for name in dir(model_module) if not name.startswith('_')]
                raise Exception(f"Student class '{student_class_name}' not found. Available: {available}")
            
            student_class = getattr(model_module, student_class_name)
            if not (isinstance(student_class, type) and issubclass(student_class, nn.Module)):
                raise Exception(f"'{student_class_name}' is not a valid PyTorch nn.Module class")
            
            # Instantiate student model
            student_model = student_class(**student_init_params)
            print(f"✓ Student model instantiated: {student_model.__class__.__name__}")
            
            # Load training script
            print(f"Loading training script from: {training_script_path}")
            training_spec = importlib.util.spec_from_file_location("training_module", training_script_path)
            training_module = importlib.util.module_from_spec(training_spec)
            
            # Clear any previous training_module to avoid conflicts
            if 'training_module' in sys.modules:
                del sys.modules['training_module']
            
            sys.modules['training_module'] = training_module
            training_spec.loader.exec_module(training_module)
            print("✓ Training script loaded successfully")
            
            # Look for training function (common names)
            # Priority: train_crd > train_distillation > train > distill
            training_function = None
            for func_name in ['train_crd', 'train_distillation', 'train', 'distill']:
                if hasattr(training_module, func_name):
                    func = getattr(training_module, func_name)
                    if callable(func):
                        training_function = func
                        print(f"✓ Found training function: '{func_name}'")
                        break
            
            if training_function is None:
                available_funcs = [name for name in dir(training_module) 
                                  if callable(getattr(training_module, name)) and not name.startswith('_')]
                raise Exception(
                    f"No training function found in training script.\n"
                    f"Expected function names: 'train_crd', 'train_distillation', 'train', or 'distill'\n"
                    f"Available functions: {available_funcs}\n"
                    f"Function signature should be: def train(teacher_model, student_model) -> trained_student"
                )
            
            # Execute CRD training
            # The training function should accept (teacher, student) and return trained student
            print("=" * 60)
            print("Starting CRD distillation training...")
            print(f"Teacher: {teacher_model.__class__.__name__}")
            print(f"Student: {student_model.__class__.__name__}")
            print("=" * 60)
            
            try:
                trained_student = training_function(teacher_model, student_model)
            except Exception as train_error:
                raise Exception(f"Training function failed: {str(train_error)}")
            
            if trained_student is None:
                raise Exception("Training function returned None. It should return the trained student model.")
            
            print("=" * 60)
            print("✓ CRD distillation training completed successfully")
            print("=" * 60)
            
            return trained_student
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise Exception(f"CRD distillation failed: {str(e)}")
    
    def optimize_model(self, input_path, output_path, technique='pruning', **kwargs):
        start_time = time.time()
        
        try:
            # Get architecture path, class name, and init params if provided
            architecture_path = kwargs.get('architecture_path', None)
            class_name = kwargs.get('class_name', None)
            init_params = kwargs.get('init_params', {})
            
            # Load model with architecture file
            model = self.load_model(
                input_path, 
                architecture_path=architecture_path,
                class_name=class_name,
                init_params=init_params
            )
            original_size = self.get_model_size(input_path)
            
            # Apply optimization
            if technique == 'pruning':
                amount = kwargs.get('pruning_amount', 50) / 100.0  # Convert percentage to fraction
                optimized_model = self.prune_model(model, amount=amount)
            elif technique == 'quantization':
                quant_type = kwargs.get('quantization_type', 'dynamic')
                optimized_model = self.quantize_model(model, quantization_type=quant_type)
            elif technique == 'crd':
                # CRD distillation - teacher is the loaded model, returns trained student
                student_class_name = kwargs.get('student_class_name')
                student_init_params = kwargs.get('student_init_params', {})
                training_script_path = kwargs.get('training_script_path')
                
                optimized_model = self.crd_distillation(
                    teacher_model=model,
                    architecture_path=architecture_path,
                    student_class_name=student_class_name,
                    student_init_params=student_init_params,
                    training_script_path=training_script_path
                )
            else:
                raise ValueError(f"Unknown technique: {technique}")
            
            # Generate architecture summary from the optimized model
            architecture_summary = self.generate_model_summary(optimized_model)
            
            # Save optimized model
            self.save_model(optimized_model, output_path)
            
            # Save architecture summary as a text file
            summary_path = output_path.replace('.pth', '_summary.txt').replace('.pt', '_summary.txt')
            with open(summary_path, 'w') as f:
                f.write(architecture_summary)
            
            optimized_size = self.get_model_size(output_path)
            
            # Calculate metrics
            size_reduction = round(((original_size - optimized_size) / original_size) * 100, 2)
            processing_time = round(time.time() - start_time, 2)
            
            return {
                'success': True,
                'technique': technique,
                'original_size_mb': original_size,
                'optimized_size_mb': optimized_size,
                'size_reduction_percent': size_reduction,
                'processing_time': processing_time
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


# Global instance
model_optimizer = ModelOptimizer()
