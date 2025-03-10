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
        # Convert interval from minutes to hours
        # First get the minutes, then convert to hours (integer division)
        self.interval_minutes = max(SCHEDULER_INTERVAL_MINUTES, 60)  # Minimum 60 minutes (1 hour)
        self.interval_hours = max(self.interval_minutes // 60, 1)  # Convert to hours, minimum 1 hour
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
                   f"interval={self.interval_hours} hours ({self.interval_minutes} minutes), "
                   f"days={','.join(self.days)}")
    
    def update_config(self):
        """Update configuration from environment variables"""
        self.enabled = os.getenv("SCHEDULER_ENABLED", "false").lower() == "true"
        self.start_hour = int(os.getenv("SCHEDULER_START_HOUR", "6"))
        self.end_hour = int(os.getenv("SCHEDULER_END_HOUR", "20"))
        
        # Handle the interval in hours
        # First get minutes from the env, then convert to hours
        raw_minutes = int(os.getenv("SCHEDULER_INTERVAL_MINUTES", "300"))
        self.interval_minutes = max(raw_minutes, 60)  # Minimum 60 minutes (1 hour)
        self.interval_hours = max(self.interval_minutes // 60, 1)  # Convert to hours, minimum 1 hour
        
        self.days = os.getenv("SCHEDULER_DAYS", "mon,tue,wed,thu,fri").lower().split(",")
        
        logger.info(f"Scheduler configuration updated: enabled={self.enabled}, "
                   f"hours={self.start_hour}-{self.end_hour}, "
                   f"interval={self.interval_hours} hours ({self.interval_minutes} minutes), "
                   f"days={','.join(self.days)}")
                   
        # Clear existing jobs and reschedule
        if self.is_running:
            self.stop()
            self.start()
    
    def run_process(self):
        """Run the combined process - the scheduler already manages when to run it"""
        now = datetime.datetime.now()
        logger.info(f"Scheduler running process at {now} (hour={now.hour}, minute={now.minute}, day={now.strftime('%a').lower()})")
        
        # Import the combined process function
        try:
            from app.combined_process import main as process_main
            asyncio.run(process_main())
            logger.info(f"Process completed successfully at {datetime.datetime.now()}")
        except Exception as e:
            logger.error(f"Error running process: {str(e)}")
    
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
        
        # Count the total jobs to be scheduled
        total_jobs = 0
        
        # Calculate fixed time points for the schedule - at specific hours
        # For example, if start_hour=7, end_hour=17, interval_hours=5,
        # we'll schedule jobs at 7:00, 12:00, and 17:00
        scheduled_hours = []
        for hour in range(self.start_hour, self.end_hour + 1, self.interval_hours):
            if hour <= self.end_hour:
                scheduled_hours.append(hour)
        
        # Log the actual hours that will be scheduled
        logger.info(f"Scheduling jobs at these hours: {scheduled_hours}")
        
        # Schedule jobs for each active day
        for day in self.days:
            if day in self.day_functions:
                # Schedule jobs at specific hours instead of at intervals
                for hour in scheduled_hours:
                    job_time = f"{hour:02d}:00"  # Always use 00 for minutes
                    # This will actually schedule the job
                    self.day_functions[day].at(job_time).do(self.run_process)
                    total_jobs += 1
                    
                    # Log all scheduled times since there will be fewer of them
                    logger.info(f"Scheduled job: {day} at {job_time}")
        
        # Start the scheduler thread
        self.is_running = True
        self.scheduler_thread = Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info(f"Scheduler started with {total_jobs} jobs scheduled at {len(scheduled_hours)} times per day, every {self.interval_hours} hours, on {', '.join(self.days)}")
        
        # Get and log the next scheduled run time to verify it's correct
        next_run = self.calculate_next_run()
        if next_run:
            logger.info(f"Next scheduled run: {next_run}")
            
        # Check if we're already in a time window when the app is starting
        # If so, run the process once immediately
        now = datetime.datetime.now()
        current_hour = now.hour
        current_minute = now.minute
        current_day = now.strftime("%a").lower()
        
        # Check if this is a time we would normally run (exact hour match)
        in_active_window = (
            current_hour in scheduled_hours and 
            current_day in self.days and 
            current_minute < 5  # Allow a 5-minute window after the hour
        )
        
        if in_active_window:
            logger.info(f"We're in an active window at {now}, running process immediately")
            # Start in a separate thread to not block
            Thread(target=self.run_process, daemon=True).start()
            
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
    
    def calculate_next_run(self):
        """Calculate the next run time based on the current schedule configuration"""
        now = datetime.datetime.now()
        current_day_name = now.strftime("%a").lower()
        current_hour = now.hour
        current_minute = now.minute
        
        # Calculate scheduled hours
        scheduled_hours = []
        for hour in range(self.start_hour, self.end_hour + 1, self.interval_hours):
            if hour <= self.end_hour:
                scheduled_hours.append(hour)
                
        # Return immediately if no hours are scheduled
        if not scheduled_hours:
            return None
        
        # Map day names to their position in the week (0 = Monday)
        day_positions = {
            'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 
            'fri': 4, 'sat': 5, 'sun': 6
        }
        
        # Get the position of the current day
        current_day_pos = day_positions.get(current_day_name, 0)
        
        # Find the next scheduled time
        # Try all days starting from today
        for day_offset in range(7):  # Check the next 7 days
            # Calculate the day we're checking
            check_day_pos = (current_day_pos + day_offset) % 7
            check_day_name = [d for d, p in day_positions.items() if p == check_day_pos][0]
            
            # If this day is not in our schedule, skip it
            if check_day_name not in self.days:
                continue
                
            # Calculate the date for this day
            check_date = now.date() + datetime.timedelta(days=day_offset)
            
            # If we're checking today, we need to find a time later than now
            if day_offset == 0:
                # Find the next hour on today's schedule
                for hour in scheduled_hours:
                    # Check if this hour is later than current time
                    if hour > current_hour or (hour == current_hour and current_minute < 5):
                        # This is our next run time today
                        next_run = datetime.datetime.combine(
                            check_date,
                            datetime.time(hour, 0)  # Always at top of the hour (XX:00)
                        )
                        return next_run
            else:
                # For future days, just return the first scheduled time
                next_run = datetime.datetime.combine(
                    check_date,
                    datetime.time(scheduled_hours[0], 0)  # First scheduled hour at 00 minutes
                )
                return next_run
                
        # If we get here, no scheduled time was found
        return None
        
    def status(self):
        """Get scheduler status"""
        # Use our own calculation for next run instead of relying on schedule.next_run()
        next_run = self.calculate_next_run() if self.is_running and self.enabled else None
        
        # Calculate scheduled hours
        scheduled_hours = []
        for hour in range(self.start_hour, self.end_hour + 1, self.interval_hours):
            if hour <= self.end_hour:
                scheduled_hours.append(hour)
        
        # Format scheduled hours for display
        scheduled_times = [f"{hour:02d}:00" for hour in scheduled_hours]
        
        return {
            "enabled": self.enabled,
            "running": self.is_running,
            "jobs_count": len(schedule.jobs),
            "active_hours": f"{self.start_hour:02d}:00 - {self.end_hour:02d}:00",
            "interval_minutes": self.interval_minutes,
            "interval_hours": self.interval_hours,
            "scheduled_times": scheduled_times,  # New field showing the exact scheduled times
            "active_days": self.days,
            "next_run": str(next_run) if next_run else None
        }

# Create a global instance of the scheduler service
scheduler_service = SchedulerService()