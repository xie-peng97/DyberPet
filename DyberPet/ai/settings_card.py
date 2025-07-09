"""
AI Settings Card
===============

AI settings card for integration with DyberPet settings interface.
"""

import os
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox, QCheckBox

try:
    from qfluentwidgets import SettingCard, SwitchSettingCard, ComboBoxSettingCard, LineEditSettingCard, FluentIcon as FIF
except ImportError:
    # Fallback to basic Qt widgets
    class SettingCard(QWidget):
        def __init__(self, icon, title, content, parent=None):
            super().__init__(parent)
            self.title = title
            self.content = content
            self.setupUI()
        
        def setupUI(self):
            layout = QVBoxLayout(self)
            title_label = QLabel(self.title)
            title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            layout.addWidget(title_label)
            
            content_label = QLabel(self.content)
            content_label.setStyleSheet("color: #666; font-size: 12px;")
            layout.addWidget(content_label)
    
    class SwitchSettingCard(SettingCard):
        def __init__(self, icon, title, content, parent=None):
            super().__init__(icon, title, content, parent)
            self.switchButton = QCheckBox()
            self.layout().addWidget(self.switchButton)
    
    class ComboBoxSettingCard(SettingCard):
        def __init__(self, icon, title, content, texts, parent=None):
            super().__init__(icon, title, content, parent)
            self.comboBox = QComboBox()
            self.comboBox.addItems(texts)
            self.layout().addWidget(self.comboBox)
    
    class LineEditSettingCard(SettingCard):
        def __init__(self, icon, title, content, parent=None):
            super().__init__(icon, title, content, parent)
            self.lineEdit = QLineEdit()
            self.layout().addWidget(self.lineEdit)
    
    class FIF:
        ROBOT = None

from ..ai.config import AIConfig
from ..ai.ai_manager import AIManager
import DyberPet.settings as settings

