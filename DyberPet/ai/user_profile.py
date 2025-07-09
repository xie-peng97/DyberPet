"""
UserProfile - Manages user profile data and preferences

This module handles user profile management including:
- Profile data storage and retrieval
- Preference management
- Profile analytics
- Data migration and backup
"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, Signal
import DyberPet.settings as settings


@dataclass
class UserPreferences:
    """User preferences data structure"""
    ai_enabled: bool = True
    proactive_enabled: bool = True
    emotion_animations: bool = True
    personalization_enabled: bool = True
    learning_enabled: bool = True
    
    # Communication preferences
    response_style: str = "casual"  # formal, casual, funny, caring
    response_length: str = "medium"  # short, medium, long
    emoji_usage: str = "normal"  # none, minimal, normal, heavy
    
    # Proactive interaction preferences
    proactive_frequency: str = "medium"  # low, medium, high
    do_not_disturb_hours: List[tuple] = None
    quiet_mode_enabled: bool = False
    
    # Privacy preferences
    data_collection: bool = True
    profile_building: bool = True
    learning_from_feedback: bool = True
    
    def __post_init__(self):
        if self.do_not_disturb_hours is None:
            self.do_not_disturb_hours = [(23, 8)]  # 11PM to 8AM
            
    def to_dict(self) -> Dict:
        return asdict(self)
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserPreferences':
        return cls(**data)


@dataclass
class UserStats:
    """User interaction statistics"""
    total_interactions: int = 0
    total_ai_responses: int = 0
    total_proactive_messages: int = 0
    total_animations_triggered: int = 0
    
    # Feedback statistics
    positive_feedback: int = 0
    negative_feedback: int = 0
    neutral_feedback: int = 0
    
    # Time statistics
    first_interaction: Optional[str] = None
    last_interaction: Optional[str] = None
    average_session_length: float = 0.0
    
    # Feature usage
    features_used: Dict[str, int] = None
    
    def __post_init__(self):
        if self.features_used is None:
            self.features_used = {}
            
    def to_dict(self) -> Dict:
        return asdict(self)
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserStats':
        return cls(**data)


class UserProfile(QObject):
    """Manages user profile data and preferences"""
    
    # Signals
    profile_loaded = Signal(dict)
    profile_saved = Signal()
    preferences_updated = Signal(dict)
    stats_updated = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # Profile data
        self.user_id: str = ""
        self.username: str = ""
        self.created_at: str = ""
        self.last_active: str = ""
        
        # Preferences and stats
        self.preferences = UserPreferences()
        self.stats = UserStats()
        
        # Profile metadata
        self.profile_version: str = "1.0"
        self.interests: List[str] = []
        self.tags: List[str] = []
        self.notes: str = ""
        
        # Load existing profile
        self._load_profile()
        
    def _get_profile_path(self) -> Path:
        """Get the path to the user profile file"""
        return Path(settings.BASEDIR) / 'DyberPet' / 'data' / 'user_profile.json'
        
    def _load_profile(self):
        """Load user profile from storage"""
        profile_path = self._get_profile_path()
        
        if profile_path.exists():
            try:
                with open(profile_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Load basic profile data
                self.user_id = data.get('user_id', '')
                self.username = data.get('username', '')
                self.created_at = data.get('created_at', '')
                self.last_active = data.get('last_active', '')
                self.profile_version = data.get('profile_version', '1.0')
                self.interests = data.get('interests', [])
                self.tags = data.get('tags', [])
                self.notes = data.get('notes', '')
                
                # Load preferences
                if 'preferences' in data:
                    self.preferences = UserPreferences.from_dict(data['preferences'])
                    
                # Load statistics
                if 'stats' in data:
                    self.stats = UserStats.from_dict(data['stats'])
                    
                self.logger.info(f"User profile loaded for user: {self.username or self.user_id}")
                self.profile_loaded.emit(self.to_dict())
                
            except Exception as e:
                self.logger.error(f"Failed to load user profile: {e}")
                self._create_default_profile()
        else:
            self._create_default_profile()
            
    def _create_default_profile(self):
        """Create a default user profile"""
        import uuid
        
        self.user_id = str(uuid.uuid4())
        self.username = "主人"
        self.created_at = datetime.now().isoformat()
        self.last_active = datetime.now().isoformat()
        self.preferences = UserPreferences()
        self.stats = UserStats()
        
        # Save the new profile
        self.save_profile()
        
        self.logger.info("Default user profile created")
        
    def save_profile(self):
        """Save user profile to storage"""
        profile_path = self._get_profile_path()
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Update last active time
            self.last_active = datetime.now().isoformat()
            
            # Prepare data for saving
            data = {
                'user_id': self.user_id,
                'username': self.username,
                'created_at': self.created_at,
                'last_active': self.last_active,
                'profile_version': self.profile_version,
                'interests': self.interests,
                'tags': self.tags,
                'notes': self.notes,
                'preferences': self.preferences.to_dict(),
                'stats': self.stats.to_dict()
            }
            
            # Save to file
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            self.logger.debug("User profile saved successfully")
            self.profile_saved.emit()
            
        except Exception as e:
            self.logger.error(f"Failed to save user profile: {e}")
            
    def update_preferences(self, preferences: Dict[str, Any]):
        """Update user preferences"""
        try:
            for key, value in preferences.items():
                if hasattr(self.preferences, key):
                    setattr(self.preferences, key, value)
                    
            self.save_profile()
            self.preferences_updated.emit(self.preferences.to_dict())
            self.logger.info(f"Preferences updated: {list(preferences.keys())}")
            
        except Exception as e:
            self.logger.error(f"Failed to update preferences: {e}")
            
    def get_preferences(self) -> UserPreferences:
        """Get current user preferences"""
        return self.preferences
        
    def update_stats(self, stats_updates: Dict[str, Any]):
        """Update user statistics"""
        try:
            for key, value in stats_updates.items():
                if hasattr(self.stats, key):
                    current_value = getattr(self.stats, key)
                    
                    # Handle different update types
                    if isinstance(current_value, int) and isinstance(value, int):
                        setattr(self.stats, key, current_value + value)
                    elif isinstance(current_value, dict) and isinstance(value, dict):
                        current_value.update(value)
                    else:
                        setattr(self.stats, key, value)
                        
            # Update interaction timestamps
            if 'total_interactions' in stats_updates:
                if not self.stats.first_interaction:
                    self.stats.first_interaction = datetime.now().isoformat()
                self.stats.last_interaction = datetime.now().isoformat()
                
            self.save_profile()
            self.stats_updated.emit(self.stats.to_dict())
            self.logger.debug("Statistics updated")
            
        except Exception as e:
            self.logger.error(f"Failed to update statistics: {e}")
            
    def get_stats(self) -> UserStats:
        """Get current user statistics"""
        return self.stats
        
    def add_interest(self, interest: str):
        """Add an interest to the user profile"""
        if interest and interest not in self.interests:
            self.interests.append(interest)
            self.save_profile()
            self.logger.info(f"Added interest: {interest}")
            
    def remove_interest(self, interest: str):
        """Remove an interest from the user profile"""
        if interest in self.interests:
            self.interests.remove(interest)
            self.save_profile()
            self.logger.info(f"Removed interest: {interest}")
            
    def add_tag(self, tag: str):
        """Add a tag to the user profile"""
        if tag and tag not in self.tags:
            self.tags.append(tag)
            self.save_profile()
            self.logger.info(f"Added tag: {tag}")
            
    def remove_tag(self, tag: str):
        """Remove a tag from the user profile"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.save_profile()
            self.logger.info(f"Removed tag: {tag}")
            
    def set_username(self, username: str):
        """Set the username"""
        if username:
            self.username = username
            self.save_profile()
            self.logger.info(f"Username updated to: {username}")
            
    def set_notes(self, notes: str):
        """Set profile notes"""
        self.notes = notes
        self.save_profile()
        self.logger.info("Profile notes updated")
        
    def get_profile_summary(self) -> Dict[str, Any]:
        """Get a summary of the user profile"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'created_at': self.created_at,
            'last_active': self.last_active,
            'total_interactions': self.stats.total_interactions,
            'interests_count': len(self.interests),
            'main_interests': self.interests[:3],
            'response_style': self.preferences.response_style,
            'ai_enabled': self.preferences.ai_enabled,
            'days_since_creation': self._calculate_days_since_creation()
        }
        
    def _calculate_days_since_creation(self) -> int:
        """Calculate days since profile creation"""
        if not self.created_at:
            return 0
            
        try:
            created = datetime.fromisoformat(self.created_at)
            now = datetime.now()
            return (now - created).days
        except:
            return 0
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'created_at': self.created_at,
            'last_active': self.last_active,
            'profile_version': self.profile_version,
            'interests': self.interests,
            'tags': self.tags,
            'notes': self.notes,
            'preferences': self.preferences.to_dict(),
            'stats': self.stats.to_dict()
        }
        
    def backup_profile(self, backup_path: Optional[str] = None) -> str:
        """Create a backup of the user profile"""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = Path(settings.BASEDIR) / 'DyberPet' / 'data' / f'profile_backup_{timestamp}.json'
            
        try:
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"Profile backup created: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"Failed to create profile backup: {e}")
            return ""
            
    def restore_profile(self, backup_path: str) -> bool:
        """Restore profile from backup"""
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Restore basic profile data
            self.user_id = data.get('user_id', self.user_id)
            self.username = data.get('username', self.username)
            self.created_at = data.get('created_at', self.created_at)
            self.profile_version = data.get('profile_version', self.profile_version)
            self.interests = data.get('interests', self.interests)
            self.tags = data.get('tags', self.tags)
            self.notes = data.get('notes', self.notes)
            
            # Restore preferences
            if 'preferences' in data:
                self.preferences = UserPreferences.from_dict(data['preferences'])
                
            # Restore statistics
            if 'stats' in data:
                self.stats = UserStats.from_dict(data['stats'])
                
            # Save restored profile
            self.save_profile()
            
            self.logger.info(f"Profile restored from backup: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore profile from backup: {e}")
            return False
            
    def reset_profile(self):
        """Reset profile to default state"""
        # Keep user_id and creation time
        user_id = self.user_id
        created_at = self.created_at
        
        # Reset everything else
        self._create_default_profile()
        
        # Restore original ID and creation time
        self.user_id = user_id
        self.created_at = created_at
        
        self.save_profile()
        self.logger.info("Profile reset to default state")
        
    def get_usage_analytics(self) -> Dict[str, Any]:
        """Get usage analytics based on profile data"""
        analytics = {
            'profile_age_days': self._calculate_days_since_creation(),
            'total_interactions': self.stats.total_interactions,
            'interactions_per_day': 0,
            'most_used_features': [],
            'feedback_ratio': 0,
            'engagement_level': 'unknown'
        }
        
        # Calculate interactions per day
        if analytics['profile_age_days'] > 0:
            analytics['interactions_per_day'] = self.stats.total_interactions / analytics['profile_age_days']
            
        # Get most used features
        if self.stats.features_used:
            sorted_features = sorted(self.stats.features_used.items(), key=lambda x: x[1], reverse=True)
            analytics['most_used_features'] = sorted_features[:5]
            
        # Calculate feedback ratio
        total_feedback = self.stats.positive_feedback + self.stats.negative_feedback + self.stats.neutral_feedback
        if total_feedback > 0:
            analytics['feedback_ratio'] = self.stats.positive_feedback / total_feedback
            
        # Determine engagement level
        if analytics['interactions_per_day'] > 10:
            analytics['engagement_level'] = 'high'
        elif analytics['interactions_per_day'] > 3:
            analytics['engagement_level'] = 'medium'
        elif analytics['interactions_per_day'] > 0:
            analytics['engagement_level'] = 'low'
            
        return analytics
        
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled in user preferences"""
        feature_map = {
            'ai': self.preferences.ai_enabled,
            'proactive': self.preferences.proactive_enabled,
            'emotions': self.preferences.emotion_animations,
            'personalization': self.preferences.personalization_enabled,
            'learning': self.preferences.learning_enabled,
            'data_collection': self.preferences.data_collection,
            'profile_building': self.preferences.profile_building,
            'feedback_learning': self.preferences.learning_from_feedback
        }
        
        return feature_map.get(feature, False)
        
    def record_feature_usage(self, feature: str):
        """Record usage of a feature"""
        if feature not in self.stats.features_used:
            self.stats.features_used[feature] = 0
            
        self.stats.features_used[feature] += 1
        
        # Update stats periodically to avoid too frequent saves
        if sum(self.stats.features_used.values()) % 10 == 0:
            self.update_stats({})