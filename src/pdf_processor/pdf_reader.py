# -*- coding: utf-8 -*-
"""PDF读取器模块"""

import os
import json
from typing import List, Dict, Optional, Tuple
from pypdf import PdfReader
from src.utils.logger import logger

class PDFReader:
    """PDF读取器类，用于读取和解析PDF文件"""
    
    def __init__(self, file_path: str = None):
        """
        初始化PDF读取器
        
        Args:
            file_path: PDF文件路径（可选）
        """
        self.file_path = file_path
        self.reader = None
        self.num_pages = 0
        if file_path:
            self.load_pdf()
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
        return False
        
    def load_pdf(self) -> bool:
        """
        加载PDF文件
        
        Returns:
            bool: 是否加载成功
        """
        try:
            if not os.path.exists(self.file_path):
                raise FileNotFoundError(f"文件不存在: {self.file_path}")
            
            self.reader = PdfReader(self.file_path)
            self.num_pages = len(self.reader.pages)
            logger.info(f"成功加载PDF文件: {self.file_path}, 页数: {self.num_pages}")
            return True
        except Exception as e:
            logger.error(f"加载PDF文件失败: {e}")
            return False
    
    def get_text_by_page_range(self, start_page: int, end_page: int) -> List[str]:
        """
        获取指定页码范围内的文本内容
        
        Args:
            start_page: 起始页码（从0开始）
            end_page: 结束页码（从0开始，包含）
            
        Returns:
            List[str]: 每页的文本内容列表
        """
        if not self.reader:
            return []
        
        # 确保页码范围有效
        start_page = max(0, start_page)
        end_page = min(self.num_pages - 1, end_page)
        
        if start_page > end_page:
            logger.warning(f"无效的页码范围: start={start_page}, end={end_page}")
            return []
        
        text_list = []
        # Batch access to pages to avoid repeated attribute lookups
        pages = self.reader.pages
        for page_num in range(start_page, end_page + 1):
            page = pages[page_num]
            text = page.extract_text()
            text_list.append(text)
        
        return text_list
    
    def get_metadata(self) -> Dict:
        """
        获取PDF文件的元数据
        
        Returns:
            Dict: 元数据字典
        """
        if not self.reader:
            return {}
        
        return self.reader.metadata
    
    def get_num_pages(self) -> int:
        """
        获取PDF文件的页数
        
        Returns:
            int: 页数
        """
        return self.num_pages
    
    def extract_table_of_contents(self, start_page: int, end_page: int) -> str:
        """
        提取目录内容
        
        Args:
            start_page: 目录起始页码（从0开始）
            end_page: 目录结束页码（从0开始）
            
        Returns:
            str: 目录文本内容
        """
        toc_pages_text = self.get_text_by_page_range(start_page, end_page)
        return "\n\n".join(toc_pages_text)
    
    def close(self):
        """关闭PDF文件"""
        # 在pypdf中，不需要显式关闭文件
        self.reader = None
        self.num_pages = 0
        self.user_toc_data = None
        
    def set_user_toc_data(self, toc_json: str) -> List[Dict]:
        """
        设置用户提供的JSON格式目录数据
        
        Args:
            toc_json: 包含目录数据的JSON字符串
            
        Returns:
            List[Dict]: 解析后的目录数据列表，每项包含title, page, level
        """
        try:
            # 解析JSON字符串
            toc_data = json.loads(toc_json)
            
            # 验证数据格式
            if not isinstance(toc_data, list):
                logger.error("目录数据必须是JSON数组格式")
                return []
            
            # 验证每个目录项的格式
            validated_data = []
            for item in toc_data:
                if isinstance(item, dict) and all(key in item for key in ['title', 'page', 'level']):
                    # 转换数据类型
                    validated_item = {
                        'title': str(item['title']),
                        'page': int(item['page']),
                        'level': int(item['level'])
                    }
                    validated_data.append(validated_item)
                else:
                    logger.warning(f"无效的目录项格式: {item}")
            
            self.user_toc_data = validated_data
            logger.info(f"成功设置用户提供的目录数据，共 {len(validated_data)} 个目录项")
            return validated_data
        except json.JSONDecodeError as e:
            logger.error(f"解析目录JSON失败: {e}")
            return []
        except Exception as e:
            logger.error(f"设置用户目录数据失败: {e}")
            return []
    
    def get_user_toc_data(self) -> List[Dict]:
        """
        获取用户提供的目录数据
        
        Returns:
            List[Dict]: 目录数据列表
        """
        return self.user_toc_data if hasattr(self, 'user_toc_data') and self.user_toc_data else []
    
    def has_user_toc(self) -> bool:
        """
        检查是否有用户提供的目录数据
        
        Returns:
            bool: 是否存在用户目录数据
        """
        return hasattr(self, 'user_toc_data') and self.user_toc_data is not None and len(self.user_toc_data) > 0