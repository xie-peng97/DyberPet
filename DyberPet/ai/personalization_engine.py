"""
PersonalizationEngine - Handles user profiling and response customization (FR-2.3)

This module manages personalization including:
- User profile construction from chat history
- Dynamic prompt adjustment based on user preferences
- Response style adaptation
- Interest and preference tracking
"""

import json
import logging
import re
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import random

from PySide6.QtCore import QObject, Signal
import DyberPet.settings as settings


@dataclass
class PersonalizationUserProfile:
    """User profile data structure for personalization"""
    interests: List[str]
    communication_style: str  # 'formal', 'casual', 'funny', 'caring'
    activity_pattern: Dict[str, any]
    emotional_preferences: Dict[str, float]
    preferred_topics: List[str]
    response_style_preferences: Dict[str, float]
    last_updated: str
    interaction_count: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'PersonalizationUserProfile':
        """Create from dictionary"""
        return cls(**data)


class PersonalizationEngine(QObject):
    """Manages user personalization and response customization"""
    
    # Signals
    profile_updated = Signal(dict)  # user_profile
    style_adapted = Signal(str)  # adapted_style
    preferences_changed = Signal(dict)  # preferences
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # Initialize user profile
        self.user_profile = self._load_user_profile()
        
        # Style templates
        self.style_templates = {
            'formal': {
                'greeting': '您好，',
                'pronouns': '您',
                'ending': '请问还有什么需要帮助的吗？',
                'tone': 'respectful'
            },
            'casual': {
                'greeting': '嗨，',
                'pronouns': '你',
                'ending': '还有什么想聊的吗？',
                'tone': 'friendly'
            },
            'funny': {
                'greeting': '哈喽，',
                'pronouns': '你',
                'ending': '还有什么有趣的事情吗？😄',
                'tone': 'humorous'
            },
            'caring': {
                'greeting': '亲爱的主人，',
                'pronouns': '主人',
                'ending': '我会一直陪伴你的哦～',
                'tone': 'affectionate'
            }
        }
        
        # Interest keywords for analysis
        self.interest_keywords = {
            'technology': ['编程', '代码', '技术', '电脑', '软件', '开发', '互联网', 'AI', '人工智能'],
            'gaming': ['游戏', '玩', '通关', '角色', '战斗', '升级', '装备', '副本'],
            'anime': ['动漫', '番剧', '动画', '漫画', '二次元', '声优', '角色', '萌'],
            'music': ['音乐', '歌', '唱', '乐器', '演奏', '歌手', '旋律', '节奏'],
            'sports': ['运动', '锻炼', '健身', '跑步', '游泳', '球类', '比赛', '训练'],
            'food': ['美食', '做饭', '菜', '料理', '餐厅', '味道', '食谱', '小吃'],
            'travel': ['旅行', '旅游', '出游', '景点', '风景', '城市', '国家', '假期'],
            'study': ['学习', '考试', '作业', '课程', '知识', '书', '研究', '学校'],
            'work': ['工作', '职业', '公司', '同事', '项目', '任务', '会议', '忙']
        }
        
        # Communication style indicators
        self.style_indicators = {
            'formal': ['请', '您', '谢谢', '不好意思', '打扰', '恳请'],
            'casual': ['哈哈', '嗯', '呃', '嗨', '好的', '行'],
            'funny': ['哈哈', '笑', '搞笑', '有趣', '好玩', '逗', '幽默'],
            'caring': ['关心', '照顾', '温暖', '贴心', '舒服', '安慰', '陪伴']
        }
        
    def _load_user_profile(self) -> PersonalizationUserProfile:
        """Load user profile from storage"""
        profile_file = Path(settings.BASEDIR) / 'DyberPet' / 'data' / 'user_profile.json'
        
        if profile_file.exists():
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return PersonalizationUserProfile.from_dict(data)
            except Exception as e:
                self.logger.warning(f"Failed to load user profile: {e}")
                
        # Create default profile
        return PersonalizationUserProfile(
            interests=[],
            communication_style='casual',
            activity_pattern={
                'active_hours': [9, 22],
                'preferred_interaction_frequency': 'medium',
                'peak_activity_times': []
            },
            emotional_preferences={
                'humor_level': 0.7,
                'formality': 0.3,
                'supportiveness': 0.8,
                'playfulness': 0.6
            },
            preferred_topics=[],
            response_style_preferences={
                'length': 0.5,  # 0=short, 1=long
                'emoji_usage': 0.7,
                'question_frequency': 0.4
            },
            last_updated=datetime.now().isoformat(),
            interaction_count=0
        )
        
    def _save_user_profile(self):
        """Save user profile to storage"""
        profile_file = Path(settings.BASEDIR) / 'DyberPet' / 'data' / 'user_profile.json'
        profile_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_profile.to_dict(), f, ensure_ascii=False, indent=2)
            self.logger.debug("User profile saved successfully")
        except Exception as e:
            self.logger.error(f"Failed to save user profile: {e}")
            
    def build_user_profile(self, chat_history: List[Dict[str, str]]):
        """Build user profile from chat history"""
        if not chat_history:
            return
            
        # Extract user messages
        user_messages = [msg['content'] for msg in chat_history if msg['role'] == 'user']
        
        if not user_messages:
            return
            
        # Analyze interests
        new_interests = self._analyze_interests(user_messages)
        
        # Analyze communication style
        new_style = self._analyze_communication_style(user_messages)
        
        # Analyze activity patterns
        new_activity = self._analyze_activity_patterns(chat_history)
        
        # Update profile
        self.user_profile.interests = list(set(self.user_profile.interests + new_interests))
        self.user_profile.communication_style = new_style
        self.user_profile.activity_pattern.update(new_activity)
        self.user_profile.last_updated = datetime.now().isoformat()
        self.user_profile.interaction_count += len(user_messages)
        
        # Save profile
        self._save_user_profile()
        
        # Emit signal
        self.profile_updated.emit(self.user_profile.to_dict())
        
        self.logger.info(f"User profile updated with {len(new_interests)} new interests")
        
    def _analyze_interests(self, messages: List[str]) -> List[str]:
        """Analyze user interests from messages"""
        interests = []
        combined_text = ' '.join(messages).lower()
        
        for interest, keywords in self.interest_keywords.items():
            score = sum(combined_text.count(keyword) for keyword in keywords)
            if score >= 2:  # Threshold for interest detection
                interests.append(interest)
                
        return interests
        
    def _analyze_communication_style(self, messages: List[str]) -> str:
        """Analyze user communication style"""
        style_scores = defaultdict(int)
        combined_text = ' '.join(messages).lower()
        
        for style, indicators in self.style_indicators.items():
            score = sum(combined_text.count(indicator) for indicator in indicators)
            style_scores[style] = score
            
        # Return most frequent style, default to casual
        return max(style_scores, key=style_scores.get) if style_scores else 'casual'
        
    def _analyze_activity_patterns(self, chat_history: List[Dict[str, str]]) -> Dict:
        """Analyze user activity patterns"""
        if not chat_history:
            return {}
            
        # Extract timestamps if available
        timestamps = []
        for msg in chat_history:
            if 'timestamp' in msg:
                try:
                    timestamp = datetime.fromisoformat(msg['timestamp'])
                    timestamps.append(timestamp)
                except:
                    pass
                    
        if not timestamps:
            return {}
            
        # Analyze active hours
        hours = [ts.hour for ts in timestamps]
        hour_counts = Counter(hours)
        
        # Find peak activity times
        peak_hours = [hour for hour, count in hour_counts.most_common(3)]
        
        # Determine active period
        if hours:
            active_start = min(hours)
            active_end = max(hours)
        else:
            active_start, active_end = 9, 22
            
        return {
            'active_hours': [active_start, active_end],
            'peak_activity_times': peak_hours,
            'total_interactions': len(timestamps)
        }
        
    def customize_prompt(self, base_prompt: str, user_profile: Optional[PersonalizationUserProfile] = None) -> str:
        """Customize prompt based on user profile"""
        profile = user_profile or self.user_profile
        
        # Build personalization context
        context_parts = []
        
        # Add interests
        if profile.interests:
            interests_str = ', '.join(profile.interests)
            context_parts.append(f"用户感兴趣的话题: {interests_str}")
            
        # Add communication style
        style_template = self.style_templates.get(profile.communication_style, self.style_templates['casual'])
        context_parts.append(f"用户偏好的交流风格: {profile.communication_style}")
        
        # Add emotional preferences
        if profile.emotional_preferences:
            humor_level = profile.emotional_preferences.get('humor_level', 0.5)
            if humor_level > 0.7:
                context_parts.append("用户喜欢幽默有趣的对话")
            elif humor_level < 0.3:
                context_parts.append("用户偏好严肃正式的对话")
                
        # Combine with base prompt
        if context_parts:
            context = '\n'.join(context_parts)
            customized_prompt = f"{base_prompt}\n\n## 用户个性化信息:\n{context}\n\n请根据以上信息调整你的回复风格和内容。"
        else:
            customized_prompt = base_prompt
            
        return customized_prompt
        
    def adapt_response_style(self, response: str, user_style: Optional[str] = None) -> str:
        """Adapt response based on user style preferences"""
        style = user_style or self.user_profile.communication_style
        style_template = self.style_templates.get(style, self.style_templates['casual'])
        
        # Apply style adaptations
        adapted_response = response
        
        # Adjust pronouns
        if style == 'formal':
            adapted_response = re.sub(r'\b你\b', '您', adapted_response)
        elif style == 'caring':
            adapted_response = re.sub(r'\b你\b', '主人', adapted_response)
            
        # Add style-specific elements
        if style == 'funny' and random.random() < 0.3:
            # Add occasional funny elements
            funny_elements = ['😄', '哈哈', '(｡◕‿◕｡)', '(￣▽￣)']
            adapted_response += ' ' + random.choice(funny_elements)
            
        # Adjust emoji usage based on preferences
        emoji_pref = self.user_profile.response_style_preferences.get('emoji_usage', 0.7)
        if emoji_pref < 0.3:
            # Remove some emojis
            adapted_response = re.sub(r'[😀-🙿🌀-🗿🚀-🛿]', '', adapted_response)
            
        self.style_adapted.emit(style)
        return adapted_response
        
    def update_preferences(self, feedback: Dict[str, any]):
        """Update user preferences based on feedback"""
        if 'style_preference' in feedback:
            self.user_profile.communication_style = feedback['style_preference']
            
        if 'emotional_preferences' in feedback:
            self.user_profile.emotional_preferences.update(feedback['emotional_preferences'])
            
        if 'response_style_preferences' in feedback:
            self.user_profile.response_style_preferences.update(feedback['response_style_preferences'])
            
        # Update timestamp
        self.user_profile.last_updated = datetime.now().isoformat()
        
        # Save changes
        self._save_user_profile()
        
        # Emit signal
        self.preferences_changed.emit(self.user_profile.to_dict())
        
        self.logger.info("User preferences updated")
        
    def get_personalized_topics(self) -> List[str]:
        """Get personalized conversation topics based on user profile"""
        topics = []
        
        # Add topics based on interests
        interest_topics = {
            'technology': ['最新的科技发展', '编程技巧', '新的软件工具'],
            'gaming': ['最近在玩什么游戏', '游戏攻略', '有趣的游戏体验'],
            'anime': ['推荐的动漫', '最新番剧', '喜欢的角色'],
            'music': ['最近听的音乐', '喜欢的歌手', '音乐推荐'],
            'sports': ['运动心得', '健身计划', '体育赛事'],
            'food': ['美食分享', '烹饪技巧', '新的餐厅'],
            'travel': ['旅行经历', '想去的地方', '旅游攻略'],
            'study': ['学习进展', '有趣的知识', '学习方法'],
            'work': ['工作近况', '职业发展', '工作心得']
        }
        
        for interest in self.user_profile.interests:
            if interest in interest_topics:
                topics.extend(interest_topics[interest])
                
        # Add general topics if no specific interests
        if not topics:
            topics = ['今天的心情', '最近的生活', '有趣的事情', '未来的计划']
            
        return topics[:5]  # Return top 5 topics
        
    def get_user_profile(self) -> PersonalizationUserProfile:
        """Get current user profile"""
        return self.user_profile
        
    def reset_user_profile(self):
        """Reset user profile to default"""
        self.user_profile = self._load_user_profile()
        self._save_user_profile()
        self.profile_updated.emit(self.user_profile.to_dict())
        self.logger.info("User profile reset to default")
        
    def get_profile_summary(self) -> Dict[str, any]:
        """Get a summary of the user profile"""
        return {
            'total_interactions': self.user_profile.interaction_count,
            'interests_count': len(self.user_profile.interests),
            'communication_style': self.user_profile.communication_style,
            'last_updated': self.user_profile.last_updated,
            'main_interests': self.user_profile.interests[:3],
            'active_hours': self.user_profile.activity_pattern.get('active_hours', [9, 22])
        }