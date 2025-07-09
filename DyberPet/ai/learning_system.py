"""
LearningSystem - Handles user feedback and learning (FR-2.4)

This module manages learning from user feedback including:
- Feedback collection from user interactions
- Interaction pattern analysis
- Behavior parameter updates
- Learning data export and import
"""

import json
import logging
import uuid
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, deque
from enum import Enum

from PySide6.QtCore import QObject, Signal
import DyberPet.settings as settings


class FeedbackType(Enum):
    """Types of feedback that can be collected"""
    LIKE = "like"
    DISLIKE = "dislike"
    LOVE = "love"
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"
    TOO_FREQUENT = "too_frequent"
    TOO_RARE = "too_rare"
    JUST_RIGHT = "just_right"


@dataclass
class FeedbackRecord:
    """Record of user feedback"""
    id: str
    message_id: str
    feedback_type: str
    timestamp: str
    context: Dict[str, Any]
    response_text: str
    emotion: Optional[str] = None
    animation: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'FeedbackRecord':
        return cls(**data)


@dataclass
class InteractionPattern:
    """Detected interaction pattern"""
    pattern_type: str
    frequency: float
    confidence: float
    details: Dict[str, Any]
    first_seen: str
    last_seen: str


@dataclass
class BehaviorParameters:
    """Parameters that control AI behavior"""
    proactive_frequency: float  # Minutes between proactive messages
    emotion_sensitivity: float  # How sensitive to emotion triggers
    response_length_preference: float  # 0=short, 1=long
    humor_level: float  # Amount of humor in responses
    formality_level: float  # Level of formality
    emoji_usage: float  # Frequency of emoji usage
    question_frequency: float  # How often to ask questions
    topic_diversity: float  # How diverse topics should be
    
    def to_dict(self) -> Dict:
        return asdict(self)
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'BehaviorParameters':
        return cls(**data)