class AISettingsCard(SettingCard):
    """AI settings card for the main settings interface."""
    
    ai_enabled_changed = Signal(bool)
    
    def __init__(self, parent=None):
        super().__init__(
            FIF.ROBOT,
            "AI 聊天功能",
            "启用与DyberPet的AI聊天功能",
            parent
        )
        self.ai_config = AIConfig()
        self.ai_manager = AIManager()
        self.setupUI()
        self.loadSettings()
    
    def setupUI(self):
        """Setup AI settings UI."""
        # Main layout
        main_layout = QVBoxLayout()
        
        # Enable/Disable AI
        enable_layout = QHBoxLayout()
        enable_layout.addWidget(QLabel("启用AI功能:"))
        
        self.ai_enabled_checkbox = QCheckBox()
        self.ai_enabled_checkbox.stateChanged.connect(self.onAIEnabledChanged)
        enable_layout.addWidget(self.ai_enabled_checkbox)
        enable_layout.addStretch()
        
        main_layout.addLayout(enable_layout)
        
        # Model selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("AI模型:"))
        
        self.model_combo = QComboBox()
        models = self.ai_config.get_supported_models()
        for model_id, model_info in models.items():
            self.model_combo.addItem(model_info['name'], model_id)
        self.model_combo.currentTextChanged.connect(self.onModelChanged)
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        
        main_layout.addLayout(model_layout)
        
        # API Key input
        api_layout = QHBoxLayout()
        api_layout.addWidget(QLabel("API Key:"))
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("请输入API Key")
        api_layout.addWidget(self.api_key_input)
        
        self.validate_button = QPushButton("验证")
        self.validate_button.clicked.connect(self.validateAPIKey)
        api_layout.addWidget(self.validate_button)
        
        main_layout.addLayout(api_layout)
        
        # Status
        self.status_label = QLabel("未配置")
        self.status_label.setStyleSheet("color: #666; font-size: 12px;")
        main_layout.addWidget(self.status_label)
        
        # Save button
        self.save_button = QPushButton("保存设置")
        self.save_button.clicked.connect(self.saveSettings)
        main_layout.addWidget(self.save_button)
        
        self.layout().addLayout(main_layout)
    
    def loadSettings(self):
        """Load current AI settings."""
        try:
            # Load AI enabled state
            self.ai_enabled_checkbox.setChecked(self.ai_config.is_enabled())
            
            # Load current model
            current_model = self.ai_config.get_current_model()
            for i in range(self.model_combo.count()):
                if self.model_combo.itemData(i) == current_model:
                    self.model_combo.setCurrentIndex(i)
                    break
            
            # Update status
            self.updateStatus()
            
        except Exception as e:
            self.status_label.setText(f"加载设置失败: {str(e)}")
            self.status_label.setStyleSheet("color: #dc3545; font-size: 12px;")
    
    def updateStatus(self):
        """Update API key status."""
        try:
            current_model = self.model_combo.itemData(self.model_combo.currentIndex())
            if current_model:
                model_info = self.ai_config.get_model_info(current_model)
                if model_info.get('requires_api_key', False):
                    has_key = self.ai_config.get_api_key(current_model) is not None
                    if has_key:
                        self.status_label.setText("✓ API Key已配置")
                        self.status_label.setStyleSheet("color: #28a745; font-size: 12px;")
                    else:
                        self.status_label.setText("✗ API Key未配置")
                        self.status_label.setStyleSheet("color: #dc3545; font-size: 12px;")
                else:
                    self.status_label.setText("✓ 无需API Key")
                    self.status_label.setStyleSheet("color: #28a745; font-size: 12px;")
        except Exception as e:
            self.status_label.setText(f"状态更新失败: {str(e)}")
            self.status_label.setStyleSheet("color: #dc3545; font-size: 12px;")
    
    def onAIEnabledChanged(self, state):
        """Handle AI enabled state change."""
        self.ai_enabled_changed.emit(state == Qt.CheckState.Checked)
    
    def onModelChanged(self):
        """Handle model selection change."""
        self.updateStatus()
    
    def validateAPIKey(self):
        """Validate the entered API key."""
        try:
            api_key = self.api_key_input.text().strip()
            if not api_key:
                self.status_label.setText("请输入API Key")
                self.status_label.setStyleSheet("color: #dc3545; font-size: 12px;")
                return
            
            current_model = self.model_combo.itemData(self.model_combo.currentIndex())
            if not current_model:
                self.status_label.setText("请选择模型")
                self.status_label.setStyleSheet("color: #dc3545; font-size: 12px;")
                return
            
            # Update UI state
            self.validate_button.setEnabled(False)
            self.validate_button.setText("验证中...")
            self.status_label.setText("验证中...")
            self.status_label.setStyleSheet("color: #ffc107; font-size: 12px;")
            
            # Validate API key
            is_valid = self.ai_manager.validate_api_key(current_model, api_key)
            
            if is_valid:
                self.ai_config.set_api_key(current_model, api_key)
                self.status_label.setText("✓ API Key验证成功")
                self.status_label.setStyleSheet("color: #28a745; font-size: 12px;")
                self.api_key_input.clear()
            else:
                self.status_label.setText("✗ API Key验证失败")
                self.status_label.setStyleSheet("color: #dc3545; font-size: 12px;")
            
        except Exception as e:
            self.status_label.setText(f"验证失败: {str(e)}")
            self.status_label.setStyleSheet("color: #dc3545; font-size: 12px;")
        
        finally:
            self.validate_button.setEnabled(True)
            self.validate_button.setText("验证")
    
    def saveSettings(self):
        """Save AI settings."""
        try:
            # Save AI enabled state
            self.ai_config.set_enabled(self.ai_enabled_checkbox.isChecked())
            
            # Save current model
            current_model = self.model_combo.itemData(self.model_combo.currentIndex())
            if current_model:
                self.ai_config.set_current_model(current_model)
            
            self.status_label.setText("✓ 设置保存成功")
            self.status_label.setStyleSheet("color: #28a745; font-size: 12px;")
            
        except Exception as e:
            self.status_label.setText(f"保存失败: {str(e)}")
            self.status_label.setStyleSheet("color: #dc3545; font-size: 12px;")