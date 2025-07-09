# coding:utf-8
"""
Enhanced Task Panel UI for AI-managed tasks
Integrates with the AI task management system
"""

import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QIcon, QPixmap, QColor
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QSpacerItem, QSizePolicy, QScrollArea, QFrame)

from qfluentwidgets import (CardWidget, StrongBodyLabel, BodyLabel, 
                           TransparentToolButton, PushButton, InfoBadge,
                           FluentIcon as FIF, MessageBox, LineEdit)

import DyberPet.settings as settings
from DyberPet.ai.task_manager import TaskManager

basedir = settings.BASEDIR
PANEL_W = 460

class AITaskCard(CardWidget):
    """Individual task card for AI-managed tasks"""
    
    completed = Signal(str)  # task_id
    deleted = Signal(str)    # task_id
    edited = Signal(str, str)  # task_id, new_content
    
    def __init__(self, task_data: Dict, parent=None):
        super().__init__(parent)
        self.task_data = task_data
        self.task_id = task_data['id']
        self.is_editing = False
        self.setupUI()
        self.update_display()
    
    def setupUI(self):
        """Setup the task card UI"""
        self.setFixedWidth(PANEL_W - 20)
        self.setMinimumHeight(80)
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 10, 15, 10)
        
        # Top row - content and actions
        self.top_layout = QHBoxLayout()
        
        # Task content
        self.content_label = BodyLabel(self)
        self.content_label.setWordWrap(True)
        self.content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        # Edit field (hidden by default)
        self.edit_field = LineEdit(self)
        self.edit_field.hide()
        
        # Action buttons
        self.action_layout = QHBoxLayout()
        
        # Complete button
        self.complete_btn = TransparentToolButton(FIF.COMPLETED, self)
        self.complete_btn.setFixedSize(32, 32)
        self.complete_btn.setToolTip("完成任务")
        self.complete_btn.clicked.connect(self.complete_task)
        
        # Edit button
        self.edit_btn = TransparentToolButton(FIF.EDIT, self)
        self.edit_btn.setFixedSize(32, 32)
        self.edit_btn.setToolTip("编辑任务")
        self.edit_btn.clicked.connect(self.toggle_edit)
        
        # Delete button
        self.delete_btn = TransparentToolButton(FIF.DELETE, self)
        self.delete_btn.setFixedSize(32, 32)
        self.delete_btn.setToolTip("删除任务")
        self.delete_btn.clicked.connect(self.delete_task)
        
        # Status badge
        self.status_badge = InfoBadge(self)
        self.status_badge.setLevel(InfoBadge.INFORMATION)
        
        # Add to action layout
        self.action_layout.addWidget(self.complete_btn)
        self.action_layout.addWidget(self.edit_btn)
        self.action_layout.addWidget(self.delete_btn)
        self.action_layout.addWidget(self.status_badge)
        
        # Add to top layout
        self.top_layout.addWidget(self.content_label, 1)
        self.top_layout.addWidget(self.edit_field, 1)
        self.top_layout.addLayout(self.action_layout)
        
        # Bottom row - time info
        self.bottom_layout = QHBoxLayout()
        
        # Time info
        self.time_label = BodyLabel(self)
        self.time_label.setProperty("lightColor", QColor(96, 96, 96))
        self.time_label.setProperty("darkColor", QColor(206, 206, 206))
        
        # Reminder icon
        self.reminder_icon = TransparentToolButton(FIF.ALARM, self)
        self.reminder_icon.setFixedSize(16, 16)
        self.reminder_icon.setEnabled(False)
        
        self.bottom_layout.addWidget(self.reminder_icon)
        self.bottom_layout.addWidget(self.time_label)
        self.bottom_layout.addStretch()
        
        # Add to main layout
        self.main_layout.addLayout(self.top_layout)
        self.main_layout.addLayout(self.bottom_layout)
    
    def update_display(self):
        """Update the display based on task data"""
        content = self.task_data.get('content', '')
        status = self.task_data.get('status', 'pending')
        remind_time = self.task_data.get('remind_time')
        created_time = self.task_data.get('created_time')
        
        # Update content
        self.content_label.setText(content)
        self.edit_field.setText(content)
        
        # Update status badge
        if status == 'pending':
            self.status_badge.setText("待完成")
            self.status_badge.setLevel(InfoBadge.INFORMATION)
        elif status == 'completed':
            self.status_badge.setText("已完成")
            self.status_badge.setLevel(InfoBadge.SUCCESS)
        elif status == 'expired':
            self.status_badge.setText("已过期")
            self.status_badge.setLevel(InfoBadge.WARNING)
        
        # Update time display
        time_parts = []
        if remind_time:
            if isinstance(remind_time, datetime):
                time_str = remind_time.strftime('%m-%d %H:%M')
                time_parts.append(f"提醒：{time_str}")
            self.reminder_icon.show()
        else:
            self.reminder_icon.hide()
        
        if created_time:
            if isinstance(created_time, datetime):
                created_str = created_time.strftime('%m-%d %H:%M')
                time_parts.append(f"创建：{created_str}")
        
        self.time_label.setText(" | ".join(time_parts))
        
        # Update button states
        if status == 'completed':
            self.complete_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)
            self.setStyleSheet("background-color: rgba(0, 255, 0, 0.1);")
        elif status == 'expired':
            self.complete_btn.setEnabled(False)
            self.setStyleSheet("background-color: rgba(255, 165, 0, 0.1);")
        else:
            self.complete_btn.setEnabled(True)
            self.edit_btn.setEnabled(True)
            self.setStyleSheet("")
    
    def complete_task(self):
        """Mark task as completed"""
        if self.task_data.get('status') != 'completed':
            self.completed.emit(self.task_id)
    
    def delete_task(self):
        """Delete the task"""
        reply = MessageBox.question(
            self, 
            "确认删除",
            "确定要删除这个任务吗？",
            MessageBox.Yes | MessageBox.No,
            MessageBox.No
        )
        
        if reply == MessageBox.Yes:
            self.deleted.emit(self.task_id)
    
    def toggle_edit(self):
        """Toggle edit mode"""
        if not self.is_editing:
            self.start_edit()
        else:
            self.save_edit()
    
    def start_edit(self):
        """Start editing mode"""
        self.is_editing = True
        self.content_label.hide()
        self.edit_field.show()
        self.edit_field.setFocus()
        self.edit_field.selectAll()
        self.edit_btn.setIcon(FIF.SAVE)
        self.edit_btn.setToolTip("保存")
    
    def save_edit(self):
        """Save edit changes"""
        new_content = self.edit_field.text().strip()
        if new_content and new_content != self.task_data.get('content', ''):
            self.edited.emit(self.task_id, new_content)
        
        self.is_editing = False
        self.edit_field.hide()
        self.content_label.show()
        self.edit_btn.setIcon(FIF.EDIT)
        self.edit_btn.setToolTip("编辑任务")
    
    def update_task_data(self, new_data: Dict):
        """Update task data and refresh display"""
        self.task_data.update(new_data)
        self.update_display()


