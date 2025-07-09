# coding:utf-8
"""
AI Chat Window - Enhanced chat interface with AI integration
Supports file drag-and-drop, function calling, and task management
"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime

from PySide6.QtCore import Qt, Signal, QThread, QTimer, QMimeData, QUrl
from PySide6.QtGui import QIcon, QPixmap, QColor, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QTextEdit, QScrollArea, QFrame, QApplication,
                               QProgressBar, QSizePolicy)

from qfluentwidgets import (CardWidget, StrongBodyLabel, BodyLabel, 
                           PushButton, LineEdit, MessageBox, InfoBar,
                           InfoBarPosition, FluentIcon as FIF)

import DyberPet.settings as settings
from DyberPet.ai.ai_manager import AIManager
from DyberPet.ai.function_calling import FunctionCallingProcessor
from DyberPet.ai.file_processor import FileProcessor
from DyberPet.ai.task_manager import TaskManager

basedir = settings.BASEDIR

class ChatMessage(CardWidget):
    """Individual chat message widget"""
    
    def __init__(self, content: str, is_user: bool = True, timestamp: Optional[datetime] = None, parent=None):
        super().__init__(parent)
        self.content = content
        self.is_user = is_user
        self.timestamp = timestamp or datetime.now()
        self.setupUI()
    
    def setupUI(self):
        """Setup message UI"""
        self.setFixedWidth(400)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 8, 10, 8)
        
        # Header with sender and time
        self.header_layout = QHBoxLayout()
        
        # Sender
        sender_name = "主人" if self.is_user else "DyberPet"
        self.sender_label = StrongBodyLabel(sender_name, self)
        
        # Timestamp
        time_str = self.timestamp.strftime('%H:%M')
        self.time_label = BodyLabel(time_str, self)
        self.time_label.setProperty("lightColor", QColor(96, 96, 96))
        self.time_label.setProperty("darkColor", QColor(206, 206, 206))
        
        self.header_layout.addWidget(self.sender_label)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.time_label)
        
        # Message content
        self.content_label = BodyLabel(self.content, self)
        self.content_label.setWordWrap(True)
        self.content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        self.layout.addLayout(self.header_layout)
        self.layout.addWidget(self.content_label)
        
        # Style based on sender
        if self.is_user:
            self.setStyleSheet("background-color: rgba(0, 120, 215, 0.1);")
        else:
            self.setStyleSheet("background-color: rgba(0, 160, 170, 0.1);")
        
        self.adjustSize()
    
    def adjustSize(self):
        """Adjust widget size based on content"""
        content_height = self.content_label.heightForWidth(self.content_label.width())
        total_height = content_height + 50  # Header + margins
        self.setFixedHeight(max(60, total_height))


class FileDropArea(QFrame):
    """File drop area for dragging files"""
    
    file_dropped = Signal(str)  # file_path
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setupUI()
    
    def setupUI(self):
        """Setup drop area UI"""
        self.setFrameStyle(QFrame.StyledPanel)
        self.setLineWidth(2)
        self.setMinimumHeight(100)
        
        self.layout = QVBoxLayout(self)
        
        # Drop icon
        self.drop_icon = QLabel("📁", self)
        self.drop_icon.setAlignment(Qt.AlignCenter)
        self.drop_icon.setStyleSheet("font-size: 24px;")
        
        # Drop text
        self.drop_text = BodyLabel("拖拽 .txt 文件到这里\n让我帮你总结内容吧~", self)
        self.drop_text.setAlignment(Qt.AlignCenter)
        self.drop_text.setProperty("lightColor", QColor(96, 96, 96))
        self.drop_text.setProperty("darkColor", QColor(206, 206, 206))
        
        self.layout.addWidget(self.drop_icon)
        self.layout.addWidget(self.drop_text)
        
        # Default style
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #ccc;
                border-radius: 8px;
                background-color: rgba(0, 0, 0, 0.05);
            }
        """)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                file_path = urls[0].toLocalFile()
                if file_path.endswith('.txt'):
                    event.acceptProposedAction()
                    self.setStyleSheet("""
                        QFrame {
                            border: 2px dashed #0078d4;
                            border-radius: 8px;
                            background-color: rgba(0, 120, 212, 0.1);
                        }
                    """)
                    return
        
        event.ignore()
    
    def dragLeaveEvent(self, event):
        """Handle drag leave event"""
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #ccc;
                border-radius: 8px;
                background-color: rgba(0, 0, 0, 0.05);
            }
        """)
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop event"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                file_path = urls[0].toLocalFile()
                if file_path.endswith('.txt'):
                    self.file_dropped.emit(file_path)
                    event.acceptProposedAction()
        
        # Reset style
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #ccc;
                border-radius: 8px;
                background-color: rgba(0, 0, 0, 0.05);
            }
        """)


