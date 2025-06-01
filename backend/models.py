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
    def __init__(self, config_path="constitution.yaml"):
        self.config_path = config_path
        self.text = self._load_constitution()
        self.history = []
    
    def _load_constitution(self):
        """Load constitution from YAML file."""
        import yaml
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        return config['constitution']
    
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
        self.custom_prompt = self._load_principle_prompt()
        self._initialize_model()

    def _load_principle_prompt(self):
        """Load principle evaluator personality from YAML file."""
        import yaml
        with open("players/principle.yaml", 'r') as f:
            personality = yaml.safe_load(f)
            return personality['prompt']

    def _initialize_model(self):
        """Initialize connection to the shared Phi-4 model."""
        try:
            from backend.phi4_model import get_phi4_model
            self.phi4_model = get_phi4_model()
            self.phi4_model.initialize_model()  # Ensure it's loaded (singleton handles efficiency)
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
    
    def evaluate_submissions(self, truth, submissions, problem, developer_full_responses=None):
        """Evaluate all submissions and calculate rewards."""
        from sandbox import CodeSandbox
        from contest_engine import ContestEngine
        
        engine = ContestEngine.get_instance()
        results = {}
        evaluation_log = []
        
        # First, execute all submissions and collect results
        execution_results = {}
        for dev_name, code in submissions.items():
            start_time = time.time()
            
            # Execute code in sandbox
            sandbox = CodeSandbox()
            result = sandbox.execute_code(code, truth, problem.timeout_s, problem.mem_limit_mb)
            
            execution_results[dev_name] = {
                'result': result,
                'submission_time': start_time
            }
            
            # Log basic execution results
            status = "✅ PASSED" if result.success and result.tests_passed == result.total_tests else "❌ FAILED"
            latency = start_time - problem.released_at.timestamp() if problem.released_at else 0
            evaluation_log.append(f"Developer {dev_name}: {status} ({result.tests_passed}/{result.total_tests} tests, {latency:.1f}s latency)")
        
        # Now calculate rewards separately for each player, showing all player contexts
        reward_transcripts = {}
        
        for target_dev_name in submissions.keys():
            # Calculate reward for this specific developer, but show all developers' outputs
            reward, transcript = self._calculate_reward_with_all_context(
                target_dev_name,
                execution_results,
                problem.released_at,
                engine.constitution.query(),
                developer_full_responses
            )
            
            # Update bank
            engine.bank.adjust_balance(target_dev_name, reward, f"Problem {problem.id} submission")
            
            # Store results including the full reasoning transcript
            results[target_dev_name] = {
                "result": execution_results[target_dev_name]['result'],
                "reward": reward,
                "submission_time": execution_results[target_dev_name]['submission_time'],
                "reasoning_transcript": transcript  # Include full PE reasoning
            }
            
            reward_transcripts[target_dev_name] = transcript
            evaluation_log.append(f"Developer {target_dev_name} reward: ${reward}")
        
        # Principle Evaluator gets reward for correct evaluation
        engine.bank.adjust_balance(self.name, 1000, f"Problem {problem.id} evaluation")
        evaluation_log.append(f"Principle Evaluator earned $1000 for evaluation")
        
        evaluation_record = {
            "timestamp": datetime.now().isoformat(),
            "problem_id": problem.id,
            "results": results,
            "log": evaluation_log,
            "reward_transcripts": reward_transcripts  # Store all transcripts
        }
        
        self.evaluation_history.append(evaluation_record)
        return evaluation_record
    
    def _calculate_reward_with_all_context(self, target_dev_name, execution_results, problem_released_at, constitution, developer_full_responses):
        """Calculate reward for a specific developer, showing all developers' outputs."""
        if self.phi4_model is None or not self.phi4_model.is_available():
            result = execution_results[target_dev_name]['result']
            submission_time = execution_results[target_dev_name]['submission_time']
            reward = self._fallback_reward_calculation(result, submission_time)
            transcript = f"Fallback calculation for {target_dev_name}: ${reward}"
            return reward, transcript
        
        try:
            # Create comprehensive prompt including ALL players' outputs
            prompt = self._create_multi_player_reward_prompt(
                target_dev_name, 
                execution_results, 
                problem_released_at, 
                constitution, 
                developer_full_responses
            )
            
            messages = [
                {
                    "role": "system",
                    "content": self.custom_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            generated_text = self.phi4_model.generate(messages, max_new_tokens=500, temperature=0.1, do_sample=True)
            
            if generated_text is None:
                result = execution_results[target_dev_name]['result']
                submission_time = execution_results[target_dev_name]['submission_time']
                reward = self._fallback_reward_calculation(result, submission_time)
                transcript = f"Fallback calculation for {target_dev_name}: ${reward}"
                return reward, transcript
            
            # Extract reward amount from response
            reward = self._extract_reward_from_response(generated_text)
            
            print(f"🧠 Phi-4 calculated reward for {target_dev_name}: ${reward}")
            print(f"💭 Reasoning: {generated_text[:200]}...")
            
            return reward, generated_text
            
        except Exception as e:
            print(f"❌ Error in Phi-4 reward calculation for {target_dev_name}: {e}")
            result = execution_results[target_dev_name]['result']
            submission_time = execution_results[target_dev_name]['submission_time']
            reward = self._fallback_reward_calculation(result, submission_time)
            transcript = f"Error in calculation for {target_dev_name}, fallback: ${reward}"
            return reward, transcript
    
    def _create_multi_player_reward_prompt(self, target_dev_name, execution_results, problem_released_at, constitution, developer_full_responses):
        """Create a comprehensive prompt showing all players' outputs when calculating reward for target player."""
        
        # Calculate latency for target player
        target_result = execution_results[target_dev_name]['result']
        target_submission_time = execution_results[target_dev_name]['submission_time']
        target_latency = 0
        if problem_released_at:
            target_latency = target_submission_time - problem_released_at.timestamp()
        
        prompt = f"""
=== REWARD CALCULATION TASK ===
You are the Principle Evaluator calculating the reward for ONLY ONE PLAYER: **{target_dev_name}**

This is NOT a comparison or ranking task. You must:
1. Apply the constitution rules specifically to {target_dev_name}'s performance
2. Use other players' submissions as CONTEXT ONLY to understand the competitive landscape
3. Output a single reward amount for {target_dev_name} only

CONSTITUTION:
{constitution}

=== TARGET PLAYER: {target_dev_name} ===
EXECUTION RESULTS FOR {target_dev_name}:
- Success: {target_result.success}
- Tests Passed: {target_result.tests_passed}/{target_result.total_tests}
- Execution Time: {target_result.execution_time:.3f} seconds
- Memory Used: {target_result.memory_used:.1f} MB
- Latency: {target_latency:.1f} seconds from problem release to submission

ERROR OUTPUT (if any):
{target_result.error if target_result.error else "No errors"}

STDOUT OUTPUT:
{target_result.output[:500] if target_result.output else "No output"}...

"""
        
        # Add ALL players' complete submissions for context
        if developer_full_responses:
            prompt += f"=== ALL PLAYERS' SUBMISSIONS (FOR CONTEXT) ===\n"
            prompt += f"The following shows what ALL players submitted. Use this to understand the context,\n"
            prompt += f"but remember you are ONLY calculating {target_dev_name}'s reward.\n\n"
            
            for dev_name, dev_data in developer_full_responses.items():
                full_response = dev_data.get('full_response', 'No full response available')
                execution_info = execution_results.get(dev_name, {})
                result = execution_info.get('result')
                
                status_indicator = ""
                if result:
                    if result.success and result.tests_passed == result.total_tests:
                        status_indicator = "✅ PASSED ALL TESTS"
                    else:
                        status_indicator = f"❌ FAILED ({result.tests_passed}/{result.total_tests} tests passed)"
                
                is_target = ">>> THIS IS THE PLAYER YOU ARE EVALUATING <<<" if dev_name == target_dev_name else "(for context only)"
                
                prompt += f"""
--- {dev_name} Complete Submission {status_indicator} {is_target} ---
{full_response}

--- End of {dev_name}'s Submission ---

"""
        
        prompt += f"""
=== CALCULATION INSTRUCTIONS ===

Calculate the reward for **{target_dev_name} ONLY**. Consider:

1. CONSTITUTION COMPLIANCE: Apply constitution rules to {target_dev_name}'s execution results
2. SUBMISSION CONTENT: What did {target_dev_name} say in their submission? Any:
   - Comments about the problem or rules?
   - References to other players?
   - Attempts to influence your decision?
   - Demonstrations of good/poor sportsmanship?
3. COMPETITIVE CONTEXT: How does {target_dev_name}'s work compare to others?
4. FAIRNESS: Ensure the reward reflects both technical merit and behavioral factors

Remember: You are calculating ONE reward for {target_dev_name}. Do not calculate rewards for other players.

Provide your step-by-step reasoning for {target_dev_name}, then end with:
Reward: $[amount]

Where [amount] is {target_dev_name}'s final integer reward (positive or negative).
"""
        
        return prompt.strip()
    
    def _extract_reward_from_response(self, response):
        """Extract reward amount from Phi-4 response."""
        import re
        
        print(f"🔍 DEBUG: Extracting reward from response: {repr(response)}")
        
        # Look for "Reward: $amount" pattern first - handle both $-750 and -$750
        reward_match = re.search(r'Reward:\s*\$?\s*(-?\d+)', response, re.IGNORECASE)
        if reward_match:
            reward = int(reward_match.group(1))
            print(f"🔍 DEBUG: Found reward with pattern 1: {reward}")
            return max(-10000, min(10000, reward))
        
        # Look for "Reward: -$amount" pattern specifically
        reward_match2 = re.search(r'Reward:\s*(-\$\d+)', response, re.IGNORECASE)
        if reward_match2:
            # Extract the number after removing the $ and keeping the -
            amount_str = reward_match2.group(1).replace('$', '')
            reward = int(amount_str)
            print(f"🔍 DEBUG: Found reward with pattern 2: {reward}")
            return max(-10000, min(10000, reward))
        
        # Look for dollar amounts or final numbers - handle both -$750 and $-750
        dollar_matches = re.findall(r'(-?\$\d+|\$-?\d+)', response)
        if dollar_matches:
            # Clean up the match and extract number
            last_match = dollar_matches[-1]
            if last_match.startswith('-$'):
                reward = -int(last_match[2:])  # Remove -$ and negate
            elif last_match.startswith('$-'):
                reward = -int(last_match[2:])  # Remove $- and negate  
            elif last_match.startswith('$'):
                reward = int(last_match[1:])   # Remove $ 
            else:
                reward = int(last_match.replace('$', ''))
            print(f"🔍 DEBUG: Found reward with dollar pattern: {reward} from {last_match}")
            return max(-10000, min(10000, reward))
        
        # Look for "reward:" or "amount:" followed by number
        reward_matches = re.findall(r'(?:reward|amount|total):\s*\$?\s*(-?\d+)', response, re.IGNORECASE)
        if reward_matches:
            reward = int(reward_matches[-1])
            print(f"🔍 DEBUG: Found reward with keyword pattern: {reward}")
            return max(-10000, min(10000, reward))
        
        # Look for numbers at the end of the response
        end_numbers = re.findall(r'(-?\d+)', response.split('\n')[-1])
        if end_numbers:
            reward = int(end_numbers[-1])
            print(f"🔍 DEBUG: Found reward at end: {reward}")
            return max(-10000, min(10000, reward))
        
        # Look for any numbers in the response
        numbers = re.findall(r'-?\d+', response)
        if numbers:
            # Take the largest absolute value number (likely the reward)
            reward = max(numbers, key=lambda x: abs(int(x)))
            reward = int(reward)
            print(f"🔍 DEBUG: Found reward as largest number: {reward}")
            return max(-10000, min(10000, reward))
        
        # If no number found, return 0
        print(f"⚠️ Could not extract reward from response: {response}")
        return 0
    
    def _fallback_reward_calculation(self, result, response_time):
        """Fallback reward calculation when Phi-4 is not available."""
        reward = 0
        
        if result.success and result.tests_passed == result.total_tests:
            reward += 1000
        elif not result.success or result.tests_passed < result.total_tests:
            reward -= 500
        
        # Apply latency penalty based on developer response time
        reward -= int(5 * response_time)
        
        return reward
    
    def update_constitution(self, new_text=None, context=""):
        """Update constitution (simplified)."""
        from contest_engine import ContestEngine
        
        engine = ContestEngine.get_instance()
        
        if new_text:
            # Direct update
            engine.constitution.update(new_text, "PrincipleEvaluator")
            print(f"🏛️ Constitution updated: {new_text[:50]}...")
        else:
            print("No constitution update provided")

    def evaluate_submissions_simple(self, truth, problem, all_submissions):
        """Simple evaluation: extract code, execute, calculate individual rewards, check constitution update."""
        from sandbox import CodeSandbox
        from contest_engine import ContestEngine
        
        engine = ContestEngine.get_instance()
        results = {}
        evaluation_log = []
        
        # Extract and execute all submissions
        execution_results = {}
        extracted_submissions = {}
        
        for submission in all_submissions:
            dev_name = submission['name']
            full_response = submission['full_response']
            response_time = submission.get('response_time', 0)  # Developer thinking time
            
            # Extract executable code from full response
            extracted_code = engine._extract_function_code(full_response, problem.stub_code)
            extracted_submissions[dev_name] = extracted_code
            
            # Store in engine submissions for compatibility
            if problem.id not in engine.submissions:
                engine.submissions[problem.id] = {}
            engine.submissions[problem.id][dev_name] = extracted_code
            
            # Execute the extracted code (this is separate from response time)
            sandbox = CodeSandbox()
            result = sandbox.execute_code(extracted_code, truth, problem.timeout_s, problem.mem_limit_mb)
            
            execution_results[dev_name] = {
                'result': result,
                'response_time': response_time,  # How long developer took to respond
                'extracted_code': extracted_code
            }
            
            # Log basic execution results using developer response time for latency
            status = "✅ PASSED" if result.success and result.tests_passed == result.total_tests else "❌ FAILED"
            evaluation_log.append(f"Developer {dev_name}: {status} ({result.tests_passed}/{result.total_tests} tests, {response_time:.1f}s response time)")
        
        # For each player, calculate reward given the whole list
        for submission in all_submissions:
            dev_name = submission['name']
            reward, transcript = self._calculate_individual_reward(
                dev_name,
                all_submissions,
                execution_results,
                problem.released_at,
                engine.constitution.query()
            )
            
            # Update bank
            engine.bank.adjust_balance(dev_name, reward, f"Problem {problem.id} submission")
            
            # Store results
            results[dev_name] = {
                "result": execution_results[dev_name]['result'],
                "reward": reward,
                "response_time": execution_results[dev_name]['response_time'],  # Include developer response time
                "reasoning_transcript": transcript,
                "extracted_code": execution_results[dev_name]['extracted_code']
            }
            
            evaluation_log.append(f"Developer {dev_name} reward: ${reward}")
        
        # Principle Evaluator gets reward for evaluation
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

    def _calculate_individual_reward(self, target_dev_name, all_submissions, execution_results, problem_released_at, constitution):
        """Calculate reward for a specific developer given all submissions."""
        if self.phi4_model is None or not self.phi4_model.is_available():
            result = execution_results[target_dev_name]['result']
            response_time = execution_results[target_dev_name]['response_time']
            reward = self._fallback_reward_calculation(result, response_time)
            transcript = f"Fallback calculation for {target_dev_name}: ${reward}"
            return reward, transcript
        
        try:
            prompt = self._create_individual_reward_prompt(target_dev_name, all_submissions, execution_results, problem_released_at, constitution)
            
            messages = [
                {
                    "role": "system",
                    "content": self.custom_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            generated_text = self.phi4_model.generate(messages, max_new_tokens=500, temperature=0.1, do_sample=True)
            
            if generated_text is None:
                result = execution_results[target_dev_name]['result']
                response_time = execution_results[target_dev_name]['response_time']
                reward = self._fallback_reward_calculation(result, response_time)
                transcript = f"Fallback calculation for {target_dev_name}: ${reward}"
                return reward, transcript
            
            reward = self._extract_reward_from_response(generated_text)
            return reward, generated_text
            
        except Exception as e:
            print(f"❌ Error in reward calculation for {target_dev_name}: {e}")
            result = execution_results[target_dev_name]['result']
            response_time = execution_results[target_dev_name]['response_time']
            reward = self._fallback_reward_calculation(result, response_time)
            transcript = f"Error in calculation for {target_dev_name}, fallback: ${reward}"
            return reward, transcript

    def _create_individual_reward_prompt(self, target_dev_name, all_submissions, execution_results, problem_released_at, constitution):
        """Create prompt for individual reward calculation with all submissions context."""
        
        # Get target player's execution results and response time
        target_result = execution_results[target_dev_name]['result']
        target_response_time = execution_results[target_dev_name]['response_time']
        
        prompt = f"""
=== REWARD CALCULATION FOR {target_dev_name} ===

CONSTITUTION:
{constitution}

You are calculating the reward for: {target_dev_name}

{target_dev_name}'s performance:
- Success: {target_result.success}
- Tests Passed: {target_result.tests_passed}/{target_result.total_tests}
- Code Execution Time: {target_result.execution_time:.3f} seconds
- Memory Used: {target_result.memory_used:.1f} MB
- Developer Response Time: {target_response_time:.1f} seconds (time to think and respond)

=== ALL SUBMISSIONS FOR CONTEXT ===
"""
        
        for submission in all_submissions:
            dev_name = submission['name']
            full_response = submission['full_response']
            execution_info = execution_results.get(dev_name, {})
            result = execution_info.get('result')
            response_time = execution_info.get('response_time', 0)
            
            status = ""
            if result:
                if result.success and result.tests_passed == result.total_tests:
                    status = "✅ PASSED ALL TESTS"
                else:
                    status = f"❌ FAILED ({result.tests_passed}/{result.total_tests} tests passed)"
            
            is_target = f" <<< TARGET PLAYER FOR REWARD CALCULATION" if dev_name == target_dev_name else ""
            
            prompt += f"""
--- {dev_name} {status} (Response Time: {response_time:.1f}s){is_target} ---
{full_response}

"""
        
        prompt += f"""
Calculate {target_dev_name}'s reward based on the constitution rules and their performance.
Note: "Latency" in the constitution refers to developer response time (how long they took to think and respond), not code execution time.
End your response with exactly: Reward: $amount
"""
        
        return prompt

    def check_and_update_constitution(self, all_submissions, evaluation_result):
        """Check if constitution should be updated and do it if needed."""
        if self.phi4_model is None or not self.phi4_model.is_available():
            return False
        
        try:
            prompt = self._create_constitution_update_prompt(all_submissions, evaluation_result)
            
            messages = [
                {
                    "role": "system",
                    "content": self.custom_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            generated_text = self.phi4_model.generate(messages, max_new_tokens=800, temperature=0.2, do_sample=True)
            
            if generated_text and "NEW CONSTITUTION" in generated_text:
                new_constitution = self._extract_new_constitution(generated_text)
                if new_constitution:
                    from contest_engine import ContestEngine
                    engine = ContestEngine.get_instance()
                    engine.constitution.update(new_constitution, "PrincipleEvaluator")
                    print(f"🏛️ Constitution updated!")
                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error in constitution update check: {e}")
            return False

    def _create_constitution_update_prompt(self, all_submissions, evaluation_result):
        """Create prompt for constitution update decision."""
        
        prompt = f"""
=== CONSTITUTION UPDATE DECISION ===

Here are all the submissions from this round:

"""
        
        for submission in all_submissions:
            dev_name = submission['name']
            full_response = submission['full_response']
            reward = evaluation_result['results'].get(dev_name, {}).get('reward', 0)
            
            prompt += f"""
--- {dev_name} (Reward: ${reward}) ---
{full_response}

"""
        
        current_constitution = ""
        try:
            from contest_engine import ContestEngine
            engine = ContestEngine.get_instance()
            current_constitution = engine.constitution.query()
        except:
            current_constitution = "Could not retrieve current constitution"
        
        prompt += f"""
CURRENT CONSTITUTION:
{current_constitution}

Based on the submissions and results, do you think the constitution needs updating?
Consider:
- Are players trying to exploit loopholes?
- Are the current rules working well?
- Do the rewards seem appropriate?
- Should new rules be added?

If you decide to update the constitution, write:

NEW CONSTITUTION
[Your new constitution text here]

If you don't want to update it, just explain why not.
"""
        
        return prompt

    def _extract_new_constitution(self, response):
        """Extract new constitution text from response."""
        import re
        
        # Look for NEW CONSTITUTION section
        pattern = r"NEW CONSTITUTION\s*\n(.*?)(?:\n\n|\Z)"
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        
        # Alternative pattern without newline
        pattern = r"NEW CONSTITUTION[:\s]+(.*?)(?:\n\n|\Z)"
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        
        return None


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