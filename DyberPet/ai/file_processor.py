# coding:utf-8
"""
File Processor - Handles file drag-and-drop and text processing
Supports .txt file validation, reading, and AI-powered summarization
"""

import os
from typing import Optional, Tuple
from PySide6.QtCore import QObject, Signal

class FileProcessor(QObject):
    """
    Handles file processing for text summarization
    """
    
    file_processed = Signal(str)  # Emitted when file is successfully processed
    error_occurred = Signal(str)  # Emitted when an error occurs
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.max_file_size = 100 * 1024  # 100KB limit
        self.supported_extensions = {'.txt'}
    
    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate if file can be processed
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not os.path.exists(file_path):
                return False, "文件不存在哦，主人确定路径正确吗？ (´･ω･`)"
            
            if not os.path.isfile(file_path):
                return False, "这不是一个文件呢，主人~ (´･ω･`)"
            
            # Check file extension
            _, ext = os.path.splitext(file_path)
            if ext.lower() not in self.supported_extensions:
                return False, f"主人，我现在只能处理 .txt 文件哦~ 您给我的是 {ext} 文件 (´･ω･`)"
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                size_kb = file_size / 1024
                return False, f"主人，这个文件太大了呢~ ({size_kb:.1f}KB > 100KB) 请给我一个小一点的文件吧 (´･ω･`)"
            
            if file_size == 0:
                return False, "这是个空文件呢，主人~ 里面什么都没有哦 (´･ω･`)"
            
            return True, ""
            
        except Exception as e:
            return False, f"检查文件时出错了~ 错误信息：{str(e)} (´･ω･`)"
    
    def read_text_file(self, file_path: str) -> Optional[str]:
        """
        Read content from text file
        
        Args:
            file_path: Path to the text file
            
        Returns:
            File content or None if error
        """
        try:
            # Try different encodings
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16', 'ascii']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                        
                    # Validate content
                    if not content or not content.strip():
                        return None
                    
                    return content
                    
                except UnicodeDecodeError:
                    continue
            
            # If all encodings fail
            return None
            
        except Exception as e:
            print(f"File reading error: {e}")
            return None
    
    def process_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Process a file and return the content or error
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (success, content_or_error)
        """
        # Validate file
        is_valid, error_message = self.validate_file(file_path)
        if not is_valid:
            self.error_occurred.emit(error_message)
            return False, error_message
        
        # Read file content
        content = self.read_text_file(file_path)
        if content is None:
            error_msg = "主人，我读取文件时遇到了问题~ 可能是编码格式不支持呢 (´･ω･`)"
            self.error_occurred.emit(error_msg)
            return False, error_msg
        
        # Check content length
        if len(content.strip()) < 10:
            error_msg = "这个文件内容太少了呢，主人~ 请给我一个内容更丰富的文件吧 (´･ω･`)"
            self.error_occurred.emit(error_msg)
            return False, error_msg
        
        self.file_processed.emit(content)
        return True, content
    
    def handle_file_error(self, error: Exception) -> str:
        """
        Handle file processing errors
        
        Args:
            error: Exception that occurred
            
        Returns:
            User-friendly error message
        """
        error_str = str(error)
        
        if "permission" in error_str.lower():
            return "主人，我没有权限访问这个文件呢~ 请检查文件权限吧 (´･ω･`)"
        elif "not found" in error_str.lower():
            return "文件不见了呢，主人~ 是不是被移动或删除了？ (´･ω･`)"
        elif "encoding" in error_str.lower() or "decode" in error_str.lower():
            return "主人，这个文件的编码格式我不认识呢~ 请尝试用UTF-8格式保存 (´･ω･`)"
        elif "size" in error_str.lower():
            return "文件太大了呢，主人~ 请给我一个小于100KB的文件吧 (´･ω･`)"
        else:
            return f"处理文件时出现了未知错误~ 错误信息：{error_str} (´･ω･`)"
    
    def get_file_info(self, file_path: str) -> dict:
        """
        Get file information
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        try:
            if not os.path.exists(file_path):
                return {}
            
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_path)[1]
            
            return {
                'name': file_name,
                'size': file_size,
                'size_kb': file_size / 1024,
                'extension': file_ext,
                'path': file_path
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def estimate_processing_time(self, content_length: int) -> str:
        """
        Estimate processing time based on content length
        
        Args:
            content_length: Length of text content
            
        Returns:
            Estimated time string
        """
        if content_length < 1000:
            return "几秒钟"
        elif content_length < 5000:
            return "10-20秒"
        elif content_length < 10000:
            return "30-60秒"
        else:
            return "1-2分钟"
    
    def format_file_summary_prompt(self, content: str, file_info: dict) -> str:
        """
        Format the prompt for AI summarization
        
        Args:
            content: File content
            file_info: File information
            
        Returns:
            Formatted prompt for AI
        """
        file_name = file_info.get('name', '未知文件')
        file_size = file_info.get('size_kb', 0)
        
        prompt = f"""主人给我发了一个文件，让我帮忙总结一下内容：

文件名：{file_name}
文件大小：{file_size:.1f}KB

文件内容：
{content}

请用我可爱的DyberPet语气总结这个文件的主要内容，要点包括：
1. 文件的主要内容是什么
2. 有哪些重要信息或要点
3. 如果是技术文档，简要说明技术要点
4. 如果是故事或文章，概括主要情节或观点

请保持我的可爱人格，用温暖友好的语气回复主人~"""
        
        return prompt