"""
Chat Window UI Module
====================

Provides the chat interface for talking with DyberPet AI.
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
from qfluentwidgets import (
    FluentWindow, BodyLabel, PushButton, LineEdit, TextEdit, 
    ScrollArea, VBoxLayout, HBoxLayout, FluentIcon as FIF,
    InfoBar, InfoBarPosition, Theme, isDarkTheme, MessageBox
)

from .ai_manager import AIManager
import DyberPet.settings as settings

class ChatDatabase:
    """Database manager for chat history."""
    
    def __init__(self):
        self.db_path = os.path.join(settings.CONFIGDIR, 'data', 'chat_history.db')
        self.init_database()
    
    def init_database(self):
        """Initialize chat history database."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
                )
            ''')
            
            conn.commit()
    
    def create_session(self, name: str) -> int:
        """Create a new chat session."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO chat_sessions (name) VALUES (?)',
                (name,)
            )
            return cursor.lastrowid
    
    def get_sessions(self) -> List[Dict[str, Any]]:
        """Get all chat sessions."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, created_at, last_used 
                FROM chat_sessions 
                ORDER BY last_used DESC
            ''')
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    'id': row[0],
                    'name': row[1],
                    'created_at': row[2],
                    'last_used': row[3]
                })
            
            return sessions
    
    def rename_session(self, session_id: int, new_name: str):
        """Rename a chat session."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE chat_sessions SET name = ? WHERE id = ?',
                (new_name, session_id)
            )
    
    def delete_session(self, session_id: int):
        """Delete a chat session and all its messages."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM chat_messages WHERE session_id = ?', (session_id,))
            cursor.execute('DELETE FROM chat_sessions WHERE id = ?', (session_id,))
    
    def add_message(self, session_id: int, role: str, content: str):
        """Add a message to a session."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO chat_messages (session_id, role, content) VALUES (?, ?, ?)',
                (session_id, role, content)
            )
            # Update session last_used timestamp
            cursor.execute(
                'UPDATE chat_sessions SET last_used = CURRENT_TIMESTAMP WHERE id = ?',
                (session_id,)
            )
    
    def get_messages(self, session_id: int) -> List[Dict[str, Any]]:
        """Get all messages from a session."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT role, content, timestamp 
                FROM chat_messages 
                WHERE session_id = ? 
                ORDER BY timestamp ASC
            ''', (session_id,))
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'role': row[0],
                    'content': row[1],
                    'timestamp': row[2]
                })
            
            return messages

class ChatWorker(QThread):
    """Worker thread for AI chat processing."""
    
    response_ready = Signal(str)
    token_received = Signal(str)
    error_occurred = Signal(str)
    
    def __init__(self, ai_manager: AIManager, prompt: str, history: List[Dict[str, str]], pet_status: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.ai_manager = ai_manager
        self.prompt = prompt
        self.history = history
        self.pet_status = pet_status
        self.is_cancelled = False
    
    def run(self):
        """Run the chat processing."""
        try:
            def stream_callback(token: str):
                if not self.is_cancelled:
                    self.token_received.emit(token)
            
            response = self.ai_manager.get_chat_response(
                self.prompt, 
                self.history, 
                stream_callback=stream_callback,
                pet_status=self.pet_status
            )
            
            if not self.is_cancelled and response:
                self.response_ready.emit(response)
        except Exception as e:
            if not self.is_cancelled:
                self.error_occurred.emit(str(e))
    
    def cancel(self):
        """Cancel the chat processing."""
        self.is_cancelled = True

class MessageWidget(QWidget):
    """Widget for displaying a single chat message."""
    
    def __init__(self, role: str, content: str, timestamp: str = None):
        super().__init__()
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now().strftime("%H:%M")
        self.init_ui()
    
    def init_ui(self):
        """Initialize the message widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Message header
        header_layout = QHBoxLayout()
        
        # Role label
        role_text = "主人" if self.role == "user" else "DyberPet"
        role_label = BodyLabel(role_text)
        role_label.setStyleSheet(f"color: {'#0078d4' if self.role == 'user' else '#7b68ee'}; font-weight: bold;")
        
        # Timestamp
        time_label = BodyLabel(self.timestamp)
        time_label.setStyleSheet("color: #666; font-size: 10px;")
        
        header_layout.addWidget(role_label)
        header_layout.addStretch()
        header_layout.addWidget(time_label)
        
        # Message content
        content_widget = TextEdit()
        content_widget.setPlainText(self.content)
        content_widget.setReadOnly(True)
        content_widget.setMaximumHeight(200)
        content_widget.setStyleSheet("""
            QTextEdit {
                background-color: %s;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 8px;
                font-size: 14px;
                line-height: 1.4;
            }
        """ % ("#f8f9fa" if self.role == "user" else "#e8f4fd"))
        
        layout.addLayout(header_layout)
        layout.addWidget(content_widget)

class ChatWindow(FluentWindow):
    """Main chat window for DyberPet AI."""
    
    def __init__(self):
        super().__init__()
        self.ai_manager = AIManager()
        self.chat_db = ChatDatabase()
        self.current_session_id = None
        self.current_worker = None
        self.current_response_widget = None
        
        self.init_ui()
        self.load_sessions()
        
        # Connect AI manager signals
        self.ai_manager.error_occurred.connect(self.show_error)
    
    def init_ui(self):
        """Initialize the chat window UI."""
        self.setWindowTitle("与DyberPet聊天")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
        # Create main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Main layout
        main_layout = QHBoxLayout(main_widget)
        
        # Left sidebar for session management
        self.create_sidebar()
        main_layout.addWidget(self.sidebar, 0)
        
        # Right chat area
        self.create_chat_area()
        main_layout.addWidget(self.chat_area, 1)
    
    def create_sidebar(self):
        """Create the session management sidebar."""
        self.sidebar = QWidget()
        self.sidebar.setMaximumWidth(250)
        self.sidebar.setStyleSheet("background-color: #f5f5f5; border-right: 1px solid #e0e0e0;")
        
        layout = QVBoxLayout(self.sidebar)
        
        # Title
        title_label = BodyLabel("聊天记录")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333; margin: 10px 0;")
        layout.addWidget(title_label)
        
        # New chat button
        new_chat_btn = PushButton("新建聊天")
        new_chat_btn.setIcon(FIF.ADD)
        new_chat_btn.clicked.connect(self.new_chat_session)
        layout.addWidget(new_chat_btn)
        
        # Session list
        self.session_list = QListWidget()
        self.session_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                padding: 10px;
                margin: 2px 0;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        self.session_list.itemClicked.connect(self.load_session)
        self.session_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.session_list.customContextMenuRequested.connect(self.show_session_context_menu)
        
        layout.addWidget(self.session_list)
        layout.addStretch()
    
    def create_chat_area(self):
        """Create the main chat area."""
        self.chat_area = QWidget()
        layout = QVBoxLayout(self.chat_area)
        
        # Chat messages area
        self.messages_scroll = ScrollArea()
        self.messages_scroll.setWidgetResizable(True)
        self.messages_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.addStretch()
        
        self.messages_scroll.setWidget(self.messages_widget)
        layout.addWidget(self.messages_scroll)
        
        # Input area
        self.create_input_area()
        layout.addWidget(self.input_area)
    
    def create_input_area(self):
        """Create the message input area."""
        self.input_area = QWidget()
        self.input_area.setMaximumHeight(120)
        layout = QVBoxLayout(self.input_area)
        
        # Input field
        self.message_input = TextEdit()
        self.message_input.setPlaceholderText("输入消息...")
        self.message_input.setMaximumHeight(80)
        self.message_input.installEventFilter(self)
        layout.addWidget(self.message_input)
        
        # Button area
        button_layout = QHBoxLayout()
        
        # AI status indicator
        self.ai_status_label = BodyLabel("AI: 准备就绪")
        self.ai_status_label.setStyleSheet("color: #28a745; font-size: 12px;")
        button_layout.addWidget(self.ai_status_label)
        
        button_layout.addStretch()
        
        # Stop button (initially hidden)
        self.stop_button = PushButton("停止")
        self.stop_button.setIcon(FIF.PAUSE)
        self.stop_button.clicked.connect(self.stop_generation)
        self.stop_button.hide()
        button_layout.addWidget(self.stop_button)
        
        # Send button
        self.send_button = PushButton("发送")
        self.send_button.setIcon(FIF.SEND)
        self.send_button.clicked.connect(self.send_message)
        button_layout.addWidget(self.send_button)
        
        layout.addLayout(button_layout)
    
    def eventFilter(self, obj, event):
        """Handle keyboard events."""
        if obj == self.message_input and event.type() == event.KeyPress:
            if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
                self.send_message()
                return True
        return super().eventFilter(obj, event)
    
    def load_sessions(self):
        """Load chat sessions from database."""
        self.session_list.clear()
        sessions = self.chat_db.get_sessions()
        
        for session in sessions:
            item = QListWidgetItem(session['name'])
            item.setData(Qt.UserRole, session['id'])
            self.session_list.addItem(item)
        
        # Select first session if available
        if sessions:
            self.session_list.setCurrentRow(0)
            self.load_session(self.session_list.currentItem())
    
    def new_chat_session(self):
        """Create a new chat session."""
        name = f"聊天 {datetime.now().strftime('%m-%d %H:%M')}"
        session_id = self.chat_db.create_session(name)
        
        # Add to list
        item = QListWidgetItem(name)
        item.setData(Qt.UserRole, session_id)
        self.session_list.insertItem(0, item)
        self.session_list.setCurrentRow(0)
        
        # Load the new session
        self.load_session(item)
    
    def load_session(self, item):
        """Load a chat session."""
        if not item:
            return
        
        session_id = item.data(Qt.UserRole)
        self.current_session_id = session_id
        
        # Clear current messages
        self.clear_messages()
        
        # Load messages from database
        messages = self.chat_db.get_messages(session_id)
        
        for message in messages:
            self.add_message_widget(message['role'], message['content'], message['timestamp'])
        
        # Update UI
        self.update_ai_status("AI: 准备就绪")
        self.message_input.setFocus()
    
    def clear_messages(self):
        """Clear all message widgets."""
        # Remove all widgets except the stretch
        for i in reversed(range(self.messages_layout.count() - 1)):
            child = self.messages_layout.itemAt(i).widget()
            if child:
                child.deleteLater()
    
    def add_message_widget(self, role: str, content: str, timestamp: str = None):
        """Add a message widget to the chat area."""
        message_widget = MessageWidget(role, content, timestamp)
        # Insert before the stretch
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, message_widget)
        
        # Scroll to bottom
        QTimer.singleShot(50, self.scroll_to_bottom)
    
    def scroll_to_bottom(self):
        """Scroll the messages area to the bottom."""
        scrollbar = self.messages_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def send_message(self):
        """Send a message to the AI."""
        if not self.current_session_id:
            self.new_chat_session()
        
        message = self.message_input.toPlainText().strip()
        if not message:
            return
        
        # Check if AI is enabled
        if not self.ai_manager.config.is_enabled():
            self.show_error("AI功能未启用，请在设置中启用AI功能")
            return
        
        # Add user message
        self.add_message_widget("user", message)
        self.chat_db.add_message(self.current_session_id, "user", message)
        
        # Clear input
        self.message_input.clear()
        
        # Get conversation history
        history = self.get_conversation_history()
        
        # Get pet status (placeholder for now)
        pet_status = self.get_pet_status()
        
        # Start AI response
        self.start_ai_response(message, history, pet_status)
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history for AI context."""
        if not self.current_session_id:
            return []
        
        messages = self.chat_db.get_messages(self.current_session_id)
        history = []
        
        for msg in messages[:-1]:  # Exclude the last message (current user message)
            history.append({
                'role': msg['role'],
                'content': msg['content']
            })
        
        return history
    
    def get_pet_status(self) -> Dict[str, Any]:
        """Get current pet status for AI context."""
        # Placeholder implementation - integrate with actual pet status
        return {
            'pet_name': 'DyberPet',
            'mood': '开心',
            'hunger': '正常',
            'cleanliness': '干净',
            'favorability': '很高'
        }
    
    def start_ai_response(self, prompt: str, history: List[Dict[str, str]], pet_status: Dict[str, Any]):
        """Start AI response generation."""
        self.update_ai_status("AI: 思考中...")
        self.send_button.setEnabled(False)
        self.stop_button.show()
        
        # Create response widget
        self.current_response_widget = MessageWidget("assistant", "")
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, self.current_response_widget)
        
        # Start worker thread
        self.current_worker = ChatWorker(self.ai_manager, prompt, history, pet_status)
        self.current_worker.token_received.connect(self.on_token_received)
        self.current_worker.response_ready.connect(self.on_response_ready)
        self.current_worker.error_occurred.connect(self.on_ai_error)
        self.current_worker.start()
    
    def on_token_received(self, token: str):
        """Handle streaming token received."""
        if self.current_response_widget:
            current_content = self.current_response_widget.content
            new_content = current_content + token
            self.current_response_widget.content = new_content
            
            # Update the text widget
            text_widget = self.current_response_widget.findChild(TextEdit)
            if text_widget:
                text_widget.setPlainText(new_content)
        
        self.scroll_to_bottom()
    
    def on_response_ready(self, response: str):
        """Handle complete AI response."""
        if self.current_session_id and response:
            self.chat_db.add_message(self.current_session_id, "assistant", response)
        
        self.finish_ai_response()
    
    def on_ai_error(self, error: str):
        """Handle AI error."""
        self.show_error(f"AI错误: {error}")
        
        # Remove the incomplete response widget
        if self.current_response_widget:
            self.current_response_widget.deleteLater()
            self.current_response_widget = None
        
        self.finish_ai_response()
    
    def finish_ai_response(self):
        """Finish AI response generation."""
        self.update_ai_status("AI: 准备就绪")
        self.send_button.setEnabled(True)
        self.stop_button.hide()
        self.current_worker = None
        self.current_response_widget = None
        self.message_input.setFocus()
    
    def stop_generation(self):
        """Stop AI response generation."""
        if self.current_worker:
            self.current_worker.cancel()
            self.current_worker.wait()
        
        self.finish_ai_response()
    
    def update_ai_status(self, status: str):
        """Update AI status display."""
        self.ai_status_label.setText(status)
        
        if "错误" in status or "失败" in status:
            self.ai_status_label.setStyleSheet("color: #dc3545; font-size: 12px;")
        elif "思考中" in status:
            self.ai_status_label.setStyleSheet("color: #ffc107; font-size: 12px;")
        else:
            self.ai_status_label.setStyleSheet("color: #28a745; font-size: 12px;")
    
    def show_error(self, message: str):
        """Show error message."""
        InfoBar.error(
            title="错误",
            content=message,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
    
    def show_session_context_menu(self, pos):
        """Show context menu for session management."""
        item = self.session_list.itemAt(pos)
        if not item:
            return
        
        menu = QMenu(self)
        
        rename_action = QAction("重命名", self)
        rename_action.triggered.connect(lambda: self.rename_session(item))
        menu.addAction(rename_action)
        
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self.delete_session(item))
        menu.addAction(delete_action)
        
        menu.exec(self.session_list.mapToGlobal(pos))
    
    def rename_session(self, item):
        """Rename a chat session."""
        session_id = item.data(Qt.UserRole)
        current_name = item.text()
        
        new_name, ok = QInputDialog.getText(self, "重命名聊天", "请输入新的聊天名称:", text=current_name)
        
        if ok and new_name.strip():
            self.chat_db.rename_session(session_id, new_name.strip())
            item.setText(new_name.strip())
    
    def delete_session(self, item):
        """Delete a chat session."""
        session_id = item.data(Qt.UserRole)
        session_name = item.text()
        
        reply = MessageBox.question(
            self,
            "确认删除",
            f"确定要删除聊天"{session_name}"吗？\n此操作不可恢复。",
            MessageBox.Yes | MessageBox.No,
            MessageBox.No
        )
        
        if reply == MessageBox.Yes:
            self.chat_db.delete_session(session_id)
            self.session_list.takeItem(self.session_list.row(item))
            
            # If this was the current session, clear the chat area
            if session_id == self.current_session_id:
                self.current_session_id = None
                self.clear_messages()
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.current_worker:
            self.current_worker.cancel()
            self.current_worker.wait()
        
        event.accept()