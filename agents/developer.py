"""
Starter Developer Template for Code-Writing Contest

This developer uses Microsoft's Phi-4 model to generate code solutions.
Contestants should modify this class to implement their strategy.
Save your modified version to /dataNAS/people/[your_name]/developer.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models import Developer, CodingProblem
import transformers
import torch
import re
from datetime import datetime
import time
import yaml


class Phi4Developer(Developer):
    """
    A developer implementation that uses Microsoft's Phi-4 model to generate code solutions.
    
    This implementation:
    - Uses the Phi-4 model for intelligent code generation
    - Analyzes problem descriptions and test cases
    - Generates contextually appropriate solutions
    - Can learn from feedback to improve future responses
    """
    
    def __init__(self, name: str):
        super().__init__(name)
        self.feedback_history = []
        self.submission_history = []
        
        self.custom_prompt = self._load_combined_prompt(name)
        
        self.last_full_response = None  # Store full response for Principle Evaluator
        
        # Get the shared Phi-4 model instance
        try:
            import sys
            sys.path.append('..')
            from backend.phi4_model import get_phi4_model
            self.phi4_model = get_phi4_model()
            self.phi4_model.initialize_model()  # Ensure it's loaded (singleton handles efficiency)
            print(f"🔗 {self.name} connected to shared Phi-4 model")
        except Exception as e:
            print(f"❌ Failed to connect to Phi-4 model: {e}")
            raise e
    
    def _load_combined_prompt(self, name: str) -> str:
        """Load and combine task instructions and personality prompts."""
        # Load individual personality
        with open(f"players/{name.lower()}.yaml", 'r') as f:
            personality_config = yaml.safe_load(f)
            personality = personality_config['personality']
        
        # Load shared task instructions
        with open("players/player.yaml", 'r') as f:
            player_config = yaml.safe_load(f)
            task_instructions = player_config['task_instructions']
        
        # Combine both prompts
        return f"{personality}\n\n{task_instructions}"
    
    def query(self, problem: CodingProblem) -> str:
        """
        Generate a solution for the given problem using Phi-4.
        """
        # Extract function name from stub code
        function_name = self._extract_function_name(problem.stub_code)
        
        # Create a comprehensive prompt for the model
        prompt = self._create_code_generation_prompt(problem, function_name)
        
        # Generate solution using Phi-4
        messages = [
            {
                "role": "user", 
                "content": f"{self.custom_prompt}\n\n{prompt}"
                # "content": f"{self.custom_prompt}"
            }
        ]
        
        print(f"🧠 Agent prompt: {messages}")
        generated_text = self.phi4_model.generate(messages, max_new_tokens=512, temperature=0.1, do_sample=True)
        
        print(f"Generated solution for {problem.id} using Phi-4")
        print(f"Full player response: {generated_text}")
        
        # Store the FULL response (including thinking) for history
        self.last_full_response = generated_text
        
        # Store in submission history for player log display (full response)
        submission_entry = {
            'timestamp': datetime.now().isoformat(),
            'problem_id': problem.id,
            'full_response': generated_text
        }
        self.submission_history.append(submission_entry)
        
        # Extract and return only the part after "RESPONSE:" for the contest engine
        response_to_pe = self._extract_response_section(generated_text)
        print(f"🔍 Response to PE: {response_to_pe}")
        return response_to_pe
    
    def _create_code_generation_prompt(self, problem: CodingProblem, function_name: str) -> str:
        """Create a simple prompt for code generation."""
        return f"""==== YOUR TASK ====
Problem: {problem.description or 'No description provided'}

Implement the function {function_name} correctly."""
    
    def _extract_function_name(self, stub_code: str) -> str:
        """Extract the function name from stub code."""
        match = re.search(r'def\s+(\w+)\s*\(', stub_code)
        return match.group(1) if match else 'unknown_function'
    
    def _extract_response_section(self, full_text: str) -> str:
        """Extract only the text after 'RESPONSE:' marker, or return full text if no marker found."""
        if "RESPONSE:" in full_text:
            # Find the RESPONSE: marker and return everything after it
            response_index = full_text.find("RESPONSE:")
            return full_text[response_index + len("RESPONSE:"):].strip()
        else:
            # No RESPONSE: marker found, return full text for backward compatibility
            return full_text
    
    def update(self, feedback: dict):
        """Process feedback from the previous submission."""
        feedback_entry = {
            'timestamp': datetime.now().isoformat(),
            'problem_id': feedback.get('problem_id'),
            'reward': feedback.get('reward'),
            'reasoning_transcript': feedback.get('reasoning_transcript', 'No reasoning available'),
            'full_feedback': feedback
        }
        self.feedback_history.append(feedback_entry)
