"""
DyberPet AI Module - Stage 2 Implementation
Proactive Interaction System for DyberPet

This module implements the Stage 2 features for DyberPet AI integration:
- Proactive dialogue triggering
- Emotion expression animations
- Personalized response generation
- User preference learning
"""

from .proactive_manager import ProactiveManager
from .emotion_manager import EmotionManager
from .personalization_engine import PersonalizationEngine
from .learning_system import LearningSystem
from .user_profile import UserProfile
from .ai_stage2_integration import AIStage2Integration

__all__ = [
    'ProactiveManager',
    'EmotionManager', 
    'PersonalizationEngine',
    'LearningSystem',
    'UserProfile',
    'AIStage2Integration'
]