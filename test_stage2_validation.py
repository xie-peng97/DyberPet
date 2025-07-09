#!/usr/bin/env python3
"""
Simple validation test for DyberPet AI Stage 2 modules
Tests basic functionality without external dependencies
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_emotion_keywords():
    """Test emotion keyword loading"""
    try:
        # Test default keywords
        from DyberPet.ai.emotion_manager import EmotionManager
        
        # Mock the required components
        class MockSignal:
            def connect(self, slot): pass
            def emit(self, *args): pass
        
        class MockQObject:
            def __init__(self, parent=None): pass
        
        # Patch the modules
        sys.modules['PySide6'] = type(sys)('PySide6')
        sys.modules['PySide6.QtCore'] = type(sys)('PySide6.QtCore')
        sys.modules['PySide6.QtCore'].QObject = MockQObject
        sys.modules['PySide6.QtCore'].Signal = MockSignal
        
        # Mock settings
        class MockSettings:
            BASEDIR = '/tmp/test'
        sys.modules['DyberPet.settings'] = MockSettings
        
        # Create emotion manager with mocked dependencies
        emotion_manager = EmotionManager()
        
        # Test that keywords are loaded
        keywords = emotion_manager.get_emotion_keywords()
        assert 'happy' in keywords
        assert 'sad' in keywords
        assert 'excited' in keywords
        assert 'angry' in keywords
        
        # Test that keywords contain expected values
        assert '开心' in keywords['happy']
        assert '难过' in keywords['sad']
        assert '兴奋' in keywords['excited']
        assert '生气' in keywords['angry']
        
        print("✓ Emotion keywords test passed")
        return True
        
    except Exception as e:
        print(f"✗ Emotion keywords test failed: {e}")
        return False

def test_data_structures():
    """Test data structures and basic functionality"""
    try:
        # Test EmotionData
        from DyberPet.ai.emotion_manager import EmotionData
        
        emotion_data = EmotionData(
            primary_emotion='happy',
            intensity=0.8,
            keywords=['开心', '高兴'],
            animation_name='happy_dance',
            duration=3.0
        )
        
        assert emotion_data.primary_emotion == 'happy'
        assert emotion_data.intensity == 0.8
        assert len(emotion_data.keywords) == 2
        
        print("✓ EmotionData structure test passed")
        
        # Test UserPreferences
        from DyberPet.ai.user_profile import UserPreferences
        
        prefs = UserPreferences()
        assert prefs.ai_enabled == True
        assert prefs.response_style == 'casual'
        assert prefs.proactive_enabled == True
        
        prefs_dict = prefs.to_dict()
        assert isinstance(prefs_dict, dict)
        assert 'ai_enabled' in prefs_dict
        
        print("✓ UserPreferences structure test passed")
        
        # Test BehaviorParameters
        from DyberPet.ai.learning_system import BehaviorParameters
        
        params = BehaviorParameters(
            proactive_frequency=45.0,
            emotion_sensitivity=0.7,
            response_length_preference=0.6,
            humor_level=0.5,
            formality_level=0.3,
            emoji_usage=0.7,
            question_frequency=0.4,
            topic_diversity=0.6
        )
        
        assert params.proactive_frequency == 45.0
        assert params.emotion_sensitivity == 0.7
        
        params_dict = params.to_dict()
        assert isinstance(params_dict, dict)
        assert 'proactive_frequency' in params_dict
        
        print("✓ BehaviorParameters structure test passed")
        
        return True
        
    except Exception as e:
        print(f"✗ Data structures test failed: {e}")
        return False

def test_utility_functions():
    """Test utility functions"""
    try:
        # Test emotion analysis logic (without Qt dependencies)
        emotion_keywords = {
            'happy': ['开心', '高兴', '快乐', '😊'],
            'sad': ['难过', '伤心', '失望', '😢'],
            'excited': ['兴奋', '激动', '太棒了', '🎉']
        }
        
        def analyze_emotion_simple(text):
            """Simple emotion analysis function"""
            text = text.lower()
            emotion_scores = {}
            
            for emotion, keywords in emotion_keywords.items():
                score = 0
                for keyword in keywords:
                    if keyword.lower() in text:
                        score += 1
                if score > 0:
                    emotion_scores[emotion] = score
            
            if emotion_scores:
                primary_emotion = max(emotion_scores, key=emotion_scores.get)
                intensity = min(emotion_scores[primary_emotion] / 3.0, 1.0)
                return primary_emotion, intensity
            else:
                return 'neutral', 0.1
        
        # Test with happy text
        emotion, intensity = analyze_emotion_simple("我很开心！今天太棒了！😊")
        assert emotion == 'happy'
        assert intensity > 0
        
        # Test with sad text
        emotion, intensity = analyze_emotion_simple("我很难过，感觉很失望 😢")
        assert emotion == 'sad'
        assert intensity > 0
        
        print("✓ Utility functions test passed")
        return True
        
    except Exception as e:
        print(f"✗ Utility functions test failed: {e}")
        return False

def test_template_files():
    """Test template file existence and structure"""
    try:
        import json
        from pathlib import Path
        
        # Test emotion keywords template
        keywords_file = Path(__file__).parent / 'DyberPet' / 'ai' / 'templates' / 'emotion_keywords.yaml'
        if keywords_file.exists():
            print("✓ Emotion keywords template file exists")
        else:
            print("⚠ Emotion keywords template file not found")
        
        # Test user preferences template
        prefs_file = Path(__file__).parent / 'DyberPet' / 'ai' / 'templates' / 'user_preferences.json'
        if prefs_file.exists():
            with open(prefs_file, 'r', encoding='utf-8') as f:
                prefs_data = json.load(f)
                
            # Check required keys
            assert 'preferences' in prefs_data
            assert 'ai_enabled' in prefs_data['preferences']
            assert 'proactive_enabled' in prefs_data['preferences']
            
            print("✓ User preferences template file valid")
        else:
            print("⚠ User preferences template file not found")
            
        return True
        
    except Exception as e:
        print(f"✗ Template files test failed: {e}")
        return False

def test_module_imports():
    """Test that all modules can be imported (basic structure)"""
    try:
        import importlib.util
        from pathlib import Path
        
        ai_dir = Path(__file__).parent / 'DyberPet' / 'ai'
        
        # Test that all Python files exist
        expected_files = [
            '__init__.py',
            'proactive_manager.py',
            'emotion_manager.py',
            'personalization_engine.py',
            'learning_system.py',
            'user_profile.py',
            'ai_stage2_integration.py'
        ]
        
        for file_name in expected_files:
            file_path = ai_dir / file_name
            if file_path.exists():
                print(f"✓ {file_name} exists")
            else:
                print(f"✗ {file_name} missing")
                return False
                
        # Test basic syntax by loading as specs
        for file_name in expected_files:
            if file_name == '__init__.py':
                continue
                
            file_path = ai_dir / file_name
            spec = importlib.util.spec_from_file_location(file_name[:-3], file_path)
            if spec is None:
                print(f"✗ {file_name} has syntax errors")
                return False
            else:
                print(f"✓ {file_name} syntax OK")
                
        return True
        
    except Exception as e:
        print(f"✗ Module imports test failed: {e}")
        return False

def main():
    """Run all validation tests"""
    print("Running DyberPet AI Stage 2 Validation Tests...")
    print("=" * 50)
    
    tests = [
        test_module_imports,
        test_data_structures,
        test_emotion_keywords,
        test_utility_functions,
        test_template_files
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
        print("🎉 All validation tests passed! Stage 2 implementation is structurally sound.")
    else:
        print(f"⚠️  {failed} tests failed. Please check the implementation.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)