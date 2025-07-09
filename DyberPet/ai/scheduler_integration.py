# coding:utf-8
"""
AI Scheduler Integration - Extends the existing scheduler with AI task reminders
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from PySide6.QtCore import QObject, Signal, QTimer
from apscheduler.triggers import date

import DyberPet.settings as settings
from DyberPet.ai.task_manager import TaskManager

class AISchedulerIntegration(QObject):
    """
    Integrates AI task reminders with the existing scheduler system
    """
    
    task_reminder_due = Signal(dict)
    bubble_reminder = Signal(str)
    
    def __init__(self, scheduler_worker, parent=None):
        super().__init__(parent)
        self.scheduler_worker = scheduler_worker
        self.task_manager = TaskManager(self)
        self.reminder_timer = QTimer(self)
        self.setup_integration()
    
    def setup_integration(self):
        """Setup the integration with existing scheduler"""
        # Connect to task manager signals
        self.task_manager.task_created.connect(self.on_task_created)
        self.task_manager.task_updated.connect(self.on_task_updated)
        self.task_manager.task_deleted.connect(self.on_task_deleted)
        
        # Setup reminder checking timer
        self.reminder_timer.timeout.connect(self.check_pending_reminders)
        self.reminder_timer.start(60000)  # Check every minute
        
        # Load existing tasks and schedule reminders
        self.schedule_existing_reminders()
    
    def schedule_existing_reminders(self):
        """Schedule reminders for existing tasks"""
        try:
            pending_tasks = self.task_manager.get_tasks(status='pending')
            
            for task in pending_tasks:
                if task.get('remind_time'):
                    self.schedule_task_reminder(task)
                    
        except Exception as e:
            print(f"Error scheduling existing reminders: {e}")
    
    def on_task_created(self, task_data: Dict):
        """Handle new task creation"""
        if task_data.get('remind_time'):
            self.schedule_task_reminder(task_data)
    
    def on_task_updated(self, task_data: Dict):
        """Handle task updates"""
        task_id = task_data['id']
        
        # Remove existing reminder
        self.cancel_task_reminder(task_id)
        
        # Schedule new reminder if needed
        if task_data.get('remind_time') and task_data.get('status') == 'pending':
            self.schedule_task_reminder(task_data)
    
    def on_task_deleted(self, task_id: str):
        """Handle task deletion"""
        self.cancel_task_reminder(task_id)
    
    def schedule_task_reminder(self, task_data: Dict):
        """Schedule a reminder for a task"""
        try:
            task_id = task_data['id']
            remind_time = task_data['remind_time']
            
            if not remind_time or not isinstance(remind_time, datetime):
                return
            
            # Don't schedule if time is in the past
            if remind_time <= datetime.now():
                return
            
            # Create job ID for the task reminder
            job_id = f"ai_task_reminder_{task_id}"
            
            # Schedule the reminder
            self.scheduler_worker.scheduler.add_job(
                self.trigger_task_reminder,
                date.DateTrigger(run_date=remind_time),
                args=[task_data],
                id=job_id,
                replace_existing=True
            )
            
            print(f"Scheduled reminder for task {task_id} at {remind_time}")
            
        except Exception as e:
            print(f"Error scheduling task reminder: {e}")
    
    def cancel_task_reminder(self, task_id: str):
        """Cancel a task reminder"""
        try:
            job_id = f"ai_task_reminder_{task_id}"
            self.scheduler_worker.scheduler.remove_job(job_id)
            print(f"Cancelled reminder for task {task_id}")
        except Exception as e:
            # Job might not exist, which is fine
            pass
    
    def trigger_task_reminder(self, task_data: Dict):
        """Trigger a task reminder"""
        try:
            task_id = task_data['id']
            task_content = task_data['content']
            
            # Check if task is still pending
            current_task = self.task_manager.get_task_by_id(task_id)
            if not current_task or current_task.get('status') != 'pending':
                return
            
            # Create reminder message
            reminder_message = f"⏰ 任务提醒\n{task_content}\n\n主人，该做这个任务了哦~ (´∀｀)"
            
            # Emit signals
            self.task_reminder_due.emit(task_data)
            self.bubble_reminder.emit(reminder_message)
            
            # Show bubble through scheduler worker
            if hasattr(self.scheduler_worker, 'sig_setup_bubble'):
                bubble_dict = {
                    'message': reminder_message,
                    'start_audio': 'system',
                    'icon': 'system'
                }
                self.scheduler_worker.sig_setup_bubble.emit(bubble_dict)
            
            print(f"Triggered reminder for task: {task_content}")
            
        except Exception as e:
            print(f"Error triggering task reminder: {e}")
    
    def check_pending_reminders(self):
        """Check for pending reminders that might have been missed"""
        try:
            pending_reminders = self.task_manager.get_pending_reminders()
            
            for task in pending_reminders:
                remind_time = task.get('remind_time')
                if remind_time and remind_time <= datetime.now():
                    # This reminder is due
                    self.trigger_task_reminder(task)
                    
                    # Update task to mark as reminded (optional)
                    # You could add a 'reminded' flag to avoid duplicate reminders
                    
        except Exception as e:
            print(f"Error checking pending reminders: {e}")
    
    def add_todo_reminder(self, task_content: str, reminder_time: datetime) -> Dict:
        """
        Add a todo reminder (compatible with existing scheduler interface)
        
        Args:
            task_content: Content of the task
            reminder_time: When to remind
            
        Returns:
            Dictionary with result status
        """
        try:
            task_id = self.task_manager.create_task(task_content, reminder_time)
            
            if task_id:
                return {
                    'status': 'success',
                    'task_id': task_id,
                    'message': f'任务已创建：{task_content}'
                }
            else:
                return {
                    'status': 'error',
                    'message': '创建任务失败'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'创建任务出错：{str(e)}'
            }
    
    def get_active_reminders(self) -> List[Dict]:
        """Get list of active reminders"""
        try:
            return self.task_manager.get_tasks(status='pending')
        except Exception as e:
            print(f"Error getting active reminders: {e}")
            return []
    
    def cancel_reminder(self, task_id: str) -> bool:
        """Cancel a specific reminder"""
        try:
            success = self.task_manager.delete_task(task_id)
            if success:
                self.cancel_task_reminder(task_id)
            return success
        except Exception as e:
            print(f"Error cancelling reminder: {e}")
            return False
    
    def update_reminder(self, task_id: str, new_time: datetime) -> bool:
        """Update a reminder time"""
        try:
            return self.task_manager.update_task(task_id, remind_time=new_time)
        except Exception as e:
            print(f"Error updating reminder: {e}")
            return False
    
    def cleanup_expired_reminders(self):
        """Clean up expired reminders"""
        try:
            expired_count = self.task_manager.mark_expired_tasks()
            print(f"Marked {expired_count} tasks as expired")
        except Exception as e:
            print(f"Error cleaning up expired reminders: {e}")
    
    def get_reminder_statistics(self) -> Dict:
        """Get statistics about reminders"""
        try:
            return self.task_manager.get_task_statistics()
        except Exception as e:
            print(f"Error getting reminder statistics: {e}")
            return {'pending': 0, 'completed': 0, 'expired': 0}