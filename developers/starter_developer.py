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
        self.phi4_model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize connection to the shared Phi-4 model."""
        try:
            import sys
            sys.path.append('..')
            from backend.phi4_model import get_phi4_model
            self.phi4_model = get_phi4_model()
            print(f"🔗 {self.name} connected to shared Phi-4 model")
        except Exception as e:
            print(f"❌ Failed to connect to Phi-4 model: {e}")
            print("💡 Falling back to basic template generation")
            self.phi4_model = None
    
    def query(self, problem: CodingProblem) -> str:
        """
        Generate a solution for the given problem using Phi-4.
        """
        if self.phi4_model is None or not self.phi4_model.is_available():
            return self._fallback_solution(problem)
        
        try:
            # Extract function name from stub code
            function_name = self._extract_function_name(problem.stub_code)
            
            # Create a comprehensive prompt for the model
            prompt = self._create_code_generation_prompt(problem, function_name)
            
            # Generate solution using Phi-4
            messages = [
                {
                    "role": "system", 
                    "content": "You are an expert Python programmer. Generate clean, efficient, and correct Python code solutions. Only return the function implementation, no explanations or markdown formatting."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
            
            generated_text = self.phi4_model.generate(messages, max_new_tokens=256, temperature=0.1, do_sample=True)
            
            if generated_text is None:
                return self._fallback_solution(problem)
            
            # Clean and extract the function from the generated text
            solution = self._extract_function_from_response(generated_text, function_name)
            
            print(f"🧠 Generated solution for {problem.id} using Phi-4")
            return solution
            
        except Exception as e:
            print(f"❌ Error generating solution with Phi-4: {e}")
            return self._fallback_solution(problem)
    
    def _create_code_generation_prompt(self, problem: CodingProblem, function_name: str) -> str:
        """Create a detailed prompt for code generation."""
        
        # Analyze test cases to understand expected behavior
        test_analysis = self._analyze_test_cases(problem.tests)
        
        # Include feedback from previous problems if available
        feedback_context = self._get_feedback_context()
        
        prompt = f"""
Problem: {problem.description or 'No description provided'}

Function signature:
{problem.stub_code}

Test cases analysis:
{test_analysis}

Requirements:
- Implement the function {function_name} correctly
- Make sure it passes all test cases
- Use efficient algorithms and handle edge cases
- Return only the complete function implementation

{feedback_context}

