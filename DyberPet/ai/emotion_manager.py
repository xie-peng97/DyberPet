"""
EmotionManager - Handles emotion analysis and animation triggering (FR-2.2)

This module manages emotion-based animations including:
- Emotion analysis from AI responses
- Animation selection based on emotion and intensity
- Integration with DyberPet animation system
- Emotion keyword matching for Chinese text
"""

import re
import json
import logging
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, Signal
import DyberPet.settings as settings


@dataclass
class EmotionData:
    """Data structure for emotion analysis results"""
    primary_emotion: str
    intensity: float  # 0.0 to 1.0
    keywords: List[str]
    animation_name: str
    duration: float


class EmotionManager(QObject):
    """Manages emotion analysis and animation triggering"""
    
    # Signals
    emotion_animation_triggered = Signal(str, dict)  # animation_name, emotion_data
    emotion_detected = Signal(str, float)  # emotion, intensity
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # Emotion keyword mappings
        self.emotion_keywords = self._load_emotion_keywords()
        
        # Animation mappings
        self.emotion_animations = {
            'happy': ['happy_dance', 'wavehand', 'bounce'],
            'sad': ['cry', 'disappointed', 'sigh'],
            'excited': ['happy_dance', 'bounce', 'celebrate'],
            'angry': ['angry_shake', 'stomp', 'mad'],
            'surprised': ['shocked', 'gasp', 'wow'],
            'confused': ['confused_tilt', 'scratch_head', 'question'],
            'sleepy': ['yawn', 'tired', 'sleep'],
            'love': ['heart_eyes', 'blush', 'kiss'],
            'shy': ['blush', 'hide', 'embarrassed'],
            'default': ['idle', 'blink', 'normal']
        }
        
        # Intensity thresholds for animation selection
        self.intensity_thresholds = {
            'low': 0.3,
            'medium': 0.6,
            'high': 1.0
        }
        
    def _load_emotion_keywords(self) -> Dict[str, List[str]]:
        """Load emotion keywords from configuration"""
        default_keywords = {
            'happy': [
                '开心', '高兴', '快乐', '愉快', '欢乐', '兴奋', '喜悦', '满足',
                '太棒了', '好棒', '真好', '很好', '不错', '赞', '哈哈', '呵呵',
                '😊', '😄', '😁', '🤗', '😍', '🥰', '😘', '🎉', '✨'
            ],
            'sad': [
                '难过', '伤心', '失望', '沮丧', '郁闷', '不开心', '痛苦', '委屈',
                '哭', '想哭', '眼泪', '泪水', '心疼', '心酸', '遗憾', '可惜',
                '😢', '😭', '😔', '😞', '💔', '😿', '🥺', '😪'
            ],
            'excited': [
                '兴奋', '激动', '狂欢', '嗨', '燃', '爽', '刺激', '振奋',
                '太棒了', 'amazing', '超级', '非常', '极其', '超', '特别',
                '🔥', '💥', '⚡', '🚀', '🎊', '🎈', '🌟', '✨'
            ],
            'angry': [
                '生气', '愤怒', '气愤', '恼火', '火大', '抓狂', '暴躁', '烦躁',
                '讨厌', '恶心', '烦', '气死了', '可恶', '该死', '混蛋',
                '😠', '😡', '🤬', '👿', '😤', '💢', '🔥', '💥'
            ],
            'surprised': [
                '惊讶', '吃惊', '震惊', '意外', '没想到', '天哪', '哇', '咦',
                '竟然', '居然', '不会吧', '真的假的', '我的天', '厉害',
                '😲', '😱', '🤯', '😳', '🙀', '😵', '🤭', '😮'
            ],
            'confused': [
                '困惑', '疑惑', '不懂', '不明白', '搞不懂', '奇怪', '纳闷', '迷茫',
                '什么', '为什么', '怎么回事', '怎么办', '不知道', '不清楚',
                '😕', '🤔', '😵‍💫', '😐', '🤷', '❓', '❔', '🤨'
            ],
            'sleepy': [
                '困', '累', '疲惫', '想睡', '睡觉', '打盹', '瞌睡', '疲倦',
                '休息', '睡眠', '床', '枕头', '梦', '晚安', '好累', '没精神',
                '😴', '😪', '🥱', '💤', '🛏️', '🌙', '💤'
            ],
            'love': [
                '爱', '喜欢', '爱你', '喜爱', '心动', '浪漫', '甜蜜', '温暖',
                '亲爱的', '宝贝', '可爱', '萌', '心', '爱心', 'kiss',
                '❤️', '💕', '💖', '💗', '💝', '💘', '😍', '🥰', '😘', '💋'
            ],
            'shy': [
                '害羞', '不好意思', '脸红', '羞涩', '腼腆', '紧张', '尴尬', '不好意思',
                '谢谢', '不敢', '不行', '太过分了', '讨厌', '人家',
                '😊', '😌', '🤭', '😳', '🙈', '🫣', '☺️', '😚'
            ]
        }
        
        # Try to load from YAML file if it exists
        keywords_file = Path(settings.BASEDIR) / 'DyberPet' / 'data' / 'emotion_keywords.yaml'
        if keywords_file.exists():
            try:
                import yaml
                with open(keywords_file, 'r', encoding='utf-8') as f:
                    loaded_keywords = yaml.safe_load(f)
                    if loaded_keywords:
                        return loaded_keywords
            except Exception as e:
                self.logger.warning(f"Failed to load emotion keywords from YAML: {e}")
                
        return default_keywords
        
    def analyze_emotion(self, text: str) -> EmotionData:
        """Analyze emotion from text and return emotion data"""
        if not text:
            return self._create_default_emotion()
            
        # Clean text
        text = text.lower().strip()
        
        # Find emotion matches
        emotion_scores = {}
        found_keywords = []
        
        for emotion, keywords in self.emotion_keywords.items():
            score = 0
            emotion_keywords = []
            
            for keyword in keywords:
                # Count occurrences of each keyword
                count = text.count(keyword.lower())
                if count > 0:
                    score += count
                    emotion_keywords.extend([keyword] * count)
                    
            if score > 0:
                emotion_scores[emotion] = score
                found_keywords.extend(emotion_keywords)
                
        # Determine primary emotion
        if not emotion_scores:
            return self._create_default_emotion()
            
        primary_emotion = max(emotion_scores, key=emotion_scores.get)
        max_score = emotion_scores[primary_emotion]
        
        # Calculate intensity based on score and text length
        text_length = len(text)
        intensity = min(max_score / max(text_length / 20, 1), 1.0)
        
        # Select animation
        animation_name = self.select_animation(primary_emotion, intensity)
        
        # Calculate duration
        duration = self._calculate_animation_duration(intensity)
        
        emotion_data = EmotionData(
            primary_emotion=primary_emotion,
            intensity=intensity,
            keywords=found_keywords[:5],  # Limit to 5 keywords
            animation_name=animation_name,
            duration=duration
        )
        
        self.logger.debug(f"Emotion analysis: {primary_emotion} (intensity: {intensity:.2f})")
        self.emotion_detected.emit(primary_emotion, intensity)
        
        return emotion_data
        
    def select_animation(self, emotion: str, intensity: float) -> str:
        """Select appropriate animation based on emotion and intensity"""
        animations = self.emotion_animations.get(emotion, self.emotion_animations['default'])
        
        # Filter animations by intensity
        if intensity >= self.intensity_thresholds['high']:
            # High intensity - prefer more dramatic animations
            preferred_animations = [anim for anim in animations if any(keyword in anim for keyword in ['dance', 'bounce', 'shake', 'celebrate'])]
            if preferred_animations:
                animations = preferred_animations
        elif intensity <= self.intensity_thresholds['low']:
            # Low intensity - prefer subtle animations
            preferred_animations = [anim for anim in animations if any(keyword in anim for keyword in ['blink', 'idle', 'normal', 'tilt'])]
            if preferred_animations:
                animations = preferred_animations
                
        return random.choice(animations)
        
    def trigger_emotion_animation(self, emotion_data: EmotionData):
        """Trigger emotion-based animation"""
        try:
            animation_dict = {
                'name': emotion_data.animation_name,
                'emotion': emotion_data.primary_emotion,
                'intensity': emotion_data.intensity,
                'duration': emotion_data.duration,
                'keywords': emotion_data.keywords
            }
            
            self.emotion_animation_triggered.emit(emotion_data.animation_name, animation_dict)
            self.logger.info(f"Emotion animation triggered: {emotion_data.animation_name} for {emotion_data.primary_emotion}")
            
        except Exception as e:
            self.logger.error(f"Failed to trigger emotion animation: {e}")
            
    def process_ai_response(self, response_text: str) -> Optional[EmotionData]:
        """Process AI response and trigger emotion animation if needed"""
        emotion_data = self.analyze_emotion(response_text)
        
        # Only trigger animation if emotion is strong enough
        if emotion_data.intensity >= 0.2:  # Minimum threshold
            self.trigger_emotion_animation(emotion_data)
            return emotion_data
            
        return None
        
    def _create_default_emotion(self) -> EmotionData:
        """Create default emotion data for neutral responses"""
        return EmotionData(
            primary_emotion='default',
            intensity=0.1,
            keywords=[],
            animation_name='idle',
            duration=2.0
        )
        
    def _calculate_animation_duration(self, intensity: float) -> float:
        """Calculate animation duration based on intensity"""
        # Base duration between 1.5 and 4.5 seconds
        base_duration = 2.0
        intensity_factor = intensity * 2.5
        return max(1.5, min(base_duration + intensity_factor, 4.5))
        
    def get_emotion_keywords(self) -> Dict[str, List[str]]:
        """Get the current emotion keywords dictionary"""
        return self.emotion_keywords.copy()
        
    def add_emotion_keyword(self, emotion: str, keyword: str):
        """Add a new keyword to an emotion category"""
        if emotion not in self.emotion_keywords:
            self.emotion_keywords[emotion] = []
            
        if keyword not in self.emotion_keywords[emotion]:
            self.emotion_keywords[emotion].append(keyword)
            self.logger.debug(f"Added keyword '{keyword}' to emotion '{emotion}'")
            
    def remove_emotion_keyword(self, emotion: str, keyword: str):
        """Remove a keyword from an emotion category"""
        if emotion in self.emotion_keywords and keyword in self.emotion_keywords[emotion]:
            self.emotion_keywords[emotion].remove(keyword)
            self.logger.debug(f"Removed keyword '{keyword}' from emotion '{emotion}'")
            
    def get_animation_mapping(self) -> Dict[str, List[str]]:
        """Get the current emotion to animation mapping"""
        return self.emotion_animations.copy()
        
    def update_animation_mapping(self, emotion: str, animations: List[str]):
        """Update the animation mapping for an emotion"""
        self.emotion_animations[emotion] = animations
        self.logger.info(f"Updated animation mapping for emotion '{emotion}': {animations}")
        
    def get_statistics(self) -> Dict:
        """Get emotion detection statistics"""
        return {
            'total_emotions': len(self.emotion_keywords),
            'total_animations': len(self.emotion_animations),
            'emotion_categories': list(self.emotion_keywords.keys()),
            'animation_categories': list(self.emotion_animations.keys())
        }