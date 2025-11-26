# -*- coding: utf-8 -*-
"""目录提取器模块"""

import re
import json
from typing import List, Dict, Optional, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from src.utils.logger import logger
from src.pdf_processor.pdf_to_image import PDFToImageConverter

class TocExtractor:
    """目录提取器类，使用LLM提取PDF目录信息"""
    
    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo", base_url: str = None):
        """
        初始化目录提取器
        
        Args:
            api_key: OpenAI API密钥
            model_name: 使用的模型名称
            base_url: API基础URL（可选）
        """
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url
        self.llm = None
        # 导入PdfReader用于从PDF直接提取文本
        try:
            from pypdf import PdfReader
            self.PdfReader = PdfReader
        except ImportError:
            logger.error("无法导入pypdf库，请确保已安装")
            self.PdfReader = None
    
    def initialize(self) -> bool:
        """
        初始化LLM
        
        Returns:
            bool: 是否初始化成功
        """
        try:
            # 配置ChatOpenAI参数
            chat_params = {
                "api_key": self.api_key,
                "model_name": self.model_name,
                "temperature": 0
            }
            
            # 如果提供了base_url，则添加到配置中
            if self.base_url:
                chat_params["base_url"] = self.base_url
            
            self.llm = ChatOpenAI(**chat_params)
            logger.info(f"成功初始化LLM模型: {self.model_name}")
            return True
        except Exception as e:
            logger.error(f"初始化LLM失败: {e}")
            return False
    
    def extract_toc_from_text_with_images(self, toc_text: str, pdf_file_path: str, page_ranges: List[Tuple[int, int]], page_offset: int = 0) -> List[Dict]:
        """
        从文本中提取目录信息，并使用PDF页面图片辅助理解
        支持多目录页的顺序处理和结果拼接
        
        Args:
            toc_text: 目录文本内容
            pdf_file_path: PDF文件路径
            page_ranges: 目录页范围列表，每个元素为(开始页码, 结束页码)元组（1基索引）
            page_offset: 页码偏移值
            
        Returns:
            List[Dict]: 目录项列表，每项包含title, page, level
        """
        if not self.llm:
            if not self.initialize():
                return []
        
        try:
            # 创建PDF转图片转换器
            converter = PDFToImageConverter(pdf_file_path)
            if not converter.load_pdf():
                logger.error("无法加载PDF文件进行图片转换")
                # 降级使用从PDF目录页提取文本的方法
                return self.extract_toc_from_pdf_toc_pages(pdf_file_path, page_ranges, page_offset)
            
            # 初始化完整的目录结果
            full_toc_data = []
            
            # 按顺序处理每个目录页范围
            for idx, (start_page, end_page) in enumerate(page_ranges):
                logger.info(f"处理目录页范围 {idx+1}/{len(page_ranges)}: 第 {start_page}-{end_page} 页")
                
                # 转换为0基索引
                zero_based_ranges = [(start_page - 1, end_page - 1)]
                # 转换目录页面为图片并获取Base64编码
                image_data_list = converter.convert_pages_to_base64(zero_based_ranges)
                
                # 构建提示词
                system_prompt = """
                你是一个专业的PDF目录提取助手。请从提供的文本和PDF页面图片中提取目录信息，并按照指定格式输出。
                
                提取规则：
                1. 结合文本内容和页面图片，识别目录项的标题、页码和层级关系
                2. 忽略页眉、页脚、页码等无关信息
                3. 正确判断每个目录项的层级（通常通过缩进或数字格式判断）
                4. 对于没有明确页码的项，尝试推断或标记为-1
                
                输出格式必须是JSON数组，每项包含三个字段：
                - title: 目录项标题
                - page: 页码（整数）
                - level: 层级（从1开始）
                
                示例输出：
                [{"title": "第一章 介绍", "page": 1, "level": 1}, {"title": "1.1 背景", "page": 2, "level": 2}]
                
                重要：请确保输出是纯JSON格式，不要包含任何额外的文本解释或说明。
                """
                
                # 构建带图片的Human Message
                human_prompt = [
                    {
                        "type": "text",
                        "text": f"请从以下文本和PDF页面图片中提取目录信息：\n\n{toc_text}"
                    }
                ]
                
                # 添加图片到prompt
                for img_data in image_data_list:
                    human_prompt.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{img_data['base64_image']}"
                        }
                    })
                
                try:
                    logger.info(f"开始使用LLM处理目录页范围 {idx+1} 的目录")
                    
                    # 对于支持多模态的模型，使用HumanMessage多模态格式
                    # 支持GPT-4系列和通义千问多模态模型
                    if self.model_name.startswith("gpt-4") or "omni" in self.model_name.lower() or "vl" in self.model_name.lower():
                        # GPT-4 Vision和通义千问多模态模型支持多模态
                        response = self.llm.invoke([
                            SystemMessage(content=system_prompt),
                            HumanMessage(content=human_prompt)
                        ])
                        
                        # 解析响应
                        toc_data = self._parse_llm_response(response.content)
                    else:
                        # 对于不支持多模态的模型，按照类似逻辑处理纯文本
                        logger.info("当前模型不支持多模态，使用纯文本方式处理")
                        
                        # 从当前页范围提取文本
                        try:
                            reader = self.PdfReader(pdf_file_path)
                            range_texts = []
                            for page_num in range(start_page - 1, end_page):  # 转换为0基索引并包含结束页
                                if page_num < len(reader.pages):
                                    page_text = reader.pages[page_num].extract_text()
                                    if page_text:
                                        range_texts.append(f"=== 第{page_num + 1}页 ===\n{page_text}")
                            
                            # 构建该页范围的完整文本
                            range_full_text = "\n\n".join(range_texts)
                            
                            # 构建文本模式的提示词
                            text_system_prompt = """
                            你是一个专业的PDF目录提取助手。请从提供的文本中提取目录信息，并按照指定格式输出。
                            
                            提取规则：
                            1. 识别目录项的标题、页码和层级关系
                            2. 忽略页眉、页脚、页码等无关信息
                            3. 正确判断每个目录项的层级（通常通过缩进或数字格式判断）
                            4. 对于没有明确页码的项，尝试推断或标记为-1
                            5. 只提取真正的目录项，忽略任何非目录内容
                            
                            输出格式必须是纯JSON数组，每项包含三个字段：
                            - title: 目录项标题
                            - page: 页码（整数）
                            - level: 层级（从1开始）
                            
                            示例输出：
                            [{"title": "第一章 介绍", "page": 1, "level": 1}, {"title": "1.1 背景", "page": 2, "level": 2}]
                            
                            重要：请确保输出是纯JSON格式，不要包含任何额外的文本解释或说明，也不要在JSON前后添加任何其他内容。
                            """
                            
                            text_human_prompt = f"""
                            请从以下PDF目录内容中提取目录信息（可能包含多个页面）：
                            
                            {range_full_text}
                            
                            注意：请只提取真正的目录条目，包括标题、对应的页码和层级关系。
                            """
                            
                            # 调用LLM处理文本
                            response = self.llm.invoke([
                                SystemMessage(content=text_system_prompt),
                                HumanMessage(content=text_human_prompt)
                            ])
                            
                            # 解析响应
                            toc_data = self._parse_llm_response(response.content)
                            
                        except Exception as text_extract_error:
                            logger.error(f"提取当前页范围文本失败: {text_extract_error}")
                            # 降级使用extract_toc_from_pdf_toc_pages方法
                            current_toc_data = self.extract_toc_from_pdf_toc_pages(pdf_file_path, [(start_page, end_page)], page_offset)
                            if current_toc_data:
                                full_toc_data.extend(current_toc_data)
                            continue
                    
                    # 应用页码偏移
                    if page_offset != 0 and toc_data:
                        for item in toc_data:
                            if item['page'] != -1:
                                item['page'] += page_offset
                    
                    if toc_data:
                        logger.info(f"成功从目录页范围 {idx+1} 提取到 {len(toc_data)} 个目录项")
                        # 将当前页范围的目录项添加到完整结果中
                        full_toc_data.extend(toc_data)
                    else:
                        logger.warning(f"从目录页范围 {idx+1} 未提取到任何目录项")
                        # 尝试降级使用extract_toc_from_pdf_toc_pages方法
                        current_toc_data = self.extract_toc_from_pdf_toc_pages(pdf_file_path, [(start_page, end_page)], page_offset)
                        if current_toc_data:
                            full_toc_data.extend(current_toc_data)
                
                except Exception as e:
                    logger.error(f"使用图片辅助提取目录页范围 {idx+1} 失败: {e}")
                    # 降级使用从PDF目录页提取文本的方法
                    logger.info("降级使用从PDF目录页提取文本的方法")
                    try:
                        current_toc_data = self.extract_toc_from_pdf_toc_pages(pdf_file_path, [(start_page, end_page)], page_offset)
                        if current_toc_data:
                            full_toc_data.extend(current_toc_data)
                    except Exception as fallback_error:
                        logger.error(f"降级方法也失败: {fallback_error}")
                    # 继续处理下一个页范围
                    continue
            
            # 如果没有提取到任何目录项，尝试使用从PDF目录页提取文本的方法
            if not full_toc_data:
                logger.info("所有目录页范围处理失败，尝试使用从PDF目录页提取文本的方法")
                return self.extract_toc_from_pdf_toc_pages(pdf_file_path, page_ranges, page_offset)
            
            # 验证和清理目录数据
            max_pages = len(converter.reader.pages) if converter.reader else 1000  # 设置默认最大值
            full_toc_data = self.validate_toc_data(full_toc_data, max_pages)
            
            logger.info(f"所有目录页范围处理完成，共提取到 {len(full_toc_data)} 个目录项")
            return full_toc_data
            
        except Exception as e:
            logger.error(f"多模态目录提取处理失败: {e}")
            # 最终降级使用从PDF目录页提取文本的方法
            logger.info("最终降级使用从PDF目录页提取文本的方法")
            return self.extract_toc_from_pdf_toc_pages(pdf_file_path, page_ranges, page_offset)
    
    def extract_toc_from_pdf_toc_pages(self, pdf_file_path: str, page_ranges: List[Tuple[int, int]], page_offset: int = 0) -> List[Dict]:
        """
        从PDF目录页提取文本数据再交给LLM处理（逐页处理方式）
        
        Args:
            pdf_file_path: PDF文件路径
            page_ranges: 目录页范围列表，每个元素为(开始页码, 结束页码)元组（1基索引）
            page_offset: 页码偏移值
            
        Returns:
            List[Dict]: 目录项列表，每项包含title, page, level
        """
        # 验证PdfReader是否可用
        if not self.PdfReader:
            logger.error("PdfReader不可用，无法从PDF提取目录页文本")
            return []
        
        try:
            # 加载PDF文件
            reader = self.PdfReader(pdf_file_path)
            logger.info(f"成功加载PDF文件: {pdf_file_path}, 总页数: {len(reader.pages)}")
            
            # 初始化完整的目录结果
            full_toc_data = []
            
            # 按顺序处理每个目录页范围
            for idx, (start_page, end_page) in enumerate(page_ranges):
                logger.info(f"处理目录页范围 {idx+1}/{len(page_ranges)}: 第 {start_page}-{end_page} 页")
                # 确保页码有效
                start_page_idx = max(0, start_page - 1)  # 转换为0基索引
                end_page_idx = min(len(reader.pages) - 1, end_page - 1)
                
                if start_page_idx > end_page_idx:
                    logger.warning(f"无效的页码范围: start={start_page}, end={end_page}")
                    continue
                
                # 逐页处理每个目录页，类似于图片处理的方式
                for page_idx in range(start_page_idx, end_page_idx + 1):
                    try:
                        page = reader.pages[page_idx]
                        text = page.extract_text()
                        
                        if text:
                            logger.info(f"成功提取第{page_idx + 1}页的文本内容，开始使用LLM处理")
                            
                            # 构建当前页的文本标识
                            page_text = f"=== 第{page_idx + 1}页 ===\n{text}"
                            
                            # 尝试使用LLM处理当前页文本
                            try:
                                # 使用extract_toc_from_text方法处理纯文本（只使用文本不使用图片）
                                page_toc_data = self.extract_toc_from_text(page_text, page_offset)
                                
                                if page_toc_data:
                                    logger.info(f"成功使用LLM从第{page_idx + 1}页提取到 {len(page_toc_data)} 个目录项")
                                    # 将当前页的目录项添加到完整结果中
                                    full_toc_data.extend(page_toc_data)
                                else:
                                    logger.warning(f"第{page_idx + 1}页LLM未返回任何目录数据")
                                    # LLM未返回数据，继续处理下一页
                                    continue
                            except Exception as llm_error:
                                logger.error(f"使用LLM处理第{page_idx + 1}页失败: {llm_error}")
                                # LLM处理失败，继续处理下一页
                                continue
                        else:
                            logger.warning(f"第{page_idx + 1}页没有提取到文本内容")
                    except Exception as e:
                        logger.error(f"处理第{page_idx + 1}页失败: {e}")
                        # 处理当前页失败，继续处理下一页
                        continue
            
            # 如果没有提取到任何目录项，尝试备用的简单文本解析方法
            if not full_toc_data:
                logger.warning("所有页面LLM处理都未成功提取到目录项，尝试使用简单解析方法")
                
                # 重新提取所有页面文本用于备用解析
                full_toc_text = []
                for start_page, end_page in page_ranges:
                    start_page_idx = max(0, start_page - 1)
                    end_page_idx = min(len(reader.pages) - 1, end_page - 1)
                    
                    for page_idx in range(start_page_idx, end_page_idx + 1):
                        try:
                            page = reader.pages[page_idx]
                            text = page.extract_text()
                            if text:
                                full_toc_text.append(f"=== 第{page_idx + 1}页 ===\n{text}")
                        except:
                            pass
                
                if full_toc_text:
                    combined_toc_text = "\n\n".join(full_toc_text)
                    return self._extract_toc_with_simple_parsing(combined_toc_text, page_offset)
                else:
                    return []
            
            # 验证和清理目录数据
            max_pages = len(reader.pages)  # 使用PDF实际页数
            full_toc_data = self.validate_toc_data(full_toc_data, max_pages)
            
            # 去重并保持顺序
            seen = set()
            unique_toc_data = []
            for item in full_toc_data:
                # 使用title和page组合作为唯一标识
                key = (item['title'], item['page'])
                if key not in seen:
                    seen.add(key)
                    unique_toc_data.append(item)
            
            logger.info(f"所有目录页处理完成，共提取到 {len(unique_toc_data)} 个唯一目录项")
            return unique_toc_data
            
        except Exception as e:
            logger.error(f"从PDF目录页提取数据失败: {e}")
            return []
    
    # 向后兼容方法，保持原有接口不变
    def _extract_toc_from_text_with_images_legacy(self, toc_text: str, pdf_file_path: str, start_page: int, end_page: int, page_offset: int = 0) -> List[Dict]:
        """
        从文本中提取目录信息，并使用PDF页面图片辅助理解（向后兼容版本）
        
        Args:
            toc_text: 目录文本内容
            pdf_file_path: PDF文件路径
            start_page: 开始页码（1基索引）
            end_page: 结束页码（1基索引）
            page_offset: 页码偏移值
            
        Returns:
            List[Dict]: 目录项列表，每项包含title, page, level
        """
        # 调用新方法，将单个页面范围转换为列表形式
        page_ranges = [(start_page, end_page)]
        return self._extract_toc_from_text_with_images_impl(toc_text, pdf_file_path, page_ranges, page_offset)
    
    # 重命名原始实现方法，避免递归问题
    _extract_toc_from_text_with_images_impl = extract_toc_from_text_with_images
    # 保留原始方法名作为向后兼容接口
    extract_toc_from_text_with_images_legacy = _extract_toc_from_text_with_images_impl
    # 设置原始方法名指向兼容方法，确保现有代码调用不会出错
    extract_toc_from_text_with_images = _extract_toc_from_text_with_images_legacy
    
    def extract_toc_from_text(self, toc_text: str, page_offset: int = 0) -> List[Dict]:
        """
        从文本中提取目录信息（纯文本方式）
        优化处理单页文本，并确保在LLM连接错误时有合理的处理机制
        
        Args:
            toc_text: 目录文本内容
            page_offset: 页码偏移值
            
        Returns:
            List[Dict]: 目录项列表，每项包含title, page, level
        """
        # 首先尝试使用LLM提取
        try:
            if not self.llm:
                if not self.initialize():
                    logger.warning("LLM初始化失败，尝试备用提取方法")
                    return self._extract_toc_with_simple_parsing(toc_text, page_offset)
            
            # 构建提示词
            system_prompt = """
            你是一个专业的PDF目录提取助手。请从提供的文本中提取目录信息，并按照指定格式输出。
            
            提取规则：
            1. 识别目录项的标题、页码和层级关系
            2. 忽略页眉、页脚、页码等无关信息
            3. 正确判断每个目录项的层级（通常通过缩进或数字格式判断）
            4. 对于没有明确页码的项，尝试推断或标记为-1
            5. 只提取真正的目录项，忽略任何非目录内容
            
            输出格式必须是纯JSON数组，每项包含三个字段：
            - title: 目录项标题
            - page: 页码（整数）
            - level: 层级（从1开始）
            
            示例输出：
            [{"title": "第一章 介绍", "page": 1, "level": 1}, {"title": "1.1 背景", "page": 2, "level": 2}]
            
            重要：请确保输出是纯JSON格式，不要包含任何额外的文本解释或说明，也不要在JSON前后添加任何其他内容。
            """
            
            # 优化human_prompt，明确指出这是单页内容
            human_prompt = f"""
            请从以下单页PDF目录内容中提取目录信息：
            
            {toc_text}
            
            注意：请只提取真正的目录条目，包括标题、对应的页码和层级关系。
            """
            
            logger.info("开始使用LLM提取目录")
            # 调用LLM（使用invoke方法代替直接调用）
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ])
            
            # 解析响应
            toc_data = self._parse_llm_response(response.content)
            
            # 如果LLM返回空数据，尝试备用方法
            if not toc_data:
                logger.warning("LLM未能提取有效目录数据，尝试备用提取方法")
                return self._extract_toc_with_simple_parsing(toc_text, page_offset)
            
            # 应用页码偏移
            if page_offset != 0:
                for item in toc_data:
                    if item['page'] != -1:
                        item['page'] += page_offset
            
            # 验证和清理目录数据
            max_pages = 1000  # 设置默认最大值
            toc_data = self.validate_toc_data(toc_data, max_pages)
            
            logger.info(f"成功提取到 {len(toc_data)} 个目录项")
            return toc_data
        except Exception as e:
            logger.error(f"提取目录失败: {e}")
            # LLM提取失败时，直接抛出异常让调用者处理
            # 这样在逐页处理模式下，失败的页面不会影响其他页面的处理
            raise
    
    def _extract_toc_with_simple_parsing(self, toc_text: str, page_offset: int = 0) -> List[Dict]:
        """
        备用的简单文本解析方法，当LLM无法使用时使用
        
        Args:
            toc_text: 目录文本内容
            page_offset: 页码偏移值
            
        Returns:
            List[Dict]: 目录项列表，每项包含title, page, level
        """
        try:
            logger.info("使用简单文本解析方法提取目录")
            toc_data = []
            
            # 按行分割文本
            lines = toc_text.split('\n')
            
            # 支持的目录行模式：
            # 1. 数字. 标题 ... 页码
            # 2. 数字.数字 标题 ... 页码
            # 3. 缩进 数字. 标题 ... 页码
            toc_line_pattern = re.compile(r'^(\s*)([0-9]+(?:\.[0-9]+)*)\s+(.+?)\s+(\d+)$')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                match = toc_line_pattern.match(line)
                if match:
                    indent, numbering, title, page_str = match.groups()
                    
                    # 根据缩进和编号格式计算层级
                    level = len(numbering.split('.'))
                    # 如果有缩进，增加层级
                    if indent and level == 1:
                        level += len(indent) // 4  # 假设4个空格为一级缩进
                    
                    try:
                        page = int(page_str)
                        toc_data.append({
                            'title': title.strip(),
                            'page': page + page_offset,
                            'level': max(1, level)  # 确保层级至少为1
                        })
                    except ValueError:
                        continue
            
            # 如果提取到数据，进行去重和排序
            if toc_data:
                # 简单去重（基于标题和页码）
                unique_toc = []
                seen = set()
                for item in toc_data:
                    key = (item['title'], item['page'])
                    if key not in seen:
                        seen.add(key)
                        unique_toc.append(item)
                
                # 按页码排序
                unique_toc.sort(key=lambda x: x['page'])
                
                logger.info(f"简单文本解析成功提取到 {len(unique_toc)} 个目录项")
                return unique_toc
            
            logger.warning("简单文本解析未能提取到目录数据")
            return []
        except Exception as e:
            logger.error(f"简单文本解析失败: {e}")
            return []
    
    def _parse_llm_response(self, response_text: str) -> List[Dict]:
        """
        解析LLM响应
        
        Args:
            response_text: LLM返回的文本
            
        Returns:
            List[Dict]: 解析后的目录数据
        """
        # 记录模型返回的原始结果
        logger.info(f"LLM模型返回结果前100字符: {response_text[:100]}...")
        
        # 预处理：去除首尾空白字符和可能的标记
        clean_text = response_text.strip()
        # 移除可能的markdown代码块标记
        if clean_text.startswith('```') and '\n' in clean_text:
            # 尝试移除代码块标记
            lines = clean_text.split('\n')
            # 移除第一行和最后一行的代码块标记
            if len(lines) >= 3 and lines[-1].strip() == '```':
                clean_text = '\n'.join(lines[1:-1])
            elif len(lines) >= 2:
                clean_text = '\n'.join(lines[1:])
            clean_text = clean_text.strip()
        
        # 移除可能的JSON标记文本
        for prefix in ['json\n', 'JSON\n']:
            if clean_text.startswith(prefix):
                clean_text = clean_text[len(prefix):].strip()
                break
        
        # 方法1: 尝试直接解析
        try:
            toc_data = json.loads(clean_text)
            if isinstance(toc_data, list):
                logger.info("成功直接解析JSON响应")
                return toc_data
        except json.JSONDecodeError as e:
            logger.warning(f"直接解析JSON失败: {e}")
        
        # 方法2: 提取[和]之间的内容
        json_start = clean_text.find('[')
        json_end = clean_text.rfind(']')
        if json_start != -1 and json_end != -1 and json_start < json_end:
            json_candidate = clean_text[json_start:json_end+1]
            try:
                toc_data = json.loads(json_candidate)
                if isinstance(toc_data, list):
                    logger.info("成功从[和]之间提取JSON")
                    return toc_data
            except json.JSONDecodeError as e:
                logger.warning(f"提取的JSON候选解析失败: {e}")
        
        # 方法3: 使用更复杂的正则表达式匹配JSON数组
        # 这个正则表达式尝试匹配完整的JSON数组结构
        json_pattern = r'(\[\s*\{[^}]*\}(\s*,\s*\{[^}]*\})*\s*\])'  # 匹配完整的JSON数组
        matches = re.findall(json_pattern, clean_text, re.DOTALL)
        for match_group in matches:
            # 取第一个捕获组（完整的JSON数组）
            json_candidate = match_group[0] if isinstance(match_group, tuple) else match_group
            try:
                toc_data = json.loads(json_candidate)
                if isinstance(toc_data, list):
                    logger.info("成功通过正则表达式提取JSON")
                    return toc_data
            except json.JSONDecodeError:
                continue
        
        logger.error("所有JSON解析方法均失败")
        return []
    

    
    def validate_toc_data(self, toc_data: List[Dict], max_pages: int) -> List[Dict]:
        """
        验证和清理目录数据
        
        Args:
            toc_data: 原始目录数据
            max_pages: PDF最大页数
            
        Returns:
            List[Dict]: 清理后的目录数据
        """
        validated_data = []
        
        # 确保输入是列表
        if not isinstance(toc_data, list):
            logger.error(f"目录数据格式错误：期望列表，实际得到{type(toc_data).__name__}")
            return []
        
        for idx, item in enumerate(toc_data):
            # 确保是字典
            if not isinstance(item, dict):
                logger.warning(f"第{idx+1}项不是字典，跳过: {item}")
                continue
            
            # 确保所有必要字段存在
            if not all(key in item for key in ['title', 'page', 'level']):
                logger.warning(f"第{idx+1}项缺少必要字段: {item}")
                continue
            
            try:
                # 验证并清理页码
                page = item['page']
                # 尝试转换为整数
                if not isinstance(page, int):
                    page = int(float(page))  # 允许通过float转换
                
                # 验证页码范围
                if page != -1 and (page < 1 or page > max_pages):
                    logger.warning(f"第{idx+1}项页码超出范围: {page}/{max_pages}")
                    continue
                
                # 验证并清理标题
                title = str(item['title']).strip()
                if not title:
                    logger.warning(f"第{idx+1}项标题为空")
                    continue
                
                # 验证并清理层级
                level = item['level']
                # 尝试转换为整数
                if not isinstance(level, int):
                    level = int(float(level))  # 允许通过float转换
                
                # 确保层级至少为1
                level = max(1, level)
                # 限制最大层级为6（通常足够）
                level = min(6, level)
                
                # 添加验证通过的项
                validated_data.append({
                    'title': title,
                    'page': page,
                    'level': level
                })
            except (ValueError, TypeError) as e:
                logger.warning(f"第{idx+1}项数据类型转换失败: {e}, 项内容: {item}")
                continue
        
        # 去重（基于标题和页码的组合）
        unique_items = []
        seen = set()
        for item in validated_data:
            # 创建一个唯一键
            key = f"{item['title']}:{item['page']}"
            if key not in seen:
                seen.add(key)
                unique_items.append(item)
        
        logger.info(f"目录数据验证完成: 原始{len(toc_data)}项 -> 验证后{len(validated_data)}项 -> 去重后{len(unique_items)}项")
        return unique_items
    
    def set_api_key(self, api_key: str):
        """
        更新API密钥
        
        Args:
            api_key: 新的API密钥
        """
        self.api_key = api_key
        self.llm = None  # 重置LLM，下次调用时重新初始化