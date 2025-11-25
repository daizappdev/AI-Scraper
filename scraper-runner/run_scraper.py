#!/usr/bin/env python3
"""
Scraper Runner - Executes generated scraping scripts in isolated containers
"""

import os
import sys
import json
import time
import subprocess
import tempfile
import shutil
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ScraperRunner:
    def __init__(self):
        self.scripts_dir = "/app/scripts"
        self.outputs_dir = "/app/outputs"
        self.temp_dir = "/tmp/scraper_exec"
        
        # Ensure directories exist
        os.makedirs(self.scripts_dir, exist_ok=True)
        os.makedirs(self.outputs_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def run_scraper(self, script_path: str, execution_id: str, output_format: str = "json") -> dict:
        """
        Execute a scraping script and return the results
        """
        try:
            logger.info(f"Starting execution {execution_id} for script {script_path}")
            
            # Create execution directory
            exec_dir = os.path.join(self.temp_dir, execution_id)
            os.makedirs(exec_dir, exist_ok=True)
            
            # Copy script to execution directory
            script_name = f"scraper_{execution_id}.py"
            script_dest = os.path.join(exec_dir, script_name)
            shutil.copy2(script_path, script_dest)
            
            # Prepare output file
            output_file = os.path.join(self.outputs_dir, f"output_{execution_id}.{output_format}")
            
            # Set environment variables
            env = os.environ.copy()
            env['OUTPUT_FILE'] = output_file
            
            # Execute script with timeout
            start_time = time.time()
            
            result = subprocess.run(
                [sys.executable, script_dest],
                cwd=exec_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            execution_time = int(time.time() - start_time)
            
            if result.returncode == 0:
                logger.info(f"Execution {execution_id} completed successfully")
                return {
                    "status": "completed",
                    "execution_time": execution_time,
                    "output_file": output_file,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            else:
                logger.error(f"Execution {execution_id} failed: {result.stderr}")
                return {
                    "status": "failed",
                    "execution_time": execution_time,
                    "error": result.stderr,
                    "stdout": result.stdout
                }
                
        except subprocess.TimeoutExpired:
            logger.error(f"Execution {execution_id} timed out")
            return {
                "status": "timeout",
                "execution_time": 300,
                "error": "Script execution timed out"
            }
        except Exception as e:
            logger.error(f"Execution {execution_id} error: {e}")
            return {
                "status": "failed",
                "execution_time": 0,
                "error": str(e)
            }
        finally:
            # Cleanup
            try:
                if os.path.exists(exec_dir):
                    shutil.rmtree(exec_dir)
            except Exception as e:
                logger.warning(f"Failed to cleanup execution directory: {e}")
    
    def monitor_queue(self):
        """
        Monitor for new execution requests
        In a real implementation, this would listen to a message queue or database
        """
        logger.info("Starting scraper runner monitor")
        
        while True:
            try:
                # Check for new execution requests
                # This is a placeholder - implement actual queue monitoring
                time.sleep(10)
                
            except KeyboardInterrupt:
                logger.info("Shutting down scraper runner")
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(5)
    
    def process_execution_request(self, execution_data: dict):
        """
        Process an execution request from the queue
        """
        execution_id = execution_data.get("execution_id")
        script_content = execution_data.get("script_content")
        output_format = execution_data.get("output_format", "json")
        
        if not execution_id or not script_content:
            logger.error("Missing execution_id or script_content")
            return
        
        # Write script to temporary file
        script_path = os.path.join(self.scripts_dir, f"temp_{execution_id}.py")
        try:
            with open(script_path, 'w') as f:
                f.write(script_content)
            
            # Execute the script
            result = self.run_scraper(script_path, execution_id, output_format)
            
            # TODO: Update execution record in database
            # This would involve making API calls to the backend
            
            logger.info(f"Execution {execution_id} result: {result['status']}")
            
        except Exception as e:
            logger.error(f"Failed to process execution {execution_id}: {e}")
        finally:
            # Cleanup temporary script file
            if os.path.exists(script_path):
                os.remove(script_path)

def main():
    runner = ScraperRunner()
    
    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        runner.monitor_queue()
    else:
        # Single execution mode
        logger.info("Scraper Runner started")
        print("AI-Scraper Runner is running...")
        
        # Start monitoring for execution requests
        runner.monitor_queue()

if __name__ == "__main__":
    main()