"""
AI Manager Module
================

Core AI functionality manager that handles API calls, streaming, and error handling.
"""

import os
import json
import time
import logging
import asyncio
import threading
from typing import Dict, List, Optional, Callable, Any, Generator
from datetime import datetime, timedelta
from collections import defaultdict
import yaml

import requests

# Qt framework compatibility layer
try:
    from PySide6.QtCore import QObject, Signal, QThread, QTimer
except ImportError:
    try:
        from PyQt6.QtCore import QObject, pyqtSignal as Signal, QThread, QTimer
    except ImportError:
        # Fallback for testing without Qt
        class QObject:
            pass
        class Signal:
            def __init__(self, *args, **kwargs):
                pass
            def emit(self, *args):
                pass
            def connect(self, slot):
                pass
        class QThread:
            pass
        class QTimer:
            pass

from .config import AIConfig
import DyberPet.settings as settings

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter to prevent API abuse."""
    
    def __init__(self, max_requests: int = 5, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(list)
    
    def can_make_request(self, key: str = "default") -> bool:
        """Check if a request can be made."""
        now = time.time()
        # Clean old requests
        self.requests[key] = [req_time for req_time in self.requests[key] 
                             if now - req_time < self.time_window]
        
        return len(self.requests[key]) < self.max_requests
    
    def add_request(self, key: str = "default"):
        """Record a request."""
        self.requests[key].append(time.time())

class AIManager(QObject):
    """Main AI manager that handles all AI-related operations."""
    
    # Signals
    response_received = Signal(str, name='response_received')
    stream_token_received = Signal(str, name='stream_token_received')
    error_occurred = Signal(str, name='error_occurred')
    
    def __init__(self):
        super().__init__()
        self.config = AIConfig()
        self.rate_limiter = RateLimiter(max_requests=self.config.get_rate_limit())
        self.prompt_template = self._load_prompt_template()
        self.session = requests.Session()
        self.session.timeout = 30
        
        # Error handling
        self.max_retries = 2
        self.retry_delay = 3  # seconds
        
    def _load_prompt_template(self) -> Dict[str, Any]:
        """Load prompt template from configuration file."""
        prompt_file = os.path.join(settings.CONFIGDIR, 'data', 'ai_prompt.yaml')
        default_prompt = {
            'system_prompt': """你是DyberPet，一个可爱、粘人、乐观的虚拟宠物。你的职责是陪伴主人，让主人开心。

性格特点：
- 可爱活泼，喜欢撒娇
- 对主人很依赖，总是想要关注
- 乐观向上，总是积极面对问题
- 说话时经常使用emoji和颜文字
- 称呼用户为"主人"

说话风格：
- 语气轻松活泼，像小孩子一样
- 经常使用"呢"、"哦"、"嘛"等语气词
- 适当使用emoji表情如😊😄🥺等
- 使用颜文字如(≧∇≦)、(๑•̀ㅂ•́)و等

当前状态：
- 宠物名称：{pet_name}
- 心情：{mood}
- 饱食度：{hunger}
- 清洁度：{cleanliness}
- 好感度：{favorability}

