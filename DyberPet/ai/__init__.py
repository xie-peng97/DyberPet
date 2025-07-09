"""
DyberPet AI Module
================

This module provides AI integration capabilities for DyberPet, including:
- AI model configuration and management
- Chat functionality with multiple AI providers
- Pet personality injection and status-aware dialogue
- Secure API key storage and validation
- Settings interface for AI configuration
"""

# Import only what's necessary to avoid Qt dependencies during testing
try:
    from .ai_manager import AIManager
    from .settings import AISettingsWidget, create_ai_settings_widget
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    AIManager = None
    AISettingsWidget = None
    create_ai_settings_widget = None

# Always import config as it doesn't depend on Qt
from .config import AIConfig

__all__ = ['AIConfig', 'AIManager', 'AISettingsWidget', 'create_ai_settings_widget', 'AI_AVAILABLE']