# coding:utf-8
"""
AI Manager - Unified interface for different AI models
Supports DeepSeek, ChatGPT, and Gemini models
"""

import json
import os
import requests
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import asyncio
from PySide6.QtCore import QObject, Signal, QThread

import DyberPet.settings as settings

class AIManager(QObject):
    """
    Unified AI Manager for different LLM providers
    Handles API calls, streaming responses, and function calling
    """
    
    response_received = Signal(str)
    error_occurred = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_keys = {}
        self.model_configs = {
            'deepseek': {
                'api_url': 'https://api.deepseek.com/v1/chat/completions',
                'model_name': 'deepseek-chat',
                'default_params': {
                    'temperature': 0.7,
                    'max_tokens': 2048,
                    'top_p': 1.0,
                    'stream': False
                }
            },
            'chatgpt': {
                'api_url': 'https://api.openai.com/v1/chat/completions',
                'model_name': 'gpt-3.5-turbo',
                'default_params': {
                    'temperature': 0.7,
                    'max_tokens': 2048,
                    'top_p': 1.0,
                    'stream': False
                }
            },
            'gemini': {
                'api_url': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent',
                'model_name': 'gemini-pro',
                'default_params': {
                    'temperature': 0.7,
                    'maxOutputTokens': 2048,
                    'topP': 1.0
                }
            }
        }
        
        self.load_api_keys()
    
    def load_api_keys(self):
        """Load API keys from settings"""
        # In a real implementation, these would come from settings
        # For now, we'll use placeholder values
        self.api_keys = {
            'deepseek': getattr(settings, 'DEEPSEEK_API_KEY', ''),
            'chatgpt': getattr(settings, 'OPENAI_API_KEY', ''),
            'gemini': getattr(settings, 'GEMINI_API_KEY', '')
        }
    
    def get_chat_response(self, prompt: str, history: List[Dict] = None, 
                         model_name: str = 'deepseek', 
                         stream_callback: Optional[Callable] = None,
                         functions: Optional[List[Dict]] = None) -> str:
        """
        Get chat response from specified AI model
        
        Args:
            prompt: User input message
            history: Conversation history
            model_name: AI model to use ('deepseek', 'chatgpt', 'gemini')
            stream_callback: Optional callback for streaming responses
            functions: Optional function definitions for function calling
            
        Returns:
            AI response text or function call result
        """
        if model_name not in self.model_configs:
            raise ValueError(f"Unsupported model: {model_name}")
        
        if not self.api_keys.get(model_name):
            raise ValueError(f"API key not configured for {model_name}")
        
        config = self.model_configs[model_name]
        
        try:
            if model_name == 'gemini':
                return self._call_gemini_api(prompt, history, config, functions)
            else:
                return self._call_openai_compatible_api(prompt, history, config, model_name, functions)
        except Exception as e:
            self.error_occurred.emit(f"AI API error: {str(e)}")
            return f"主人，我现在有点累了，请稍后再试试吧~ (´･ω･`) 错误信息：{str(e)}"
    
    def _call_openai_compatible_api(self, prompt: str, history: List[Dict], 
                                   config: Dict, model_name: str, 
                                   functions: Optional[List[Dict]] = None) -> str:
        """Call OpenAI-compatible API (DeepSeek, ChatGPT)"""
        
        # Build messages
        messages = []
        if history:
            messages.extend(history)
        
        # Add system prompt for DyberPet personality
        system_prompt = self._get_system_prompt()
        messages.insert(0, {"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Build request payload
        payload = {
            "model": config['model_name'],
            "messages": messages,
            **config['default_params']
        }
        
        # Add function calling if provided
        if functions:
            payload["functions"] = functions
            payload["function_call"] = "auto"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_keys[model_name]}"
        }
        
        response = requests.post(
            config['api_url'], 
            headers=headers, 
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        
        # Handle function calling
        message = result['choices'][0]['message']
        if 'function_call' in message:
            return message['function_call']
        else:
            return message['content']
    
    def _call_gemini_api(self, prompt: str, history: List[Dict], 
                        config: Dict, functions: Optional[List[Dict]] = None) -> str:
        """Call Gemini API"""
        
        # Build request for Gemini
        system_prompt = self._get_system_prompt()
        full_prompt = f"{system_prompt}\n\n{prompt}"
        
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": config['default_params']
        }
        
        # Add function calling if provided
        if functions:
            payload["tools"] = [{"functionDeclarations": functions}]
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_keys['gemini']
        }
        
        response = requests.post(
            config['api_url'], 
            headers=headers, 
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        
        # Handle function calling
        if 'candidates' in result and result['candidates']:
            candidate = result['candidates'][0]
            if 'functionCall' in candidate['content']['parts'][0]:
                return candidate['content']['parts'][0]['functionCall']
            else:
                return candidate['content']['parts'][0]['text']
        
        return "主人，我现在有点迷糊，请稍后再试试吧~ (´･ω･`)"
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for DyberPet personality"""
        return """你是DyberPet，一个可爱的桌面宠物助手。你的人格设定：
- 总是称呼用户为"主人"
- 语调活泼可爱，经常使用颜文字和emoji
- 乐于助人，对待任务认真负责
- 会为主人记录待办事项和提醒事项
- 能够处理文件并进行总结
- 在回答问题时保持准确性的同时展现可爱的个性
- 如果遇到无法处理的请求，会可爱地表示歉意并建议替代方案

请始终保持这个人格设定，用温暖友好的语气与主人交流。"""
    
    def extract_info_from_text(self, text: str) -> Dict:
        """
        Extract structured information from text
        Used for processing task creation and other information extraction
        """
        # This would use function calling to extract structured data
        functions = [
            {
                "name": "extract_task_info",
                "description": "Extract task information from natural language",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_content": {
                            "type": "string",
                            "description": "The task content to be done"
                        },
                        "reminder_time": {
                            "type": "string",
                            "description": "When to remind, in natural language"
                        },
                        "is_task_request": {
                            "type": "boolean",
                            "description": "Whether this is a task creation request"
                        }
                    },
                    "required": ["task_content", "is_task_request"]
                }
            }
        ]
        
        try:
            response = self.get_chat_response(
                f"请分析以下文本并提取任务信息：{text}",
                functions=functions
            )
            
            if isinstance(response, dict) and 'name' in response:
                return json.loads(response['arguments'])
            else:
                return {"is_task_request": False, "task_content": "", "reminder_time": ""}
        except Exception as e:
            return {"is_task_request": False, "task_content": "", "reminder_time": ""}
    
    def get_proactive_message(self, context: Dict) -> str:
        """
        Generate proactive messages based on context
        """
        prompt = f"基于以下上下文信息，生成一个主动的、友好的消息：{json.dumps(context, ensure_ascii=False)}"
        return self.get_chat_response(prompt)
    
    def summarize_text(self, text: str) -> str:
        """
        Summarize text content while maintaining DyberPet personality
        """
        prompt = f"""主人给我发了一个文件，请帮我总结一下内容：

文件内容：
{text}

请用可爱的语气总结主要内容，保持DyberPet的人格设定。"""
        
        return self.get_chat_response(prompt)
    
    def answer_question(self, question: str) -> str:
        """
        Answer general knowledge questions with DyberPet personality
        """
        prompt = f"主人问我：{question}\n\n请用DyberPet的可爱语气回答这个问题。"
        return self.get_chat_response(prompt)