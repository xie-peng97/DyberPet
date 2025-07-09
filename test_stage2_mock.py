#!/usr/bin/env python3
"""
Mock test for DyberPet AI Stage 2 modules
Tests basic functionality without requiring PySide6 or full DyberPet environment
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock PySide6 modules
class MockSignal:
    def __init__(self, *args, **kwargs):
        pass
    def connect(self, slot):
        pass
    def emit(self, *args):
        pass

class MockQObject:
    def __init__(self, parent=None):
        self.parent = parent

class MockQTimer:
    def __init__(self):
        pass
    def start(self, interval):
        pass
    def stop(self):
        pass
    def setSingleShot(self, single):
        pass

# Mock PySide6 before importing our modules
sys.modules['PySide6'] = type(sys)('PySide6')
sys.modules['PySide6.QtCore'] = type(sys)('PySide6.QtCore')
sys.modules['PySide6.QtWidgets'] = type(sys)('PySide6.QtWidgets')

# Add mocks to the modules
sys.modules['PySide6.QtCore'].QObject = MockQObject
sys.modules['PySide6.QtCore'].Signal = MockSignal
sys.modules['PySide6.QtCore'].QTimer = MockQTimer
sys.modules['PySide6.QtWidgets'].QApplication = MockQObject

# Mock apscheduler
class MockScheduler:
    def start(self):
        pass
    def add_job(self, *args, **kwargs):
        pass
    def remove_job(self, job_id):
        pass
    def remove_all_jobs(self):
        pass

sys.modules['apscheduler'] = type(sys)('apscheduler')
sys.modules['apscheduler.schedulers'] = type(sys)('apscheduler.schedulers')
sys.modules['apscheduler.schedulers.qt'] = type(sys)('apscheduler.schedulers.qt')
sys.modules['apscheduler.triggers'] = type(sys)('apscheduler.triggers')
sys.modules['apscheduler.schedulers.qt'].QtScheduler = MockScheduler
sys.modules['apscheduler.triggers'].interval = type(sys)('interval')
sys.modules['apscheduler.triggers'].date = type(sys)('date')
sys.modules['apscheduler.triggers'].cron = type(sys)('cron')

# Mock settings module
class MockSettings:
    BASEDIR = '/tmp/test'
    pet_data = type('obj', (object,), {'hp_tier': 2, 'fv_tier': 2})()
    petname = 'TestPet'

sys.modules['DyberPet.settings'] = MockSettings

def test_emotion_analysis():
    """Test emotion analysis functionality"""
    try:
        from DyberPet.ai.emotion_manager import EmotionManager
        
        emotion_manager = EmotionManager()
        
        # Test happy emotion
        happy_text = "我很开心！今天太棒了！😊"
        emotion_data = emotion_manager.analyze_emotion(happy_text)
        
        assert emotion_data.primary_emotion == 'happy'
        assert emotion_data.intensity > 0
        assert len(emotion_data.keywords) > 0
        
        print("✓ Happy emotion analysis test passed")
        
        # Test sad emotion
        sad_text = "我很难过，感觉很失望 😢"
        sad_emotion = emotion_manager.analyze_emotion(sad_text)
        
        assert sad_emotion.primary_emotion == 'sad'
        assert sad_emotion.intensity > 0
        
        print("✓ Sad emotion analysis test passed")
        
        # Test animation selection
        animation = emotion_manager.select_animation('happy', 0.8)
        assert animation in emotion_manager.emotion_animations['happy']
        
        print("✓ Animation selection test passed")
        
        return True
        
    except Exception as e:
        print(f"✗ Emotion analysis test failed: {e}")
        return False

def test_personalization():
    """Test personalization functionality"""
    try:
        from DyberPet.ai.personalization_engine import PersonalizationEngine
        
        personalization = PersonalizationEngine()
        
        # Test interest analysis
        messages = [
            "我喜欢编程和写代码",
            "最近在玩一个很有趣的游戏",
            "我是个程序员，工作很忙"
        ]
        
        interests = personalization._analyze_interests(messages)
        assert 'technology' in interests
        assert 'gaming' in interests
        
        print("✓ Interest analysis test passed")
        
        # Test communication style analysis
        formal_messages = ["请问您好，谢谢您的帮助"]
        style = personalization._analyze_communication_style(formal_messages)
        assert style == 'formal'
        
        casual_messages = ["哈哈，好的，行"]
        style = personalization._analyze_communication_style(casual_messages)
        assert style == 'casual'
        
        print("✓ Communication style analysis test passed")
        
        # Test prompt customization
        base_prompt = "你是一个桌面宠物"
        customized = personalization.customize_prompt(base_prompt)
        assert len(customized) >= len(base_prompt)
        
        print("✓ Prompt customization test passed")
        
        return True
        
    except Exception as e:
        print(f"✗ Personalization test failed: {e}")
        return False

def test_learning_system():
    """Test learning system functionality"""
    try:
        from DyberPet.ai.learning_system import LearningSystem, FeedbackType
        
        learning = LearningSystem()
        
        # Test feedback collection
        learning.collect_feedback("msg_001", FeedbackType.LIKE.value, {
            "response_text": "测试回复",
            "emotion": "happy"
        })
        
        assert len(learning.feedback_records) > 0
        assert learning.feedback_records[0].feedback_type == FeedbackType.LIKE.value
        
        print("✓ Feedback collection test passed")
        
        # Test behavior parameters
        params = learning.get_behavior_parameters()
        assert hasattr(params, 'proactive_frequency')
        assert hasattr(params, 'emotion_sensitivity')
        
        print("✓ Behavior parameters test passed")
        
        # Test parameter updates
        original_freq = params.proactive_frequency
        learning.update_behavior_parameters({'proactive_frequency': 60.0})
        updated_params = learning.get_behavior_parameters()
        assert updated_params.proactive_frequency == 60.0
        
        print("✓ Parameter updates test passed")
        
        return True
        
    except Exception as e:
        print(f"✗ Learning system test failed: {e}")
        return False

def test_proactive_manager():
    """Test proactive manager functionality"""
    try:
        from DyberPet.ai.proactive_manager import ProactiveManager
        
        proactive = ProactiveManager()
        
        # Test message generation
        from DyberPet.ai.proactive_manager import ProactiveContext
        context = ProactiveContext(
            trigger_type='time',
            time_of_day='morning',
            pet_status={'hp_tier': 2, 'fv_tier': 3},
            user_activity={},
            last_interaction=None,
            interaction_count=0
        )
        
        message = proactive.generate_proactive_message(context)
        assert isinstance(message, str)
        assert len(message) > 0
        
        print("✓ Message generation test passed")
        
        # Test frequency updates
        original_freq = proactive.current_frequency
        proactive.update_interaction_frequency('too_frequent')
        assert proactive.current_frequency > original_freq
        
        proactive.update_interaction_frequency('too_rare')
        assert proactive.current_frequency < original_freq
        
        print("✓ Frequency updates test passed")
        
        return True
        
    except Exception as e:
        print(f"✗ Proactive manager test failed: {e}")
        return False

def test_user_profile():
    """Test user profile functionality"""
    try:
        from DyberPet.ai.user_profile import UserProfile, UserPreferences
        
        profile = UserProfile()
        
        # Test preferences
        assert isinstance(profile.preferences, UserPreferences)
        assert profile.preferences.ai_enabled == True
        
        print("✓ User profile initialization test passed")
        
        # Test preference updates
        profile.update_preferences({
            'response_style': 'funny',
            'proactive_enabled': False
        })
        
        assert profile.preferences.response_style == 'funny'
        assert profile.preferences.proactive_enabled == False
        
        print("✓ Preference updates test passed")
        
        # Test stats updates
        profile.update_stats({
            'total_interactions': 5,
            'positive_feedback': 3
        })
        
        assert profile.stats.total_interactions == 5
        assert profile.stats.positive_feedback == 3
        
        print("✓ Stats updates test passed")
        
        return True
        
    except Exception as e:
        print(f"✗ User profile test failed: {e}")
        return False

def main():
    """Run all mock tests"""
    print("Running DyberPet AI Stage 2 Mock Tests...")
    print("=" * 50)
    
    tests = [
        test_emotion_analysis,
        test_personalization,
        test_learning_system,
        test_proactive_manager,
        test_user_profile
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Stage 2 modules are working correctly.")
    else:
        print(f"⚠️  {failed} tests failed. Please check the implementation.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)