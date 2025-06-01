import subprocess
import tempfile
import os
import time
import psutil
import signal
from models import SubmissionResult
import re


class CodeSandbox:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def execute_code(self, code, tests, timeout_s=1, mem_limit_mb=256):
        """Execute code with tests in a sandboxed environment."""
        try:
            # Create temporary files
            code_file = os.path.join(self.temp_dir, "solution.py")
            test_file = os.path.join(self.temp_dir, "test_solution.py")
            
            # Write code to file
            with open(code_file, 'w') as f:
                f.write(code)
            
            # Write tests to file (modify to import the solution)
            test_content = self._prepare_test_content(tests, code)
            with open(test_file, 'w') as f:
                f.write(test_content)
            
            # Execute tests with resource limits
            start_time = time.time()
            result = self._run_with_limits(test_file, timeout_s, mem_limit_mb)
            execution_time = time.time() - start_time
            
            # Parse test results
            tests_passed, total_tests = self._parse_test_output(result['output'])
            
            return SubmissionResult(
                success=result['returncode'] == 0,
                output=result['output'],
                error=result['error'],
                execution_time=execution_time,
                memory_used=result['memory_used'],
                tests_passed=tests_passed,
                total_tests=total_tests
            )
            
        except Exception as e:
            return SubmissionResult(
                success=False,
                output="",
                error=str(e),
                execution_time=0.0,
                memory_used=0,
                tests_passed=0,
                total_tests=1
            )
        finally:
            self._cleanup()
    
    def _prepare_test_content(self, tests, code):
        """Prepare test content by combining code and tests."""
        # Extract function definitions from code
        combined_content = f"""
# Solution code
{code}

# Test code
{tests}
"""
        return combined_content
    
    def _run_with_limits(self, test_file, timeout_s, mem_limit_mb):
        """Run the test file with time and memory limits."""
        cmd = ["python", test_file]
        
        try:
            # Start process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.temp_dir,
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Monitor memory usage
            max_memory = 0
            start_time = time.time()
            
            while process.poll() is None:
                current_time = time.time()
                
                # Check timeout
                if current_time - start_time > timeout_s:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    process.wait()
                    return {
                        'returncode': -1,
                        'output': '',
                        'error': f'Timeout after {timeout_s} seconds',
                        'memory_used': max_memory
                    }
                
                # Check memory usage
                try:
                    proc = psutil.Process(process.pid)
                    memory_mb = proc.memory_info().rss / 1024 / 1024
                    max_memory = max(max_memory, memory_mb)
                    
                    if memory_mb > mem_limit_mb:
                        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                        process.wait()
                        return {
                            'returncode': -1,
                            'output': '',
                            'error': f'Memory limit exceeded: {memory_mb:.1f}MB > {mem_limit_mb}MB',
                            'memory_used': max_memory
                        }
                except psutil.NoSuchProcess:
                    break
                
                time.sleep(0.01)  # Small delay to prevent busy waiting
            
            # Get output
            stdout, stderr = process.communicate()
            
            return {
                'returncode': process.returncode,
                'output': stdout,
                'error': stderr,
                'memory_used': max_memory
            }
            
        except Exception as e:
            return {
                'returncode': -1,
                'output': '',
                'error': str(e),
                'memory_used': 0
            }
    
    def _parse_test_output(self, output):
        """Parse pytest output to extract test results."""
        # Look for pytest summary line
        patterns = [
            r'(\d+) passed',
            r'(\d+) failed',
            r'(\d+) error',
        ]
        
        passed = 0
        failed = 0
        errors = 0
        
        for line in output.split('\n'):
            if 'passed' in line and 'failed' in line:
                # Parse line like "2 failed, 1 passed in 0.03s"
                passed_match = re.search(r'(\d+) passed', line)
                failed_match = re.search(r'(\d+) failed', line)
                error_match = re.search(r'(\d+) error', line)
                
                if passed_match:
                    passed = int(passed_match.group(1))
                if failed_match:
                    failed = int(failed_match.group(1))
                if error_match:
                    errors = int(error_match.group(1))
                break
            elif 'passed in' in line and 'failed' not in line:
                # Parse line like "3 passed in 0.02s"
                passed_match = re.search(r'(\d+) passed', line)
                if passed_match:
                    passed = int(passed_match.group(1))
                break
        
        total_tests = passed + failed + errors
        if total_tests == 0:
            # If we can't parse, assume 1 test that failed
            total_tests = 1
            passed = 0
        
        return passed, total_tests
    
    def _cleanup(self):
        """Clean up temporary files."""
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except:
            pass


class DockerSandbox(CodeSandbox):
    """Alternative Docker-based sandbox (requires Docker)."""
    
    def _run_with_limits(self, test_file: str, timeout_s: int, mem_limit_mb: int) -> dict:
        """Run using Docker for better isolation."""
        try:
            import docker
            client = docker.from_env()
            
            # Create container with limits
            container = client.containers.run(
                "python:3.11-slim",
                f"python {os.path.basename(test_file)}",
                volumes={self.temp_dir: {'bind': '/app', 'mode': 'rw'}},
                working_dir='/app',
                mem_limit=f"{mem_limit_mb}m",
                detach=True,
                remove=True
            )
            
            # Wait for completion with timeout
            try:
                result = container.wait(timeout=timeout_s)
                logs = container.logs().decode('utf-8')
                
                return {
                    'returncode': result['StatusCode'],
                    'output': logs,
                    'error': '',
                    'memory_used': 0  # Docker stats would need separate call
                }
            except:
                container.kill()
                return {
                    'returncode': -1,
                    'output': '',
                    'error': f'Timeout after {timeout_s} seconds',
                    'memory_used': 0
                }
                
        except ImportError:
            # Fall back to regular sandbox if Docker not available
            return super()._run_with_limits(test_file, timeout_s, mem_limit_mb)
        except Exception as e:
            return {
                'returncode': -1,
                'output': '',
                'error': str(e),
                'memory_used': 0
            } 