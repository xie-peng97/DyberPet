"""
AI Configuration Module
=======================

Handles AI model configuration, API key management, and secure storage.
"""

import os
import json
import logging
from typing import Dict, Optional, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

import DyberPet.settings as settings

logger = logging.getLogger(__name__)

class AIConfig:
    """AI configuration manager with secure API key storage."""
    
    SUPPORTED_MODELS = {
        'deepseek': {
            'name': 'DeepSeek',
            'api_base': 'https://api.deepseek.com/v1',
            'model_name': 'deepseek-chat',
            'requires_api_key': True
        },
        'chatgpt': {
            'name': 'ChatGPT',
            'api_base': 'https://api.openai.com/v1',
            'model_name': 'gpt-3.5-turbo',
            'requires_api_key': True
        },
        'gemini': {
            'name': 'Gemini',
            'api_base': 'https://generativelanguage.googleapis.com/v1',
            'model_name': 'gemini-pro',
            'requires_api_key': True
        },
        'local': {
            'name': 'Local Model',
            'api_base': 'http://localhost:11434',
            'model_name': 'llama2',
            'requires_api_key': False
        }
    }
    
    def __init__(self):
        self.config_dir = os.path.join(settings.CONFIGDIR, 'data')
        self.config_file = os.path.join(self.config_dir, 'ai_config.json')
        self.key_file = os.path.join(self.config_dir, 'ai_key.bin')
        
        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Default configuration
        self.config = {
            'enabled': False,
            'current_model': 'deepseek',
            'stream_enabled': True,
            'context_limit': 4096,
            'rate_limit': 5,  # requests per minute
            'models': {}
        }
        
        self.load_config()
        
    def _get_encryption_key(self) -> bytes:
        """Generate or load encryption key for API keys."""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            return key
    
    def _encrypt_api_key(self, api_key: str) -> str:
        """Encrypt API key using AES-256."""
        key = self._get_encryption_key()
        cipher = Fernet(key)
        encrypted = cipher.encrypt(api_key.encode())
        return base64.b64encode(encrypted).decode()
    
    def _decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt API key."""
        try:
            key = self._get_encryption_key()
            cipher = Fernet(key)
            encrypted_bytes = base64.b64decode(encrypted_key.encode())
            decrypted = cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt API key: {e}")
            return ""
    
    def load_config(self):
        """Load AI configuration from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    self.config.update(saved_config)
        except Exception as e:
            logger.error(f"Failed to load AI config: {e}")
    
    def save_config(self):
        """Save AI configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save AI config: {e}")
    
    def is_enabled(self) -> bool:
        """Check if AI features are enabled."""
        return self.config.get('enabled', False)
    
    def set_enabled(self, enabled: bool):
        """Enable or disable AI features."""
        self.config['enabled'] = enabled
        self.save_config()
    
    def get_current_model(self) -> str:
        """Get current AI model."""
        return self.config.get('current_model', 'deepseek')
    
    def set_current_model(self, model_name: str):
        """Set current AI model."""
        if model_name in self.SUPPORTED_MODELS:
            self.config['current_model'] = model_name
            self.save_config()
        else:
            raise ValueError(f"Unsupported model: {model_name}")
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get model information."""
        return self.SUPPORTED_MODELS.get(model_name, {})
    
    def get_api_key(self, model_name: str) -> Optional[str]:
        """Get decrypted API key for a model."""
        model_config = self.config['models'].get(model_name, {})
        encrypted_key = model_config.get('api_key_encrypted')
        if encrypted_key:
            return self._decrypt_api_key(encrypted_key)
        return None
    
    def set_api_key(self, model_name: str, api_key: str):
        """Set encrypted API key for a model."""
        if model_name not in self.config['models']:
            self.config['models'][model_name] = {}
        
        encrypted_key = self._encrypt_api_key(api_key)
        self.config['models'][model_name]['api_key_encrypted'] = encrypted_key
        self.save_config()
    
    def remove_api_key(self, model_name: str):
        """Remove API key for a model."""
        if model_name in self.config['models']:
            self.config['models'][model_name].pop('api_key_encrypted', None)
            self.save_config()
    
    def get_context_limit(self) -> int:
        """Get context limit for conversations."""
        return self.config.get('context_limit', 4096)
    
    def set_context_limit(self, limit: int):
        """Set context limit for conversations."""
        self.config['context_limit'] = max(1024, min(limit, 32768))
        self.save_config()
    
    def is_stream_enabled(self) -> bool:
        """Check if streaming is enabled."""
        return self.config.get('stream_enabled', True)
    
    def set_stream_enabled(self, enabled: bool):
        """Enable or disable streaming."""
        self.config['stream_enabled'] = enabled
        self.save_config()
    
    def get_rate_limit(self) -> int:
        """Get rate limit (requests per minute)."""
        return self.config.get('rate_limit', 5)
    
    def set_rate_limit(self, limit: int):
        """Set rate limit (requests per minute)."""
        self.config['rate_limit'] = max(1, min(limit, 60))
        self.save_config()
    
    def get_supported_models(self) -> Dict[str, Dict[str, Any]]:
        """Get all supported models."""
        return self.SUPPORTED_MODELS.copy()
    
    def is_model_configured(self, model_name: str) -> bool:
        """Check if a model is properly configured."""
        model_info = self.get_model_info(model_name)
        if not model_info:
            return False
        
        if model_info.get('requires_api_key', False):
            return self.get_api_key(model_name) is not None
        
        return True
    
    def get_model_status(self, model_name: str) -> Dict[str, Any]:
        """Get model configuration status."""
        model_info = self.get_model_info(model_name)
        return {
            'name': model_info.get('name', model_name),
            'configured': self.is_model_configured(model_name),
            'requires_api_key': model_info.get('requires_api_key', False),
            'has_api_key': self.get_api_key(model_name) is not None
        }