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

# Scheduler configuration
SCHEDULER_ENABLED = os.getenv("SCHEDULER_ENABLED", "false").lower() == "true"
SCHEDULER_START_HOUR = int(os.getenv("SCHEDULER_START_HOUR", "6"))
SCHEDULER_END_HOUR = int(os.getenv("SCHEDULER_END_HOUR", "20"))
SCHEDULER_INTERVAL_MINUTES = int(os.getenv("SCHEDULER_INTERVAL_MINUTES", "60"))
SCHEDULER_DAYS = os.getenv("SCHEDULER_DAYS", "mon,tue,wed,thu,fri").lower().split(",")

class SchedulerService:
    """Service for scheduling the combined process"""
    
    def __init__(self):
        """Initialize the scheduler service"""
        self.enabled = SCHEDULER_ENABLED
        self.start_hour = SCHEDULER_START_HOUR
        self.end_hour = SCHEDULER_END_HOUR
        self.interval_minutes = max(SCHEDULER_INTERVAL_MINUTES, 15)  # Minimum 15 minutes
        self.days = SCHEDULER_DAYS
        self.is_running = False
        self.scheduler_thread = None
        
        # Convert day names to schedule day functions
        self.day_functions = {
            'mon': schedule.every().monday,
            'tue': schedule.every().tuesday,
            'wed': schedule.every().wednesday,
            'thu': schedule.every().thursday,
            'fri': schedule.every().friday,
            'sat': schedule.every().saturday,
            'sun': schedule.every().sunday
        }
        
        logger.info(f"Scheduler initialized with settings: enabled={self.enabled}, "
                   f"hours={self.start_hour}-{self.end_hour}, "
                   f"interval={self.interval_minutes} minutes, "
                   f"days={','.join(self.days)}")
    
    def update_config(self):
        """Update configuration from environment variables"""
        self.enabled = os.getenv("SCHEDULER_ENABLED", "false").lower() == "true"
        self.start_hour = int(os.getenv("SCHEDULER_START_HOUR", "6"))
        self.end_hour = int(os.getenv("SCHEDULER_END_HOUR", "20"))
        self.interval_minutes = max(int(os.getenv("SCHEDULER_INTERVAL_MINUTES", "60")), 15)
        self.days = os.getenv("SCHEDULER_DAYS", "mon,tue,wed,thu,fri").lower().split(",")
        
        logger.info(f"Scheduler configuration updated: enabled={self.enabled}, "
                   f"hours={self.start_hour}-{self.end_hour}, "
                   f"interval={self.interval_minutes} minutes, "
                   f"days={','.join(self.days)}")
                   
        # Clear existing jobs and reschedule
        if self.is_running:
            self.stop()
            self.start()
    
    def run_process(self):
        """Run the combined process if within active hours and days"""
        now = datetime.datetime.now()
        current_hour = now.hour
        current_day = now.strftime("%a").lower()
        
        # Check if we're in the active time window
        if current_hour >= self.start_hour and current_hour < self.end_hour and current_day in self.days:
            logger.info(f"Scheduler running process at {now}")
            
            # Import the combined process function
            try:
                from app.combined_process import main as process_main
                asyncio.run(process_main())
                logger.info(f"Process completed successfully at {datetime.datetime.now()}")
            except Exception as e:
                logger.error(f"Error running process: {str(e)}")
        else:
            logger.info(f"Scheduler skipped run at {now} (outside active window)")
    
    def _run_scheduler(self):
        """Run the scheduler loop in a separate thread"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(1)
    
    def start(self):
        """Start the scheduler"""
        if not self.enabled:
            logger.info("Scheduler is disabled, not starting")
            return False
            
        if self.is_running:
            logger.info("Scheduler is already running")
            return True
            
        # Clear any existing jobs
        schedule.clear()
        
        # Schedule jobs for each active day
        for day in self.days:
            if day in self.day_functions:
                # Use the day function to schedule a job every X minutes during active hours
                for hour in range(self.start_hour, self.end_hour):
                    for minute in range(0, 60, self.interval_minutes):
                        job_time = f"{hour:02d}:{minute:02d}"
                        self.day_functions[day].at(job_time).do(self.run_process)
                        logger.info(f"Scheduled job for {day} at {job_time}")
        
        # Start the scheduler thread
        self.is_running = True
        self.scheduler_thread = Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info(f"Scheduler started with {len(schedule.jobs)} jobs")
        return True
    
    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            logger.info("Scheduler is not running")
            return
            
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
            self.scheduler_thread = None
            
        # Clear all scheduled jobs
        schedule.clear()
        logger.info("Scheduler stopped")
    
    def status(self):
        """Get scheduler status"""
        return {
            "enabled": self.enabled,
            "running": self.is_running,
            "jobs_count": len(schedule.jobs),
            "active_hours": f"{self.start_hour:02d}:00 - {self.end_hour:02d}:00",
            "interval_minutes": self.interval_minutes,
            "active_days": self.days,
            "next_run": str(schedule.next_run()) if schedule.next_run() else None
        }

# Create a global instance of the scheduler service
scheduler_service = SchedulerService()