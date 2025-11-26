#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF页码自动添加工具
基于PySide6开发
"""

import sys
import os
# 兼容PyQt6和PySide6的导入方式
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt, QFileInfo
    from PySide6.QtGui import QIcon, QPixmap
    print("使用PySide6库")
except ImportError:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt, QFileInfo
    from PyQt6.QtGui import QIcon, QPixmap
    print("使用PyQt6库")

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入语言管理器
from src.utils.language_manager import language_manager
from src.gui.main_window import MainWindow

# 确保中文显示正常
def get_resource_path(relative_path):
    """
    获取资源文件的绝对路径，支持PyInstaller打包后的环境
    """
    try:
        # PyInstaller创建临时文件夹，将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
        print(f"PyInstaller环境，使用临时路径: {base_path}")
    except Exception:
        # 非打包环境，使用当前目录
        base_path = os.path.dirname(os.path.abspath(__file__))
        print(f"开发环境，使用当前路径: {base_path}")
    
    return os.path.join(base_path, relative_path)

def set_app_icon(app):
    """
    设置应用程序图标，支持Windows任务栏显示和文件资源管理器图标
    使用PySide6/PyQt6最佳实践
    """
    # 首先尝试获取ICO图标路径
    logo_ico_path = get_resource_path("assets/logo.ico")
    logo_svg_path = get_resource_path("assets/logo.svg")
    
    print(f"图标路径 - ICO: {logo_ico_path}, SVG: {logo_svg_path}")
    
    # 创建图标对象
    app_icon = QIcon()
    
    # 优先使用ICO格式（Windows上文件资源管理器显示需要）
    if os.path.exists(logo_ico_path):
        try:
            print(f"尝试加载ICO图标: {logo_ico_path}")
            app_icon.addFile(logo_ico_path)
            print("成功添加ICO图标")
        except Exception as e:
            print(f"加载ICO图标时出错: {str(e)}")
    
    # 加载SVG图标作为补充，提供更好的缩放效果
    if os.path.exists(logo_svg_path):
        try:
            print(f"尝试加载SVG图标: {logo_svg_path}")
            pixmap = QPixmap(logo_svg_path)
            
            if not pixmap.isNull():
                print(f"成功加载SVG图标，尺寸: {pixmap.width()}x{pixmap.height()}")
                
                # 添加不同尺寸的图标，提高在不同DPI设置下的显示效果
                sizes = [16, 24, 32, 48, 64, 128, 256]
                for size in sizes:
                    scaled_pixmap = pixmap.scaled(
                        size, size, 
                        Qt.AspectRatioMode.KeepAspectRatio, 
                        Qt.TransformationMode.SmoothTransformation
                    )
                    app_icon.addPixmap(scaled_pixmap)
                    print(f"添加了{size}x{size}尺寸的图标")
            else:
                print("警告: 无法加载SVG图标文件")
        except Exception as e:
            print(f"加载SVG图标时出错: {str(e)}")
    
    # 设置应用程序图标
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)
        print("应用程序图标已设置")
        return app_icon
    else:
        print("警告: 无法创建有效的应用图标")
        return None

def setup_windows_taskbar():
    """
    为Windows系统设置任务栏图标和应用程序ID
    这是确保文件资源管理器和任务栏图标正确显示的关键步骤
    """
    if sys.platform != 'win32':
        return True
    
    try:
        import ctypes
        
        # 这一步非常关键，必须在创建QApplication实例之前设置
        myappid = 'EasyBookmark.pdf-bookmark-tool.v1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        print("成功设置Windows任务栏应用程序ID")
        
        # 确保sys.argv包含应用名称，这对某些Windows图标显示场景很重要
        if not sys.argv:
            sys.argv = ['EasyBookmark']
            print("已设置sys.argv以支持Windows图标显示")
            
        return True
    except Exception as e:
        print(f"设置Windows任务栏时出错: {str(e)}")
        import traceback
        print(f"详细错误信息: {traceback.format_exc()}")
        return False

def main():
    """主函数"""
    # 第一步：在创建QApplication之前设置Windows任务栏
    setup_windows_taskbar()
    
    # 创建并设置应用程序实例
    app = QApplication(sys.argv)
    
    # 设置应用程序元数据
    app.setApplicationName("EasyBookmark")
    app.setOrganizationName("EasyBookmark")
    
    # 设置应用程序图标
    app_icon = set_app_icon(app)
    
    # 初始化语言管理器
    language_manager.initialize()
    
    # 确保中文显示正常
    font = app.font()
    # PyQt6中移除了FontStyleStrategy，保留字体设置
    app.setFont(font)
    
    # 创建并显示主窗口
    window = MainWindow()
    
    # 确保主窗口也设置了图标
    if app_icon:
        window.setWindowIcon(app_icon)
        print("主窗口图标已设置")
    
    # 先显示窗口，确保窗口句柄已创建
    window.show()
    
    # 对于Windows，在窗口显示后执行额外的图标处理
    if sys.platform == 'win32' and app_icon:
        try:
            import ctypes
            
            # 获取窗口句柄
            hwnd = window.winId().__int__()
            if hwnd:
                print(f"成功获取窗口句柄: {hwnd}")
                
                # 直接使用Windows API设置窗口图标，这对文件资源管理器显示很重要
                ico_path = get_resource_path("assets/logo.ico")
                if os.path.exists(ico_path):
                    try:
                        # 加载ICO文件
                        IMAGE_ICON = 1
                        LR_LOADFROMFILE = 0x0010
                        icon_handle = ctypes.windll.user32.LoadImageW(
                            None, ico_path, IMAGE_ICON, 0, 0, LR_LOADFROMFILE
                        )
                        
                        if icon_handle:
                            print(f"成功加载ICO图标句柄: {icon_handle}")
                            
                            # 设置大图标和小图标
                            WM_SETICON = 0x0080
                            ICON_BIG = 1
                            ICON_SMALL = 0
                            
                            ctypes.windll.user32.SendMessageW(
                                hwnd, WM_SETICON, ICON_BIG, icon_handle
                            )
                            ctypes.windll.user32.SendMessageW(
                                hwnd, WM_SETICON, ICON_SMALL, icon_handle
                            )
                            
                            print("成功通过Windows API设置窗口图标")
                    except Exception as ico_e:
                        print(f"使用Windows API加载ICO图标时出错: {str(ico_e)}")
                
                # 刷新Windows外壳缓存
                try:
                    print("刷新Windows外壳图标缓存...")
                    ctypes.windll.shell32.SHChangeNotify(
                        0x08000000,  # SHCNE_ASSOCCHANGED
                        0x0000,      # SHCNF_IDLIST
                        None, None
                    )
                    
                    # 更新窗口
                    ctypes.windll.user32.UpdateWindow(hwnd)
                    app.processEvents()
                    
                    print("Windows图标缓存已刷新")
                except Exception as cache_e:
                    print(f"刷新图标缓存时出错: {str(cache_e)}")
            else:
                print("无法获取窗口句柄")
        except Exception as e:
            print(f"Windows图标额外处理时出错: {str(e)}")
    
    # 运行应用程序
    sys.exit(app.exec())

if __name__ == "__main__":
    main()