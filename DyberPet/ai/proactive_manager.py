"""
ProactiveManager - Handles proactive dialogue triggering (FR-2.1)

This module manages proactive interactions including:
- Time-based triggers (30-60 minute intervals)
- Event-based triggers (status changes, system events)
- Intelligent scheduling to avoid user disturbance
- Frequency adjustment based on user feedback
"""

import time
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass

from PySide6.QtCore import QObject, QTimer, Signal
from apscheduler.schedulers.qt import QtScheduler
from apscheduler.triggers import interval, date, cron

import DyberPet.settings as settings


@dataclass
class ProactiveContext:
    """Context information for proactive message generation"""
    trigger_type: str  # 'time', 'event', 'status'
    time_of_day: str  # 'morning', 'afternoon', 'evening', 'night'
    pet_status: Dict[str, any]  # Current pet status
    user_activity: Dict[str, any]  # User activity patterns
    last_interaction: Optional[datetime]  # Last interaction time
    interaction_count: int  # Recent interaction count


class ProactiveManager(QObject):
    """Manages proactive dialogue triggering for DyberPet"""
    
    # Signals
    proactive_message_generated = Signal(str, dict)  # message, context
    interaction_frequency_changed = Signal(int)  # new frequency in minutes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scheduler = QtScheduler()
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.config = {
            'base_interval_min': 30,  # Minimum interval in minutes
            'base_interval_max': 60,  # Maximum interval in minutes
            'do_not_disturb_hours': [(23, 8)],  # Hours when not to trigger
            'active_hours': (9, 22),  # User's typical active hours
            'max_daily_proactive': 20,  # Maximum proactive messages per day
            'cooldown_after_user_interaction': 15,  # Minutes to wait after user interaction
        }
        
        # State tracking
        self.daily_proactive_count = 0
        self.last_proactive_time = None
        self.last_user_interaction = None
        self.is_running = False
        self.current_frequency = self.config['base_interval_min']
        
        # Initialize scheduler
        self.scheduler.start()
        
    def start_proactive_system(self):
        """Start the proactive interaction system"""
        if self.is_running:
            self.logger.warning("Proactive system already running")
            return
            
        self.is_running = True
        self.daily_proactive_count = 0
        self.schedule_next_interaction()
        self.logger.info("Proactive system started")
        
    def stop_proactive_system(self):
        """Stop the proactive interaction system"""
        if not self.is_running:
            return
            
        self.is_running = False
        self.scheduler.remove_all_jobs()
        self.logger.info("Proactive system stopped")
        
    def schedule_next_interaction(self):
        """Schedule the next proactive interaction"""
        if not self.is_running:
            return
            
        # Calculate next trigger time
        base_interval = random.randint(
            self.config['base_interval_min'],
            self.config['base_interval_max']
        )
        
        # Apply frequency adjustment
        adjusted_interval = int(base_interval * (self.current_frequency / 45))  # 45 is default
        
        # Schedule job
        trigger_time = datetime.now() + timedelta(minutes=adjusted_interval)
        self.scheduler.add_job(
            self.check_trigger_conditions,
            'date',
            run_date=trigger_time,
            id='proactive_trigger',
            replace_existing=True
        )
        
        self.logger.debug(f"Next proactive trigger scheduled in {adjusted_interval} minutes")
        
    def check_trigger_conditions(self):
        """Check if conditions are right for proactive interaction"""
        current_time = datetime.now()
        
        # Check daily limit
        if self.daily_proactive_count >= self.config['max_daily_proactive']:
            self.logger.debug("Daily proactive limit reached")
            self.schedule_next_interaction()
            return
            
        # Check do not disturb hours
        if self._is_do_not_disturb_time(current_time):
            self.logger.debug("In do not disturb hours")
            self.schedule_next_interaction()
            return
            
        # Check cooldown after user interaction
        if (self.last_user_interaction and 
            (current_time - self.last_user_interaction).total_seconds() < 
            self.config['cooldown_after_user_interaction'] * 60):
            self.logger.debug("Still in cooldown period after user interaction")
            self.schedule_next_interaction()
            return
            
        # Check if user seems to be working (focus/pomodoro mode)
        if self._is_user_focused():
            self.logger.debug("User appears to be focused/working")
            self.schedule_next_interaction()
            return
            
        # Conditions met, trigger proactive message
        self._trigger_proactive_message('time')
        
    def trigger_event_based_message(self, event_type: str, event_data: Dict):
        """Trigger proactive message based on specific events"""
        if not self.is_running:
            return
            
        # High priority events can override some restrictions
        high_priority_events = ['pet_hungry', 'pet_sick', 'user_greeting']
        
        if event_type not in high_priority_events:
            # Check basic conditions
            if self.daily_proactive_count >= self.config['max_daily_proactive']:
                return
                
            if self._is_do_not_disturb_time(datetime.now()):
                return
                
        self._trigger_proactive_message('event', event_data)
        
    def _trigger_proactive_message(self, trigger_type: str, event_data: Dict = None):
        """Generate and emit proactive message"""
        context = self._build_context(trigger_type, event_data)
        message = self.generate_proactive_message(context)
        
        if message:
            self.daily_proactive_count += 1
            self.last_proactive_time = datetime.now()
            self.proactive_message_generated.emit(message, context.__dict__)
            self.logger.info(f"Proactive message triggered: {trigger_type}")
            
        # Schedule next interaction
        self.schedule_next_interaction()
        
    def _build_context(self, trigger_type: str, event_data: Dict = None) -> ProactiveContext:
        """Build context for proactive message generation"""
        current_time = datetime.now()
        
        # Determine time of day
        hour = current_time.hour
        if 6 <= hour < 12:
            time_of_day = 'morning'
        elif 12 <= hour < 18:
            time_of_day = 'afternoon'
        elif 18 <= hour < 22:
            time_of_day = 'evening'
        else:
            time_of_day = 'night'
            
        # Get pet status
        pet_status = {
            'hp_tier': getattr(settings.pet_data, 'hp_tier', 2),
            'fv_tier': getattr(settings.pet_data, 'fv_tier', 2),
            'mood': 'happy',  # Default mood
            'name': getattr(settings, 'petname', 'DyberPet')
        }
        
        # Build context
        context = ProactiveContext(
            trigger_type=trigger_type,
            time_of_day=time_of_day,
            pet_status=pet_status,
            user_activity={},
            last_interaction=self.last_user_interaction,
            interaction_count=self.daily_proactive_count
        )
        
        return context
        
    def generate_proactive_message(self, context: ProactiveContext) -> str:
        """Generate proactive message based on context"""
        # This is a simplified version - in a full implementation,
        # this would integrate with the AI system for dynamic generation
        
        templates = {
            'time': {
                'morning': [
                    "主人，早上好！☀️ 新的一天开始了呢～",
                    "早安，主人！今天也要元气满满哦！(＾▽＾)",
                    "主人醒啦～今天想做什么呢？✨"
                ],
                'afternoon': [
                    "主人，午安！记得要休息一下哦～",
                    "下午好，主人！要不要喝点水休息一下？💧",
                    "主人，工作辛苦了！陪我聊聊天吧～"
                ],
                'evening': [
                    "主人，晚上好！今天过得怎么样呢？🌙",
                    "晚安前陪我说说话吧，主人～",
                    "主人，傍晚时光最温馨了呢！"
                ],
                'night': [
                    "主人，夜深了，该休息了哦～😴",
                    "主人还在忙吗？记得早点睡觉哦！",
                    "晚安，主人！明天见～🌟"
                ]
            },
            'event': {
                'pet_hungry': [
                    "主人～我有点饿了呢... 🥺",
                    "主人，能给我点好吃的吗？",
                    "我的肚子咕咕叫了，主人～"
                ],
                'pet_sick': [
                    "主人，我感觉不太舒服...",
                    "主人，我需要你的关心～",
                    "主人，陪陪我吧..."
                ],
                'long_idle': [
                    "主人去哪里了呢？想你了～",
                    "主人，我在这里等你很久了哦",
                    "主人，记得我在这里等你呢～"
                ]
            }
        }
        
        # Select appropriate template
        if context.trigger_type == 'time':
            options = templates['time'].get(context.time_of_day, templates['time']['afternoon'])
        else:
            options = templates['event'].get('long_idle', templates['event']['long_idle'])
            
        # Add status-specific modifications
        if context.pet_status['hp_tier'] <= 1:  # Hungry
            options = templates['event']['pet_hungry']
        elif context.pet_status['fv_tier'] <= 1:  # Sad
            options = templates['event']['pet_sick']
            
        return random.choice(options)
        
    def update_interaction_frequency(self, feedback: str):
        """Update interaction frequency based on user feedback"""
        if feedback == 'too_frequent':
            self.current_frequency = min(self.current_frequency + 15, 120)
        elif feedback == 'too_rare':
            self.current_frequency = max(self.current_frequency - 15, 15)
        elif feedback == 'just_right':
            # Slight adjustment towards ideal frequency
            target = 45  # Default target
            if self.current_frequency > target:
                self.current_frequency -= 5
            elif self.current_frequency < target:
                self.current_frequency += 5
                
        self.interaction_frequency_changed.emit(self.current_frequency)
        self.logger.info(f"Interaction frequency updated to {self.current_frequency} minutes")
        
    def notify_user_interaction(self):
        """Notify that user has interacted with the system"""
        self.last_user_interaction = datetime.now()
        self.logger.debug("User interaction recorded")
        
    def _is_do_not_disturb_time(self, current_time: datetime) -> bool:
        """Check if current time is in do not disturb period"""
        hour = current_time.hour
        
        for start_hour, end_hour in self.config['do_not_disturb_hours']:
            if start_hour > end_hour:  # Overnight period
                if hour >= start_hour or hour < end_hour:
                    return True
            else:  # Same day period
                if start_hour <= hour < end_hour:
                    return True
                    
        return False
        
    def _is_user_focused(self) -> bool:
        """Check if user is in focus/pomodoro mode"""
        # This would integrate with the existing focus/pomodoro system
        # For now, return False as a placeholder
        return False
        
    def get_status(self) -> Dict:
        """Get current proactive system status"""
        return {
            'is_running': self.is_running,
            'daily_count': self.daily_proactive_count,
            'current_frequency': self.current_frequency,
            'last_proactive': self.last_proactive_time,
            'last_user_interaction': self.last_user_interaction
        }