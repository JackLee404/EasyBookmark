# -*- coding: utf-8 -*-
"""PDF转图片模块"""

import os
import base64
from typing import List, Dict, Tuple, Optional
from pypdf import PdfReader
from PIL import Image
import io
import requests
from src.utils.logger import logger

# 尝试导入pdf2image，如果不可用则使用备选方案
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    logger.warning("pdf2image库未安装，将使用备选方案")
    PDF2IMAGE_AVAILABLE = False

class PDFToImageConverter:
    """PDF转图片转换器类，用于将PDF页面转换为图片并生成Base64编码"""
    
    def __init__(self, file_path: str = None):
        """
        初始化PDF转图片转换器
        
        Args:
            file_path: PDF文件路径（可选）
        """
        self.file_path = file_path
        self.reader = None
        self.num_pages = 0
        # Add cache for converted images to avoid redundant conversions
        self._image_cache = {}
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
            logger.info(f"成功加载PDF文件用于转换: {self.file_path}, 页数: {self.num_pages}")
            return True
        except Exception as e:
            logger.error(f"加载PDF文件失败: {e}")
            return False
    
    def convert_page_to_image(self, page_num: int, dpi: int = 300) -> Optional[bytes]:
        """
        将指定页码的PDF页面转换为图片
        
        Args:
            page_num: 页码（从0开始）
            dpi: 图片分辨率
            
        Returns:
            Optional[bytes]: 图片字节数据，如果失败返回None
        """
        if not self.reader or page_num < 0 or page_num >= self.num_pages:
            logger.error(f"无效的页码: {page_num}")
            return None
        
        # Check cache first
        cache_key = (page_num, dpi)
        if cache_key in self._image_cache:
            logger.debug(f"使用缓存的页面 {page_num} 图片")
            return self._image_cache[cache_key]
        
        try:
            if PDF2IMAGE_AVAILABLE:
                # 使用pdf2image库（推荐方式）
                images = convert_from_path(self.file_path, dpi=dpi, first_page=page_num + 1, last_page=page_num + 1)
                if images and len(images) > 0:
                    image = images[0]
                    # 保存到内存
                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format='PNG')
                    img_byte_arr.seek(0)
                    img_data = img_byte_arr.getvalue()
                    # Cache the result
                    self._image_cache[cache_key] = img_data
                    logger.info(f"成功将页码 {page_num} 转换为图片")
                    return img_data
            else:
                # 备选方案：创建空白图片作为示例
                # 注意：在实际使用时，应安装pdf2image库以获得真实的PDF转图片功能
                page = self.reader.pages[page_num]
                width, height = int(page.mediabox.width), int(page.mediabox.height)
                # 调整尺寸以符合实际需要
                width, height = int(width * 0.5), int(height * 0.5)
                image = Image.new('RGB', (width, height), color='white')
                
                # 添加页码文字作为标识
                from PIL import ImageDraw, ImageFont
                draw = ImageDraw.Draw(image)
                try:
                    font = ImageFont.truetype("arial.ttf", 36)
                except:
                    font = ImageFont.load_default()
                
                text = f"页面 {page_num + 1}"
                text_width, text_height = draw.textsize(text, font=font)
                text_x = (width - text_width) // 2
                text_y = (height - text_height) // 2
                draw.text((text_x, text_y), text, fill='black', font=font)
                
                # 保存到内存
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                img_data = img_byte_arr.getvalue()
                # Cache the result
                self._image_cache[cache_key] = img_data
                logger.info(f"使用备选方案将页码 {page_num} 转换为示例图片")
                return img_data
                
        except Exception as e:
            logger.error(f"转换页面 {page_num} 为图片失败: {e}")
            return None
    
    def encode_image_to_base64(self, image_data: bytes) -> str:
        """
        将图片数据编码为Base64字符串
        
        Args:
            image_data: 图片字节数据
            
        Returns:
            str: Base64编码后的字符串
        """
        try:
            encoded = base64.b64encode(image_data).decode('utf-8')
            logger.info("成功将图片数据编码为Base64")
            return encoded
        except Exception as e:
            logger.error(f"Base64编码失败: {e}")
            return ""
    
    def convert_pages_to_base64(self, page_ranges: List[Tuple[int, int]], dpi: int = 300) -> List[Dict]:
        """
        将指定页码范围的PDF页面转换为图片并生成Base64编码，用于AI处理
        
        Args:
            page_ranges: 页码范围列表，每个元素为(start, end)元组（0基索引）
            dpi: 图片分辨率
            
        Returns:
            List[Dict]: 包含页码和Base64编码的列表
        """
        result = []
        
        for start, end in page_ranges:
            # 确保页码范围有效
            start = max(0, start)
            end = min(self.num_pages - 1, end)
            
            if start > end:
                logger.warning(f"无效的页码范围: start={start}, end={end}")
                continue
            
            # 转换每个页面
            for page_num in range(start, end + 1):
                image_data = self.convert_page_to_image(page_num, dpi)
                if image_data:
                    base64_str = self.encode_image_to_base64(image_data)
                    result.append({
                        'page_number': page_num + 1,  # 转换为1基索引
                        'base64_image': base64_str,
                        'image_format': 'png'
                    })
        
        logger.info(f"成功转换 {len(result)} 页为图片并生成Base64编码用于AI处理")
        return result
    
    def extract_and_convert_pages(self, page_ranges: List[Tuple[int, int]], dpi: int = 300) -> List[Dict]:
        """
        提取指定页码范围的PDF页面，转换为图片并生成Base64编码
        
        Args:
            page_ranges: 页码范围列表，每个元素为(start, end)元组
            dpi: 图片分辨率
            
        Returns:
            List[Dict]: 包含图片信息和Base64编码的列表
        """
        return self.convert_pages_to_base64(page_ranges, dpi)
    
    def create_api_json_payload(self, image_data_list: List[Dict], document_info: Dict = None) -> Dict:
        """
        创建用于API调用的JSON payload，按照特定格式输出
        
        Args:
            image_data_list: 图片数据列表
            document_info: 文档信息字典（可选）
            
        Returns:
            Dict: 格式化的JSON payload
        """
        # 按照特定的JSON格式构建payload
        payload = {
            "document_info": {
                "total_pages": len(image_data_list),
                "source_file": os.path.basename(self.file_path) if self.file_path else "unknown.pdf",
                "processing_time": "auto"
            },
            "page_data": []
        }
        
        # 添加文档信息（如果提供）
        if document_info:
            payload["document_info"].update(document_info)
        
        # 添加页面数据，使用特定格式
        for img_data in image_data_list:
            # 计算图片大小（字节）
            image_size = len(img_data['base64_image']) * 3 // 4  # Base64编码后大小估算
            
            payload["page_data"].append({
                "page_num": img_data['page_number'],
                "base64_encoded_image": img_data['base64_image'],
                "image_type": img_data['image_format'],
                "image_size_bytes": image_size,
                "dpi": 300,
                "status": "success"
            })
        
        logger.info(f"成功创建符合特定格式的API JSON payload，包含 {len(image_data_list)} 页数据")
        return payload
    
    def save_json_payload_to_file(self, payload: Dict, output_file: str) -> bool:
        """
        将JSON payload保存到文件
        
        Args:
            payload: JSON数据
            output_file: 输出文件路径
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 确保输出目录存在
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                logger.info(f"创建输出目录: {output_dir}")
            
            # 保存文件
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            
            logger.info(f"成功保存JSON payload到文件: {output_file}")
            return True
        except Exception as e:
            logger.error(f"保存JSON payload失败: {e}")
            return False
    
    def send_to_api(self, api_url: str, payload: Dict, headers: Dict = None) -> Optional[Dict]:
        """
        将数据发送到API接口
        
        Args:
            api_url: API接口URL
            payload: 请求数据
            headers: 请求头（可选）
            
        Returns:
            Optional[Dict]: API响应，如果失败返回None
        """
        try:
            # 默认请求头
            if not headers:
                headers = {
                    'Content-Type': 'application/json'
                }
            
            # 发送POST请求
            response = requests.post(api_url, json=payload, headers=headers, timeout=30)
            
            # 检查响应状态
            if response.status_code == 200:
                logger.info("API请求成功")
                return response.json()
            else:
                logger.error(f"API请求失败，状态码: {response.status_code}")
                logger.error(f"响应内容: {response.text}")
                return None
        except Exception as e:
            logger.error(f"发送API请求失败: {e}")
            return None
    
    def close(self):
        """关闭资源"""
        self.reader = None
        self.num_pages = 0
        # Clear cache to free memory
        self._image_cache.clear()