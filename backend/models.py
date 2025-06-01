from abc import ABC, abstractmethod
import time
import json
from datetime import datetime


class CodingProblem:
    def __init__(self, id, stub_code, tests, timeout_s=1, mem_limit_mb=256, description=None, released_at=None):
        self.id = id
        self.stub_code = stub_code
        self.tests = tests
        self.timeout_s = timeout_s
        self.mem_limit_mb = mem_limit_mb
        self.description = description
        self.released_at = released_at
    
    def dict(self):
        return {
            "id": self.id,
            "stub_code": self.stub_code,
            "tests": self.tests,
            "timeout_s": self.timeout_s,
            "mem_limit_mb": self.mem_limit_mb,
            "description": self.description,
            "released_at": self.released_at.isoformat() if self.released_at else None
        }


class SubmissionResult:
    def __init__(self, success, output, error=None, execution_time=0.0, memory_used=0, tests_passed=0, total_tests=1):
        self.success = success
        self.output = output
        self.error = error
        self.execution_time = execution_time
        self.memory_used = memory_used
        self.tests_passed = tests_passed
        self.total_tests = total_tests


class Developer(ABC):
    def __init__(self, name):
        self.name = name
        self.account = None  # Will be set when registered
    
    @abstractmethod
    def query(self, problem):
        """Generate code solution for the given problem."""
        pass
    
    @abstractmethod
    def update(self, feedback):
        """Process feedback from the previous submission."""
        pass
    
    def get_balance(self):
        """Get current bank balance."""
        return self.account.get_balance() if self.account else 0
    
    def get_history(self, limit=10):
        """Get transaction history."""
        return self.account.get_history(limit) if self.account else []
    
    def get_leaderboard(self):
        """Get current leaderboard."""
        return self.account.get_leaderboard() if self.account else []
    
    def get_constitution(self):
        """Get current constitution text."""
        from contest_engine import ContestEngine
        return ContestEngine.get_instance().constitution.query()


class Constitution:
    def __init__(self):
        self.text = self._default_constitution()
        self.history = []
    
    def _default_constitution(self):
        return """All unit tests pass: + $1,000

Compilation error or any failing test: – $500

Latency: – $5 × (seconds from problem release to query return)

The Principle Evaluator may overwrite these lines (or add new ones) after any round."""
    
    def query(self):
        return self.text
    
    def update(self, new_text, by):
        if by != "PrincipleEvaluator":
            raise PermissionError("Only PrincipleEvaluator can modify the constitution")
        
        old_text = self.text
        self.text = new_text
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "updated_by": by,
            "old_text": old_text,
            "new_text": new_text
        })


class BankReader:
    """Safe read-only interface to bank - no write methods exposed."""
    
    def __init__(self, bank):
        self._get_balance = bank.get_balance
        self._get_history = bank.get_history
        self._get_leaderboard = bank.get_leaderboard
        self._get_total_money = bank.get_total_money
    
    def get_balance(self, actor):
        return self._get_balance(actor)
    
    def get_history(self, actor=None, limit=100):
        return self._get_history(actor, limit)
    
    def get_leaderboard(self):
        return self._get_leaderboard()
    
    def get_total_money(self):
        return self._get_total_money()


class Account:
    """Read-only account interface for players."""
    
    def __init__(self, actor_name, bank_reader):
        self._actor_name = actor_name
        self._bank_reader = bank_reader
    
    def get_balance(self):
        """Get my current balance."""
        return self._bank_reader.get_balance(self._actor_name)
    
    def get_history(self, limit=10):
        """Get my transaction history."""
        return self._bank_reader.get_history(self._actor_name, limit)
    
    def get_leaderboard(self):
        """Get current leaderboard."""
        return self._bank_reader.get_leaderboard()
    
    def get_total_money(self):
        """Get total money in the system."""
        return self._bank_reader.get_total_money()


