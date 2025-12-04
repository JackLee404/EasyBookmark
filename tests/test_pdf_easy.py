#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
EasyBookmark 测试脚本
用于测试主要功能模块
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pdf_processor import PDFReader, PDFWriter
from src.llm import TocExtractor
from src.utils import ConfigManager, logger


class TestPDFReader(unittest.TestCase):
    """测试PDFReader类"""
    
    def setUp(self):
        """设置测试环境"""
        self.sample_pdf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample.pdf")
    
    def test_initialization(self):
        """测试初始化"""
        reader = PDFReader()
        self.assertIsNotNone(reader)
    
    def test_load_pdf(self):
        """测试加载PDF"""
        # 如果测试目录下有sample.pdf，测试实际加载
        if os.path.exists(self.sample_pdf):
            reader = PDFReader()
            result = reader.load_pdf(self.sample_pdf)
            self.assertTrue(result)
            self.assertIsNotNone(reader.pdf)


class TestConfigManager(unittest.TestCase):
    """测试ConfigManager类"""
    
    def setUp(self):
        """设置测试环境"""
        self.test_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_config.json")
        # 确保测试前删除旧的测试配置文件
        if os.path.exists(self.test_config_path):
            os.remove(self.test_config_path)
        
        self.config = ConfigManager(config_path=self.test_config_path)
    
    def tearDown(self):
        """清理测试环境"""
        if os.path.exists(self.test_config_path):
            os.remove(self.test_config_path)
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.config)
        # 检查默认配置是否正确加载
        self.assertEqual(self.config.get("default_start_page"), 1)
    
    def test_save_and_load(self):
        """测试保存和加载配置"""
        # 设置并保存配置
        self.config.set("api_key", "test_api_key")
        self.config.set("test_value", 42)
        self.config.save_config()
        
        # 创建新的配置管理器实例来加载保存的配置
        new_config = ConfigManager(config_path=self.test_config_path)
        self.assertEqual(new_config.get("api_key"), "test_api_key")
        self.assertEqual(new_config.get("test_value"), 42)


class TestTocExtractor(unittest.TestCase):
    """测试TocExtractor类（使用mock）"""
    
    @patch('src.llm.toc_extractor.ChatOpenAI')
    def test_extract_from_text(self, mock_chat_openai_class):
        """测试从文本提取目录"""
        # 设置mock返回值
        mock_instance = MagicMock()
        # 模拟invoke方法返回值
        mock_response = MagicMock()
        mock_response.content = '''
        [
            {"title": "第一章 简介", "page": 1, "level": 1},
            {"title": "1.1 项目背景", "page": 2, "level": 2},
            {"title": "第二章 实现", "page": 5, "level": 1}
        ]
        '''
        # 修正：设置invoke方法的返回值
        mock_instance.invoke.return_value = mock_response
        mock_chat_openai_class.return_value = mock_instance
        
        extractor = TocExtractor(api_key="test_key")
        toc_data = extractor.extract_toc_from_text("示例PDF内容", page_offset=0)
        
        self.assertIsNotNone(toc_data)
        self.assertEqual(len(toc_data), 3)
        self.assertEqual(toc_data[0]["title"], "第一章 简介")


if __name__ == "__main__":
    unittest.main()
    print("EasyBookmark测试完成！")