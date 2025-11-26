# -*- coding: utf-8 -*-
"""配置管理器模块"""

import os
import json
from typing import Dict, Any, Optional

class ConfigManager:
    """配置管理器类"""
    
    def __init__(self, config_path: str = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径（可选）
        """
        # 如果提供了自定义配置路径，使用自定义路径
        if config_path:
            self.config_file = config_path
        else:
            # 默认配置文件路径 - 使用当前工作目录，确保与language_manager.py保持一致
            self.config_file = os.path.join(os.getcwd(), "config.json")
        self.config_data = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        
        Returns:
            Dict[str, Any]: 配置数据
        """
        # 默认配置
        default_config = {
            "api_key": "",
            "model_name": "gpt-3.5-turbo",
            "default_start_page": 1,
            "default_end_page": 5,
            "default_offset": 0,
            # 添加更多默认模型相关配置
            "model_temperature": 0.7,
            "model_max_tokens": 2000,
            "model_top_p": 1.0,
            "model_frequency_penalty": 0.0,
            "model_presence_penalty": 0.0,
            # 添加默认起始位置设置，不再从注册表读取
            "app_start_position": {"x": 100, "y": 100},
            "app_window_size": {"width": 1024, "height": 768}
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    existing_config = json.load(f)
                    # 将现有配置与默认配置合并，确保所有必需的键都存在
                    default_config.update(existing_config)
                    return default_config
            except Exception as e:
                print(f"加载配置文件失败: {e}")
        
        # 返回默认配置
        return default_config
    
    def save_config(self) -> bool:
        """
        保存配置到文件
        
        Returns:
            bool: 是否保存成功
        """
        try:
            # 确保目录存在
            config_dir = os.path.dirname(self.config_file)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        return self.config_data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        self.config_data[key] = value
    
    def update(self, updates: Dict[str, Any]) -> None:
        """
        批量更新配置
        
        Args:
            updates: 更新的配置字典
        """
        self.config_data.update(updates)
    
    def get_all(self) -> Dict[str, Any]:
        """
        获取所有配置
        
        Returns:
            Dict[str, Any]: 所有配置
        """
        return self.config_data.copy()
    
    def reset(self) -> None:
        """
        重置配置为默认值
        """
        self.config_data = {
            "api_key": "",
            "model_name": "gpt-3.5-turbo",
            "default_start_page": 1,
            "default_end_page": 5,
            "default_offset": 0,
            # 添加更多默认模型相关配置
            "model_temperature": 0.7,
            "model_max_tokens": 2000,
            "model_top_p": 1.0,
            "model_frequency_penalty": 0.0,
            "model_presence_penalty": 0.0,
            # 添加默认起始位置设置，不再从注册表读取
            "app_start_position": {"x": 100, "y": 100},
            "app_window_size": {"width": 1024, "height": 768}
        }