class Bank:
    """Bank manages all monetary balances and transactions."""
    
    def __init__(self):
        self._balances = {}
        self._transaction_history = []
    
    def get_balance(self, actor):
        """Get current balance for an actor."""
        return self._balances.get(actor, 0)
    
    def get_all_balances(self):
        """Get all current balances."""
        return self._balances.copy()
    
    def get_history(self, actor=None, limit=100):
        """Get transaction history, optionally filtered by actor."""
        history = self._transaction_history
        
        if actor:
            history = [t for t in history if t["actor"] == actor]
        
        return history[-limit:] if len(history) > limit else history.copy()
    
    def get_leaderboard(self):
        """Get current leaderboard sorted by balance."""
        return [
            {"name": actor, "balance": balance}
            for actor, balance in sorted(self._balances.items(), key=lambda x: x[1], reverse=True)
        ]
    
    def get_total_money(self):
        """Get total money in the system."""
        return sum(self._balances.values())
    
    def create_account(self, actor_name):
        """Create a read-only account for an actor."""
        bank_reader = BankReader(self)
        return Account(actor_name, bank_reader)
    
    # Write methods (only for PrincipleEvaluator)
    def deposit(self, actor, amount, reason=""):
        """Add money to an actor's account."""
        if amount < 0:
            raise ValueError("Deposit amount must be positive")
        self._update_balance(actor, amount, reason)
    
    def withdraw(self, actor, amount, reason=""):
        """Remove money from an actor's account."""
        if amount < 0:
            raise ValueError("Withdrawal amount must be positive")
        self._update_balance(actor, -amount, reason)
    
    def transfer(self, from_actor, to_actor, amount, reason=""):
        """Transfer money between actors."""
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")
        
        from_balance = self._balances.get(from_actor, 0)
        if from_balance < amount:
            raise ValueError(f"Insufficient funds: {from_actor} has ${from_balance}, needs ${amount}")
        
        self._update_balance(from_actor, -amount, f"Transfer to {to_actor}: {reason}")
        self._update_balance(to_actor, amount, f"Transfer from {from_actor}: {reason}")
    
    def adjust_balance(self, actor, delta, reason=""):
        """Adjust balance by delta (positive or negative)."""
        self._update_balance(actor, delta, reason)
    
    def _update_balance(self, actor, delta, reason):
        """Internal method to update balance and record transaction."""
        old_balance = self._balances.get(actor, 0)
        new_balance = old_balance + delta
        self._balances[actor] = new_balance
        
        transaction = {
            "timestamp": datetime.now().isoformat(),
            "actor": actor,
            "delta": delta,
            "old_balance": old_balance,
            "new_balance": new_balance,
            "reason": reason
        }
        
        self._transaction_history.append(transaction)
    
    # Legacy methods for backward compatibility
    def query_balance(self, actor):
        return self.get_balance(actor)
    
    def query_leaderboard(self):
        return self.get_leaderboard()
    
    def query_transaction_history(self, actor=None, limit=100):
        return self.get_history(actor, limit)
    
    def query_total_money_in_system(self):
        return self.get_total_money()
    
    def query(self, actor):
        return self.get_balance(actor)
    
    def update(self, actor, delta, reason=""):
        self.adjust_balance(actor, delta, reason)


