"""
Task data models.

This module defines the models for tracking tasks, issues and feature requests
for the ResumeAI application.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime
import uuid


class TaskStatus(str, Enum):
    """Status of a task."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority(str, Enum):
    """Priority of a task."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskType(str, Enum):
    """Type of a task."""
    BUG = "bug"
    FEATURE = "feature"
    IMPROVEMENT = "improvement"
    TASK = "task"


class TaskCreate(BaseModel):
    """Model for creating a new task."""
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=3)
    type: TaskType = Field(default=TaskType.TASK)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    status: TaskStatus = Field(default=TaskStatus.TODO)
    due_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    """Model for updating an existing task."""
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=3)
    type: Optional[TaskType] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[datetime] = None


class Task(BaseModel):
    """Full task model with all fields."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    type: TaskType
    priority: TaskPriority
    status: TaskStatus
    due_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class TaskList(BaseModel):
    """Model for returning a list of tasks."""
    items: List[Task]
    total: int