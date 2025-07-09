#!/usr/bin/env python3
"""
Example integration of DyberPet AI Stage 2 features
Demonstrates how to integrate the new components with existing DyberPet system
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, QTimer
from DyberPet.ai import AIStage2Integration

class DyberPetAIExample(QObject):
    """Example integration of Stage 2 AI features with DyberPet"""
    
    # Signals that would connect to DyberPet systems
    show_bubble_text = Signal(str)
    trigger_animation = Signal(str)
    update_settings = Signal(dict)
    
    def __init__(self):
        super().__init__()
        
        # Initialize Stage 2 AI system
        self.ai_system = AIStage2Integration()
        
        # Connect AI system signals to DyberPet functions
        self.ai_system.proactive_bubble_requested.connect(self.handle_proactive_bubble)
        self.ai_system.animation_requested.connect(self.handle_animation_request)
        self.ai_system.user_preferences_updated.connect(self.handle_preferences_update)
        self.ai_system.learning_recommendation.connect(self.handle_learning_recommendation)
        
        # Start the AI system
        self.ai_system.start_ai_system()
        
        print("DyberPet AI Stage 2 system initialized")
        print(f"System status: {self.ai_system.get_system_status()}")
        
    def handle_proactive_bubble(self, message: str, context: dict):
        """Handle proactive bubble text display"""
        print(f"📢 Proactive message: {message}")
        print(f"   Context: {context}")
        self.show_bubble_text.emit(message)
        
    def handle_animation_request(self, animation_name: str, emotion_data: dict):
        """Handle animation trigger request"""
        print(f"🎭 Animation requested: {animation_name}")
        print(f"   Emotion: {emotion_data.get('emotion', 'unknown')} (intensity: {emotion_data.get('intensity', 0):.2f})")
        self.trigger_animation.emit(animation_name)
        
    def handle_preferences_update(self, preferences: dict):
        """Handle user preferences update"""
        print(f"⚙️ Preferences updated: {preferences}")
        self.update_settings.emit(preferences)
        
    def handle_learning_recommendation(self, recommendation: str):
        """Handle learning system recommendation"""
        print(f"💡 Learning recommendation: {recommendation}")
        
    def simulate_ai_response(self, response_text: str):
        """Simulate processing an AI response"""
        print(f"🤖 Processing AI response: {response_text}")
        
        # Process the response for emotions and animations
        emotion_data = self.ai_system.process_ai_response(response_text)
        
        if emotion_data:
            print(f"   Detected emotion: {emotion_data.primary_emotion} (intensity: {emotion_data.intensity:.2f})")
            print(f"   Suggested animation: {emotion_data.animation_name}")
            
    def simulate_user_interaction(self, interaction_type: str, data: dict):
        """Simulate user interaction"""
        print(f"👤 User interaction: {interaction_type}")
        self.ai_system.handle_user_interaction(interaction_type, data)
        
    def simulate_pet_status_change(self, status_type: str, old_value, new_value):
        """Simulate pet status change"""
        print(f"🐾 Pet status changed: {status_type} {old_value} -> {new_value}")
        self.ai_system.handle_pet_status_change(status_type, old_value, new_value)
        
    def simulate_user_feedback(self, message_id: str, feedback_type: str):
        """Simulate user feedback collection"""
        print(f"👍 User feedback: {feedback_type} for message {message_id}")
        self.ai_system.collect_user_feedback(message_id, feedback_type)
        
    def run_demonstration(self):
        """Run a demonstration of the Stage 2 features"""
        print("\n" + "="*60)
        print("🎯 DyberPet AI Stage 2 Feature Demonstration")
        print("="*60)
        
        # 1. Simulate AI responses with different emotions
        print("\n1. Testing Emotion Detection and Animation:")
        test_responses = [
            "主人，我好开心！今天天气真好！😊",
            "主人，我感觉有点难过... 😢",
            "哇！太令人兴奋了！🎉",
            "主人，我有点困了，想休息一下... 😴",
            "主人，我爱你！❤️"
        ]
        
        for response in test_responses:
            self.simulate_ai_response(response)
            
        # 2. Test user interactions
        print("\n2. Testing User Interactions:")
        self.simulate_user_interaction("chat_message", {
            "message": "我喜欢编程和游戏",
            "timestamp": "2024-01-01T10:00:00"
        })
        
        self.simulate_user_interaction("pet_click", {
            "click_count": 3,
            "timestamp": "2024-01-01T10:05:00"
        })
        
        # 3. Test pet status changes
        print("\n3. Testing Pet Status Changes:")
        self.simulate_pet_status_change("hp_tier", 3, 1)  # Pet becomes hungry
        self.simulate_pet_status_change("fv_tier", 2, 3)  # Pet becomes happy
        
        # 4. Test user feedback
        print("\n4. Testing User Feedback:")
        self.simulate_user_feedback("msg_001", "like")
        self.simulate_user_feedback("msg_002", "too_frequent")
        self.simulate_user_feedback("msg_003", "love")
        
        # 5. Show learning recommendations
        print("\n5. Learning System Recommendations:")
        recommendations = self.ai_system.get_user_recommendations()
        for rec in recommendations:
            print(f"   📋 {rec}")
        
        # 6. Show system status
        print("\n6. System Status:")
        status = self.ai_system.get_system_status()
        print(f"   Active: {status['is_active']}")
        print(f"   Initialized: {status['is_initialized']}")
        print(f"   Proactive system running: {status['components']['proactive_manager']['is_running']}")
        print(f"   Daily proactive count: {status['components']['proactive_manager']['daily_count']}")
        
        # 7. Test personalization
        print("\n7. Testing Personalization:")
        chat_history = [
            {"role": "user", "content": "我是一个程序员，喜欢写代码"},
            {"role": "assistant", "content": "太棒了！编程很有趣"},
            {"role": "user", "content": "我也喜欢玩游戏，特别是RPG游戏"},
            {"role": "assistant", "content": "RPG游戏很有意思！"},
            {"role": "user", "content": "最近在学习AI技术"}
        ]
        
        self.ai_system.build_user_profile_from_chat(chat_history)
        
        # Test prompt personalization
        base_prompt = "你是一个可爱的桌面宠物，要和用户聊天。"
        personalized_prompt = self.ai_system.get_personalized_prompt(base_prompt)
        print(f"   Original prompt: {base_prompt}")
        print(f"   Personalized prompt: {personalized_prompt}")
        
        # Test response adaptation
        response = "你好！今天想聊什么呢？"
        adapted_response = self.ai_system.adapt_response_style(response)
        print(f"   Original response: {response}")
        print(f"   Adapted response: {adapted_response}")
        
        print("\n" + "="*60)
        print("🎉 Demonstration completed!")
        print("="*60)
        
    def cleanup(self):
        """Cleanup resources"""
        print("\n🧹 Cleaning up...")
        self.ai_system.cleanup()
        print("✓ Cleanup completed")

def main():
    """Main function"""
    app = QApplication([])
    
    # Create and run the example
    example = DyberPetAIExample()
    
    # Run demonstration
    example.run_demonstration()
    
    # Cleanup
    example.cleanup()
    
    print("\n✅ Example completed successfully!")

if __name__ == "__main__":
    main()