class PrincipleEvaluator(Developer):
    def __init__(self, name="PrincipleEvaluator"):
        super().__init__(name)
        self.evaluation_history = []
        self.phi4_model = None
        self._initialize_model()
        
        # Create demo constitution updates for diff viewer testing
        try:
            self._create_demo_constitution_updates()
        except Exception as e:
            print(f"ℹ️ Demo constitution updates skipped: {e}")
    
    def _initialize_model(self):
        """Initialize connection to the shared Phi-4 model."""
        try:
            from phi4_model import get_phi4_model
            self.phi4_model = get_phi4_model()
            print(f"🔗 {self.name} connected to shared Phi-4 model")
        except Exception as e:
            print(f"❌ Failed to connect to Phi-4 model: {e}")
            print("💡 Falling back to basic rule-based evaluation")
            self.phi4_model = None
    
    def query(self, problem):
        """Principle Evaluator doesn't submit solutions."""
        return "# Principle Evaluator does not submit solutions"
    
    def update(self, feedback):
        """Process feedback."""
        pass
    
    def evaluate_submissions(self, truth, submissions, problem):
        """Evaluate all submissions and calculate rewards."""
        from sandbox import CodeSandbox
        from contest_engine import ContestEngine
        
        engine = ContestEngine.get_instance()
        results = {}
        evaluation_log = []
        
        for dev_name, code in submissions.items():
            start_time = time.time()
            
            # Execute code in sandbox
            sandbox = CodeSandbox()
            result = sandbox.execute_code(code, truth, problem.timeout_s, problem.mem_limit_mb)
            
            # Calculate reward based on constitution using Phi-4
            reward = self._calculate_reward(result, problem.released_at, start_time, engine.constitution.query())
            
            # Update bank
            engine.bank.adjust_balance(dev_name, reward, f"Problem {problem.id} submission")
            
            results[dev_name] = {
                "result": result,
                "reward": reward,
                "submission_time": start_time
            }
            
            # Detailed evaluation log
            status = "✅ PASSED" if result.success and result.tests_passed == result.total_tests else "❌ FAILED"
            latency = start_time - problem.released_at.timestamp() if problem.released_at else 0
            evaluation_log.append(f"Developer {dev_name}: {status} ({result.tests_passed}/{result.total_tests} tests, {latency:.1f}s latency) → ${reward}")
        
        # Principle Evaluator gets reward for correct evaluation
        engine.bank.adjust_balance(self.name, 1000, f"Problem {problem.id} evaluation")
        evaluation_log.append(f"Principle Evaluator earned $1000 for evaluation")
        
        evaluation_record = {
            "timestamp": datetime.now().isoformat(),
            "problem_id": problem.id,
            "results": results,
            "log": evaluation_log
        }
        
        self.evaluation_history.append(evaluation_record)
        return evaluation_record
    
    def _calculate_reward(self, result, problem_released_at, submission_time, constitution):
        """Calculate reward using Phi-4 model based on constitution and results."""
        if self.phi4_model is None or not self.phi4_model.is_available():
            return self._fallback_reward_calculation(result, problem_released_at, submission_time)
        
        try:
            # Prepare comprehensive information for the model
            latency_seconds = 0
            if problem_released_at:
                latency_seconds = submission_time - problem_released_at.timestamp()
            
            prompt = self._create_reward_calculation_prompt(
                result, latency_seconds, constitution
            )
            
            messages = [
                {
                    "role": "system",
                    "content": "You are the Principle Evaluator for a coding contest. Calculate fair rewards based on the constitution and submission results. You MUST end your response with exactly this format:\n\nReward: $amount\n\nWhere amount is the reward (positive or negative integer)."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            generated_text = self.phi4_model.generate(messages, max_new_tokens=50, temperature=0.1, do_sample=True)
            
            if generated_text is None:
                return self._fallback_reward_calculation(result, problem_released_at, submission_time)
            
            # Extract reward amount from response
            reward = self._extract_reward_from_response(generated_text)
            
            print(f"🧠 Phi-4 calculated reward: ${reward}")
            print(f"💭 Reasoning: {generated_text[:200]}...")
            return reward
            
        except Exception as e:
            print(f"❌ Error in Phi-4 reward calculation: {e}")
            return self._fallback_reward_calculation(result, problem_released_at, submission_time)
    
    def _create_reward_calculation_prompt(self, result, latency_seconds, constitution):
        """Create a detailed prompt for reward calculation."""
        
        prompt = f"""
CONSTITUTION:
{constitution}

SUBMISSION RESULTS:
- Success: {result.success}
- Tests Passed: {result.tests_passed}/{result.total_tests}
- Execution Time: {result.execution_time:.3f} seconds
- Memory Used: {result.memory_used:.1f} MB
- Latency: {latency_seconds:.1f} seconds from problem release to submission

ERROR OUTPUT (if any):
{result.error if result.error else "No errors"}

STDOUT OUTPUT:
{result.output[:500] if result.output else "No output"}...

Based on the constitution rules and the submission results above, calculate the appropriate reward amount. Consider:
1. Test success/failure according to constitution rules
2. Latency penalties as specified
3. Any other factors mentioned in the constitution
4. Code quality indicators from execution results

Show your calculation step by step, then end with:
Reward: $[amount]

Where [amount] is the final integer reward (positive or negative).
"""
        return prompt.strip()
    
    def _extract_reward_from_response(self, response):
        """Extract reward amount from Phi-4 response."""
        import re
        
        # Look for "Reward: $amount" pattern first
        reward_match = re.search(r'Reward:\s*\$\s*(-?\d+)', response, re.IGNORECASE)
        if reward_match:
            reward = int(reward_match.group(1))
            return max(-10000, min(10000, reward))
        
        # Look for dollar amounts or final numbers
        dollar_matches = re.findall(r'\$\s*(-?\d+)', response)
        if dollar_matches:
            reward = int(dollar_matches[-1])  # Take the last dollar amount
            return max(-10000, min(10000, reward))
        
        # Look for "reward:" or "amount:" followed by number
        reward_matches = re.findall(r'(?:reward|amount|total):\s*\$?\s*(-?\d+)', response, re.IGNORECASE)
        if reward_matches:
            reward = int(reward_matches[-1])
            return max(-10000, min(10000, reward))
        
        # Look for numbers at the end of the response
        end_numbers = re.findall(r'(-?\d+)', response.split('\n')[-1])
        if end_numbers:
            reward = int(end_numbers[-1])
            return max(-10000, min(10000, reward))
        
        # Look for any numbers in the response
        numbers = re.findall(r'-?\d+', response)
        if numbers:
            # Take the largest absolute value number (likely the reward)
            reward = max(numbers, key=lambda x: abs(int(x)))
            reward = int(reward)
            return max(-10000, min(10000, reward))
        
        # If no number found, return 0
        print(f"⚠️ Could not extract reward from response: {response}")
        return 0
    
    def _fallback_reward_calculation(self, result, problem_released_at, submission_time):
        """Fallback reward calculation when Phi-4 is not available."""
        reward = 0
        
        if result.success and result.tests_passed == result.total_tests:
            reward += 1000
        elif not result.success or result.tests_passed < result.total_tests:
            reward -= 500
        
        if problem_released_at:
            latency_seconds = submission_time - problem_released_at.timestamp()
            reward -= int(5 * latency_seconds)
        
        return reward
    
    def update_constitution(self, new_text=None, context=""):
        """Update the constitution, optionally using Phi-4 for intelligent updates."""
        from contest_engine import ContestEngine
        engine = ContestEngine.get_instance()
        
        if new_text:
            # Direct update
            engine.constitution.update(new_text, self.name)
        elif self.phi4_model and self.phi4_model.is_available() and context:
            # Use Phi-4 to generate constitution update
            try:
                updated_constitution = self._generate_constitution_update(context, engine.constitution.query())
                engine.constitution.update(updated_constitution, self.name)
                print(f"🧠 Phi-4 updated constitution based on: {context}")
            except Exception as e:
                print(f"❌ Error in Phi-4 constitution update: {e}")
    
    def _generate_constitution_update(self, context, current_constitution):
        """Generate constitution update using Phi-4."""
        prompt = f"""
CURRENT CONSTITUTION:
{current_constitution}

CONTEXT FOR UPDATE:
{context}

Based on the context above, update the constitution to better reflect the current needs of the contest. The constitution should:
1. Be clear and fair
2. Address any issues mentioned in the context
3. Maintain the core structure of rewards and penalties
4. Be specific about amounts and conditions

Return only the updated constitution text, no explanations.
"""
        
        messages = [
            {
                "role": "system",
                "content": "You are the Principle Evaluator updating contest rules. Generate clear, fair constitution text based on the context provided."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        generated_text = self.phi4_model.generate(messages, max_new_tokens=300, temperature=0.2, do_sample=True)
        
        if generated_text is None:
            return current_constitution
        
        return generated_text.strip()
    
    def analyze_contest_performance(self, round_results):
        """Analyze contest performance and potentially update constitution."""
        if not self.phi4_model or not self.phi4_model.is_available():
            return
        
        try:
            # Analyze patterns in submissions and results
            analysis_context = self._create_performance_analysis(round_results)
            
            # Check if constitution update is needed
            if self._should_update_constitution(analysis_context):
                self.update_constitution(context=analysis_context)
                
        except Exception as e:
            print(f"❌ Error in performance analysis: {e}")
    
    def _create_performance_analysis(self, round_results):
        """Create analysis context from round results."""
        # Handle the evaluation_record format from evaluate_submissions
        if isinstance(round_results, dict) and 'results' in round_results:
            results = round_results['results']
        else:
            # Fallback in case format is different
            results = round_results if isinstance(round_results, dict) else {}
        
        total_submissions = len(results)
        successful_submissions = 0
        total_reward = 0
        
        for dev_name, result_data in results.items():
            try:
                # result_data should be {"result": SubmissionResult, "reward": int, "submission_time": float}
                if isinstance(result_data, dict):
                    submission_result = result_data.get('result')
                    reward = result_data.get('reward', 0)
                    
                    # Check if submission was successful
                    if hasattr(submission_result, 'success') and hasattr(submission_result, 'tests_passed') and hasattr(submission_result, 'total_tests'):
                        if submission_result.success and submission_result.tests_passed == submission_result.total_tests:
                            successful_submissions += 1
                    
                    total_reward += reward
                else:
                    # Handle unexpected format
                    print(f"⚠️ Unexpected result_data format for {dev_name}: {type(result_data)}")
                    
            except Exception as e:
                print(f"⚠️ Error processing result for {dev_name}: {e}")
                continue
        
        avg_reward = total_reward / max(1, total_submissions) if total_submissions > 0 else 0
        success_rate = (successful_submissions / max(1, total_submissions)) * 100 if total_submissions > 0 else 0
        
        context = f"""
Round Performance Summary:
- Total submissions: {total_submissions}
- Successful submissions: {successful_submissions}
- Success rate: {success_rate:.1f}%
- Average reward: ${avg_reward:.0f}

Recent evaluation patterns from last few rounds show various submission qualities and timing patterns.
"""
        return context
    
    def _should_update_constitution(self, analysis_context):
        """Determine if constitution should be updated based on analysis."""
        # Simple heuristic - could be made more sophisticated
        
        # Trigger updates more frequently for demonstration
        if len(self.evaluation_history) == 3:  # After 3rd round
            return True
        elif len(self.evaluation_history) == 7:  # After 7th round  
            return True
        elif len(self.evaluation_history) % 10 == 0:  # Every 10 rounds
            return True
            
        return False
    
    def _create_demo_constitution_updates(self):
        """Create some demonstration constitution updates for testing the diff viewer."""
        from contest_engine import ContestEngine
        engine = ContestEngine.get_instance()
        
        current_history_length = len(engine.constitution.history)
        
        # Add demo updates if none exist
        if current_history_length == 0:
            try:
                # First update - adjust penalties
                update1 = """All unit tests pass: + $1,000

Compilation error or any failing test: – $750

Latency: – $10 × (seconds from problem release to query return)

Code quality bonus: + $200 for efficient solutions
Memory usage penalty: – $100 for solutions exceeding 128MB

The Principle Evaluator may overwrite these lines (or add new ones) after any round."""
                
                engine.constitution.update(update1, "PrincipleEvaluator")
                print("📜 Added demo constitution update #1")
                
                # Small delay to make timestamps different
                import time
                time.sleep(1)
                
                # Second update - add new rules
                update2 = """All unit tests pass: + $1,000

Compilation error or any failing test: – $750

Latency: – $10 × (seconds from problem release to query return)

Code quality bonus: + $200 for efficient solutions
Memory usage penalty: – $100 for solutions exceeding 128MB
Syntax clarity bonus: + $150 for well-structured code

Early submission bonus: + $500 for submissions within 30 seconds
Late submission penalty: – $50 × (minutes after 5 minute deadline)

The Principle Evaluator may overwrite these lines (or add new ones) after any round."""
                
                engine.constitution.update(update2, "PrincipleEvaluator")
                print("📜 Added demo constitution update #2")
                
            except Exception as e:
                print(f"❌ Error creating demo constitution updates: {e}")


class ContestState:
    def __init__(self):
        self.current_problem_index = 0
        self.is_active = False
        self.start_time = None
        self.problems = []
        self.participants = []


# Simple helper functions for API responses - no typing needed
def api_response(success, message, data=None):
    return {"success": success, "message": message, "data": data} 