import asyncio
import time
import logging
import yaml
from datetime import datetime, timedelta
from pathlib import Path

from models import (
    CodingProblem, Developer, Constitution, Bank, PrincipleEvaluator,
    ContestState, SubmissionResult
)


class ContestEngine:
    _instance = None
    
    def __init__(self, config_path="config.yaml"):
        if ContestEngine._instance is not None:
            raise Exception("ContestEngine is a singleton!")
        
        ContestEngine._instance = self
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Logging (initialize first)
        logging.basicConfig(
            level=getattr(logging, self.config['logging']['level']),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config['logging']['file']),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize shared Phi-4 model
        self._initialize_shared_model()
        
        # Initialize core components
        self.constitution = Constitution()
        self.bank = Bank()
        self.principle_evaluator = PrincipleEvaluator()
        
        # Contest state
        self.state = ContestState()
        self.problems = []
        self.developers = {}
        self.submissions = {}
        
        # Event callbacks
        self.event_callbacks = []
        
        # Load problems
        self._load_problems()
    
    def _initialize_shared_model(self):
        """Initialize the shared Phi-4 model."""
        try:
            from backend.phi4_model import get_phi4_model
            phi4_model = get_phi4_model()
            phi4_model.initialize_model()
            self.logger.info(f"Shared Phi-4 model initialized: {phi4_model.get_device_info()}")
        except Exception as e:
            self.logger.error(f"Failed to initialize shared Phi-4 model: {e}")
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ContestEngine()
        return cls._instance
    
    def add_event_callback(self, callback):
        """Add callback for events."""
        self.event_callbacks.append(callback)
    
    def _emit_event(self, event_type, data):
        """Emit event to all callbacks."""
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        for callback in self.event_callbacks:
            try:
                callback(event)
            except Exception as e:
                self.logger.error(f"Error in event callback: {e}")
    
    def _load_problems(self):
        """Load problems directly from Kaggle dataset."""
        try:
            import kagglehub
            import pandas as pd
            
            # Download the dataset
            self.logger.info("Downloading Kaggle dataset...")
            path = kagglehub.dataset_download("bhaveshmittal/python-programming-questions-dataset")
            
            # Load the CSV file
            csv_file = Path(path) / "Python Programming Questions Dataset.csv"
            if not csv_file.exists():
                self.logger.error(f"Dataset CSV not found at {csv_file}")
                return
            
            df = pd.read_csv(csv_file)
            self.logger.info(f"Loaded {len(df)} problems from dataset")
            
            # Convert first 5 problems to CodingProblem objects
            num_problems = min(5, len(df))
            for i in range(num_problems):
                row = df.iloc[i]
                problem = self._create_problem_from_dataset(row, i+1)
                self.problems.append(problem)
                self.logger.info(f"Loaded problem {problem.id}: {problem.description[:50]}...")
                
        except Exception as e:
            self.logger.error(f"Error loading problems from dataset: {e}")
            # Create a few simple fallback problems
            self._create_fallback_problems()
        
        self.problems.sort(key=lambda p: int(p.id))
        self.state.problems = self.problems
    
    def _create_problem_from_dataset(self, row, problem_id):
        """Create a CodingProblem from dataset row."""
        import pandas as pd
        
        instruction = row['Instruction']
        input_data = row['Input'] if pd.notna(row['Input']) else ""
        expected_output = row['Output'] if pd.notna(row['Output']) else ""
        
        # Create a simple function stub
        stub_code = f"""def solve():
    \"\"\"
    {instruction}
    
    Input: {input_data}
    Expected Output: {expected_output}
    \"\"\"
    pass"""
        
        # Create a simple test that checks if the function runs
        test_code = f"""def test_solve():
    # Basic test - function should run without error
    try:
        result = solve()
        assert True  # If we get here, function ran successfully
    except Exception as e:
        assert False, f"Function failed with error: {{e}}\""""
        
        return CodingProblem(
            id=f"{problem_id:03d}",
            stub_code=stub_code,
            tests=test_code,
            description=instruction,
            timeout_s=self.config['execution']['timeout_seconds'],
            mem_limit_mb=self.config['execution']['memory_limit_mb']
        )
    
    def _create_fallback_problems(self):
        """Create simple fallback problems if dataset loading fails."""
        fallback_problems = [
            {
                "id": "001",
                "instruction": "Write a function that adds two numbers",
                "input": "a=5, b=3",
                "output": "8"
            },
            {
                "id": "002", 
                "instruction": "Write a function that returns the length of a string",
                "input": "text='hello'",
                "output": "5"
            },
            {
                "id": "003",
                "instruction": "Write a function that checks if a number is even",
                "input": "n=4",
                "output": "True"
            },
            {
                "id": "004",
                "instruction": "Write a function that finds the maximum in a list",
                "input": "numbers=[1, 5, 3, 9, 2]",
                "output": "9"
            },
            {
                "id": "005",
                "instruction": "Write a function that reverses a string",
                "input": "text='hello'",
                "output": "'olleh'"
            }
        ]
        
        for prob_data in fallback_problems:
            stub_code = f"""def solve():
    \"\"\"
    {prob_data['instruction']}
    
    Input: {prob_data['input']}
    Expected Output: {prob_data['output']}
    \"\"\"
    pass"""
            
            test_code = """def test_solve():
    try:
        result = solve()
        assert True
    except Exception as e:
        assert False, f"Function failed: {e}\""""
            
            problem = CodingProblem(
                id=prob_data['id'],
                stub_code=stub_code,
                tests=test_code,
                description=prob_data['instruction'],
                timeout_s=self.config['execution']['timeout_seconds'],
                mem_limit_mb=self.config['execution']['memory_limit_mb']
            )
            self.problems.append(problem)
            self.logger.info(f"Created fallback problem {problem.id}")
    

    
    def register_developer(self, developer):
        """Register a developer for the contest."""
        self.developers[developer.name] = developer
        self.bank.adjust_balance(developer.name, 0, "Initial registration")
        
        # Give developer a read-only account
        developer.account = self.bank.create_account(developer.name)
        
        self.state.participants.append(developer.name)
        
        self.logger.info(f"Registered developer: {developer.name}")
        self._emit_event("developer_registered", {"name": developer.name})
    
    def start_contest(self):
        """Start the contest."""
        if self.state.is_active:
            raise Exception("Contest is already active")
        
        if not self.problems:
            raise Exception("No problems loaded")
        
        self.state.is_active = True
        self.state.start_time = datetime.now()
        self.state.current_problem_index = 0
        
        self.logger.info("Contest started")
        self._emit_event("contest_started", {
            "start_time": self.state.start_time.isoformat(),
            "total_problems": len(self.problems)
        })
    
    def get_current_problem(self):
        """Get the current problem."""
        if not self.state.is_active or self.state.current_problem_index >= len(self.problems):
            return None
        
        return self.problems[self.state.current_problem_index]
    
    def submit_solution(self, developer_name, code):
        """Submit a solution for the current problem."""
        current_problem = self.get_current_problem()
        if not current_problem:
            self.logger.warning(f"No current problem when {developer_name} tried to submit")
            return False

        if developer_name not in self.developers:
            self.logger.warning(f"Developer {developer_name} not registered when trying to submit")
            return False

        if current_problem.id not in self.submissions:
            self.submissions[current_problem.id] = {}

        self.submissions[current_problem.id][developer_name] = code
        
        # Debug logging
        self.logger.info(f"✅ Saved submission from {developer_name} for problem {current_problem.id}")
        self.logger.info(f"📝 Submission length: {len(code)} characters")
        self.logger.info(f"🗂️ Total submissions for {current_problem.id}: {len(self.submissions[current_problem.id])}")
        self.logger.info(f"🗂️ All problem IDs with submissions: {list(self.submissions.keys())}")

        self.logger.info(f"Received submission from {developer_name} for problem {current_problem.id}")
        self._emit_event("submission_received", {
            "developer": developer_name,
            "problem_id": current_problem.id,
            "submission_time": datetime.now().isoformat()
        })

        return True
    
    def run_contest_round(self):
        """Run a single contest round."""
        current_problem = self.get_current_problem()
        if not current_problem:
            return
        
        # Set problem release time
        current_problem.released_at = datetime.now()
        
        self.logger.info(f"Starting round for problem {current_problem.id}")
        self._emit_event("round_started", {
            "problem_id": current_problem.id,
            "problem": current_problem.dict()
        })
        
        # STEP 1: Collect all submissions into a big list with names AND developer response times
        all_submissions = []
        
        # Ask each developer to generate a solution
        self.logger.info(f"Requesting solutions from {len(self.developers)} developers...")
        for dev_name, developer in self.developers.items():
            try:
                self.logger.info(f"Requesting solution from {dev_name}...")
                
                # Time just this line
                start_time = time.time()
                full_response = developer.query(current_problem)
                response_time = time.time() - start_time
                
                # Add to big list for PE evaluation with response timing
                all_submissions.append({
                    'name': dev_name,
                    'full_response': full_response,
                    'response_time': response_time
                })
                
                self.logger.info(f"Received solution from {dev_name} (took {response_time:.2f}s to respond)")
            except Exception as e:
                self.logger.error(f"Error getting solution from {dev_name}: {e}")
        
        # STEP 2-4: PE handles extraction, execution, rewards, and constitution updates
        evaluation_result = self.principle_evaluator.evaluate_submissions_simple(
            current_problem.tests,
            current_problem,
            all_submissions  # Pass the big list with response times
        )
        
        # Send feedback to developers
        for dev_name, dev in self.developers.items():
            if dev_name in evaluation_result.get('results', {}):
                result_data = evaluation_result['results'][dev_name]
                
                feedback = {
                    "timestamp": datetime.now().isoformat(),
                    "problem_id": current_problem.id,
                    "result": result_data.get('result'),
                    "reward": result_data.get('reward', 0),
                    "bank_balance": self.bank.query_balance(dev_name),
                    "constitution": self.constitution.query(),
                    "submission_code": result_data.get('extracted_code'),
                    "full_response": next((s['full_response'] for s in all_submissions if s['name'] == dev_name), ''),
                    "response_time": result_data.get('response_time'),  # Add developer response time
                    "reasoning_transcript": result_data.get('reasoning_transcript', 'No reasoning available')
                }
                
                dev.update(feedback)
        
        # STEP 3 & 4: PE decides whether to update constitution and extracts new one if needed
        constitution_updated = self.principle_evaluator.check_and_update_constitution(all_submissions, evaluation_result)
        
        self.logger.info(f"Completed round for problem {current_problem.id}")
        self._emit_event("round_completed", {
            "problem_id": current_problem.id,
            "evaluation": evaluation_result,
            "constitution_updated": constitution_updated,
            "leaderboard": self.bank.query_leaderboard()
        })
        
        # Move to next problem
        self.state.current_problem_index += 1
        
        if self.state.current_problem_index >= len(self.problems):
            self._end_contest()
    
    def _end_contest(self):
        """End the contest and declare winner."""
        self.state.is_active = False
        leaderboard = self.bank.query_leaderboard()
        winner = leaderboard[0] if leaderboard else None
        
        self.logger.info(f"Contest ended. Winner: {winner['name'] if winner else 'None'}")
        self._emit_event("contest_ended", {
            "winner": winner,
            "final_leaderboard": leaderboard
        })
    
    def run_full_contest(self):
        """Run the complete contest."""
        if not self.state.is_active:
            self.start_contest()
        
        while self.state.is_active and self.state.current_problem_index < len(self.problems):
            self.run_contest_round()
            
            # Brief pause between rounds
            if self.state.current_problem_index < len(self.problems):
                print(f"⏸️ Brief pause before next round...")
                import time
                time.sleep(2)
    
    def get_contest_status(self):
        """Get current contest status."""
        current_problem = self.get_current_problem()
        
        return {
            "is_active": self.state.is_active,
            "start_time": self.state.start_time.isoformat() if self.state.start_time else None,
            "current_problem_index": self.state.current_problem_index,
            "total_problems": len(self.problems),
            "current_problem": current_problem.dict() if current_problem else None,
            "participants": self.state.participants,
            "leaderboard": self.bank.query_leaderboard()
        }
    
    def get_logs(self, limit=100):
        """Get recent contest logs."""
        try:
            with open(self.config['logging']['file'], 'r') as f:
                lines = f.readlines()
                return lines[-limit:] if len(lines) > limit else lines
        except FileNotFoundError:
            return []

    def _extract_function_code(self, full_response, stub_code):
        """Extract executable function code from full developer response."""
        import re
        
        # Extract function name from stub code
        function_name_match = re.search(r'def\s+(\w+)\s*\(', stub_code)
        function_name = function_name_match.group(1) if function_name_match else 'solve'
        
        # First, try to find code in markdown blocks
        code_block_match = re.search(r'```python\s*(.*?)\s*```', full_response, re.DOTALL)
        if code_block_match:
            code_content = code_block_match.group(1).strip()
            if f"def {function_name}" in code_content:
                return code_content
        
        # Try to find the function definition in the response
        lines = full_response.split('\n')
        function_lines = []
        in_function = False
        
        for line in lines:
            if f"def {function_name}" in line:
                in_function = True
                function_lines.append(line)
            elif in_function:
                if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                    # End of function (new non-indented line that's not empty)
                    break
                function_lines.append(line)
        
        if function_lines:
            return '\n'.join(function_lines)
        
        # Last resort: look for any Python-like code (lines that look like code)
        code_lines = []
        for line in lines:
            line = line.strip()
            # Skip commentary lines and empty lines
            if (line and 
                not line.endswith(':') and  # Skip commentary headers
                not line.startswith('#') and  # Skip comments
                ('=' in line or 'return' in line or 'def ' in line or 'if ' in line or 'for ' in line)):
                code_lines.append(line)
        
        if code_lines:
            # Wrap the extracted code-like lines in a function
            return f"""def {function_name}():
    {chr(10).join('    ' + line for line in code_lines)}"""
        
        # Ultimate fallback - empty function
        return f"""def {function_name}():
    pass""" 