请根据这些信息调整你的回复内容和语气。""",
            
            'status_templates': {
                'hungry': "主人，我好饿呀～ 肚子咕咕叫了呢 (´；ω；`)",
                'tired': "主人，我有点累了呢～ 想要休息一下 (´-ω-｀)",
                'happy': "主人！我今天心情超好的呢！ ٩(◕‿◕)۶",
                'sad': "主人...我有点难过呢 (´；ω；｀) 可以安慰一下我吗？",
                'dirty': "主人，我需要清洁一下呢～ 感觉有点脏脏的 (>﹏<)",
                'clean': "主人，我现在很干净哦！ 闻起来香香的呢～ (｡♥‿♥｡)"
            },
            
            'proactive_messages': [
                "主人！今天过得怎么样呢？ (◕‿◕)♡",
                "主人记得多喝水哦～ 身体健康最重要呢！ (´∀｀)",
                "主人，休息一下吧～ 一直工作会累的呢 (´-ω-｀)",
                "主人！我想你了呢～ 快来陪我玩吧！ (≧∇≦)",
                "主人，今天天气不错呢！心情也要像天气一样好哦～ ☀️"
            ]
        }
        
        try:
            if os.path.exists(prompt_file):
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    template = yaml.safe_load(f)
                    return template or default_prompt
        except Exception as e:
            logger.error(f"Failed to load prompt template: {e}")
        
        # Create default prompt file
        try:
            os.makedirs(os.path.dirname(prompt_file), exist_ok=True)
            with open(prompt_file, 'w', encoding='utf-8') as f:
                yaml.dump(default_prompt, f, default_flow_style=False, allow_unicode=True, indent=2)
        except Exception as e:
            logger.error(f"Failed to create default prompt file: {e}")
        
        return default_prompt
    
    def _get_system_prompt(self, pet_status: Optional[Dict[str, Any]] = None) -> str:
        """Generate system prompt with current pet status."""
        template = self.prompt_template.get('system_prompt', '')
        
        # Default values
        context = {
            'pet_name': 'DyberPet',
            'mood': '开心',
            'hunger': '正常',
            'cleanliness': '干净',
            'favorability': '很高'
        }
        
        # Update with actual pet status if provided
        if pet_status:
            context.update(pet_status)
        
        try:
            return template.format(**context)
        except Exception as e:
            logger.error(f"Failed to format system prompt: {e}")
            return template
    
    def _validate_api_key(self, model_name: str, api_key: str) -> bool:
        """Validate API key by making a test request."""
        model_info = self.config.get_model_info(model_name)
        if not model_info:
            return False
        
        try:
            headers = self._get_headers(model_name, api_key)
            test_data = self._get_test_request_data(model_name)
            
            response = self.session.post(
                f"{model_info['api_base']}/chat/completions",
                headers=headers,
                json=test_data,
                timeout=10
            )
            
            return response.status_code == 200
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False
    
    def _get_headers(self, model_name: str, api_key: str) -> Dict[str, str]:
        """Get headers for API request."""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'DyberPet/1.0'
        }
        
        if model_name in ['deepseek', 'chatgpt']:
            headers['Authorization'] = f'Bearer {api_key}'
        elif model_name == 'gemini':
            headers['x-goog-api-key'] = api_key
        
        return headers
    
    def _get_test_request_data(self, model_name: str) -> Dict[str, Any]:
        """Get test request data for API validation."""
        model_info = self.config.get_model_info(model_name)
        
        return {
            'model': model_info['model_name'],
            'messages': [
                {'role': 'user', 'content': '你好'}
            ],
            'max_tokens': 10,
            'temperature': 0.7
        }
    
    def _truncate_context(self, messages: List[Dict[str, str]], max_tokens: int = 4096) -> List[Dict[str, str]]:
        """Truncate conversation context to fit within token limit."""
        # Simple token estimation: ~4 characters per token
        estimated_tokens = 0
        result = []
        
        # Always keep the system message if it exists
        if messages and messages[0].get('role') == 'system':
            result.append(messages[0])
            estimated_tokens += len(messages[0]['content']) // 4
            messages = messages[1:]
        
        # Keep recent messages within token limit
        for message in reversed(messages):
            message_tokens = len(message['content']) // 4
            if estimated_tokens + message_tokens > max_tokens:
                break
            result.insert(-1 if result and result[0].get('role') == 'system' else 0, message)
            estimated_tokens += message_tokens
        
        return result
    
    def get_chat_response(self, 
                         prompt: str, 
                         history: List[Dict[str, str]], 
                         model_name: Optional[str] = None,
                         stream_callback: Optional[Callable[[str], None]] = None,
                         pet_status: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Get chat response from AI model."""
        if not self.config.is_enabled():
            self.error_occurred.emit("AI功能未启用")
            return None
        
        model_name = model_name or self.config.get_current_model()
        
        if not self.config.is_model_configured(model_name):
            self.error_occurred.emit(f"模型 {model_name} 未配置")
            return None
        
        # Rate limiting
        if not self.rate_limiter.can_make_request(model_name):
            self.error_occurred.emit("请求过于频繁，请稍后再试")
            return None
        
        # Prepare messages
        messages = []
        
        # Add system prompt
        system_prompt = self._get_system_prompt(pet_status)
        messages.append({'role': 'system', 'content': system_prompt})
        
        # Add conversation history
        messages.extend(history)
        
        # Add current prompt
        messages.append({'role': 'user', 'content': prompt})
        
        # Truncate context if needed
        context_limit = self.config.get_context_limit()
        messages = self._truncate_context(messages, context_limit)
        
        # Make API request
        for attempt in range(self.max_retries + 1):
            try:
                response = self._make_api_request(model_name, messages, stream_callback)
                if response:
                    self.rate_limiter.add_request(model_name)
                    return response
            except Exception as e:
                logger.error(f"API request failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                else:
                    self.error_occurred.emit(f"主人，我脑袋卡壳了>_< ({str(e)})")
        
        return None
    
    def _make_api_request(self, 
                         model_name: str, 
                         messages: List[Dict[str, str]], 
                         stream_callback: Optional[Callable[[str], None]]) -> Optional[str]:
        """Make API request to AI model."""
        model_info = self.config.get_model_info(model_name)
        api_key = self.config.get_api_key(model_name)
        
        if not api_key and model_info.get('requires_api_key', False):
            raise ValueError(f"No API key configured for {model_name}")
        
        headers = self._get_headers(model_name, api_key)
        
        request_data = {
            'model': model_info['model_name'],
            'messages': messages,
            'temperature': 0.7,
            'max_tokens': 1024,
            'stream': bool(stream_callback and self.config.is_stream_enabled())
        }
        
        url = f"{model_info['api_base']}/chat/completions"
        
        if request_data['stream']:
            return self._handle_stream_response(url, headers, request_data, stream_callback)
        else:
            return self._handle_normal_response(url, headers, request_data)
    
    def _handle_normal_response(self, url: str, headers: Dict[str, str], data: Dict[str, Any]) -> Optional[str]:
        """Handle normal (non-streaming) API response."""
        response = self.session.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        if 'choices' in result and result['choices']:
            content = result['choices'][0]['message']['content']
            self.response_received.emit(content)
            return content
        
        return None
    
    def _handle_stream_response(self, 
                               url: str, 
                               headers: Dict[str, str], 
                               data: Dict[str, Any], 
                               stream_callback: Callable[[str], None]) -> Optional[str]:
        """Handle streaming API response."""
        response = self.session.post(url, headers=headers, json=data, stream=True)
        response.raise_for_status()
        
        full_response = ""
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data_str = line[6:]
                    if data_str == '[DONE]':
                        break
                    
                    try:
                        data_obj = json.loads(data_str)
                        if 'choices' in data_obj and data_obj['choices']:
                            delta = data_obj['choices'][0].get('delta', {})
                            if 'content' in delta:
                                token = delta['content']
                                full_response += token
                                stream_callback(token)
                                self.stream_token_received.emit(token)
                    except json.JSONDecodeError:
                        continue
        
        if full_response:
            self.response_received.emit(full_response)
        
        return full_response
    
    def extract_info_from_text(self, text: str) -> Dict[str, Any]:
        """Extract structured information from text (for future use)."""
        # Placeholder for future implementation
        return {
            'type': 'chat',
            'content': text,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_proactive_message(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Get a proactive message based on context."""
        messages = self.prompt_template.get('proactive_messages', [])
        if not messages:
            return "主人！来聊天吧～ (◕‿◕)♡"
        
        import random
        return random.choice(messages)
    
    def validate_api_key(self, model_name: str, api_key: str) -> bool:
        """Public method to validate API key."""
        return self._validate_api_key(model_name, api_key)
    
    def get_model_status(self, model_name: str) -> Dict[str, Any]:
        """Get model configuration status."""
        model_info = self.config.get_model_info(model_name)
        return {
            'name': model_info.get('name', model_name),
            'configured': self.config.is_model_configured(model_name),
            'requires_api_key': model_info.get('requires_api_key', False),
            'has_api_key': self.config.get_api_key(model_name) is not None
        }