#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
EasyBookmark - PDF目录自动添加页码工具
主应用入口文件
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.gui import MainWindow
from src.utils.logger import logger

def set_app_icon(app):
    """
    设置应用程序图标，支持Windows任务栏显示
    在Windows上，任务栏图标显示需要特别处理
    """
    # 在Windows上优先使用ICO格式图标
    if sys.platform == 'win32':
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "logo.ico")
        # 如果ICO文件不存在，回退到SVG
        if not os.path.exists(logo_path):
            logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "logo.svg")
    else:
        # 非Windows系统继续使用SVG
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "logo.svg")
    
    if os.path.exists(logo_path):
        logger.info(f"找到图标文件: {logo_path}")
        
        # 创建图标并添加多种尺寸支持
        app_icon = QIcon()
        
        # 尝试加载原始图片
        pixmap = QPixmap(logo_path)
        
        if pixmap.isNull():
            logger.warning("无法加载图标文件，请检查图片格式")
        else:
            logger.info(f"成功加载图标，原始尺寸: {pixmap.width()}x{pixmap.height()}")
            
            # 添加不同尺寸的图标，提高在不同DPI设置下的显示效果
            sizes = [16, 24, 32, 48, 64, 128, 256]
            for size in sizes:
                scaled_pixmap = pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                app_icon.addPixmap(scaled_pixmap)
                logger.info(f"添加了{size}x{size}尺寸的图标")
            
            # 设置应用程序图标
            app.setWindowIcon(app_icon)
            logger.info("应用程序图标已设置")
            
            return app_icon
    else:
        logger.warning(f"未找到图标文件: {logo_path}")
    
    return None


def main():
    """主函数"""
    try:
        # 对于Windows系统，在创建QApplication之前就设置进程ID
        # 这是解决Windows任务栏图标问题的关键
        if sys.platform == 'win32':
            import ctypes
            # 使用推荐的反向DNS格式的应用ID
            myappid = 'com.easybookmark.pdfeditor.v1.0.0'
            
            # 确保shell32库正确加载
            if hasattr(ctypes.windll, 'shell32'):
                # 这是解决Windows任务栏图标问题的核心代码
                # 显式设置当前应用程序ID，而不是使用Python解释器默认值
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
                logger.info(f"Windows任务栏应用程序ID已设置: {myappid}")
            else:
                logger.warning("无法访问shell32库，任务栏图标可能无法正确显示")
        
        # 创建应用程序实例
        app = QApplication(sys.argv)
        app.setApplicationName("EasyBookmark - PDF目录自动添加页码工具")
        
        # 设置高DPI支持
        try:
            app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
        except AttributeError:
            logger.warning("AA_UseHighDpiPixmaps属性不可用，可能是PyQt6版本问题")
        
        # 设置应用程序图标
        app_icon = set_app_icon(app)
        
        # 创建主窗口
        window = MainWindow()
        
        # 确保主窗口也设置了图标
        if app_icon:
            window.setWindowIcon(app_icon)
        
        # 显示窗口
        window.show()
        
        logger.info("应用程序已启动")
        
        # 运行应用程序
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"应用程序启动失败: {str(e)}")
        print(f"错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()