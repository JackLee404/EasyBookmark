import os
import sys
import json
from typing import List, Dict, Tuple

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.llm.toc_extractor import TocExtractor


def test_toc_extractor():
    """
    测试目录提取器的主要功能
    """
    print("===== 开始测试目录提取器 =====")
    
    # 测试配置
    test_pdf_path = input("请输入测试PDF文件路径: ")
    if not os.path.exists(test_pdf_path):
        print(f"错误：文件不存在: {test_pdf_path}")
        return
    
    api_key = input("请输入OpenAI API密钥: ")
    if not api_key:
        print("错误：API密钥不能为空")
        return
    
    # 测试目录页范围
    try:
        start_page = int(input("请输入目录开始页码（1基索引）: "))
        end_page = int(input("请输入目录结束页码（1基索引）: "))
        page_ranges = [(start_page, end_page)]
    except ValueError:
        print("错误：页码必须是整数")
        return
    
    # 页码偏移
    try:
        page_offset = int(input("请输入页码偏移值（通常为0）: ") or "0")
    except ValueError:
        page_offset = 0
    
    # 创建提取器实例
    extractor = TocExtractor(api_key=api_key, model_name="gpt-3.5-turbo")
    
    print(f"\n1. 测试从PDF目录页提取文本的方法...")
    try:
        toc_data = extractor.extract_toc_from_pdf_toc_pages(
            pdf_file_path=test_pdf_path,
            page_ranges=page_ranges,
            page_offset=page_offset
        )
        
        print(f"   结果: 提取到 {len(toc_data)} 个目录项")
        
        # 验证JSON格式
        if toc_data:
            print("\n   JSON格式验证:")
            json_str = json.dumps(toc_data, ensure_ascii=False, indent=2)
            print(f"   成功序列化为JSON，长度: {len(json_str)} 字符")
            
            # 显示前几个目录项作为示例
            print("\n   目录项示例:")
            for i, item in enumerate(toc_data[:3]):
                print(f"   {i+1}. {item}")
            
            # 验证每个项目的字段
            all_valid = True
            for i, item in enumerate(toc_data):
                required_fields = ['title', 'page', 'level']
                if not all(field in item for field in required_fields):
                    print(f"   警告：第{i+1}项缺少必要字段: {item}")
                    all_valid = False
                
                # 验证数据类型
                if not isinstance(item['title'], str) or not item['title'].strip():
                    print(f"   警告：第{i+1}项标题格式错误: {item['title']}")
                    all_valid = False
                
                if not isinstance(item['page'], int):
                    print(f"   警告：第{i+1}项页码不是整数: {item['page']}")
                    all_valid = False
                
                if not isinstance(item['level'], int) or item['level'] < 1:
                    print(f"   警告：第{i+1}项层级格式错误: {item['level']}")
                    all_valid = False
            
            if all_valid:
                print("   所有目录项格式验证通过！")
    except Exception as e:
        print(f"   测试失败: {e}")
    
    print("\n===== 测试完成 =====")


if __name__ == "__main__":
    test_toc_extractor()