class LearningSystem(QObject):
    """Manages user feedback collection and learning"""
    
    # Signals
    feedback_collected = Signal(str, str)  # feedback_type, message_id
    pattern_detected = Signal(str, dict)  # pattern_type, pattern_details
    behavior_updated = Signal(dict)  # new_parameters
    learning_stats_updated = Signal(dict)  # statistics
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # Data storage
        self.feedback_records: List[FeedbackRecord] = []
        self.interaction_patterns: List[InteractionPattern] = []
        self.behavior_parameters = self._load_behavior_parameters()
        
        # Configuration
        self.config = {
            'max_feedback_records': 1000,
            'min_pattern_confidence': 0.7,
            'learning_rate': 0.1,
            'pattern_detection_window': 7,  # days
            'auto_save_interval': 300,  # seconds
        }
        
        # Temporary storage for analysis
        self.recent_interactions = deque(maxlen=100)
        self.interaction_times = deque(maxlen=500)
        
        # Load existing data
        self._load_feedback_data()
        self._load_patterns()
        
        # Initialize auto-save timer
        self._setup_auto_save()
        
    def _load_behavior_parameters(self) -> BehaviorParameters:
        """Load behavior parameters from storage"""
        params_file = Path(settings.BASEDIR) / 'DyberPet' / 'data' / 'behavior_parameters.json'
        
        if params_file.exists():
            try:
                with open(params_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return BehaviorParameters.from_dict(data)
            except Exception as e:
                self.logger.warning(f"Failed to load behavior parameters: {e}")
                
        # Default parameters
        return BehaviorParameters(
            proactive_frequency=45.0,
            emotion_sensitivity=0.7,
            response_length_preference=0.6,
            humor_level=0.5,
            formality_level=0.3,
            emoji_usage=0.7,
            question_frequency=0.4,
            topic_diversity=0.6
        )
        
    def _save_behavior_parameters(self):
        """Save behavior parameters to storage"""
        params_file = Path(settings.BASEDIR) / 'DyberPet' / 'data' / 'behavior_parameters.json'
        params_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(params_file, 'w', encoding='utf-8') as f:
                json.dump(self.behavior_parameters.to_dict(), f, indent=2)
            self.logger.debug("Behavior parameters saved")
        except Exception as e:
            self.logger.error(f"Failed to save behavior parameters: {e}")
            
    def _load_feedback_data(self):
        """Load feedback data from storage"""
        feedback_file = Path(settings.BASEDIR) / 'DyberPet' / 'data' / 'feedback_records.json'
        
        if feedback_file.exists():
            try:
                with open(feedback_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.feedback_records = [FeedbackRecord.from_dict(record) for record in data]
                    self.logger.info(f"Loaded {len(self.feedback_records)} feedback records")
            except Exception as e:
                self.logger.warning(f"Failed to load feedback data: {e}")
                
    def _save_feedback_data(self):
        """Save feedback data to storage"""
        feedback_file = Path(settings.BASEDIR) / 'DyberPet' / 'data' / 'feedback_records.json'
        feedback_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Keep only the most recent records
            recent_records = self.feedback_records[-self.config['max_feedback_records']:]
            data = [record.to_dict() for record in recent_records]
            
            with open(feedback_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.debug(f"Saved {len(data)} feedback records")
        except Exception as e:
            self.logger.error(f"Failed to save feedback data: {e}")
            
    def _load_patterns(self):
        """Load interaction patterns from storage"""
        patterns_file = Path(settings.BASEDIR) / 'DyberPet' / 'data' / 'interaction_patterns.json'
        
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.interaction_patterns = [InteractionPattern(**pattern) for pattern in data]
                    self.logger.info(f"Loaded {len(self.interaction_patterns)} interaction patterns")
            except Exception as e:
                self.logger.warning(f"Failed to load interaction patterns: {e}")
                
    def _save_patterns(self):
        """Save interaction patterns to storage"""
        patterns_file = Path(settings.BASEDIR) / 'DyberPet' / 'data' / 'interaction_patterns.json'
        patterns_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            data = [asdict(pattern) for pattern in self.interaction_patterns]
            with open(patterns_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.debug(f"Saved {len(data)} interaction patterns")
        except Exception as e:
            self.logger.error(f"Failed to save interaction patterns: {e}")
            
    def _setup_auto_save(self):
        """Setup auto-save timer"""
        from PySide6.QtCore import QTimer
        
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._auto_save)
        self.auto_save_timer.start(self.config['auto_save_interval'] * 1000)
        
    def _auto_save(self):
        """Auto-save all data"""
        self._save_feedback_data()
        self._save_patterns()
        self._save_behavior_parameters()
        
    def collect_feedback(self, message_id: str, feedback_type: str, context: Dict[str, Any] = None):
        """Collect feedback from user"""
        if not message_id or not feedback_type:
            self.logger.warning("Invalid feedback data")
            return
            
        # Create feedback record
        feedback = FeedbackRecord(
            id=str(uuid.uuid4()),
            message_id=message_id,
            feedback_type=feedback_type,
            timestamp=datetime.now().isoformat(),
            context=context or {},
            response_text=context.get('response_text', '') if context else '',
            emotion=context.get('emotion') if context else None,
            animation=context.get('animation') if context else None
        )
        
        # Add to records
        self.feedback_records.append(feedback)
        
        # Process immediate feedback
        self._process_immediate_feedback(feedback)
        
        # Emit signal
        self.feedback_collected.emit(feedback_type, message_id)
        
        self.logger.info(f"Feedback collected: {feedback_type} for message {message_id}")
        
    def _process_immediate_feedback(self, feedback: FeedbackRecord):
        """Process feedback immediately for quick adjustments"""
        feedback_type = feedback.feedback_type
        
        # Adjust parameters based on feedback
        if feedback_type == FeedbackType.TOO_FREQUENT.value:
            self.behavior_parameters.proactive_frequency *= 1.2
            self.behavior_parameters.proactive_frequency = min(
                self.behavior_parameters.proactive_frequency, 120.0
            )
        elif feedback_type == FeedbackType.TOO_RARE.value:
            self.behavior_parameters.proactive_frequency *= 0.8
            self.behavior_parameters.proactive_frequency = max(
                self.behavior_parameters.proactive_frequency, 10.0
            )
        elif feedback_type == FeedbackType.LIKE.value or feedback_type == FeedbackType.LOVE.value:
            # Slightly increase similar behavior
            if feedback.emotion:
                self.behavior_parameters.emotion_sensitivity *= 1.05
            if feedback.animation:
                self.behavior_parameters.emotion_sensitivity *= 1.05
        elif feedback_type == FeedbackType.DISLIKE.value:
            # Slightly decrease similar behavior
            if feedback.emotion:
                self.behavior_parameters.emotion_sensitivity *= 0.95
                
        # Clamp values
        self._clamp_parameters()
        
        # Emit update signal
        self.behavior_updated.emit(self.behavior_parameters.to_dict())
        
    def _clamp_parameters(self):
        """Clamp all parameters to valid ranges"""
        self.behavior_parameters.proactive_frequency = max(10.0, min(120.0, self.behavior_parameters.proactive_frequency))
        self.behavior_parameters.emotion_sensitivity = max(0.1, min(1.0, self.behavior_parameters.emotion_sensitivity))
        self.behavior_parameters.response_length_preference = max(0.0, min(1.0, self.behavior_parameters.response_length_preference))
        self.behavior_parameters.humor_level = max(0.0, min(1.0, self.behavior_parameters.humor_level))
        self.behavior_parameters.formality_level = max(0.0, min(1.0, self.behavior_parameters.formality_level))
        self.behavior_parameters.emoji_usage = max(0.0, min(1.0, self.behavior_parameters.emoji_usage))
        self.behavior_parameters.question_frequency = max(0.0, min(1.0, self.behavior_parameters.question_frequency))
        self.behavior_parameters.topic_diversity = max(0.0, min(1.0, self.behavior_parameters.topic_diversity))
        
    def record_interaction(self, interaction_type: str, details: Dict[str, Any]):
        """Record an interaction for pattern analysis"""
        interaction = {
            'type': interaction_type,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        
        self.recent_interactions.append(interaction)
        self.interaction_times.append(datetime.now())
        
        # Trigger pattern analysis periodically
        if len(self.recent_interactions) % 10 == 0:
            self.analyze_interaction_patterns()
            
    def analyze_interaction_patterns(self):
        """Analyze interaction patterns from recent data"""
        if len(self.recent_interactions) < 5:
            return
            
        # Analyze time patterns
        self._analyze_time_patterns()
        
        # Analyze feedback patterns
        self._analyze_feedback_patterns()
        
        # Analyze response patterns
        self._analyze_response_patterns()
        
    def _analyze_time_patterns(self):
        """Analyze temporal interaction patterns"""
        if len(self.interaction_times) < 10:
            return
            
        # Convert to hours
        hours = [dt.hour for dt in self.interaction_times]
        
        # Find most common hours
        hour_counts = defaultdict(int)
        for hour in hours:
            hour_counts[hour] += 1
            
        # Detect peak hours
        if hour_counts:
            max_count = max(hour_counts.values())
            peak_hours = [hour for hour, count in hour_counts.items() if count >= max_count * 0.8]
            
            if len(peak_hours) >= 2:
                pattern = InteractionPattern(
                    pattern_type='peak_hours',
                    frequency=max_count / len(hours),
                    confidence=min(max_count / len(hours) * 2, 1.0),
                    details={'peak_hours': peak_hours, 'total_interactions': len(hours)},
                    first_seen=datetime.now().isoformat(),
                    last_seen=datetime.now().isoformat()
                )
                
                self._add_or_update_pattern(pattern)
                
    def _analyze_feedback_patterns(self):
        """Analyze feedback patterns"""
        if len(self.feedback_records) < 5:
            return
            
        # Recent feedback (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        recent_feedback = [
            f for f in self.feedback_records
            if datetime.fromisoformat(f.timestamp) > week_ago
        ]
        
        if not recent_feedback:
            return
            
        # Analyze feedback types
        feedback_counts = defaultdict(int)
        for feedback in recent_feedback:
            feedback_counts[feedback.feedback_type] += 1
            
        total_feedback = len(recent_feedback)
        
        # Detect concerning patterns
        if feedback_counts[FeedbackType.TOO_FREQUENT.value] / total_feedback > 0.3:
            pattern = InteractionPattern(
                pattern_type='too_frequent_feedback',
                frequency=feedback_counts[FeedbackType.TOO_FREQUENT.value] / total_feedback,
                confidence=0.9,
                details={'feedback_counts': dict(feedback_counts)},
                first_seen=datetime.now().isoformat(),
                last_seen=datetime.now().isoformat()
            )
            self._add_or_update_pattern(pattern)
            
        elif feedback_counts[FeedbackType.DISLIKE.value] / total_feedback > 0.4:
            pattern = InteractionPattern(
                pattern_type='negative_feedback',
                frequency=feedback_counts[FeedbackType.DISLIKE.value] / total_feedback,
                confidence=0.8,
                details={'feedback_counts': dict(feedback_counts)},
                first_seen=datetime.now().isoformat(),
                last_seen=datetime.now().isoformat()
            )
            self._add_or_update_pattern(pattern)
            
    def _analyze_response_patterns(self):
        """Analyze response patterns"""
        # Implementation would analyze response characteristics
        # and user reactions to different types of responses
        pass
        
    def _add_or_update_pattern(self, new_pattern: InteractionPattern):
        """Add or update an interaction pattern"""
        # Check if pattern already exists
        existing = None
        for pattern in self.interaction_patterns:
            if pattern.pattern_type == new_pattern.pattern_type:
                existing = pattern
                break
                
        if existing:
            # Update existing pattern
            existing.frequency = new_pattern.frequency
            existing.confidence = new_pattern.confidence
            existing.details = new_pattern.details
            existing.last_seen = new_pattern.last_seen
        else:
            # Add new pattern
            self.interaction_patterns.append(new_pattern)
            
        # Emit signal
        self.pattern_detected.emit(new_pattern.pattern_type, new_pattern.details)
        
    def update_behavior_parameters(self, adjustments: Dict[str, float]):
        """Update behavior parameters with manual adjustments"""
        for param, value in adjustments.items():
            if hasattr(self.behavior_parameters, param):
                setattr(self.behavior_parameters, param, value)
                
        self._clamp_parameters()
        self.behavior_updated.emit(self.behavior_parameters.to_dict())
        self.logger.info(f"Behavior parameters updated: {adjustments}")
        
    def get_behavior_parameters(self) -> BehaviorParameters:
        """Get current behavior parameters"""
        return self.behavior_parameters
        
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get learning system statistics"""
        total_feedback = len(self.feedback_records)
        recent_feedback = [
            f for f in self.feedback_records
            if datetime.fromisoformat(f.timestamp) > datetime.now() - timedelta(days=7)
        ]
        
        feedback_distribution = defaultdict(int)
        for feedback in recent_feedback:
            feedback_distribution[feedback.feedback_type] += 1
            
        return {
            'total_feedback_records': total_feedback,
            'recent_feedback_count': len(recent_feedback),
            'feedback_distribution': dict(feedback_distribution),
            'total_patterns': len(self.interaction_patterns),
            'recent_interactions': len(self.recent_interactions),
            'last_pattern_analysis': datetime.now().isoformat(),
            'behavior_parameters': self.behavior_parameters.to_dict()
        }
        
    def export_learning_data(self, file_path: Optional[str] = None) -> str:
        """Export learning data to file"""
        if not file_path:
            file_path = Path(settings.BASEDIR) / 'DyberPet' / 'data' / f'learning_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'feedback_records': [record.to_dict() for record in self.feedback_records],
            'interaction_patterns': [asdict(pattern) for pattern in self.interaction_patterns],
            'behavior_parameters': self.behavior_parameters.to_dict(),
            'statistics': self.get_learning_statistics()
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Learning data exported to {file_path}")
            return str(file_path)
        except Exception as e:
            self.logger.error(f"Failed to export learning data: {e}")
            return ""
            
    def import_learning_data(self, file_path: str) -> bool:
        """Import learning data from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Import feedback records
            if 'feedback_records' in data:
                self.feedback_records = [FeedbackRecord.from_dict(record) for record in data['feedback_records']]
                
            # Import patterns
            if 'interaction_patterns' in data:
                self.interaction_patterns = [InteractionPattern(**pattern) for pattern in data['interaction_patterns']]
                
            # Import behavior parameters
            if 'behavior_parameters' in data:
                self.behavior_parameters = BehaviorParameters.from_dict(data['behavior_parameters'])
                
            self.logger.info(f"Learning data imported from {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import learning data: {e}")
            return False
            
    def reset_learning_data(self):
        """Reset all learning data"""
        self.feedback_records.clear()
        self.interaction_patterns.clear()
        self.behavior_parameters = self._load_behavior_parameters()
        self.recent_interactions.clear()
        self.interaction_times.clear()
        
        # Save reset state
        self._save_feedback_data()
        self._save_patterns()
        self._save_behavior_parameters()
        
        self.logger.info("Learning data reset")
        
    def get_recommendations(self) -> List[str]:
        """Get recommendations based on learning data"""
        recommendations = []
        
        # Analyze feedback patterns
        if len(self.feedback_records) >= 10:
            recent_feedback = self.feedback_records[-20:]
            dislike_ratio = sum(1 for f in recent_feedback if f.feedback_type == FeedbackType.DISLIKE.value) / len(recent_feedback)
            
            if dislike_ratio > 0.3:
                recommendations.append("考虑调整回复风格，最近收到较多负面反馈")
                
        # Analyze interaction patterns
        for pattern in self.interaction_patterns:
            if pattern.pattern_type == 'too_frequent_feedback' and pattern.confidence > 0.7:
                recommendations.append("建议降低主动交互频率")
            elif pattern.pattern_type == 'negative_feedback' and pattern.confidence > 0.7:
                recommendations.append("建议分析负面反馈原因并调整策略")
                
        return recommendations