class AITaskPanel(CardWidget):
    """Enhanced Task Panel with AI integration"""
    
    addCoins = Signal(int)
    task_reminder = Signal(dict)
    
    def __init__(self, sizeHintdb: tuple, parent=None):
        super().__init__(parent)
        self.sizeHintdb = sizeHintdb
        self.task_manager = TaskManager(self)
        self.task_cards = {}  # task_id -> AITaskCard
        self.refresh_timer = QTimer(self)
        self.setupUI()
        self.connectSignals()
        self.load_tasks()
        self.start_refresh_timer()
    
    def setupUI(self):
        """Setup the task panel UI"""
        self.setFixedSize(QSize(PANEL_W, 400))
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        self.header_layout = QHBoxLayout()
        
        # Title
        self.title_label = StrongBodyLabel("AI智能任务", self)
        
        # Statistics
        self.stats_layout = QHBoxLayout()
        self.pending_badge = InfoBadge("0", self)
        self.pending_badge.setLevel(InfoBadge.INFORMATION)
        self.completed_badge = InfoBadge("0", self)
        self.completed_badge.setLevel(InfoBadge.SUCCESS)
        
        self.stats_layout.addWidget(QLabel("待完成:"))
        self.stats_layout.addWidget(self.pending_badge)
        self.stats_layout.addWidget(QLabel("已完成:"))
        self.stats_layout.addWidget(self.completed_badge)
        
        # Refresh button
        self.refresh_btn = TransparentToolButton(FIF.SYNC, self)
        self.refresh_btn.setFixedSize(32, 32)
        self.refresh_btn.setToolTip("刷新任务")
        self.refresh_btn.clicked.connect(self.refresh_tasks)
        
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()
        self.header_layout.addLayout(self.stats_layout)
        self.header_layout.addWidget(self.refresh_btn)
        
        # Scroll area for tasks
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Task container
        self.task_container = QWidget()
        self.task_layout = QVBoxLayout(self.task_container)
        self.task_layout.setContentsMargins(5, 5, 5, 5)
        self.task_layout.setSpacing(10)
        
        # Empty state
        self.empty_label = BodyLabel("暂无AI任务\n通过聊天创建新任务吧~", self)
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setProperty("lightColor", QColor(96, 96, 96))
        self.empty_label.setProperty("darkColor", QColor(206, 206, 206))
        self.task_layout.addWidget(self.empty_label)
        
        self.scroll_area.setWidget(self.task_container)
        
        # Add to main layout
        self.main_layout.addLayout(self.header_layout)
        self.main_layout.addWidget(self.scroll_area)
    
    def connectSignals(self):
        """Connect signals"""
        self.task_manager.task_created.connect(self.on_task_created)
        self.task_manager.task_updated.connect(self.on_task_updated)
        self.task_manager.task_deleted.connect(self.on_task_deleted)
        self.refresh_timer.timeout.connect(self.check_reminders)
    
    def start_refresh_timer(self):
        """Start the refresh timer"""
        self.refresh_timer.start(60000)  # Check every minute
    
    def load_tasks(self):
        """Load tasks from database"""
        try:
            tasks = self.task_manager.get_tasks()
            self.clear_task_cards()
            
            if tasks:
                self.empty_label.hide()
                for task in tasks:
                    self.add_task_card(task)
            else:
                self.empty_label.show()
            
            self.update_statistics()
            
        except Exception as e:
            print(f"Error loading tasks: {e}")
    
    def add_task_card(self, task_data: Dict):
        """Add a new task card"""
        task_id = task_data['id']
        
        if task_id not in self.task_cards:
            card = AITaskCard(task_data, self)
            card.completed.connect(self.on_task_completed)
            card.deleted.connect(self.on_task_delete_requested)
            card.edited.connect(self.on_task_edited)
            
            self.task_cards[task_id] = card
            self.task_layout.insertWidget(self.task_layout.count() - 1, card)
            
            if self.empty_label.isVisible():
                self.empty_label.hide()
    
    def clear_task_cards(self):
        """Clear all task cards"""
        for card in self.task_cards.values():
            card.deleteLater()
        self.task_cards.clear()
    
    def update_statistics(self):
        """Update task statistics"""
        stats = self.task_manager.get_task_statistics()
        self.pending_badge.setText(str(stats.get('pending', 0)))
        self.completed_badge.setText(str(stats.get('completed', 0)))
    
    def refresh_tasks(self):
        """Refresh task list"""
        self.load_tasks()
    
    def check_reminders(self):
        """Check for tasks that need reminders"""
        try:
            pending_reminders = self.task_manager.get_pending_reminders()
            for task in pending_reminders:
                self.task_reminder.emit(task)
                # Mark as reminded to avoid duplicate reminders
                # (In a real implementation, you'd add a 'reminded' flag)
        except Exception as e:
            print(f"Error checking reminders: {e}")
    
    def on_task_created(self, task_data: Dict):
        """Handle task creation"""
        self.add_task_card(task_data)
        self.update_statistics()
    
    def on_task_updated(self, task_data: Dict):
        """Handle task update"""
        task_id = task_data['id']
        if task_id in self.task_cards:
            self.task_cards[task_id].update_task_data(task_data)
        self.update_statistics()
    
    def on_task_deleted(self, task_id: str):
        """Handle task deletion"""
        if task_id in self.task_cards:
            card = self.task_cards.pop(task_id)
            card.deleteLater()
            
            if not self.task_cards:
                self.empty_label.show()
        
        self.update_statistics()
    
    def on_task_completed(self, task_id: str):
        """Handle task completion"""
        if self.task_manager.mark_completed(task_id):
            # Award coins for task completion
            self.addCoins.emit(settings.SINGLETASK_REWARD)
    
    def on_task_delete_requested(self, task_id: str):
        """Handle task deletion request"""
        self.task_manager.delete_task(task_id)
    
    def on_task_edited(self, task_id: str, new_content: str):
        """Handle task editing"""
        self.task_manager.update_task(task_id, content=new_content)
    
    def create_task_from_ai(self, content: str, remind_time: Optional[datetime] = None) -> str:
        """Create a new task from AI interaction"""
        try:
            task_id = self.task_manager.create_task(content, remind_time)
            return task_id
        except Exception as e:
            print(f"Error creating AI task: {e}")
            return ""