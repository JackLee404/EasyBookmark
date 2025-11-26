# -*- coding: utf-8 -*-
"""语言管理器模块，负责处理应用程序的多语言支持"""
import os
import json
import locale
from typing import Dict, Optional


class LanguageManager:
    """语言管理器类，提供多语言支持功能"""
    
    def __init__(self):
        """初始化语言管理器"""
        self.current_language = "en"
        self.translations = {}
        self.language_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "languages")
        # 配置文件路径 - 使用当前工作目录，确保打包后也能在应用运行目录创建配置文件
        self.config_file_path = os.path.join(os.getcwd(), "config.json")
        
    def detect_system_language(self) -> str:
        """
        检测系统语言设置
        
        Returns:
            str: 检测到的语言代码，如 'zh_CN', 'en_US' 等
        """
        try:
            # 获取系统默认语言
            system_lang = locale.getdefaultlocale()[0]
            print(f"检测到的系统语言: {system_lang}")
            if system_lang:
                # 简化语言代码，只保留前两个字符，如 'zh_CN' -> 'zh'
                lang_code = system_lang.split('_')[0]
                print(f"简化后的语言代码: {lang_code}")
                return lang_code
        except Exception as e:
            print(f"获取系统语言失败: {e}")
        
        # 备选方案：尝试通过环境变量获取语言设置
        try:
            # 检查常见的语言环境变量
            lang_env = os.environ.get('LANG') or os.environ.get('LANGUAGE')
            if lang_env:
                lang_code = lang_env.split('_')[0].split('.')[0]
                print(f"通过环境变量获取的语言: {lang_code}")
                return lang_code
        except Exception:
            pass
        
        # 默认返回英语
        print("无法检测系统语言，默认使用英语")
        return "en"
    
    def load_language(self, language_code: str) -> bool:
        """
        加载指定语言的翻译资源
        
        Args:
            language_code: 语言代码，如 'zh', 'en' 等
            
        Returns:
            bool: 是否成功加载
        """
        try:
            print(f"尝试加载语言: {language_code}")
            # 尝试加载指定语言的文件
            lang_file = os.path.join(self.language_dir, f"{language_code}.json")
            
            print(f"语言文件路径: {lang_file}")
            print(f"文件是否存在: {os.path.exists(lang_file)}")
            
            if os.path.exists(lang_file):
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
                self.current_language = language_code
                print(f"成功加载语言: {language_code}")
                return True
            else:
                print(f"语言文件不存在: {lang_file}")
                # 如果指定语言文件不存在，尝试加载默认语言（英语）
                default_lang_file = os.path.join(self.language_dir, "en.json")
                if os.path.exists(default_lang_file):
                    print(f"尝试加载默认语言文件: {default_lang_file}")
                    with open(default_lang_file, 'r', encoding='utf-8') as f:
                        self.translations = json.load(f)
                    self.current_language = "en"
                    print("成功加载默认语言: en")
                    return True
        except Exception as e:
            print(f"加载语言文件失败: {e}")
        
        # 打印语言目录信息用于调试
        print(f"语言目录: {self.language_dir}")
        if os.path.exists(self.language_dir):
            print(f"语言目录中的文件: {os.listdir(self.language_dir)}")
        else:
            print("语言目录不存在")
        
        # 如果都失败了，使用空的翻译字典
        self.translations = {}
        self.current_language = "en"
        return False
    
    def _(self, key: str, default: str = None) -> str:
        """
        获取翻译后的字符串
        
        Args:
            key: 字符串键
            default: 如果键不存在，返回的默认值
            
        Returns:
            str: 翻译后的字符串或默认值
        """
        return self.translations.get(key, default or key)
    
    def load_from_config_file(self) -> Optional[str]:
        """
        从配置文件加载语言设置
        
        Returns:
            Optional[str]: 配置文件中的语言代码，如果不存在则返回None
        """
        try:
            if os.path.exists(self.config_file_path):
                print(f"尝试从配置文件加载语言设置: {self.config_file_path}")
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if 'language' in config:
                        language = config['language']
                        print(f"从配置文件读取到语言设置: {language}")
                        return language
        except Exception as e:
            print(f"从配置文件加载语言设置失败: {e}")
        return None
    
    def save_to_config_file(self, language: str) -> bool:
        """
        将语言设置保存到配置文件
        
        Args:
            language: 语言代码
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 确保配置文件目录存在
            config_dir = os.path.dirname(self.config_file_path)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            # 读取现有配置（如果存在），避免覆盖其他配置项
            existing_config = {}
            if os.path.exists(self.config_file_path):
                try:
                    with open(self.config_file_path, 'r', encoding='utf-8') as f:
                        existing_config = json.load(f)
                except Exception:
                    # 如果读取失败，创建空配置
                    existing_config = {}
            
            # 更新语言设置，保留其他配置
            existing_config['language'] = language
            
            # 保存完整配置
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(existing_config, f, indent=2, ensure_ascii=False)
            
            print(f"语言设置已保存到配置文件: {self.config_file_path}")
            return True
        except Exception as e:
            print(f"保存语言设置到配置文件失败: {e}")
            return False
    
    def initialize(self) -> None:
        """
        初始化语言管理器，优先从配置文件加载语言设置，其次检测系统语言
        当配置文件不存在时，根据系统语言自动生成配置文件
        """
        print("开始初始化语言管理器...")
        # 确保语言目录存在
        if not os.path.exists(self.language_dir):
            os.makedirs(self.language_dir)
            print(f"创建语言目录: {self.language_dir}")
        
        # 检查配置文件是否存在
        config_exists = os.path.exists(self.config_file_path)
        
        # 优先从配置文件加载语言设置
        config_language = self.load_from_config_file()
        if config_language:
            print(f"尝试加载配置文件中的语言: {config_language}")
            if self.load_language(config_language):
                print(f"最终使用的语言(从配置文件): {self.current_language}")
                return
        
        # 如果配置文件中没有设置或加载失败，检测系统语言
        system_lang = self.detect_system_language()
        
        # 尝试加载检测到的语言，如果失败则加载默认语言
        print(f"尝试加载系统检测到的语言: {system_lang}")
        self.load_language(system_lang)
        print(f"最终使用的语言: {self.current_language}")
        
        # 如果配置文件不存在，根据检测到的系统语言自动生成配置文件
        if not config_exists:
            print(f"配置文件不存在，根据系统语言创建默认配置文件: {self.config_file_path}")
            self.save_to_config_file(self.current_language)
            print(f"已创建默认配置文件，语言设置为: {self.current_language}")


# 创建全局语言管理器实例
language_manager = LanguageManager()