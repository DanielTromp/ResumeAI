"""
Tasks API Router

This module provides API endpoints for managing tasks (bugs, features, improvements).
"""

from fastapi import APIRouter, HTTPException, Query, Path as FastAPIPath, Depends
from typing import List, Optional, Dict, Any
import logging
import os
import json
from datetime import datetime
import uuid

from app.models.task import Task, TaskCreate, TaskUpdate, TaskList, TaskStatus, TaskPriority, TaskType

# Set up logging
logger = logging.getLogger(__name__)

# Define tasks storage path - using a JSON file for simplicity
TASKS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "tasks.json")

# Create router
router = APIRouter()

def ensure_data_dir():
    """Ensure the data directory exists."""
    data_dir = os.path.dirname(TASKS_FILE)
    os.makedirs(data_dir, exist_ok=True)

def read_tasks():
    """Read tasks from JSON file."""
    ensure_data_dir()
    if not os.path.exists(TASKS_FILE):
        return []
    
    try:
        with open(TASKS_FILE, 'r') as f:
            tasks_data = json.load(f)
            
        # Convert JSON data to Task objects
        tasks = []
        for task_data in tasks_data:
            # Handle datetime fields
            if 'created_at' in task_data:
                task_data['created_at'] = datetime.fromisoformat(task_data['created_at'])
            if 'updated_at' in task_data:
                task_data['updated_at'] = datetime.fromisoformat(task_data['updated_at'])
            if 'due_date' in task_data and task_data['due_date']:
                task_data['due_date'] = datetime.fromisoformat(task_data['due_date'])
                
            tasks.append(Task(**task_data))
        return tasks
    except Exception as e:
        logger.error(f"Error reading tasks: {str(e)}")
        return []

def write_tasks(tasks: List[Task]):
    """Write tasks to JSON file."""
    ensure_data_dir()
    try:
        # Convert Task objects to dictionaries
        tasks_data = []
        for task in tasks:
            task_dict = task.dict()
            # Convert datetime objects to ISO format strings
            task_dict['created_at'] = task_dict['created_at'].isoformat()
            task_dict['updated_at'] = task_dict['updated_at'].isoformat()
            if task_dict['due_date']:
                task_dict['due_date'] = task_dict['due_date'].isoformat()
            tasks_data.append(task_dict)
            
        # Write to file
        with open(TASKS_FILE, 'w') as f:
            json.dump(tasks_data, f, indent=2)
    except Exception as e:
        logger.error(f"Error writing tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error writing tasks: {str(e)}")

@router.get("/", response_model=TaskList)
@router.get("", response_model=TaskList)  # Add route without trailing slash
async def get_tasks(
    skip: int = Query(0, description="Number of items to skip"),
    limit: int = Query(100, description="Number of items to return"),
    search: str = Query(None, description="Search term for filtering tasks"),
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    type: Optional[TaskType] = Query(None, description="Filter by type"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by priority")
):
    """
    Get a list of tasks with filtering and pagination.
    """
    try:
        # Read tasks from file
        all_tasks = read_tasks()
        
        # Apply filters
        filtered_tasks = all_tasks
        
        if search:
            search_lower = search.lower()
            filtered_tasks = [t for t in filtered_tasks 
                             if search_lower in t.title.lower() 
                             or search_lower in t.description.lower()]
        
        if status:
            filtered_tasks = [t for t in filtered_tasks if t.status == status]
            
        if type:
            filtered_tasks = [t for t in filtered_tasks if t.type == type]
            
        if priority:
            filtered_tasks = [t for t in filtered_tasks if t.priority == priority]
        
        # Sort by priority (high to low) and then created date (newest first)
        priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3
        }
        
        filtered_tasks.sort(key=lambda t: (
            priority_order.get(t.priority, 999), 
            -t.created_at.timestamp()
        ))
        
        # Apply pagination
        total = len(filtered_tasks)
        paginated_tasks = filtered_tasks[skip:skip+limit]
        
        return TaskList(items=paginated_tasks, total=total)
    
    except Exception as e:
        logger.error(f"Error getting tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting tasks: {str(e)}")

@router.post("/", response_model=Task, status_code=201)
async def create_task(task: TaskCreate):
    """
    Create a new task.
    """
    try:
        # Read existing tasks
        tasks = read_tasks()
        
        # Create new task with metadata
        new_task = Task(
            id=str(uuid.uuid4()),
            title=task.title,
            description=task.description,
            type=task.type,
            priority=task.priority,
            status=task.status,
            due_date=task.due_date,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Add to list and save
        tasks.append(new_task)
        write_tasks(tasks)
        
        return new_task
    
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating task: {str(e)}")

@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: str = FastAPIPath(..., description="The ID of the task to get")):
    """
    Get a single task by ID.
    """
    try:
        tasks = read_tasks()
        
        # Find task by ID
        for task in tasks:
            if task.id == task_id:
                return task
                
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting task: {str(e)}")

@router.put("/{task_id}", response_model=Task)
async def update_task(
    task_id: str = FastAPIPath(..., description="The ID of the task to update"),
    task_update: TaskUpdate = None
):
    """
    Update an existing task.
    """
    try:
        tasks = read_tasks()
        
        # Find task by ID
        task_index = None
        for i, task in enumerate(tasks):
            if task.id == task_id:
                task_index = i
                break
                
        if task_index is None:
            raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
        
        # Update task fields
        existing_task = tasks[task_index]
        update_data = task_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(existing_task, field, value)
            
        # Set updated timestamp
        existing_task.updated_at = datetime.now()
        
        # Save changes
        write_tasks(tasks)
        
        return existing_task
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating task: {str(e)}")

@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: str = FastAPIPath(..., description="The ID of the task to delete")):
    """
    Delete a task.
    """
    try:
        tasks = read_tasks()
        
        # Find task by ID
        task_index = None
        for i, task in enumerate(tasks):
            if task.id == task_id:
                task_index = i
                break
                
        if task_index is None:
            raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
        
        # Remove task
        tasks.pop(task_index)
        
        # Save changes
        write_tasks(tasks)
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting task: {str(e)}")