Generate the complete Python function:
"""
        return prompt.strip()
    
    def _analyze_test_cases(self, tests: str) -> str:
        """Analyze test cases to understand the expected behavior."""
        if not tests:
            return "No test cases provided"
        
        # Extract assert statements to understand expected behavior
        assert_lines = []
        for line in tests.split('\n'):
            line = line.strip()
            if line.startswith('assert '):
                assert_lines.append(line)
        
        if assert_lines:
            analysis = "Expected behavior based on test cases:\n"
            for i, assert_line in enumerate(assert_lines[:5], 1):  # Limit to first 5 tests
                analysis += f"{i}. {assert_line}\n"
            return analysis
        else:
            return "Test cases present but format unclear"
    
    def _get_feedback_context(self) -> str:
        """Get context from previous feedback to improve solutions."""
        if not self.feedback_history:
            return ""
        
        # Analyze recent feedback for patterns
        recent_feedback = self.feedback_history[-3:]  # Last 3 submissions
        
        successful_patterns = []
        failed_patterns = []
        
        for feedback in recent_feedback:
            result = feedback.get('result')
            if result and result.success:
                successful_patterns.append(f"✅ Problem {feedback.get('problem_id')}: Success")
            else:
                error = result.error if result and result.error else 'Unknown error'
                failed_patterns.append(f"❌ Problem {feedback.get('problem_id')}: {error}")
        
        if successful_patterns or failed_patterns:
            context = "\nPrevious performance context:\n"
            for pattern in successful_patterns:
                context += f"{pattern}\n"
            for pattern in failed_patterns:
                context += f"{pattern}\n"
            context += "Learn from these patterns to improve the current solution.\n"
            return context
        
        return ""
    
    def _extract_function_from_response(self, response: str, function_name: str) -> str:
        """Extract the function implementation from the model's response."""
        # Try to find the function definition
        lines = response.split('\n')
        function_lines = []
        in_function = False
        
        for line in lines:
            if f"def {function_name}" in line:
                in_function = True
                function_lines.append(line)
            elif in_function:
                if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                    # End of function (new non-indented line)
                    break
                function_lines.append(line)
        
        if function_lines:
            return '\n'.join(function_lines)
        else:
            # If we can't extract properly, return the whole response cleaned up
            return self._clean_response(response, function_name)
    
    def _clean_response(self, response: str, function_name: str) -> str:
        """Clean up the response and ensure it's a valid function."""
        # Remove markdown formatting
        response = re.sub(r'```python\s*', '', response)
        response = re.sub(r'```\s*', '', response)
        
        # If no function definition found, wrap in basic template
        if f"def {function_name}" not in response:
            return f"""
def {function_name}(*args, **kwargs):
    \"\"\"Generated solution\"\"\"
    {response.strip()}
"""
        
        return response.strip()
    
    def _extract_function_name(self, stub_code: str) -> str:
        """Extract the function name from stub code."""
        match = re.search(r'def\s+(\w+)\s*\(', stub_code)
        return match.group(1) if match else 'unknown_function'
    
    def _fallback_solution(self, problem: CodingProblem) -> str:
        """Fallback solution when Phi-4 is not available."""
        function_name = self._extract_function_name(problem.stub_code)
        
        return f"""
def {function_name}(*args, **kwargs):
    \"\"\"
    Fallback solution - Phi-4 model not available.
    TODO: Implement the actual logic based on the problem requirements.
    
    Problem: {problem.description or 'No description'}
    \"\"\"
    # Analyze the problem description and tests to understand what to implement
    # This is a placeholder that should be replaced with actual logic
    pass
"""
    
    def update(self, feedback: dict):
        """
        Process feedback from the previous submission to improve future solutions.
        """
        self.feedback_history.append(feedback)
        
        # Log feedback for analysis
        print(f"🔄 Developer {self.name} received feedback:")
        print(f"  Problem: {feedback.get('problem_id')}")
        print(f"  Reward: {feedback.get('reward')}")
        print(f"  Bank Balance: {feedback.get('bank_balance')}")
        
        if feedback.get('result'):
            result = feedback['result']
            print(f"  Tests Passed: {result.tests_passed}/{result.total_tests}")
            if not result.success:
                print(f"  Error: {result.error}")
        
        # Keep only recent feedback to avoid memory issues
        if len(self.feedback_history) > 10:
            self.feedback_history = self.feedback_history[-10:]


class SimpleDeveloper(Developer):
    """
    A simple fallback developer for when Phi-4 is not available.
    """
    
    def __init__(self, name: str):
        super().__init__(name)
        self.feedback_history = []
    
    def query(self, problem: CodingProblem) -> str:
        """Generate a basic solution template."""
        function_name = self._extract_function_name(problem.stub_code)
        
        return f"""
def {function_name}(*args, **kwargs):
    \"\"\"
    Simple template solution.
    Problem: {problem.description or 'No description'}
    \"\"\"
    # TODO: Implement the actual logic
    pass
"""
    
    def update(self, feedback: dict):
        """Process feedback."""
        self.feedback_history.append(feedback)
        print(f"Simple developer {self.name} received feedback for problem {feedback.get('problem_id')}")
    
    def _extract_function_name(self, stub_code: str) -> str:
        """Extract the function name from stub code."""
        match = re.search(r'def\s+(\w+)\s*\(', stub_code)
        return match.group(1) if match else 'unknown_function'


# Default developer class for the contest
StarterDeveloper = Phi4Developer


# Example usage for contestants
if __name__ == "__main__":
    # Test your developer locally
    developer = Phi4Developer("TestDeveloper")
    
    # Create a sample problem
    sample_problem = CodingProblem(
        id="test",
        stub_code="""
def add_numbers(a, b):
    \"\"\"Add two numbers.\"\"\"
    pass
""",
        tests="""
def test_add_numbers():
    assert add_numbers(2, 3) == 5
    assert add_numbers(-1, 1) == 0
""",
        description="Add two numbers together"
    )
    
    # Generate solution
    solution = developer.query(sample_problem)
    print("Generated solution:")
    print(solution)
    
    # Test feedback
    sample_feedback = {
        "problem_id": "test",
        "reward": 1000,
        "bank_balance": 1000,
        "result": {
            "success": True,
            "tests_passed": 2,
            "total_tests": 2
        }
    }
    
    developer.update(sample_feedback) 