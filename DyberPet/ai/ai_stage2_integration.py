"""
AI Integration Module - Stage 2 Main Integration

This module integrates all Stage 2 AI components with the existing DyberPet system:
- Connects proactive manager with scheduler
- Integrates emotion manager with animation system
- Connects learning system with user interactions
- Provides unified AI interface for Stage 2 features
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

from PySide6.QtCore import QObject, Signal, QTimer

from .proactive_manager import ProactiveManager
from .emotion_manager import EmotionManager
from .personalization_engine import PersonalizationEngine
from .learning_system import LearningSystem
from .user_profile import UserProfile

import DyberPet.settings as settings


class AIStage2Integration(QObject):
    """Main integration class for Stage 2 AI features"""
    
    # Signals for DyberPet integration
    proactive_bubble_requested = Signal(str, dict)  # message, context
    animation_requested = Signal(str, dict)  # animation_name, emotion_data
    user_preferences_updated = Signal(dict)  # preferences
    learning_recommendation = Signal(str)  # recommendation_text
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.proactive_manager = ProactiveManager(self)
        self.emotion_manager = EmotionManager(self)
        self.personalization_engine = PersonalizationEngine(self)
        self.learning_system = LearningSystem(self)
        self.user_profile = UserProfile(self)
        
        # State tracking
        self.is_initialized = False
        self.is_active = False
        
        # Connect internal signals
        self._connect_signals()
        
        # Initialize components
        self._initialize_components()
        
    def _connect_signals(self):
        """Connect signals between components"""
        # Proactive Manager signals
        self.proactive_manager.proactive_message_generated.connect(
            self._handle_proactive_message
        )
        self.proactive_manager.interaction_frequency_changed.connect(
            self._handle_frequency_change
        )
        
        # Emotion Manager signals
        self.emotion_manager.emotion_animation_triggered.connect(
            self._handle_emotion_animation
        )
        self.emotion_manager.emotion_detected.connect(
            self._handle_emotion_detection
        )
        
        # Learning System signals
        self.learning_system.behavior_updated.connect(
            self._handle_behavior_update
        )
        self.learning_system.pattern_detected.connect(
            self._handle_pattern_detection
        )
        
        # User Profile signals
        self.user_profile.preferences_updated.connect(
            self._handle_preferences_update
        )
        self.user_profile.stats_updated.connect(
            self._handle_stats_update
        )
        
        # Personalization Engine signals
        self.personalization_engine.profile_updated.connect(
            self._handle_profile_update
        )
        
    def _initialize_components(self):
        """Initialize all components"""
        try:
            # Load user profile first
            self.user_profile._load_profile()
            
            # Initialize other components based on user preferences
            prefs = self.user_profile.get_preferences()
            
            if prefs.proactive_enabled:
                self.proactive_manager.start_proactive_system()
                
            # Update behavior parameters from learning system
            behavior_params = self.learning_system.get_behavior_parameters()
            self.proactive_manager.current_frequency = behavior_params.proactive_frequency
            
            self.is_initialized = True
            self.logger.info("Stage 2 AI components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Stage 2 AI components: {e}")
            
    def start_ai_system(self):
        """Start the AI system"""
        if not self.is_initialized:
            self._initialize_components()
            
        if self.is_active:
            return
            
        self.is_active = True
        
        # Start proactive system if enabled
        prefs = self.user_profile.get_preferences()
        if prefs.proactive_enabled:
            self.proactive_manager.start_proactive_system()
            
        self.logger.info("Stage 2 AI system started")
        
    def stop_ai_system(self):
        """Stop the AI system"""
        if not self.is_active:
            return
            
        self.is_active = False
        self.proactive_manager.stop_proactive_system()
        
        self.logger.info("Stage 2 AI system stopped")
        
    def process_ai_response(self, response_text: str, context: Dict[str, Any] = None):
        """Process AI response for emotion detection and animation"""
        if not self.is_active:
            return
            
        prefs = self.user_profile.get_preferences()
        if not prefs.emotion_animations:
            return
            
        # Record interaction
        self.learning_system.record_interaction('ai_response', {
            'response_text': response_text,
            'context': context or {},
            'timestamp': datetime.now().isoformat()
        })
        
        # Process emotion and trigger animation
        emotion_data = self.emotion_manager.process_ai_response(response_text)
        
        # Update user profile stats
        self.user_profile.update_stats({
            'total_ai_responses': 1
        })
        
        # Record feature usage
        self.user_profile.record_feature_usage('ai_response_processing')
        
        return emotion_data
        
    def handle_user_interaction(self, interaction_type: str, data: Dict[str, Any]):
        """Handle user interaction events"""
        if not self.is_active:
            return
            
        # Notify proactive manager
        self.proactive_manager.notify_user_interaction()
        
        # Record interaction for learning
        self.learning_system.record_interaction(interaction_type, data)
        
        # Update user profile
        self.user_profile.update_stats({
            'total_interactions': 1
        })
        
        # Record feature usage
        self.user_profile.record_feature_usage(interaction_type)
        
    def handle_pet_status_change(self, status_type: str, old_value: Any, new_value: Any):
        """Handle pet status changes for proactive triggers"""
        if not self.is_active:
            return
            
        # Trigger event-based proactive message
        event_data = {
            'status_type': status_type,
            'old_value': old_value,
            'new_value': new_value,
            'timestamp': datetime.now().isoformat()
        }
        
        self.proactive_manager.trigger_event_based_message(f'pet_{status_type}', event_data)
        
    def collect_user_feedback(self, message_id: str, feedback_type: str, context: Dict[str, Any] = None):
        """Collect user feedback for learning"""
        if not self.is_active:
            return
            
        # Record feedback
        self.learning_system.collect_feedback(message_id, feedback_type, context)
        
        # Update user profile stats
        if feedback_type in ['like', 'love', 'helpful']:
            self.user_profile.update_stats({'positive_feedback': 1})
        elif feedback_type in ['dislike', 'not_helpful']:
            self.user_profile.update_stats({'negative_feedback': 1})
        else:
            self.user_profile.update_stats({'neutral_feedback': 1})
            
        # Record feature usage
        self.user_profile.record_feature_usage('feedback_collection')
        
    def update_user_preferences(self, preferences: Dict[str, Any]):
        """Update user preferences"""
        self.user_profile.update_preferences(preferences)
        
        # Apply preference changes
        prefs = self.user_profile.get_preferences()
        
        # Update proactive system
        if prefs.proactive_enabled and not self.proactive_manager.is_running:
            self.proactive_manager.start_proactive_system()
        elif not prefs.proactive_enabled and self.proactive_manager.is_running:
            self.proactive_manager.stop_proactive_system()
            
    def build_user_profile_from_chat(self, chat_history: List[Dict[str, str]]):
        """Build user profile from chat history"""
        if not self.is_active:
            return
            
        prefs = self.user_profile.get_preferences()
        if not prefs.profile_building:
            return
            
        self.personalization_engine.build_user_profile(chat_history)
        
    def get_personalized_prompt(self, base_prompt: str) -> str:
        """Get personalized prompt based on user profile"""
        if not self.is_active:
            return base_prompt
            
        prefs = self.user_profile.get_preferences()
        if not prefs.personalization_enabled:
            return base_prompt
            
        user_profile = self.personalization_engine.get_user_profile()
        return self.personalization_engine.customize_prompt(base_prompt, user_profile)
        
    def adapt_response_style(self, response: str) -> str:
        """Adapt response style based on user preferences"""
        if not self.is_active:
            return response
            
        prefs = self.user_profile.get_preferences()
        if not prefs.personalization_enabled:
            return response
            
        return self.personalization_engine.adapt_response_style(response)
        
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        prefs = self.user_profile.get_preferences()
        
        return {
            'is_active': self.is_active,
            'is_initialized': self.is_initialized,
            'components': {
                'proactive_manager': self.proactive_manager.get_status(),
                'emotion_manager': self.emotion_manager.get_statistics(),
                'learning_system': self.learning_system.get_learning_statistics(),
                'user_profile': self.user_profile.get_profile_summary()
            },
            'preferences': prefs.to_dict() if prefs else {},
            'last_update': datetime.now().isoformat()
        }
        
    def get_user_recommendations(self) -> List[str]:
        """Get user recommendations based on learning"""
        if not self.is_active:
            return []
            
        return self.learning_system.get_recommendations()
        
    def export_user_data(self, include_learning_data: bool = True) -> Dict[str, str]:
        """Export user data"""
        exports = {}
        
        # Export user profile
        profile_backup = self.user_profile.backup_profile()
        if profile_backup:
            exports['profile'] = profile_backup
            
        # Export learning data if requested
        if include_learning_data:
            learning_export = self.learning_system.export_learning_data()
            if learning_export:
                exports['learning'] = learning_export
                
        return exports
        
    def _handle_proactive_message(self, message: str, context: Dict):
        """Handle proactive message generation"""
        self.proactive_bubble_requested.emit(message, context)
        
        # Update stats
        self.user_profile.update_stats({
            'total_proactive_messages': 1
        })
        
        # Record feature usage
        self.user_profile.record_feature_usage('proactive_message')
        
    def _handle_emotion_animation(self, animation_name: str, emotion_data: Dict):
        """Handle emotion animation trigger"""
        self.animation_requested.emit(animation_name, emotion_data)
        
        # Update stats
        self.user_profile.update_stats({
            'total_animations_triggered': 1
        })
        
        # Record feature usage
        self.user_profile.record_feature_usage('emotion_animation')
        
    def _handle_frequency_change(self, new_frequency: int):
        """Handle interaction frequency change"""
        self.logger.info(f"Interaction frequency changed to {new_frequency} minutes")
        
    def _handle_emotion_detection(self, emotion: str, intensity: float):
        """Handle emotion detection"""
        self.logger.debug(f"Emotion detected: {emotion} (intensity: {intensity:.2f})")
        
    def _handle_behavior_update(self, new_parameters: Dict):
        """Handle behavior parameter updates"""
        self.logger.info("Behavior parameters updated")
        
        # Update proactive frequency
        if 'proactive_frequency' in new_parameters:
            self.proactive_manager.current_frequency = new_parameters['proactive_frequency']
            
    def _handle_pattern_detection(self, pattern_type: str, pattern_details: Dict):
        """Handle pattern detection"""
        self.logger.info(f"Pattern detected: {pattern_type}")
        
        # Generate recommendation if needed
        if pattern_type in ['too_frequent_feedback', 'negative_feedback']:
            recommendation = f"检测到用户反馈模式: {pattern_type}，建议调整交互策略"
            self.learning_recommendation.emit(recommendation)
            
    def _handle_preferences_update(self, preferences: Dict):
        """Handle user preference updates"""
        self.user_preferences_updated.emit(preferences)
        
    def _handle_stats_update(self, stats: Dict):
        """Handle user stats updates"""
        self.logger.debug("User statistics updated")
        
    def _handle_profile_update(self, profile: Dict):
        """Handle user profile updates"""
        self.logger.info("User profile updated")
        
    def cleanup(self):
        """Cleanup resources"""
        self.stop_ai_system()
        
        # Save all data
        self.user_profile.save_profile()
        self.learning_system._save_feedback_data()
        self.learning_system._save_patterns()
        self.learning_system._save_behavior_parameters()
        
        self.logger.info("Stage 2 AI system cleanup completed")