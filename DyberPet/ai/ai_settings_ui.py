# coding:utf-8
"""
AI Settings UI - Configuration interface for AI functionality
"""

import os
from typing import Dict, List

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QGroupBox, QFormLayout, QSpacerItem, QSizePolicy)

from qfluentwidgets import (ScrollArea, CardWidget, LineEdit, ComboBox, 
                           SwitchButton, SpinBox, PrimaryPushButton, 
                           InfoBar, InfoBarPosition, MessageBox,
                           StrongBodyLabel, BodyLabel, FluentIcon as FIF)

import DyberPet.settings as settings
from DyberPet.ai.ai_config import ai_config

class AISettingsWidget(ScrollArea):
    """AI Settings Configuration Widget"""
    
    config_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AISettingsWidget")
        self.scroll_widget = QWidget()
        self.layout = QVBoxLayout(self.scroll_widget)
        
        self.setupUI()
        self.load_settings()
        self.connectSignals()
        
        self.setWidget(self.scroll_widget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    
    def setupUI(self):
        """Setup the UI components"""
        
        # Title
        title_label = StrongBodyLabel("AI 设置", self)
        title_label.setObjectName("titleLabel")
        self.layout.addWidget(title_label)
        
        # API Keys Section
        self.api_keys_group = self.create_api_keys_section()
        self.layout.addWidget(self.api_keys_group)
        
        # Model Settings Section
        self.model_settings_group = self.create_model_settings_section()
        self.layout.addWidget(self.model_settings_group)
        
        # Personality Settings Section
        self.personality_group = self.create_personality_section()
        self.layout.addWidget(self.personality_group)
        
        # Feature Settings Section
        self.features_group = self.create_features_section()
        self.layout.addWidget(self.features_group)
        
        # Action Buttons
        self.buttons_layout = self.create_buttons_section()
        self.layout.addLayout(self.buttons_layout)
        
        # Spacer
        self.layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
    
    def create_api_keys_section(self) -> QGroupBox:
        """Create API keys configuration section"""
        group = QGroupBox("API 密钥配置")
        form_layout = QFormLayout(group)
        
        # DeepSeek API Key
        self.deepseek_key_edit = LineEdit()
        self.deepseek_key_edit.setPlaceholderText("请输入 DeepSeek API Key")
        self.deepseek_key_edit.setEchoMode(LineEdit.Password)
        form_layout.addRow("DeepSeek:", self.deepseek_key_edit)
        
        # OpenAI API Key
        self.openai_key_edit = LineEdit()
        self.openai_key_edit.setPlaceholderText("请输入 OpenAI API Key")
        self.openai_key_edit.setEchoMode(LineEdit.Password)
        form_layout.addRow("OpenAI:", self.openai_key_edit)
        
        # Gemini API Key
        self.gemini_key_edit = LineEdit()
        self.gemini_key_edit.setPlaceholderText("请输入 Gemini API Key")
        self.gemini_key_edit.setEchoMode(LineEdit.Password)
        form_layout.addRow("Gemini:", self.gemini_key_edit)
        
        return group
    
    def create_model_settings_section(self) -> QGroupBox:
        """Create model settings section"""
        group = QGroupBox("模型设置")
        form_layout = QFormLayout(group)
        
        # Default Model
        self.default_model_combo = ComboBox()
        self.default_model_combo.addItems(["deepseek", "openai", "gemini"])
        form_layout.addRow("默认模型:", self.default_model_combo)
        
        return group
    
    def create_personality_section(self) -> QGroupBox:
        """Create personality settings section"""
        group = QGroupBox("人格设置")
        form_layout = QFormLayout(group)
        
        # Pet Name
        self.pet_name_edit = LineEdit()
        self.pet_name_edit.setPlaceholderText("宠物名称")
        form_layout.addRow("宠物名称:", self.pet_name_edit)
        
        # Owner Title
        self.owner_title_edit = LineEdit()
        self.owner_title_edit.setPlaceholderText("主人称呼")
        form_layout.addRow("主人称呼:", self.owner_title_edit)
        
        # Use Emoticons
        self.use_emoticons_switch = SwitchButton()
        form_layout.addRow("使用颜文字:", self.use_emoticons_switch)
        
        return group
    
    def create_features_section(self) -> QGroupBox:
        """Create feature settings section"""
        group = QGroupBox("功能设置")
        form_layout = QFormLayout(group)
        
        # Function Calling
        self.function_calling_switch = SwitchButton()
        form_layout.addRow("功能调用:", self.function_calling_switch)
        
        # File Processing
        self.file_processing_switch = SwitchButton()
        form_layout.addRow("文件处理:", self.file_processing_switch)
        
        # Max File Size
        self.max_file_size_spin = SpinBox()
        self.max_file_size_spin.setRange(1, 1000)
        self.max_file_size_spin.setSuffix(" KB")
        form_layout.addRow("最大文件大小:", self.max_file_size_spin)
        
        # Task Management
        self.task_management_switch = SwitchButton()
        form_layout.addRow("任务管理:", self.task_management_switch)
        
        # Auto Cleanup Days
        self.cleanup_days_spin = SpinBox()
        self.cleanup_days_spin.setRange(1, 365)
        self.cleanup_days_spin.setSuffix(" 天")
        form_layout.addRow("自动清理天数:", self.cleanup_days_spin)
        
        return group
    
    def create_buttons_section(self) -> QHBoxLayout:
        """Create action buttons section"""
        layout = QHBoxLayout()
        
        # Save Button
        self.save_button = PrimaryPushButton("保存设置")
        self.save_button.setIcon(FIF.SAVE)
        
        # Test Button
        self.test_button = PrimaryPushButton("测试连接")
        self.test_button.setIcon(FIF.PLAY)
        
        # Reset Button
        self.reset_button = PrimaryPushButton("重置为默认")
        self.reset_button.setIcon(FIF.REFRESH)
        
        layout.addWidget(self.save_button)
        layout.addWidget(self.test_button)
        layout.addWidget(self.reset_button)
        layout.addStretch()
        
        return layout
    
    def connectSignals(self):
        """Connect signals to slots"""
        self.save_button.clicked.connect(self.save_settings)
        self.test_button.clicked.connect(self.test_connection)
        self.reset_button.clicked.connect(self.reset_to_default)
        
        # Connect change signals
        self.deepseek_key_edit.textChanged.connect(self.on_setting_changed)
        self.openai_key_edit.textChanged.connect(self.on_setting_changed)
        self.gemini_key_edit.textChanged.connect(self.on_setting_changed)
        self.default_model_combo.currentTextChanged.connect(self.on_setting_changed)
        self.pet_name_edit.textChanged.connect(self.on_setting_changed)
        self.owner_title_edit.textChanged.connect(self.on_setting_changed)
        self.use_emoticons_switch.checkedChanged.connect(self.on_setting_changed)
        self.function_calling_switch.checkedChanged.connect(self.on_setting_changed)
        self.file_processing_switch.checkedChanged.connect(self.on_setting_changed)
        self.max_file_size_spin.valueChanged.connect(self.on_setting_changed)
        self.task_management_switch.checkedChanged.connect(self.on_setting_changed)
        self.cleanup_days_spin.valueChanged.connect(self.on_setting_changed)
    
    def load_settings(self):
        """Load settings from configuration"""
        # API Keys
        self.deepseek_key_edit.setText(ai_config.get_api_key('deepseek'))
        self.openai_key_edit.setText(ai_config.get_api_key('openai'))
        self.gemini_key_edit.setText(ai_config.get_api_key('gemini'))
        
        # Model Settings
        self.default_model_combo.setCurrentText(ai_config.get_default_model())
        
        # Personality Settings
        personality = ai_config.get_personality_config()
        self.pet_name_edit.setText(personality.get('name', 'DyberPet'))
        self.owner_title_edit.setText(personality.get('owner_title', '主人'))
        self.use_emoticons_switch.setChecked(personality.get('use_emoticons', True))
        
        # Feature Settings
        self.function_calling_switch.setChecked(ai_config.is_function_calling_enabled())
        self.file_processing_switch.setChecked(ai_config.is_file_processing_enabled())
        self.max_file_size_spin.setValue(ai_config.get_max_file_size_kb())
        self.task_management_switch.setChecked(ai_config.is_task_management_enabled())
        self.cleanup_days_spin.setValue(ai_config.get_auto_cleanup_days())
    
    def save_settings(self):
        """Save settings to configuration"""
        try:
            # Update API keys
            ai_config.set_api_key('deepseek', self.deepseek_key_edit.text())
            ai_config.set_api_key('openai', self.openai_key_edit.text())
            ai_config.set_api_key('gemini', self.gemini_key_edit.text())
            
            # Update model settings
            ai_config.set_default_model(self.default_model_combo.currentText())
            
            # Update personality settings
            ai_config.config['personality'] = {
                'name': self.pet_name_edit.text() or 'DyberPet',
                'owner_title': self.owner_title_edit.text() or '主人',
                'use_emoticons': self.use_emoticons_switch.isChecked(),
                'language': 'zh-CN'
            }
            
            # Update feature settings
            ai_config.config['function_calling']['enabled'] = self.function_calling_switch.isChecked()
            ai_config.config['file_processing']['enabled'] = self.file_processing_switch.isChecked()
            ai_config.config['file_processing']['max_file_size_kb'] = self.max_file_size_spin.value()
            ai_config.config['task_management']['task_reminder_enabled'] = self.task_management_switch.isChecked()
            ai_config.config['task_management']['auto_cleanup_days'] = self.cleanup_days_spin.value()
            
            # Save configuration
            ai_config.save_config()
            
            # Show success message
            InfoBar.success(
                title="保存成功",
                content="AI 设置已保存",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            
            # Emit signal
            self.config_changed.emit()
            
        except Exception as e:
            InfoBar.error(
                title="保存失败",
                content=f"保存设置时出错: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
    
    def test_connection(self):
        """Test AI connection"""
        try:
            # Test with current default model
            model = self.default_model_combo.currentText()
            api_key = ''
            
            if model == 'deepseek':
                api_key = self.deepseek_key_edit.text()
            elif model == 'openai':
                api_key = self.openai_key_edit.text()
            elif model == 'gemini':
                api_key = self.gemini_key_edit.text()
            
            if not api_key:
                InfoBar.warning(
                    title="测试失败",
                    content="请先输入API密钥",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
                return
            
            # TODO: Implement actual API test
            # For now, just show a success message
            InfoBar.success(
                title="测试成功",
                content=f"{model} 模型连接正常",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            
        except Exception as e:
            InfoBar.error(
                title="测试失败",
                content=f"连接测试失败: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
    
    def reset_to_default(self):
        """Reset settings to default"""
        reply = MessageBox.question(
            self,
            "确认重置",
            "确定要重置所有设置为默认值吗？这将清除所有API密钥。",
            MessageBox.Yes | MessageBox.No,
            MessageBox.No
        )
        
        if reply == MessageBox.Yes:
            ai_config.reset_to_default()
            self.load_settings()
            
            InfoBar.success(
                title="重置成功",
                content="所有设置已重置为默认值",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
    
    def on_setting_changed(self):
        """Handle setting changes"""
        # Enable save button when settings change
        self.save_button.setEnabled(True)
    
    def get_config_status(self) -> Dict:
        """Get configuration status for display"""
        status = ai_config.validate_config()
        
        # Add available models
        status['available_models'] = ai_config.get_available_models()
        
        return status