class AIWorkerThread(QThread):
    """Worker thread for AI processing"""
    
    response_ready = Signal(str)
    error_occurred = Signal(str)
    
    def __init__(self, ai_manager: AIManager, prompt: str, history: List[Dict], parent=None):
        super().__init__(parent)
        self.ai_manager = ai_manager
        self.prompt = prompt
        self.history = history
    
    def run(self):
        """Run AI processing"""
        try:
            response = self.ai_manager.get_chat_response(self.prompt, self.history)
            self.response_ready.emit(response)
        except Exception as e:
            self.error_occurred.emit(str(e))


class AIChatWindow(QWidget):
    """AI Chat Window with enhanced functionality"""
    
    task_created = Signal(dict)
    bubble_requested = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.chat_history = []
        self.conversation_history = []
        self.is_processing = False
        
        # Initialize AI components
        self.ai_manager = AIManager(self)
        self.function_processor = FunctionCallingProcessor()
        self.file_processor = FileProcessor(self)
        self.task_manager = TaskManager(self)
        
        self.setupUI()
        self.connectSignals()
        self.show_welcome_message()
    
    def setupUI(self):
        """Setup chat window UI"""
        self.setWindowTitle("DyberPet AI聊天")
        self.setFixedSize(500, 600)
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        self.title_label = StrongBodyLabel("💬 与DyberPet聊天", self)
        
        # Chat area
        self.chat_scroll = QScrollArea(self)
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(5, 5, 5, 5)
        self.chat_layout.setSpacing(10)
        
        self.chat_scroll.setWidget(self.chat_container)
        
        # File drop area
        self.file_drop_area = FileDropArea(self)
        
        # Input area
        self.input_layout = QHBoxLayout()
        
        self.input_field = LineEdit(self)
        self.input_field.setPlaceholderText("输入消息或拖拽文件...")
        self.input_field.returnPressed.connect(self.send_message)
        
        self.send_button = PushButton("发送", self)
        self.send_button.clicked.connect(self.send_message)
        
        self.input_layout.addWidget(self.input_field)
        self.input_layout.addWidget(self.send_button)
        
        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.hide()
        
        # Status label
        self.status_label = BodyLabel("", self)
        self.status_label.setProperty("lightColor", QColor(96, 96, 96))
        self.status_label.setProperty("darkColor", QColor(206, 206, 206))
        
        # Add to main layout
        self.main_layout.addWidget(self.title_label)
        self.main_layout.addWidget(self.chat_scroll, 1)
        self.main_layout.addWidget(self.file_drop_area)
        self.main_layout.addLayout(self.input_layout)
        self.main_layout.addWidget(self.progress_bar)
        self.main_layout.addWidget(self.status_label)
        
        # Set window icon
        self.setWindowIcon(QIcon(os.path.join(basedir, "res/icons/dashboard.svg")))
    
    def connectSignals(self):
        """Connect signals"""
        self.file_drop_area.file_dropped.connect(self.handle_file_drop)
        self.file_processor.file_processed.connect(self.handle_file_processed)
        self.file_processor.error_occurred.connect(self.handle_file_error)
        self.task_manager.task_created.connect(self.handle_task_created)
    
    def show_welcome_message(self):
        """Show welcome message"""
        welcome_text = """你好，主人！我是DyberPet~ (´∀｀)

我可以帮你做这些事情：
• 📝 创建待办事项和提醒
• 🤔 回答各种问题
• 📄 总结文件内容（拖拽.txt文件）
• 💬 日常聊天互动

试试对我说："明天下午3点提醒我开会"吧~"""
        
        self.add_message(welcome_text, is_user=False)
    
    def add_message(self, content: str, is_user: bool = True, timestamp: Optional[datetime] = None):
        """Add a message to the chat"""
        message = ChatMessage(content, is_user, timestamp, self)
        self.chat_layout.addWidget(message)
        
        # Scroll to bottom
        QTimer.singleShot(100, self.scroll_to_bottom)
        
        # Update history
        self.chat_history.append({
            'content': content,
            'is_user': is_user,
            'timestamp': timestamp or datetime.now()
        })
        
        # Update conversation history for AI
        role = "user" if is_user else "assistant"
        self.conversation_history.append({
            'role': role,
            'content': content
        })
        
        # Keep only last 10 messages for AI context
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
    
    def scroll_to_bottom(self):
        """Scroll chat to bottom"""
        scrollbar = self.chat_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def send_message(self):
        """Send a message"""
        if self.is_processing:
            return
        
        message = self.input_field.text().strip()
        if not message:
            return
        
        # Add user message
        self.add_message(message, is_user=True)
        self.input_field.clear()
        
        # Process message
        self.process_message(message)
    
    def process_message(self, message: str):
        """Process user message"""
        self.is_processing = True
        self.show_processing_status("正在思考...")
        
        # Check if it's a task request
        task_info = self.function_processor.parse_task_command(message)
        
        if task_info.get('is_task_request', False):
            self.handle_task_request(task_info)
        else:
            # Regular chat
            self.handle_chat_request(message)
    
    def handle_task_request(self, task_info: Dict):
        """Handle task creation request"""
        if task_info.get('error'):
            self.add_message(task_info['error'], is_user=False)
            self.hide_processing_status()
            self.is_processing = False
            return
        
        task_content = task_info['task_content']
        reminder_time_str = task_info.get('reminder_time', '')
        
        # Parse reminder time
        reminder_time = None
        if reminder_time_str:
            reminder_time = self.function_processor.extract_time_info(reminder_time_str)
        
        # Create task
        try:
            task_id = self.task_manager.create_task(task_content, reminder_time)
            
            if task_id:
                confirmation_msg = self.function_processor.format_confirmation_message({
                    'task_content': task_content,
                    'reminder_time': reminder_time
                })
                self.add_message(confirmation_msg, is_user=False)
                
                # Emit task created signal
                self.task_created.emit({
                    'id': task_id,
                    'content': task_content,
                    'remind_time': reminder_time
                })
            else:
                self.add_message("主人，创建任务时出现了问题呢~ 请稍后再试试吧 (´･ω･`)", is_user=False)
                
        except Exception as e:
            self.add_message(f"主人，创建任务时出错了~ 错误信息：{str(e)} (´･ω･`)", is_user=False)
        
        self.hide_processing_status()
        self.is_processing = False
    
    def handle_chat_request(self, message: str):
        """Handle regular chat request"""
        # Create worker thread for AI processing
        self.ai_worker = AIWorkerThread(self.ai_manager, message, self.conversation_history, self)
        self.ai_worker.response_ready.connect(self.handle_ai_response)
        self.ai_worker.error_occurred.connect(self.handle_ai_error)
        self.ai_worker.start()
    
    def handle_ai_response(self, response: str):
        """Handle AI response"""
        self.add_message(response, is_user=False)
        self.hide_processing_status()
        self.is_processing = False
    
    def handle_ai_error(self, error: str):
        """Handle AI error"""
        error_msg = f"主人，我遇到了一点问题~ 错误信息：{error} (´･ω･`)"
        self.add_message(error_msg, is_user=False)
        self.hide_processing_status()
        self.is_processing = False
    
    def handle_file_drop(self, file_path: str):
        """Handle file drop"""
        if self.is_processing:
            return
        
        self.is_processing = True
        self.show_processing_status("正在处理文件...")
        
        # Add file info message
        file_name = os.path.basename(file_path)
        self.add_message(f"📄 文件: {file_name}", is_user=True)
        
        # Process file
        success, result = self.file_processor.process_file(file_path)
        
        if success:
            # Get AI summary
            file_info = self.file_processor.get_file_info(file_path)
            prompt = self.file_processor.format_file_summary_prompt(result, file_info)
            
            self.ai_worker = AIWorkerThread(self.ai_manager, prompt, [], self)
            self.ai_worker.response_ready.connect(self.handle_file_summary_response)
            self.ai_worker.error_occurred.connect(self.handle_file_summary_error)
            self.ai_worker.start()
        else:
            self.add_message(result, is_user=False)
            self.hide_processing_status()
            self.is_processing = False
    
    def handle_file_processed(self, content: str):
        """Handle file processed signal"""
        # This is called when file is successfully read
        pass
    
    def handle_file_error(self, error: str):
        """Handle file error"""
        self.add_message(error, is_user=False)
        self.hide_processing_status()
        self.is_processing = False
    
    def handle_file_summary_response(self, summary: str):
        """Handle file summary response"""
        self.add_message(summary, is_user=False)
        self.hide_processing_status()
        self.is_processing = False
    
    def handle_file_summary_error(self, error: str):
        """Handle file summary error"""
        error_msg = f"主人，总结文件时出现了问题~ 错误信息：{error} (´･ω･`)"
        self.add_message(error_msg, is_user=False)
        self.hide_processing_status()
        self.is_processing = False
    
    def handle_task_created(self, task_data: Dict):
        """Handle task created signal"""
        # This is called when a task is created
        pass
    
    def show_processing_status(self, message: str):
        """Show processing status"""
        self.status_label.setText(message)
        self.progress_bar.show()
        self.send_button.setEnabled(False)
    
    def hide_processing_status(self):
        """Hide processing status"""
        self.status_label.setText("")
        self.progress_bar.hide()
        self.send_button.setEnabled(True)
    
    def closeEvent(self, event):
        """Handle close event"""
        # Clean up worker thread
        if hasattr(self, 'ai_worker') and self.ai_worker.isRunning():
            self.ai_worker.terminate()
            self.ai_worker.wait()
        
        super().closeEvent(event)