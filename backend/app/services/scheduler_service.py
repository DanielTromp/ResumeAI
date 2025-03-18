#!/usr/bin/env python3
"""
Scheduler Service for ResumeAI

This service provides a scheduler that runs the combined process at scheduled times.
It reads configuration from environment variables and schedules the process to run
periodically based on that configuration.

Author: Daniel Tromp
Email: drpgmtromp@gmail.com
Version: 0.1.0
Created: 2025-03-06
License: MIT
"""

import os
import asyncio
import logging
import time
import datetime
from threading import Thread
import schedule
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Legacy Scheduler configuration - no longer used (replaced by cron)
# These variables are kept for backward compatibility
SCHEDULER_ENABLED = False  # Always disabled - cron is now used instead
SCHEDULER_START_HOUR = 0
SCHEDULER_END_HOUR = 0
SCHEDULER_INTERVAL_MINUTES = 0
SCHEDULER_DAYS = []

class SchedulerService:
    """
    Legacy scheduler service - no longer used.
    This service has been replaced by system cron.
    Maintained for backward compatibility only.
    """
    
    def __init__(self):
        """Initialize the stub scheduler service"""
        self.enabled = False  # Always disabled - cron is now used instead
        self.start_hour = 0
        self.end_hour = 0
        self.interval_minutes = 0
        self.interval_hours = 0
        self.days = []
        self.is_running = False
        self.scheduler_thread = None
        self.day_functions = {}
        
        logger.info("Scheduler service is disabled. Use system cron instead.")
    
    def update_config(self):
        """Update configuration - stub method (scheduler has been replaced by cron)"""
        # All settings are fixed and ignored - scheduler is always disabled
        logger.info("Scheduler configuration cannot be updated - use system cron instead")
        return False
    
    def run_process(self):
        """Run process - stub method (scheduler has been replaced by cron)"""
        logger.warning("The scheduler has been replaced by system cron. This method is no longer functional.")
        logger.info("To run the process manually, use the API endpoint /api/process/start")
        return False
    
    def _run_scheduler(self):
        """Run scheduler - stub method (scheduler has been replaced by cron)"""
        logger.warning("The scheduler has been replaced by system cron. This method is no longer functional.")
        return False
    
    def start(self):
        """Start scheduler - stub method (scheduler has been replaced by cron)"""
        logger.warning("The scheduler has been replaced by system cron. This method is no longer functional.")
        logger.info("To schedule processing, configure a cron job to call the API endpoint")
        return False
    
    def stop(self):
        """Stop scheduler - stub method (scheduler has been replaced by cron)"""
        logger.warning("The scheduler has been replaced by system cron. This method is no longer functional.")
        logger.info("To manage scheduling, use 'crontab -e' to edit system cron jobs")
        return False
    
    def calculate_next_run(self):
        """Next run calculator - stub method (scheduler has been replaced by cron)"""
        logger.warning("The scheduler has been replaced by system cron. This method is no longer functional.")
        logger.info("To see scheduled jobs, use 'crontab -l' to view system cron jobs")
        return None
        
    def status(self):
        """Get scheduler status - stub method (scheduler has been replaced by cron)"""
        logger.warning("The scheduler has been replaced by system cron.")
        
        # Return minimal status object with default values
        return {
            "enabled": False,
            "running": False,
            "jobs_count": 0,
            "active_hours": "N/A",
            "interval_minutes": 0,
            "interval_hours": 0,
            "scheduled_times": [],
            "active_days": [],
            "next_run": None,
            "message": "Scheduler has been replaced by system cron. Use 'crontab -l' to view current schedule."
        }

# Create a global instance of the scheduler service
scheduler_service = SchedulerService()