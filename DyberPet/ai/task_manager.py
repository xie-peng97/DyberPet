# coding:utf-8
"""
Task Manager - Database-backed task management system
Handles task creation, storage, and retrieval with SQLite persistence
"""

import os
import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from PySide6.QtCore import QObject, Signal

import DyberPet.settings as settings

class TaskManager(QObject):
    """
    Manages AI-created tasks with database persistence
    """
    
    task_created = Signal(dict)
    task_updated = Signal(dict)
    task_deleted = Signal(str)
    task_reminder_due = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_path = os.path.join(settings.CONFIGDIR, 'data', 'tasks.db')
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database and create tables"""
        try:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create tasks table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tasks (
                        id TEXT PRIMARY KEY,
                        content TEXT NOT NULL,
                        remind_time DATETIME,
                        created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                        modified_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'pending',
                        recurring_rule TEXT NULL,
                        source TEXT DEFAULT 'ai',
                        metadata TEXT NULL
                    )
                ''')
                
                # Create index for efficient queries
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_tasks_remind_time ON tasks(remind_time)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_tasks_created_time ON tasks(created_time)
                ''')
                
                conn.commit()
                
        except Exception as e:
            print(f"Database initialization error: {e}")
    
    def create_task(self, content: str, remind_time: Optional[datetime] = None, 
                   recurring_rule: Optional[str] = None, metadata: Optional[Dict] = None) -> str:
        """
        Create a new task
        
        Args:
            content: Task content
            remind_time: Optional reminder time
            recurring_rule: Optional recurring rule (future expansion)
            metadata: Optional metadata dictionary
            
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO tasks (id, content, remind_time, status, recurring_rule, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    task_id,
                    content,
                    remind_time.isoformat() if remind_time else None,
                    'pending',
                    recurring_rule,
                    json.dumps(metadata) if metadata else None
                ))
                
                conn.commit()
                
                # Emit signal
                task_data = {
                    'id': task_id,
                    'content': content,
                    'remind_time': remind_time,
                    'status': 'pending',
                    'recurring_rule': recurring_rule,
                    'metadata': metadata
                }
                self.task_created.emit(task_data)
                
                return task_id
                
        except Exception as e:
            print(f"Task creation error: {e}")
            return ""
    
    def get_tasks(self, status: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
        """
        Get tasks with optional filtering
        
        Args:
            status: Optional status filter ('pending', 'completed', 'expired')
            limit: Optional result limit
            
        Returns:
            List of task dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = 'SELECT * FROM tasks'
                params = []
                
                if status:
                    query += ' WHERE status = ?'
                    params.append(status)
                
                query += ' ORDER BY created_time DESC'
                
                if limit:
                    query += ' LIMIT ?'
                    params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                tasks = []
                for row in rows:
                    task = {
                        'id': row[0],
                        'content': row[1],
                        'remind_time': datetime.fromisoformat(row[2]) if row[2] else None,
                        'created_time': datetime.fromisoformat(row[3]) if row[3] else None,
                        'modified_time': datetime.fromisoformat(row[4]) if row[4] else None,
                        'status': row[5],
                        'recurring_rule': row[6],
                        'source': row[7],
                        'metadata': json.loads(row[8]) if row[8] else None
                    }
                    tasks.append(task)
                
                return tasks
                
        except Exception as e:
            print(f"Task retrieval error: {e}")
            return []
    
    def update_task(self, task_id: str, **kwargs) -> bool:
        """
        Update an existing task
        
        Args:
            task_id: Task ID
            **kwargs: Fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build update query
                update_fields = []
                params = []
                
                for field, value in kwargs.items():
                    if field in ['content', 'status', 'recurring_rule', 'source']:
                        update_fields.append(f'{field} = ?')
                        params.append(value)
                    elif field == 'remind_time' and isinstance(value, datetime):
                        update_fields.append('remind_time = ?')
                        params.append(value.isoformat())
                    elif field == 'metadata' and value is not None:
                        update_fields.append('metadata = ?')
                        params.append(json.dumps(value))
                
                if not update_fields:
                    return False
                
                # Always update modified_time
                update_fields.append('modified_time = CURRENT_TIMESTAMP')
                
                query = f'UPDATE tasks SET {", ".join(update_fields)} WHERE id = ?'
                params.append(task_id)
                
                cursor.execute(query, params)
                
                if cursor.rowcount > 0:
                    conn.commit()
                    
                    # Get updated task
                    updated_task = self.get_task_by_id(task_id)
                    if updated_task:
                        self.task_updated.emit(updated_task)
                    
                    return True
                else:
                    return False
                    
        except Exception as e:
            print(f"Task update error: {e}")
            return False
    
    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task
        
        Args:
            task_id: Task ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    self.task_deleted.emit(task_id)
                    return True
                else:
                    return False
                    
        except Exception as e:
            print(f"Task deletion error: {e}")
            return False
    
    def mark_completed(self, task_id: str) -> bool:
        """
        Mark a task as completed
        
        Args:
            task_id: Task ID
            
        Returns:
            True if successful, False otherwise
        """
        return self.update_task(task_id, status='completed')
    
    def get_task_by_id(self, task_id: str) -> Optional[Dict]:
        """
        Get a specific task by ID
        
        Args:
            task_id: Task ID
            
        Returns:
            Task dictionary or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
                row = cursor.fetchone()
                
                if row:
                    task = {
                        'id': row[0],
                        'content': row[1],
                        'remind_time': datetime.fromisoformat(row[2]) if row[2] else None,
                        'created_time': datetime.fromisoformat(row[3]) if row[3] else None,
                        'modified_time': datetime.fromisoformat(row[4]) if row[4] else None,
                        'status': row[5],
                        'recurring_rule': row[6],
                        'source': row[7],
                        'metadata': json.loads(row[8]) if row[8] else None
                    }
                    return task
                else:
                    return None
                    
        except Exception as e:
            print(f"Task retrieval by ID error: {e}")
            return None
    
    def get_pending_reminders(self) -> List[Dict]:
        """
        Get tasks that need reminders (past due or due soon)
        
        Returns:
            List of task dictionaries that need reminders
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                now = datetime.now()
                
                cursor.execute('''
                    SELECT * FROM tasks 
                    WHERE status = 'pending' 
                    AND remind_time IS NOT NULL 
                    AND remind_time <= ?
                    ORDER BY remind_time ASC
                ''', (now.isoformat(),))
                
                rows = cursor.fetchall()
                
                tasks = []
                for row in rows:
                    task = {
                        'id': row[0],
                        'content': row[1],
                        'remind_time': datetime.fromisoformat(row[2]) if row[2] else None,
                        'created_time': datetime.fromisoformat(row[3]) if row[3] else None,
                        'modified_time': datetime.fromisoformat(row[4]) if row[4] else None,
                        'status': row[5],
                        'recurring_rule': row[6],
                        'source': row[7],
                        'metadata': json.loads(row[8]) if row[8] else None
                    }
                    tasks.append(task)
                
                return tasks
                
        except Exception as e:
            print(f"Pending reminders retrieval error: {e}")
            return []
    
    def mark_expired_tasks(self) -> int:
        """
        Mark overdue tasks without reminders as expired
        
        Returns:
            Number of tasks marked as expired
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Mark tasks as expired if they have a reminder time in the past
                # and haven't been completed
                one_day_ago = datetime.now() - timedelta(days=1)
                
                cursor.execute('''
                    UPDATE tasks 
                    SET status = 'expired', modified_time = CURRENT_TIMESTAMP
                    WHERE status = 'pending' 
                    AND remind_time IS NOT NULL 
                    AND remind_time < ?
                ''', (one_day_ago.isoformat(),))
                
                expired_count = cursor.rowcount
                conn.commit()
                
                return expired_count
                
        except Exception as e:
            print(f"Mark expired tasks error: {e}")
            return 0
    
    def get_task_statistics(self) -> Dict:
        """
        Get task statistics
        
        Returns:
            Dictionary with task counts by status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT status, COUNT(*) as count
                    FROM tasks
                    GROUP BY status
                ''')
                
                rows = cursor.fetchall()
                
                stats = {'pending': 0, 'completed': 0, 'expired': 0}
                for row in rows:
                    stats[row[0]] = row[1]
                
                return stats
                
        except Exception as e:
            print(f"Task statistics error: {e}")
            return {'pending': 0, 'completed': 0, 'expired': 0}
    
    def cleanup_old_tasks(self, days_old: int = 30) -> int:
        """
        Clean up old completed/expired tasks
        
        Args:
            days_old: Remove tasks older than this many days
            
        Returns:
            Number of tasks removed
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cutoff_date = datetime.now() - timedelta(days=days_old)
                
                cursor.execute('''
                    DELETE FROM tasks 
                    WHERE status IN ('completed', 'expired') 
                    AND modified_time < ?
                ''', (cutoff_date.isoformat(),))
                
                removed_count = cursor.rowcount
                conn.commit()
                
                return removed_count
                
        except Exception as e:
            print(f"Task cleanup error: {e}")
            return 0