"""
Process Router

This module provides API endpoints for running the combined vacancy and resume matching process.
"""

import asyncio
import logging
import sys
import io
import importlib
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import time
import queue
import threading

# Get the combined_process_main function - using a safer approach
# Import a reference to the module first
from app import combined_process

# Create router
router = APIRouter()

# Create a logger for the API
logger = logging.getLogger(__name__)

# Create a queue to store log messages
log_queue = queue.Queue()

# Create a model for the response
class ProcessStatus(BaseModel):
    status: str
    message: str
    logs: List[str] = []

class ProcessOutput(BaseModel):
    process_id: str
    status: str
    logs: List[str] = []
    
# Store the process status and logs
process_status = {
    "status": "idle",
    "message": "No process has been started yet",
    "logs": [],
    "process_id": ""
}

# Custom log handler to capture logs
class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        log_entry = self.format(record)
        self.log_queue.put(log_entry)

# Set up the queue log handler
queue_handler = QueueHandler(log_queue)
queue_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
queue_handler.setFormatter(formatter)

# Function to capture stdout/stderr
class StreamCapture(io.StringIO):
    def __init__(self, queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = queue
        self.original_stdout = sys.stdout
    
    def write(self, s):
        if s.strip():
            self.queue.put(s.strip())
        return super().write(s)

# Function to run the process and capture output
async def run_process(process_id: str):
    global process_status
    
    # Initialize the process status
    process_status = {
        "status": "running",
        "message": "Process is running",
        "logs": [],
        "process_id": process_id
    }
    
    # Add the queue handler to the root logger
    logging.getLogger().addHandler(queue_handler)
    logging.getLogger('progress').addHandler(queue_handler)
    
    # Redirect stdout and stderr
    stdout_capture = StreamCapture(log_queue)
    stderr_capture = StreamCapture(log_queue)
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = stdout_capture
    sys.stderr = stderr_capture
    
    try:
        # Run the combined process
        logger.info(f"Starting process {process_id}")
        process_status["logs"].append(f"Starting process {process_id}")
        
        # Run the actual process
        await combined_process.main()
        
        process_status["status"] = "completed"
        process_status["message"] = "Process completed successfully"
        logger.info("Process completed successfully")
        process_status["logs"].append("Process completed successfully")
    except Exception as e:
        process_status["status"] = "failed"
        process_status["message"] = f"Process failed: {str(e)}"
        logger.error(f"Process failed: {str(e)}")
        process_status["logs"].append(f"Process failed: {str(e)}")
    finally:
        # Restore stdout and stderr
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        
        # Remove the queue handler
        logging.getLogger().removeHandler(queue_handler)
        logging.getLogger('progress').removeHandler(queue_handler)
        
        # Get any remaining logs from the queue
        while not log_queue.empty():
            try:
                log_message = log_queue.get_nowait()
                if log_message and log_message.strip():
                    process_status["logs"].append(log_message.strip())
            except queue.Empty:
                break

# Background log collector
def collect_logs():
    global process_status
    while process_status["status"] == "running":
        try:
            while not log_queue.empty():
                log_message = log_queue.get_nowait()
                if log_message and log_message.strip():
                    process_status["logs"].append(log_message.strip())
        except queue.Empty:
            pass
        time.sleep(0.5)

@router.post("/start", response_model=ProcessStatus)
async def start_process(background_tasks: BackgroundTasks):
    """
    Start the combined vacancy and resume matching process.
    Returns a process ID that can be used to check the status.
    """
    global process_status
    
    # Check if a process is already running
    if process_status["status"] == "running":
        return ProcessStatus(
            status="error",
            message="A process is already running",
            logs=[]
        )
    
    # Generate a process ID
    process_id = f"process_{int(time.time())}"
    
    # Start the process in the background
    background_tasks.add_task(run_process, process_id)
    
    # Start the log collector in a background thread
    collector_thread = threading.Thread(target=collect_logs)
    collector_thread.daemon = True
    collector_thread.start()
    
    return ProcessStatus(
        status="started",
        message=f"Process {process_id} started",
        logs=[]
    )

@router.get("/status", response_model=ProcessOutput)
async def get_process_status():
    """
    Get the status of the running or last run process.
    """
    global process_status
    
    return ProcessOutput(
        process_id=process_status["process_id"],
        status=process_status["status"],
        logs=process_status["logs"]
    )