#!/usr/bin/env python3

import torch
import transformers
from typing import Optional, List, Dict, Any


class Phi4ModelManager:
    """Singleton manager for the Phi-4 model that can be shared across all components."""
    
    _instance: Optional['Phi4ModelManager'] = None
    _model_loaded: bool = False
    
    def __init__(self):
        if Phi4ModelManager._instance is not None:
            raise Exception("Phi4ModelManager is a singleton! Use get_instance() instead.")
        
        self.pipeline = None
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        
    @classmethod
    def get_instance(cls) -> 'Phi4ModelManager':
        """Get the singleton instance of the Phi-4 model manager."""
        if cls._instance is None:
            cls._instance = Phi4ModelManager()
        return cls._instance
    
    def initialize_model(self) -> bool:
        """Initialize the Phi-4 model if not already loaded."""
        if self._model_loaded and self.pipeline is not None:
            print(f"🔄 Phi-4 model already loaded on {self.device}")
            return True
        
        try:
            print(f"🤖 Initializing shared Phi-4 model on {self.device}...")
            
            self.pipeline = transformers.pipeline(
                "text-generation",
                model="microsoft/Phi-4-mini-instruct",
                model_kwargs={"torch_dtype": "auto"},
                device_map="cuda:0" if torch.cuda.is_available() else "auto",
                trust_remote_code=True
            )
            
            self._model_loaded = True
            print(f"✅ Shared Phi-4 model initialized successfully on {self.device}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize Phi-4 model: {e}")
            self.pipeline = None
            self._model_loaded = False
            return False
    
    def generate(self, messages: List[Dict[str, str]], max_new_tokens: int = 100, 
                temperature: float = 0.1, do_sample: bool = True) -> Optional[str]:
        """Generate text using the Phi-4 model."""
        if not self._model_loaded or self.pipeline is None:
            if not self.initialize_model():
                return None
        
        try:
            outputs = self.pipeline(
                messages, 
                max_new_tokens=max_new_tokens, 
                temperature=temperature, 
                do_sample=do_sample
            )
            
            if outputs and len(outputs) > 0:
                return outputs[0]["generated_text"][-1]["content"]
            return None
            
        except Exception as e:
            print(f"❌ Error generating text with Phi-4: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if the model is available and loaded."""
        return self._model_loaded and self.pipeline is not None
    
    def get_device_info(self) -> str:
        """Get information about the device the model is running on."""
        if self.pipeline is not None:
            return f"Device: {self.device}, Available: {self.is_available()}"
        return "Model not loaded"
    



# Global function for easy access
def get_phi4_model() -> Phi4ModelManager:
    """Get the global Phi-4 model manager instance."""
    return Phi4ModelManager.get_instance() 