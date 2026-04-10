import os
import tempfile
import asyncio
import time
from typing import Dict, Any, Tuple
import traceback

class ScriptRunnerService:
    """Service to execute generated test scripts"""
    
    @staticmethod
    async def execute_script(script_content: str, framework: str) -> Dict[str, Any]:
        """Execute a test script in a sandboxed/temporary environment"""
        
        # Create a temporary directory to run the test
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path, cmd = ScriptRunnerService._prepare_execution(
                temp_dir, script_content, framework
            )
            
            if not cmd:
                return {
                    "success": False,
                    "output": f"Unsupported framework: {framework}",
                    "execution_time": 0.0,
                    "error_message": "Unsupported framework"
                }
                
            start_time = time.time()
            
            try:
                # Run the command as a subprocess
                process = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=temp_dir
                )
                
                # Wait for completion with timeout
                try:
                    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)
                except asyncio.TimeoutError:
                    process.kill()
                    stdout, stderr = await process.communicate()
                    return {
                        "success": False,
                        "output": stdout.decode('utf-8', errors='replace') + "\n" + stderr.decode('utf-8', errors='replace'),
                        "execution_time": 30.0,
                        "error_message": "Execution timed out after 30 seconds"
                    }
                
                execution_time = time.time() - start_time
                
                # Process results
                output_str = stdout.decode('utf-8', errors='replace')
                error_str = stderr.decode('utf-8', errors='replace')
                full_output = f"{output_str}\n{error_str}".strip()
                
                success = process.returncode == 0
                
                return {
                    "success": success,
                    "output": full_output or "No output generated",
                    "execution_time": round(execution_time, 2),
                    "error_message": error_str if not success else None
                }
                
            except Exception as e:
                execution_time = time.time() - start_time
                return {
                    "success": False,
                    "output": traceback.format_exc(),
                    "execution_time": round(execution_time, 2),
                    "error_message": str(e)
                }

    @staticmethod
    def _prepare_execution(temp_dir: str, script_content: str, framework: str) -> Tuple[str, str]:
        """Prepare file and command based on framework"""
        if framework == "pytest":
            file_path = os.path.join(temp_dir, "test_case.py")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(script_content)
            cmd = f"python -m pytest {file_path} -v --tb=short"
            return file_path, cmd
            
        elif framework == "jest" or framework == "cypress":
            file_path = os.path.join(temp_dir, "test_case.test.js")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(script_content)
            cmd = f"node {file_path}" # Fallback for pure node execution since jest might not be installed globally
            return file_path, cmd
            
        elif framework.startswith("playwright"):
            ext = ".ts" if framework == "playwright-ts" else ".py"
            file_path = os.path.join(temp_dir, f"test_case{ext}")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(script_content)
                
            if ext == ".ts":
                # For TS we might need ts-node or just npx, assuming node execution context
                cmd = f"npx ts-node {file_path}"
            else:
                cmd = f"python {file_path}"
                
            return file_path, cmd
            
        return "", ""
