# -*- coding: utf-8 -*-
"""日志记录器模块"""

import logging
import os
from datetime import datetime

# 创建日志目录
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 创建日志文件名
log_filename = os.path.join(log_dir, f"easybookmark_{datetime.now().strftime('%Y%m%d')}.log")

# 配置日志记录器
logger = logging.getLogger("easybookmark")
logger.setLevel(logging.DEBUG)

# 创建文件处理器
file_handler = logging.FileHandler(log_filename, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 设置日志格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# 添加处理器到日志记录器
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# 示例用法
# logger.debug("调试信息")
# logger.info("普通信息")
# logger.warning("警告信息")
# logger.error("错误信息")
# logger.critical("严重错误")