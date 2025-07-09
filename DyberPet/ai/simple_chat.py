"""
Simple Chat Window for Testing
==============================

A simplified chat window implementation that uses basic Qt widgets.
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Any

# Use PySide6 consistently with the main application
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSize
from PySide6.QtGui import QFont, QTextCursor, QIcon, QPixmap, QAction

from .ai_manager import AIManager
from .config import AIConfig
import DyberPet.settings as settings

class SimpleChatWindow(QMainWindow):
    """Simple chat window for testing AI functionality."""
    
    def __init__(self):
        super().__init__()
        self.ai_manager = AIManager()
        self.ai_config = AIConfig()
        self.current_worker = None
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the simple chat UI."""
        self.setWindowTitle("与DyberPet聊天 (简化版)")
        self.setMinimumSize(600, 500)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        
        # Chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.chat_display)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("输入消息...")
        self.message_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input)
        
        self.send_button = QPushButton("发送")
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        
        layout.addLayout(input_layout)
        
        # Status bar
        self.status_label = QLabel("AI: 准备就绪")
        self.status_label.setStyleSheet("color: #28a745; font-size: 12px; padding: 5px;")
        layout.addWidget(self.status_label)
        
        # Add some initial messages
        self.add_message("system", "欢迎使用DyberPet AI聊天功能！")
        self.add_message("assistant", "主人～我是DyberPet！很高兴和你聊天呢！(◕‿◕)♡")
        
    def add_message(self, role: str, content: str):
        """Add a message to the chat display."""
        timestamp = datetime.now().strftime("%H:%M")
        
        if role == "user":
            sender = "主人"
            color = "#0078d4"
        elif role == "assistant":
            sender = "DyberPet"
            color = "#7b68ee"
        else:
            sender = "系统"
            color = "#666"
        
        html = f"""
        <div style="margin-bottom: 10px;">
            <span style="color: {color}; font-weight: bold;">{sender}</span>
            <span style="color: #666; font-size: 10px; margin-left: 10px;">{timestamp}</span>
            <br>
            <span style="margin-left: 10px;">{content}</span>
        </div>
        """
        
        self.chat_display.append(html)
        
        # Scroll to bottom
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.chat_display.setTextCursor(cursor)
    
    def send_message(self):
        """Send a message to the AI."""
        message = self.message_input.text().strip()
        if not message:
            return
        
        # Check if AI is enabled
        if not self.ai_config.is_enabled():
            self.add_message("system", "AI功能未启用，请在设置中启用AI功能")
            return
        
        # Add user message
        self.add_message("user", message)
        self.message_input.clear()
        
        # Get AI response
        self.get_ai_response(message)
    
    def get_ai_response(self, message: str):
        """Get AI response."""
        self.status_label.setText("AI: 思考中...")
        self.status_label.setStyleSheet("color: #ffc107; font-size: 12px; padding: 5px;")
        self.send_button.setEnabled(False)
        
        # Start AI worker thread
        self.current_worker = AIResponseWorker(self.ai_manager, message)
        self.current_worker.response_ready.connect(self.on_ai_response)
        self.current_worker.error_occurred.connect(self.on_ai_error)
        self.current_worker.start()
    
    def on_ai_response(self, response: str):
        """Handle AI response."""
        self.add_message("assistant", response)
        self.finish_ai_response()
    
    def on_ai_error(self, error: str):
        """Handle AI error."""
        self.add_message("system", f"AI错误: {error}")
        self.finish_ai_response()
    
    def finish_ai_response(self):
        """Finish AI response."""
        self.status_label.setText("AI: 准备就绪")
        self.status_label.setStyleSheet("color: #28a745; font-size: 12px; padding: 5px;")
        self.send_button.setEnabled(True)
        self.current_worker = None
        self.message_input.setFocus()
    
    def closeEvent(self, event):
        """Handle close event."""
        if self.current_worker:
            self.current_worker.terminate()
            self.current_worker.wait()
        event.accept()

class AIResponseWorker(QThread):
    """Worker thread for AI response."""
    
    response_ready = Signal(str)
    error_occurred = Signal(str)
    
    def __init__(self, ai_manager: AIManager, message: str):
        super().__init__()
        self.ai_manager = ai_manager
        self.message = message
    
    def run(self):
        """Run AI response generation."""
        try:
            # Get pet status (mock for now)
            pet_status = {
                'pet_name': 'DyberPet',
                'mood': '开心',
                'hunger': '正常',
                'cleanliness': '干净',
                'favorability': '很高'
            }
            
            # Get AI response
            response = self.ai_manager.get_chat_response(
                self.message,
                [],  # Empty history for now
                pet_status=pet_status
            )
            
            if response:
                self.response_ready.emit(response)
            else:
                self.error_occurred.emit("AI响应为空")
                
        except Exception as e:
            self.error_occurred.emit(str(e))

# For testing purposes
if __name__ == "__main__":
    app = QApplication([])
    window = SimpleChatWindow()
    window.show()
    app.exec()