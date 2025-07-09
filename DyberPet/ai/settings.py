"""
AI Settings Interface
====================

AI configuration interface for DyberPet settings panel.
"""

import os
import sys
from typing import Dict, Any, Optional

# Use PySide6 consistently with the main application
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QFont, QIcon

# Try to import qfluentwidgets, fall back to standard Qt widgets
try:
    from qfluentwidgets import (
        BodyLabel, PushButton, LineEdit, ComboBox, SwitchButton,
        CardWidget, ScrollArea, VBoxLayout, HBoxLayout, FluentIcon as FIF,
        InfoBar, InfoBarPosition, MessageBox, PasswordLineEdit,
        FluentStyleSheet, Theme
    )
except ImportError:
    # Fallback to standard Qt widgets
    class BodyLabel(QLabel):
        pass
    class PushButton(QPushButton):
        pass
    class LineEdit(QLineEdit):
        pass
    class ComboBox(QComboBox):
        pass
    class SwitchButton(QCheckBox):
        pass
    class CardWidget(QWidget):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.setStyleSheet("QWidget { border: 1px solid #e0e0e0; border-radius: 8px; background-color: #f8f9fa; padding: 10px; }")
    class ScrollArea(QScrollArea):
        pass
    class VBoxLayout(QVBoxLayout):
        pass
    class HBoxLayout(QHBoxLayout):
        pass
    class InfoBar:
        @staticmethod
        def success(title, content, parent=None, **kwargs):
            QMessageBox.information(parent, title, content)
        @staticmethod
        def error(title, content, parent=None, **kwargs):
            QMessageBox.critical(parent, title, content)
    class InfoBarPosition:
        TOP = 0
    class MessageBox:
        @staticmethod
        def information(parent, title, text, **kwargs):
            QMessageBox.information(parent, title, text)
    class PasswordLineEdit(QLineEdit):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.setEchoMode(QLineEdit.EchoMode.Password)
    class FluentStyleSheet:
        pass
    class Theme:
        pass
    class FIF:
        SETTING = None
        ROBOT = None
        SAVE = None
        CANCEL = None

from ..ai.config import AIConfig
from ..ai.ai_manager import AIManager

class APIKeyValidationWorker(QThread):
    """Worker thread for API key validation."""
    
    validation_completed = Signal(bool, str)
    
    def __init__(self, ai_manager: AIManager, model_name: str, api_key: str):
        super().__init__()
        self.ai_manager = ai_manager
        self.model_name = model_name
        self.api_key = api_key
    
    def run(self):
        """Run API key validation."""
        try:
            is_valid = self.ai_manager.validate_api_key(self.model_name, self.api_key)
            message = "API Key验证成功" if is_valid else "API Key验证失败"
            self.validation_completed.emit(is_valid, message)
        except Exception as e:
            self.validation_completed.emit(False, f"验证过程中发生错误: {str(e)}")

