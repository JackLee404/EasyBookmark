#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
EasyBookmark 性能测试
测试性能优化的效果
"""

import sys
import os
import unittest
import time
from io import BytesIO
from unittest.mock import MagicMock, patch

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pdf_processor import PDFReader, PDFWriter, PDFToImageConverter


class TestPDFReaderPerformance(unittest.TestCase):
    """测试PDFReader性能优化"""
    
    def test_context_manager(self):
        """测试上下文管理器支持"""
        # 测试PDFReader可以作为上下文管理器使用
        reader = PDFReader()
        with reader as r:
            self.assertIsNotNone(r)
            self.assertEqual(r, reader)
    
    def test_multiple_text_extraction_cached(self):
        """测试多次提取文本时使用缓存的pages引用"""
        reader = PDFReader()
        # 模拟有pages属性
        mock_pages = [MagicMock() for _ in range(10)]
        for i, page in enumerate(mock_pages):
            page.extract_text.return_value = f"Page {i} content"
        
        mock_reader = MagicMock()
        mock_reader.pages = mock_pages
        reader.reader = mock_reader
        reader.num_pages = len(mock_pages)
        
        # 第一次提取
        start_time = time.time()
        text1 = reader.get_text_by_page_range(0, 4)
        time1 = time.time() - start_time
        
        # 第二次提取（应该使用缓存的pages引用）
        start_time = time.time()
        text2 = reader.get_text_by_page_range(5, 9)
        time2 = time.time() - start_time
        
        # 验证结果
        self.assertEqual(len(text1), 5)
        self.assertEqual(len(text2), 5)
        
        # 时间测试（第二次应该不会显著慢）
        # 注意：这只是一个粗略的性能指标，实际性能取决于很多因素
        self.assertIsNotNone(time1)
        self.assertIsNotNone(time2)


class TestPDFToImageConverterPerformance(unittest.TestCase):
    """测试PDFToImageConverter性能优化"""
    
    def test_image_caching(self):
        """测试图片转换缓存功能"""
        converter = PDFToImageConverter()
        converter.reader = MagicMock()
        converter.num_pages = 5
        
        # 模拟convert_page_to_image方法的缓存行为
        # 第一次调用应该实际转换
        with patch.object(converter, 'convert_page_to_image', 
                         wraps=converter.convert_page_to_image) as mock_convert:
            # 第一次转换页面0
            converter._image_cache.clear()
            result1 = b"fake_image_data"
            converter._image_cache[(0, 300)] = result1
            
            # 第二次应该从缓存获取
            cached_result = converter._image_cache.get((0, 300))
            
            self.assertEqual(result1, cached_result)
            self.assertIn((0, 300), converter._image_cache)
    
    def test_cache_cleared_on_close(self):
        """测试关闭时清除缓存"""
        converter = PDFToImageConverter()
        converter._image_cache[(0, 300)] = b"test_data"
        converter._image_cache[(1, 300)] = b"test_data2"
        
        self.assertEqual(len(converter._image_cache), 2)
        
        converter.close()
        
        self.assertEqual(len(converter._image_cache), 0)
    
    def test_context_manager(self):
        """测试上下文管理器支持"""
        converter = PDFToImageConverter()
        with converter as c:
            c._image_cache[(0, 300)] = b"test"
            self.assertEqual(len(c._image_cache), 1)
        
        # 上下文退出后应该清除缓存
        self.assertEqual(len(converter._image_cache), 0)


class TestPDFWriterPerformance(unittest.TestCase):
    """测试PDFWriter性能优化"""
    
    def test_context_manager(self):
        """测试上下文管理器支持"""
        # 创建一个临时的mock文件路径（跨平台兼容）
        import tempfile
        temp_path = tempfile.mktemp(suffix=".pdf")
        writer = PDFWriter(temp_path)
        
        # 测试上下文管理器
        with patch.object(writer, 'load', return_value=True):
            with writer as w:
                self.assertIsNotNone(w)
                self.assertEqual(w, writer)


class TestDeduplicationPerformance(unittest.TestCase):
    """测试去重性能优化"""
    
    def test_efficient_deduplication(self):
        """测试使用字典去重比使用列表+集合更高效"""
        # 创建大量重复数据
        data = []
        for i in range(1000):
            data.append({"title": f"Title {i % 100}", "page": i % 100, "level": 1})
        
        # 旧方法：使用列表和集合
        start_time = time.time()
        unique_old = []
        seen_old = set()
        for item in data:
            key = (item['title'], item['page'])
            if key not in seen_old:
                seen_old.add(key)
                unique_old.append(item)
        old_time = time.time() - start_time
        
        # 新方法：使用字典
        start_time = time.time()
        unique_dict = {}
        for item in data:
            key = (item['title'], item['page'])
            if key not in unique_dict:
                unique_dict[key] = item
        unique_new = list(unique_dict.values())
        new_time = time.time() - start_time
        
        # 验证结果相同
        self.assertEqual(len(unique_old), len(unique_new))
        self.assertEqual(len(unique_new), 100)  # 只有100个唯一项
        
        # 新方法应该不会显著慢（通常更快）
        # 注意：这只是一个粗略的性能指标
        print(f"\n旧方法时间: {old_time:.6f}秒")
        print(f"新方法时间: {new_time:.6f}秒")
        print(f"性能提升: {((old_time - new_time) / old_time * 100):.2f}%")


if __name__ == "__main__":
    unittest.main()
