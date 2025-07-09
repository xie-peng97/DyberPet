# coding:utf-8
"""
AI Configuration Management
Handles API keys and AI settings
"""

import os
import json
from typing import Dict, Optional

import DyberPet.settings as settings

class AIConfig:
    """
    Manages AI configuration and API keys
    """
    
    def __init__(self):
        self.config_file = os.path.join(settings.CONFIGDIR, 'data', 'ai_config.json')
        self.default_config = {
            'api_keys': {
                'deepseek': '',
                'openai': '',
                'gemini': ''
            },
            'default_model': 'deepseek',
            'personality': {
                'name': 'DyberPet',
                'owner_title': '主人',
                'use_emoticons': True,
                'language': 'zh-CN'
            },
            'function_calling': {
                'enabled': True,
                'time_parsing_enabled': True,
                'task_creation_enabled': True
            },
            'file_processing': {
                'enabled': True,
                'max_file_size_kb': 100,
                'supported_formats': ['.txt']
            },
            'task_management': {
                'auto_cleanup_days': 30,
                'task_reminder_enabled': True,
                'coin_reward_enabled': True
            }
        }
        self.config = self.load_config()
    
    def load_config(self) -> dict:
        """Load AI configuration from file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Merge with default config to ensure all keys exist
                return self._merge_configs(self.default_config, config)
            else:
                # Create default config file
                self.save_config(self.default_config)
                return self.default_config.copy()
                
        except Exception as e:
            print(f"Error loading AI config: {e}")
            return self.default_config.copy()
    
    def save_config(self, config: Optional[dict] = None):
        """Save AI configuration to file"""
        try:
            if config is None:
                config = self.config
            
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.config = config
            
        except Exception as e:
            print(f"Error saving AI config: {e}")
    
    def _merge_configs(self, default: dict, user: dict) -> dict:
        """Merge user config with default config"""
        merged = default.copy()
        
        for key, value in user.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def get_api_key(self, provider: str) -> str:
        """Get API key for specified provider"""
        return self.config.get('api_keys', {}).get(provider, '')
    
    def set_api_key(self, provider: str, api_key: str):
        """Set API key for specified provider"""
        if 'api_keys' not in self.config:
            self.config['api_keys'] = {}
        
        self.config['api_keys'][provider] = api_key
        self.save_config()
    
    def get_default_model(self) -> str:
        """Get default AI model"""
        return self.config.get('default_model', 'deepseek')
    
    def set_default_model(self, model: str):
        """Set default AI model"""
        if model in ['deepseek', 'openai', 'gemini']:
            self.config['default_model'] = model
            self.save_config()
    
    def is_function_calling_enabled(self) -> bool:
        """Check if function calling is enabled"""
        return self.config.get('function_calling', {}).get('enabled', True)
    
    def is_file_processing_enabled(self) -> bool:
        """Check if file processing is enabled"""
        return self.config.get('file_processing', {}).get('enabled', True)
    
    def get_max_file_size_kb(self) -> int:
        """Get maximum file size in KB"""
        return self.config.get('file_processing', {}).get('max_file_size_kb', 100)
    
    def is_task_management_enabled(self) -> bool:
        """Check if task management is enabled"""
        return self.config.get('task_management', {}).get('task_reminder_enabled', True)
    
    def get_personality_config(self) -> dict:
        """Get personality configuration"""
        return self.config.get('personality', {
            'name': 'DyberPet',
            'owner_title': '主人',
            'use_emoticons': True,
            'language': 'zh-CN'
        })
    
    def get_auto_cleanup_days(self) -> int:
        """Get auto cleanup days for old tasks"""
        return self.config.get('task_management', {}).get('auto_cleanup_days', 30)
    
    def has_valid_api_key(self, provider: str = None) -> bool:
        """Check if valid API key exists"""
        if provider:
            return bool(self.get_api_key(provider))
        else:
            # Check if any API key is configured
            api_keys = self.config.get('api_keys', {})
            return any(key.strip() for key in api_keys.values())
    
    def get_available_models(self) -> list:
        """Get list of available models with valid API keys"""
        available = []
        api_keys = self.config.get('api_keys', {})
        
        if api_keys.get('deepseek'):
            available.append('deepseek')
        if api_keys.get('openai'):
            available.append('openai')
        if api_keys.get('gemini'):
            available.append('gemini')
        
        return available
    
    def export_config(self) -> dict:
        """Export configuration (without API keys for security)"""
        export_config = self.config.copy()
        export_config['api_keys'] = {
            provider: '***' if key else ''
            for provider, key in export_config['api_keys'].items()
        }
        return export_config
    
    def reset_to_default(self):
        """Reset configuration to default values"""
        self.config = self.default_config.copy()
        self.save_config()
    
    def validate_config(self) -> dict:
        """Validate configuration and return status"""
        status = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check API keys
        if not self.has_valid_api_key():
            status['warnings'].append("No API keys configured")
        
        # Check default model
        default_model = self.get_default_model()
        if not self.has_valid_api_key(default_model):
            status['warnings'].append(f"Default model '{default_model}' has no API key")
        
        # Check file size limits
        max_size = self.get_max_file_size_kb()
        if max_size <= 0 or max_size > 1000:
            status['warnings'].append(f"File size limit {max_size}KB may be too restrictive")
        
        # Check cleanup days
        cleanup_days = self.get_auto_cleanup_days()
        if cleanup_days < 1:
            status['errors'].append("Auto cleanup days must be at least 1")
            status['valid'] = False
        
        return status

# Global AI config instance
ai_config = AIConfig()