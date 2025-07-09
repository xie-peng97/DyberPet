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

from .ai_manager import AIManager
from .config import AIConfig
from .settings import AISettingsWidget, create_ai_settings_widget

__all__ = ['AIManager', 'AIConfig', 'AISettingsWidget', 'create_ai_settings_widget']