class AISettingsWidget(QWidget):
    """AI settings widget for integration with DyberPet settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ai_config = AIConfig()
        self.ai_manager = AIManager()
        self.validation_worker = None
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize the AI settings UI."""
        layout = QVBoxLayout(self)
        
        # Main title
        title = BodyLabel("AI 设置")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # AI enabled toggle
        self.create_ai_toggle(layout)
        
        # Model selection
        self.create_model_selection(layout)
        
        # API key configuration
        self.create_api_key_section(layout)
        
        # Advanced settings
        self.create_advanced_settings(layout)
        
        # Save/Cancel buttons
        self.create_action_buttons(layout)
        
        layout.addStretch()
    
    def create_ai_toggle(self, layout):
        """Create AI enable/disable toggle."""
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        
        # Title
        title = BodyLabel("AI 功能总开关")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        card_layout.addWidget(title)
        
        # Description
        desc = BodyLabel("启用或禁用所有AI功能")
        desc.setStyleSheet("color: #666; margin-bottom: 10px;")
        card_layout.addWidget(desc)
        
        # Toggle switch
        toggle_layout = QHBoxLayout()
        toggle_layout.addWidget(BodyLabel("AI功能:"))
        
        self.ai_enabled_switch = SwitchButton()
        toggle_layout.addWidget(self.ai_enabled_switch)
        toggle_layout.addStretch()
        
        card_layout.addLayout(toggle_layout)
        layout.addWidget(card)
    
    def create_model_selection(self, layout):
        """Create model selection section."""
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        
        # Title
        title = BodyLabel("AI 模型选择")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        card_layout.addWidget(title)
        
        # Model combo box
        model_layout = QHBoxLayout()
        model_layout.addWidget(BodyLabel("选择模型:"))
        
        self.model_combo = ComboBox()
        models = self.ai_config.get_supported_models()
        for model_id, model_info in models.items():
            self.model_combo.addItem(model_info['name'], model_id)
        
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        
        card_layout.addLayout(model_layout)
        layout.addWidget(card)
    
    def create_api_key_section(self, layout):
        """Create API key configuration section."""
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        
        # Title
        title = BodyLabel("API Key 配置")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        card_layout.addWidget(title)
        
        # API key input
        key_layout = QHBoxLayout()
        key_layout.addWidget(BodyLabel("API Key:"))
        
        self.api_key_input = PasswordLineEdit()
        self.api_key_input.setPlaceholderText("请输入API Key")
        key_layout.addWidget(self.api_key_input)
        
        # Validate button
        self.validate_button = PushButton("验证")
        self.validate_button.clicked.connect(self.validate_api_key)
        key_layout.addWidget(self.validate_button)
        
        card_layout.addLayout(key_layout)
        
        # Status label
        self.api_status_label = BodyLabel("未配置")
        self.api_status_label.setStyleSheet("color: #666; margin-top: 5px;")
        card_layout.addWidget(self.api_status_label)
        
        layout.addWidget(card)
    
    def create_advanced_settings(self, layout):
        """Create advanced settings section."""
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        
        # Title
        title = BodyLabel("高级设置")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        card_layout.addWidget(title)
        
        # Stream toggle
        stream_layout = QHBoxLayout()
        stream_layout.addWidget(BodyLabel("流式输出:"))
        
        self.stream_switch = SwitchButton()
        stream_layout.addWidget(self.stream_switch)
        stream_layout.addStretch()
        
        card_layout.addLayout(stream_layout)
        
        # Context limit
        context_layout = QHBoxLayout()
        context_layout.addWidget(BodyLabel("上下文限制:"))
        
        self.context_input = LineEdit()
        self.context_input.setPlaceholderText("4096")
        context_layout.addWidget(self.context_input)
        context_layout.addWidget(BodyLabel("tokens"))
        context_layout.addStretch()
        
        card_layout.addLayout(context_layout)
        
        # Rate limit
        rate_layout = QHBoxLayout()
        rate_layout.addWidget(BodyLabel("请求限制:"))
        
        self.rate_input = LineEdit()
        self.rate_input.setPlaceholderText("5")
        rate_layout.addWidget(self.rate_input)
        rate_layout.addWidget(BodyLabel("次/分钟"))
        rate_layout.addStretch()
        
        card_layout.addLayout(rate_layout)
        
        layout.addWidget(card)
    
    def create_action_buttons(self, layout):
        """Create save/cancel action buttons."""
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Cancel button
        cancel_button = PushButton("取消")
        cancel_button.clicked.connect(self.cancel_changes)
        button_layout.addWidget(cancel_button)
        
        # Save button
        save_button = PushButton("保存")
        save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(save_button)
        
        layout.addLayout(button_layout)
    
    def load_settings(self):
        """Load current settings into UI."""
        try:
            # Load AI enabled state
            self.ai_enabled_switch.setChecked(self.ai_config.is_enabled())
            
            # Load current model
            current_model = self.ai_config.get_current_model()
            for i in range(self.model_combo.count()):
                if self.model_combo.itemData(i) == current_model:
                    self.model_combo.setCurrentIndex(i)
                    break
            
            # Load API key status
            self.update_api_key_status()
            
            # Load advanced settings
            self.stream_switch.setChecked(self.ai_config.is_stream_enabled())
            self.context_input.setText(str(self.ai_config.get_context_limit()))
            self.rate_input.setText(str(self.ai_config.get_rate_limit()))
            
        except Exception as e:
            self.show_error(f"加载设置失败: {str(e)}")
    
    def update_api_key_status(self):
        """Update API key status display."""
        try:
            current_model = self.model_combo.itemData(self.model_combo.currentIndex())
            if current_model:
                model_info = self.ai_config.get_model_info(current_model)
                if model_info.get('requires_api_key', False):
                    has_key = self.ai_config.get_api_key(current_model) is not None
                    if has_key:
                        self.api_status_label.setText("✓ 已配置")
                        self.api_status_label.setStyleSheet("color: #28a745;")
                    else:
                        self.api_status_label.setText("✗ 未配置")
                        self.api_status_label.setStyleSheet("color: #dc3545;")
                else:
                    self.api_status_label.setText("✓ 无需API Key")
                    self.api_status_label.setStyleSheet("color: #28a745;")
        except Exception as e:
            self.api_status_label.setText(f"错误: {str(e)}")
            self.api_status_label.setStyleSheet("color: #dc3545;")
    
    def validate_api_key(self):
        """Validate the entered API key."""
        try:
            api_key = self.api_key_input.text().strip()
            if not api_key:
                self.show_error("请输入API Key")
                return
            
            current_model = self.model_combo.itemData(self.model_combo.currentIndex())
            if not current_model:
                self.show_error("请选择模型")
                return
            
            # Update UI state
            self.validate_button.setEnabled(False)
            self.validate_button.setText("验证中...")
            
            # Start validation worker
            self.validation_worker = APIKeyValidationWorker(
                self.ai_manager, current_model, api_key
            )
            self.validation_worker.validation_completed.connect(self.on_validation_completed)
            self.validation_worker.start()
            
        except Exception as e:
            self.show_error(f"验证失败: {str(e)}")
            self.reset_validate_button()
    
    def on_validation_completed(self, is_valid: bool, message: str):
        """Handle validation completion."""
        try:
            self.reset_validate_button()
            
            if is_valid:
                self.show_success(message)
                # Save the API key
                current_model = self.model_combo.itemData(self.model_combo.currentIndex())
                api_key = self.api_key_input.text().strip()
                self.ai_config.set_api_key(current_model, api_key)
                self.update_api_key_status()
                self.api_key_input.clear()
            else:
                self.show_error(message)
                
        except Exception as e:
            self.show_error(f"处理验证结果失败: {str(e)}")
    
    def reset_validate_button(self):
        """Reset validate button state."""
        self.validate_button.setEnabled(True)
        self.validate_button.setText("验证")
    
    def save_settings(self):
        """Save all AI settings."""
        try:
            # Save AI enabled state
            self.ai_config.set_enabled(self.ai_enabled_switch.isChecked())
            
            # Save current model
            current_model = self.model_combo.itemData(self.model_combo.currentIndex())
            if current_model:
                self.ai_config.set_current_model(current_model)
            
            # Save advanced settings
            self.ai_config.set_stream_enabled(self.stream_switch.isChecked())
            
            # Save context limit
            context_text = self.context_input.text().strip()
            if context_text:
                try:
                    context_limit = int(context_text)
                    self.ai_config.set_context_limit(context_limit)
                except ValueError:
                    self.show_error("上下文限制必须是数字")
                    return
            
            # Save rate limit
            rate_text = self.rate_input.text().strip()
            if rate_text:
                try:
                    rate_limit = int(rate_text)
                    self.ai_config.set_rate_limit(rate_limit)
                except ValueError:
                    self.show_error("请求限制必须是数字")
                    return
            
            self.show_success("AI设置保存成功")
            
        except Exception as e:
            self.show_error(f"保存设置失败: {str(e)}")
    
    def cancel_changes(self):
        """Cancel changes and reload settings."""
        self.load_settings()
        self.api_key_input.clear()
    
    def show_success(self, message: str):
        """Show success message."""
        try:
            InfoBar.success(
                title="成功",
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        except:
            # Fallback for testing
            print(f"SUCCESS: {message}")
    
    def show_error(self, message: str):
        """Show error message."""
        try:
            InfoBar.error(
                title="错误",
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        except:
            # Fallback for testing
            print(f"ERROR: {message}")

# Utility function for easy integration
def create_ai_settings_widget(parent=None):
    """Create and return an AI settings widget."""
    return AISettingsWidget(parent)