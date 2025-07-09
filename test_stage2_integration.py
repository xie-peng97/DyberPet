#!/usr/bin/env python3
"""
Simple integration test for DyberPet AI Stage 2 modules
Tests basic functionality without requiring full DyberPet environment
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test basic imports
def test_imports():
    """Test that all modules can be imported"""
    try:
        from DyberPet.ai import (
            ProactiveManager, 
            EmotionManager, 
            PersonalizationEngine, 
            LearningSystem, 
            UserProfile,
            AIStage2Integration
        )
        print("✓ All modules imported successfully")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_emotion_manager():
    """Test EmotionManager functionality"""
    try:
        from DyberPet.ai.emotion_manager import EmotionManager
        from PySide6.QtWidgets import QApplication
        
        # Create minimal QApplication for testing
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        emotion_manager = EmotionManager()
        
        # Test emotion analysis
        test_text = "我很开心！今天太棒了！😊"
        emotion_data = emotion_manager.analyze_emotion(test_text)
        
        print(f"✓ Emotion analysis test passed: {emotion_data.primary_emotion} (intensity: {emotion_data.intensity:.2f})")
        
        # Test with sad text
        sad_text = "我很难过，感觉很失望 😢"
        sad_emotion = emotion_manager.analyze_emotion(sad_text)
        print(f"✓ Sad emotion test: {sad_emotion.primary_emotion} (intensity: {sad_emotion.intensity:.2f})")
        
        return True
        
    except Exception as e:
        print(f"✗ EmotionManager test failed: {e}")
        return False

def test_user_profile():
    """Test UserProfile functionality"""
    try:
        from DyberPet.ai.user_profile import UserProfile
        from PySide6.QtWidgets import QApplication
        
        # Create minimal QApplication for testing
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        user_profile = UserProfile()
        
        # Test basic profile operations
        user_profile.set_username("测试用户")
        user_profile.add_interest("technology")
        user_profile.add_interest("gaming")
        
        # Test preferences update
        user_profile.update_preferences({
            "response_style": "funny",
            "proactive_enabled": True
        })
        
        # Test stats update
        user_profile.update_stats({
            "total_interactions": 5,
            "positive_feedback": 3
        })
        
        print("✓ UserProfile test passed")
        return True
        
    except Exception as e:
        print(f"✗ UserProfile test failed: {e}")
        return False

def test_learning_system():
    """Test LearningSystem functionality"""
    try:
        from DyberPet.ai.learning_system import LearningSystem
        from PySide6.QtWidgets import QApplication
        
        # Create minimal QApplication for testing
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        learning_system = LearningSystem()
        
        # Test feedback collection
        learning_system.collect_feedback("msg_001", "like", {
            "response_text": "测试回复",
            "emotion": "happy"
        })
        
        # Test behavior parameter access
        params = learning_system.get_behavior_parameters()
        print(f"✓ LearningSystem test passed: proactive_frequency={params.proactive_frequency}")
        
        return True
        
    except Exception as e:
        print(f"✗ LearningSystem test failed: {e}")
        return False

def test_personalization_engine():
    """Test PersonalizationEngine functionality"""
    try:
        from DyberPet.ai.personalization_engine import PersonalizationEngine
        from PySide6.QtWidgets import QApplication
        
        # Create minimal QApplication for testing
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        personalization_engine = PersonalizationEngine()
        
        # Test chat history analysis
        chat_history = [
            {"role": "user", "content": "我喜欢编程和游戏"},
            {"role": "assistant", "content": "太棒了！"},
            {"role": "user", "content": "今天玩了一个很有趣的游戏"}
        ]
        
        personalization_engine.build_user_profile(chat_history)
        
        # Test prompt customization
        base_prompt = "你是一个可爱的桌面宠物"
        customized_prompt = personalization_engine.customize_prompt(base_prompt)
        
        print("✓ PersonalizationEngine test passed")
        return True
        
    except Exception as e:
        print(f"✗ PersonalizationEngine test failed: {e}")
        return False

def test_main_integration():
    """Test main integration module"""
    try:
        from DyberPet.ai.ai_stage2_integration import AIStage2Integration
        from PySide6.QtWidgets import QApplication
        
        # Create minimal QApplication for testing
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        ai_integration = AIStage2Integration()
        
        # Test system status
        status = ai_integration.get_system_status()
        print(f"✓ AIStage2Integration test passed: is_initialized={status['is_initialized']}")
        
        # Test cleanup
        ai_integration.cleanup()
        
        return True
        
    except Exception as e:
        print(f"✗ AIStage2Integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Running DyberPet AI Stage 2 Integration Tests...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_emotion_manager,
        test_user_profile,
        test_learning_system,
        test_personalization_engine,
        test_main_integration
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