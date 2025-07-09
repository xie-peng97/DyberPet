#!/usr/bin/env python3
"""
DyberPet AI Test Script
======================

Test script to verify AI functionality is working correctly.
"""

import os
import sys
import time
import tempfile

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock settings module to avoid PySide6 dependency
class MockSettings:
    CONFIGDIR = tempfile.mkdtemp()

# Add mock settings to sys.modules before importing AI modules
sys.modules['DyberPet.settings'] = MockSettings()

def test_ai_config():
    """Test AI configuration functionality."""
    print("Testing AI Configuration...")
    
    try:
        from DyberPet.ai.config import AIConfig
        
        config = AIConfig()
        print("✓ AI Config created successfully")
        print(f"  - Config directory: {config.config_dir}")
        print(f"  - AI enabled: {config.is_enabled()}")
        print(f"  - Current model: {config.get_current_model()}")
        print(f"  - Supported models: {list(config.get_supported_models().keys())}")
        
        # Test enabling AI
        config.set_enabled(True)
        print(f"  - AI enabled after setting: {config.is_enabled()}")
        
        # Test API key storage (with dummy key)
        test_key = "test_key_12345"
        config.set_api_key("deepseek", test_key)
        retrieved_key = config.get_api_key("deepseek")
        print(f"  - API key storage/retrieval: {'✓' if retrieved_key == test_key else '✗'}")
        
        # Test model configuration
        print(f"  - Model configured: {config.is_model_configured('deepseek')}")
        
        return True
        
    except Exception as e:
        print(f"✗ AI Config test failed: {e}")
        return False

def test_ai_manager():
    """Test AI manager functionality."""
    print("\nTesting AI Manager...")
    
    try:
        from DyberPet.ai.ai_manager import AIManager
        
        ai_manager = AIManager()
        print("✓ AI Manager created successfully")
        
        # Test prompt template loading
        print(f"  - Prompt template loaded: {'✓' if ai_manager.prompt_template else '✗'}")
        
        # Test system prompt generation
        pet_status = {
            'pet_name': 'DyberPet',
            'mood': '开心',
            'hunger': '正常',
            'cleanliness': '干净',
            'favorability': '很高'
        }
        
        system_prompt = ai_manager._get_system_prompt(pet_status)
        print(f"  - System prompt generated: {'✓' if system_prompt else '✗'}")
        print(f"  - System prompt length: {len(system_prompt)} characters")
        
        # Test proactive message
        proactive_msg = ai_manager.get_proactive_message()
        print(f"  - Proactive message: {proactive_msg}")
        
        return True
        
    except Exception as e:
        print(f"✗ AI Manager test failed: {e}")
        return False

def test_ai_integration():
    """Test AI integration with main application."""
    print("\nTesting AI Integration...")
    
    try:
        # Test if AI can be imported from main module
        from DyberPet.ai import AIConfig, AIManager
        print("✓ AI modules can be imported successfully")
        
        # Test configuration persistence
        config = AIConfig()
        config.set_enabled(True)
        config.set_current_model("deepseek")
        
        # Create new config instance to test persistence
        config2 = AIConfig()
        enabled = config2.is_enabled()
        model = config2.get_current_model()
        
        print(f"  - Configuration persistence: {'✓' if enabled and model == 'deepseek' else '✗'}")
        
        return True
        
    except Exception as e:
        print(f"✗ AI Integration test failed: {e}")
        return False

def test_prompt_template():
    """Test prompt template loading."""
    print("\nTesting Prompt Template...")
    
    try:
        from DyberPet.ai.ai_manager import AIManager
        
        ai_manager = AIManager()
        template = ai_manager.prompt_template
        
        # Check required sections
        required_sections = ['system_prompt', 'status_templates', 'proactive_messages']
        for section in required_sections:
            if section in template:
                print(f"  - {section}: ✓")
            else:
                print(f"  - {section}: ✗")
                return False
        
        # Check proactive messages count
        proactive_count = len(template.get('proactive_messages', []))
        print(f"  - Proactive messages count: {proactive_count}")
        
        # Check status templates count
        status_count = len(template.get('status_templates', {}))
        print(f"  - Status templates count: {status_count}")
        
        return True
        
    except Exception as e:
        print(f"✗ Prompt Template test failed: {e}")
        return False

def test_encryption():
    """Test API key encryption/decryption."""
    print("\nTesting API Key Encryption...")
    
    try:
        from DyberPet.ai.config import AIConfig
        
        config = AIConfig()
        
        # Test encryption with different keys
        test_keys = [
            "sk-12345678901234567890123456789012",
            "deepseek-api-key-test-1234567890",
            "AIzaSyDEFGHIJKLMNOPQRSTUVWXYZ123456789"
        ]
        
        for i, test_key in enumerate(test_keys):
            config.set_api_key(f"model_{i}", test_key)
            retrieved_key = config.get_api_key(f"model_{i}")
            
            if retrieved_key == test_key:
                print(f"  - Encryption test {i+1}: ✓")
            else:
                print(f"  - Encryption test {i+1}: ✗")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Encryption test failed: {e}")
        return False

def main():
    """Main test function."""
    print("DyberPet AI Test Suite")
    print("=" * 50)
    
    tests = [
        test_ai_config,
        test_ai_manager,
        test_ai_integration,
        test_prompt_template,
        test_encryption
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! AI functionality is working correctly.")
        return 0
    else:
        print("✗ Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    exit(main())