#!/usr/bin/env python3

import torch
import transformers
from typing import Optional, List, Dict, Any


class Phi4ModelManager:
    """Singleton manager for the Phi-4 model that can be shared across all components."""
    
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Phi4ModelManager, cls).__new__(cls)
            # Initialization code can go here
            cls._instance.initialized = False
        return cls._instance

    def initialize_model(self) -> bool:
        """Initialize the Phi-4 model if not already attempted."""
        if not self.initialized:
            try:
                print(f"🤖 Initializing shared Phi-4 model...")
                
                self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
                self.pipeline = transformers.pipeline(
                    "text-generation",
                    model="microsoft/Phi-4-mini-instruct",
                    model_kwargs={"torch_dtype": "auto"},
                    device_map="cuda:0" if torch.cuda.is_available() else "auto",
                    trust_remote_code=True
                )
                
                self.model_loaded = True
                self.initialized = True
                print(f"✅ Shared Phi-4 model initialized successfully on {self.device}")
                return True
                
            except Exception as e:
                print(f"❌ Failed to initialize Phi-4 model: {e}")
                print(f"🚫 Will not attempt to load model again in this session")
                self.pipeline = None
                self.model_loaded = False
                self.initialized = True  # Mark as initialized even if failed
                return False
        else:
            if self.model_loaded:
                print(f"🔄 Phi-4 model already loaded on {self.device}")
            else:
                print(f"⚠️ Phi-4 model initialization was previously attempted and failed")
            return self.model_loaded
    
    def generate(self, messages: List[Dict[str, str]], max_new_tokens: int = 100, 
                temperature: float = 0.1, do_sample: bool = True) -> Optional[str]:
        """Generate text using the Phi-4 model."""
        # Don't even try if we know it failed
        if self.initialized and not self.model_loaded:
            return None
            
        if not self.initialized or not hasattr(self, 'pipeline') or self.pipeline is None:
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
        return (self.initialized and 
                hasattr(self, 'model_loaded') and 
                self.model_loaded and 
                hasattr(self, 'pipeline') and 
                self.pipeline is not None)
    
    def get_device_info(self) -> str:
        """Get information about the device the model is running on."""
        if hasattr(self, 'pipeline') and self.pipeline is not None:
            device = getattr(self, 'device', 'unknown')
            return f"Device: {device}, Available: {self.is_available()}"
        return "Model not loaded"


# Global function for easy access
def get_phi4_model() -> Phi4ModelManager:
    """Get the global Phi-4 model manager instance."""
    return Phi4ModelManager()


# Verification that singleton works correctly
if __name__ == "__main__":
    print("Testing Phi4ModelManager singleton behavior...")
    
    # Test 1: Multiple calls to constructor return same object
    instance1 = Phi4ModelManager()
    instance2 = Phi4ModelManager()
    assert instance1 is instance2, "Singleton broken - different instances returned!"
    print("✅ Singleton test passed - same instance returned")
    
    # Test 2: Multiple calls to get_phi4_model() return same object  
    model1 = get_phi4_model()
    model2 = get_phi4_model()
    assert model1 is model2, "get_phi4_model() broken - different instances returned!"
    print("✅ get_phi4_model() test passed - same instance returned")
    
    # Test 3: All instances are the same
    assert instance1 is model1, "Inconsistent singleton - different instances!"
    print("✅ All access methods return same singleton instance")
    
    # Test 4: Multiple initialize_model calls should be safe
    print("Testing multiple initialize_model() calls...")
    result1 = model1.initialize_model()
    result2 = model1.initialize_model()  # Should not reload
    result3 = model2.initialize_model()  # Should not reload
    print(f"✅ Multiple initialize_model() calls handled safely")
    print(f"   First call: {result1}, Second call: {result2}, Third call: {result3}")
    
    print("🎉 All singleton tests passed!") 