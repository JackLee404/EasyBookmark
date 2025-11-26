# -*- coding: utf-8 -*-
"""PDF写入器模块"""

import os
from typing import List, Dict, Tuple, Optional
from pypdf import PdfReader, PdfWriter
from src.utils.logger import logger

class PDFWriter:
    """PDF写入器类，用于修改和保存PDF文件"""
    
    def __init__(self, input_file_path: str):
        """
        初始化PDF写入器
        
        Args:
            input_file_path: 输入PDF文件路径
        """
        self.input_file_path = input_file_path
        self.reader = None
        self.writer = None
        
    def load(self) -> bool:
        """
        加载输入PDF文件
        
        Returns:
            bool: 是否加载成功
        """
        try:
            if not os.path.exists(self.input_file_path):
                raise FileNotFoundError(f"文件不存在: {self.input_file_path}")
            
            self.reader = PdfReader(self.input_file_path)
            self.writer = PdfWriter()
            
            # 复制所有页面到写入器
            for page in self.reader.pages:
                self.writer.add_page(page)
            
            logger.info(f"成功加载PDF文件用于写入: {self.input_file_path}")
            return True
        except Exception as e:
            logger.error(f"加载PDF文件失败: {e}")
            return False
    
    def update_page_content(self, page_num: int, new_content: str) -> bool:
        """
        更新指定页面的内容（注意：pypdf不支持直接修改页面内容，此方法需要扩展）
        
        Args:
            page_num: 页码（从0开始）
            new_content: 新内容
            
        Returns:
            bool: 是否更新成功
        """
        # 注意：pypdf本身不支持直接修改PDF页面的文本内容
        # 这里只是预留接口，实际实现需要使用其他库如reportlab结合pypdf
        logger.warning(f"pypdf不支持直接修改页面内容，页码: {page_num}")
        return False
    
    def add_outline_item(self, title: str, page_num: int, parent: Optional[int] = None) -> int:
        """
        添加大纲项（目录项）
        
        Args:
            title: 大纲标题
            page_num: 目标页码
            parent: 父大纲项ID
            
        Returns:
            int: 大纲项ID
        """
        if not self.writer:
            return -1
        
        try:
            outline_id = self.writer.add_outline_item(title, page_num, parent=parent)
            logger.debug(f"添加大纲项: '{title}' -> 页码 {page_num}, ID: {outline_id}")
            return outline_id
        except Exception as e:
            logger.error(f"添加大纲项失败: {e}")
            return -1
    
    def create_bookmarks_from_toc(self, toc_data: List[Dict]) -> bool:
        """
        根据目录数据创建书签（大纲）
        
        Args:
            toc_data: 目录数据列表，每项包含'title', 'page', 'level'
            
        Returns:
            bool: 是否成功
        """
        if not self.writer:
            return False
        
        try:
            # 清空现有大纲
            self.writer.outline_root = []
            
            # 用于跟踪不同级别的父ID
            parent_map = {}
            
            for item in toc_data:
                title = item['title']
                page_num = item['page']
                level = item['level']
                
                # 确保页码有效
                if page_num < 0 or page_num >= len(self.reader.pages):
                    logger.warning(f"无效的页码: {page_num}, 跳过大纲项: {title}")
                    continue
                
                parent_id = None
                if level > 1:
                    # 查找上一个低一级别的大纲项作为父项
                    for prev_level in range(level - 1, 0, -1):
                        if prev_level in parent_map:
                            parent_id = parent_map[prev_level]
                            break
                
                # 添加大纲项
                outline_id = self.add_outline_item(title, page_num, parent_id)
                
                # 更新当前级别的最新父ID
                if outline_id != -1:
                    parent_map[level] = outline_id
            
            return True
        except Exception as e:
            print(f"创建书签失败: {e}")
            return False
    
    def save(self, output_file_path: str) -> bool:
        """
        保存修改后的PDF文件
        
        Args:
            output_file_path: 输出文件路径
            
        Returns:
            bool: 是否保存成功
        """
        if not self.writer:
            return False
        
        try:
            # 确保输出目录存在
            output_dir = os.path.dirname(output_file_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                logger.info(f"创建输出目录: {output_dir}")
            
            # 保存文件
            with open(output_file_path, 'wb') as output_file:
                self.writer.write(output_file)
            
            logger.info(f"成功保存PDF文件: {output_file_path}")
            return True
        except Exception as e:
            logger.error(f"保存PDF文件失败: {e}")
            return False
    
    def close(self):
        """关闭资源"""
        self.reader = None
        self.writer = None