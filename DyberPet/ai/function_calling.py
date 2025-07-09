# coding:utf-8
"""
Function Calling Processor
Handles natural language parsing for task creation and management
"""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from dateutil import parser
from dateutil.relativedelta import relativedelta

class FunctionCallingProcessor:
    """
    Processes natural language commands for task creation and management
    """
    
    def __init__(self):
        self.task_function_schema = {
            "name": "set_todo_reminder",
            "description": "Set a todo task with optional reminder time",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_content": {
                        "type": "string",
                        "description": "The content of the task to be completed"
                    },
                    "reminder_time": {
                        "type": "string",
                        "description": "When to remind about the task (natural language)"
                    }
                },
                "required": ["task_content"]
            }
        }
    
    def parse_task_command(self, user_input: str) -> Dict:
        """
        Parse user input to extract task creation intent
        
        Returns:
            Dict with parsed task information or error
        """
        # Check if this is a task-related command
        task_keywords = ['提醒', '任务', '待办', '记住', '做', '完成', '处理', '安排']
        time_keywords = ['点', '分', '时', '天', '周', '月', '明天', '后天', '今天', '小时后', '分钟后']
        
        if not any(keyword in user_input for keyword in task_keywords):
            return {"is_task_request": False, "error": "Not a task request"}
        
        # Extract task content (simplified parsing)
        task_content = self._extract_task_content(user_input)
        if not task_content:
            return {
                "is_task_request": True,
                "error": "主人，我没听清楚要做什么事呢？能再说一遍吗？ (´･ω･`)",
                "task_content": "",
                "reminder_time": ""
            }
        
        # Extract time information
        reminder_time = self._extract_time_info(user_input)
        
        return {
            "is_task_request": True,
            "task_content": task_content,
            "reminder_time": reminder_time,
            "error": None
        }
    
    def _extract_task_content(self, text: str) -> str:
        """
        Extract the actual task content from natural language
        """
        # Simple extraction - remove time-related parts and keep the core task
        # This is a simplified version - in reality, you'd use more sophisticated NLP
        
        # Remove common time expressions
        time_patterns = [
            r'\d+点\d*分*',
            r'\d+:\d+',
            r'明天|后天|今天|昨天',
            r'\d+小时后|\d+分钟后|\d+天后',
            r'下午|上午|中午|晚上|早上',
            r'周一|周二|周三|周四|周五|周六|周日',
            r'下周|这周|上周',
            r'提醒我|帮我记住|记住要'
        ]
        
        cleaned_text = text
        for pattern in time_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text)
        
        # Clean up the text
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        # Remove common command words
        command_words = ['提醒', '记住', '任务', '待办', '帮我', '我要', '需要']
        for word in command_words:
            cleaned_text = cleaned_text.replace(word, '')
        
        cleaned_text = cleaned_text.strip()
        
        # If nothing meaningful remains, return empty
        if len(cleaned_text) < 2:
            return ""
        
        return cleaned_text
    
    def _extract_time_info(self, text: str) -> str:
        """
        Extract time information from natural language
        """
        # Look for time patterns
        time_patterns = [
            r'\d+点\d*分*',
            r'\d+:\d+',
            r'明天|后天|今天',
            r'\d+小时后|\d+分钟后|\d+天后',
            r'下午|上午|中午|晚上|早上',
            r'周一|周二|周三|周四|周五|周六|周日',
            r'下周|这周'
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]  # Return the first match
        
        return ""
    
    def extract_time_info(self, time_text: str) -> Optional[datetime]:
        """
        Convert natural language time to datetime object
        
        Args:
            time_text: Natural language time expression
            
        Returns:
            datetime object or None if parsing fails
        """
        if not time_text:
            return None
        
        now = datetime.now()
        
        try:
            # Handle specific patterns
            if '明天' in time_text:
                target_date = now + timedelta(days=1)
                time_part = self._extract_time_part(time_text)
                if time_part:
                    hour, minute = self._parse_time_part(time_part)
                    return target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                else:
                    return target_date.replace(hour=9, minute=0, second=0, microsecond=0)
            
            elif '后天' in time_text:
                target_date = now + timedelta(days=2)
                time_part = self._extract_time_part(time_text)
                if time_part:
                    hour, minute = self._parse_time_part(time_part)
                    return target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                else:
                    return target_date.replace(hour=9, minute=0, second=0, microsecond=0)
            
            elif '今天' in time_text:
                time_part = self._extract_time_part(time_text)
                if time_part:
                    hour, minute = self._parse_time_part(time_part)
                    target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if target_time <= now:
                        target_time += timedelta(days=1)
                    return target_time
            
            elif '小时后' in time_text:
                hours_match = re.search(r'(\d+)小时后', time_text)
                if hours_match:
                    hours = int(hours_match.group(1))
                    return now + timedelta(hours=hours)
            
            elif '分钟后' in time_text:
                minutes_match = re.search(r'(\d+)分钟后', time_text)
                if minutes_match:
                    minutes = int(minutes_match.group(1))
                    return now + timedelta(minutes=minutes)
            
            elif '天后' in time_text:
                days_match = re.search(r'(\d+)天后', time_text)
                if days_match:
                    days = int(days_match.group(1))
                    return now + timedelta(days=days)
            
            elif re.search(r'\d+点', time_text):
                time_part = self._extract_time_part(time_text)
                if time_part:
                    hour, minute = self._parse_time_part(time_part)
                    target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if target_time <= now:
                        target_time += timedelta(days=1)
                    return target_time
            
            # Handle weekdays
            weekdays = {
                '周一': 0, '周二': 1, '周三': 2, '周四': 3, '周五': 4, '周六': 5, '周日': 6
            }
            
            for day_name, day_num in weekdays.items():
                if day_name in time_text:
                    days_ahead = day_num - now.weekday()
                    if days_ahead <= 0:  # Target day already happened this week
                        days_ahead += 7
                    target_date = now + timedelta(days=days_ahead)
                    
                    time_part = self._extract_time_part(time_text)
                    if time_part:
                        hour, minute = self._parse_time_part(time_part)
                        return target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    else:
                        return target_date.replace(hour=9, minute=0, second=0, microsecond=0)
            
            # Try parsing with dateutil as fallback
            try:
                return parser.parse(time_text, fuzzy=True)
            except:
                pass
            
        except Exception as e:
            print(f"Time parsing error: {e}")
            return None
        
        return None
    
    def _extract_time_part(self, text: str) -> Optional[str]:
        """Extract time part like '3点' or '15:30' from text"""
        # Look for time patterns
        time_patterns = [
            r'\d+点\d*分*',
            r'\d+:\d+',
            r'上午|下午|中午|晚上|早上'
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        
        return None
    
    def _parse_time_part(self, time_part: str) -> Tuple[int, int]:
        """Parse time part to hour and minute"""
        # Handle different time formats
        if '点' in time_part:
            if '分' in time_part:
                # Format: 3点30分
                hour_match = re.search(r'(\d+)点', time_part)
                minute_match = re.search(r'(\d+)分', time_part)
                hour = int(hour_match.group(1)) if hour_match else 0
                minute = int(minute_match.group(1)) if minute_match else 0
            else:
                # Format: 3点
                hour_match = re.search(r'(\d+)点', time_part)
                hour = int(hour_match.group(1)) if hour_match else 0
                minute = 0
        elif ':' in time_part:
            # Format: 15:30
            parts = time_part.split(':')
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
        else:
            hour, minute = 9, 0  # Default time
        
        return hour, minute
    
    def validate_task_data(self, task_data: Dict) -> bool:
        """
        Validate task data structure
        
        Args:
            task_data: Dictionary containing task information
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(task_data, dict):
            return False
        
        # Check required fields
        if 'task_content' not in task_data:
            return False
        
        if not task_data['task_content'] or not isinstance(task_data['task_content'], str):
            return False
        
        # Validate task content length
        if len(task_data['task_content'].strip()) < 2:
            return False
        
        return True
    
    def format_confirmation_message(self, task: Dict) -> str:
        """
        Generate confirmation message for task creation
        
        Args:
            task: Task dictionary with content and reminder time
            
        Returns:
            Formatted confirmation message
        """
        task_content = task.get('task_content', '')
        reminder_time = task.get('reminder_time', '')
        
        if reminder_time:
            # Format the reminder time nicely
            try:
                if isinstance(reminder_time, datetime):
                    time_str = reminder_time.strftime('%Y年%m月%d日 %H:%M')
                else:
                    time_str = str(reminder_time)
                
                return f"✅ 主人，我已经记住了！\n📝 任务：{task_content}\n⏰ 提醒时间：{time_str}\n到时候我会提醒您的哦~ (´∀｀)"
            except:
                return f"✅ 主人，我已经记住了！\n📝 任务：{task_content}\n⏰ 我会在适当的时候提醒您的~ (´∀｀)"
        else:
            return f"✅ 主人，我已经记住了！\n📝 任务：{task_content}\n我会帮您记着的~ (´∀｀)"