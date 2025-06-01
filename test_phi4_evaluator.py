#!/usr/bin/env python3

from backend.models import PrincipleEvaluator, SubmissionResult
import time
from datetime import datetime

def test_phi4_reward_calculation():
    """Test the Phi-4 based reward calculation."""
    
    print("🧪 Testing Phi-4 PrincipleEvaluator reward calculation...")
    
    # Initialize PrincipleEvaluator
    pe = PrincipleEvaluator()
    
    # Test case 1: Perfect submission
    print("\n📝 Test Case 1: Perfect submission (all tests pass)")
    result1 = SubmissionResult(
        success=True,
        output="42\n",
        error=None,
        execution_time=0.05,
        memory_used=8.2,
        tests_passed=3,
        total_tests=3
    )
    
    constitution = """All unit tests pass: + $1,000

Compilation error or any failing test: – $500

Latency: – $5 × (seconds from problem release to query return)

The Principle Evaluator may overwrite these lines (or add new ones) after any round."""
    
    problem_released_at = datetime.now()
    submission_time = time.time() + 1.5  # 1.5 seconds later
    
    reward1 = pe._calculate_reward(result1, problem_released_at, submission_time, constitution)
    print(f"Result: ${reward1}")
    
    # Test case 2: Failed submission
    print("\n📝 Test Case 2: Failed submission (compilation error)")
    result2 = SubmissionResult(
        success=False,
        output="",
        error="SyntaxError: invalid syntax",
        execution_time=0.0,
        memory_used=0.0,
        tests_passed=0,
        total_tests=3
    )
    
    submission_time2 = time.time() + 3.0  # 3 seconds later
    reward2 = pe._calculate_reward(result2, problem_released_at, submission_time2, constitution)
    print(f"Result: ${reward2}")
    
    # Test case 3: Partial success
    print("\n📝 Test Case 3: Partial success (2/3 tests pass)")
    result3 = SubmissionResult(
        success=True,
        output="Some output\n",
        error=None,
        execution_time=0.12,
        memory_used=15.7,
        tests_passed=2,
        total_tests=3
    )
    
    submission_time3 = time.time() + 0.8  # 0.8 seconds later
    reward3 = pe._calculate_reward(result3, problem_released_at, submission_time3, constitution)
    print(f"Result: ${reward3}")
    
    print("\n✅ Phi-4 reward calculation test completed!")

if __name__ == "__main__":
    test_phi4_reward_calculation() 