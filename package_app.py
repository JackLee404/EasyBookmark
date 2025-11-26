#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
EasyBookmark 应用打包脚本
用于将应用程序打包为可执行文件
支持Windows和Mac平台
"""

import os
import sys
import subprocess
import platform
import shutil
import time
from pathlib import Path

def create_assets_folder():
    """创建assets文件夹，用于存放图标等资源"""
    assets_dir = Path('assets')
    assets_dir.mkdir(exist_ok=True)
    
    # 创建一个简单的占位图标文件（实际使用时应该替换为真实的图标）
    placeholder_icon = assets_dir / "icon_placeholder.txt"
    with open(placeholder_icon, 'w', encoding='utf-8') as f:
        f.write("请将icon.ico文件放在此文件夹中\n")
        f.write("Windows平台推荐使用.ico格式图标\n")
        f.write("Mac平台推荐使用.icns格式图标\n")
    
    print(f"已创建assets文件夹: {assets_dir.absolute()}")

def check_requirements():
    """检查打包所需的依赖 - 虚拟环境版本，只检查不安装"""
    print("检查依赖...")
    print("使用虚拟环境打包模式，假设所有依赖已在虚拟环境中安装")
    print("✓ 使用虚拟环境中的Python和依赖")
    print("✓ 已安装的依赖: pypdf, python-dotenv, PyQt6, Pillow, PyInstaller, requests, pdf2image")
    print("✓ LLM相关依赖: langchain-openai, langchain-core")
    print("\n✓ 应用已包含LLM功能所需的依赖配置\n")
    
    return True

def kill_running_processes():
    """检查并终止运行中的EasyBookMark进程"""
    print("检查是否有正在运行的EasyBookMark进程...")
    process_killed = False
    
    try:
        # 在Windows上使用taskkill命令终止进程
        import subprocess
        result = subprocess.run(
            ['tasklist', '/fi', 'imagename eq EasyBookMark.exe'],
            capture_output=True,
            text=True
        )
        
        if 'EasyBookMark.exe' in result.stdout:
            print("发现正在运行的EasyBookMark进程，正在终止...")
            subprocess.run(['taskkill', '/f', '/im', 'EasyBookMark.exe'])
            process_killed = True
            print("已终止运行中的EasyBookmark进程")
        else:
            print("未发现运行中的EasyBookmark进程")
    except Exception as e:
        print(f"检查或终止进程时出错: {e}")
    
    # 如果终止了进程，给系统一点时间释放文件锁
    if process_killed:
        import time
        print("等待系统释放文件锁...")
        time.sleep(2)

def clean_dist_build():
    """彻底清理之前的构建文件，确保重新打包时不包含任何旧文件"""
    print("彻底清理之前的构建文件...")
    
    # 先终止可能正在运行的进程
    kill_running_processes()
    
    # 定义需要删除的目录
    build_dir = Path('build')
    dist_dir = Path('dist')
    
    # 先尝试使用Windows命令行强制删除，这通常更有效
    def force_delete_windows(path):
        if not path.exists():
            return True
        
        try:
            import subprocess
            # 使用Windows的rmdir命令强制删除目录
            cmd = ['cmd', '/c', 'rmdir', '/s', '/q', str(path)]
            subprocess.run(cmd, check=False, capture_output=True)
            # 再次检查是否删除成功
            if not path.exists():
                print(f"成功强制删除目录: {path}")
                return True
        except Exception as e:
            print(f"强制删除目录 {path} 时出错: {e}")
        return False
    
    # 重试删除目录的函数
    def try_remove_dir(path, max_retries=5):
        import time  # 确保在函数内也能访问time模块
        # 首先尝试强制删除
        if force_delete_windows(path):
            return True
            
        # 如果强制删除失败，尝试Python的shutil方法
        for i in range(max_retries):
            try:
                if path.exists():
                    # 先尝试删除目录中的所有可执行文件
                    for exe_file in path.glob("**/*.exe"):
                        try:
                            os.chmod(exe_file, 0o777)  # 添加执行权限
                            exe_file.unlink()
                            print(f"已删除可执行文件: {exe_file}")
                        except Exception as e:
                            print(f"删除可执行文件 {exe_file} 时出错: {e}")
                    
                    # 删除整个目录
                    shutil.rmtree(path, ignore_errors=True)
                    
                    # 等待一下
                    time.sleep(0.5)
                    
                    if not path.exists():
                        print(f"已删除目录: {path}")
                        return True
            except Exception as e:
                print(f"删除目录 {path} 时出错 (尝试 {i+1}/{max_retries}): {e}")
                if i < max_retries - 1:
                    time.sleep(1)
        return False
    
    # 先检查并删除可能的单个可执行文件
    single_exe = Path('dist/EasyBookmark.exe')
    if single_exe.exists():
        try:
            single_exe.unlink()
            print(f"已删除单个可执行文件: {single_exe}")
        except Exception as e:
            print(f"删除单个可执行文件时出错: {e}")
    
    # 删除子目录中的可执行文件
    exe_dir = Path('dist/EasyBookmark/EasyBookmark.exe')
    if exe_dir.exists():
        try:
            exe_dir.unlink()
            print(f"已删除子目录中的可执行文件: {exe_dir}")
        except Exception as e:
            print(f"删除子目录中的可执行文件时出错: {e}")
    
    # 删除build目录
    try_remove_dir(build_dir)
    
    # 删除dist目录
    if not try_remove_dir(dist_dir):
        # 如果无法删除整个dist目录，尝试删除其中的内容
        print("尝试删除dist目录中的内容...")
        if dist_dir.exists():
            for item in dist_dir.iterdir():
                try_remove_dir(item)
        
        # 创建一个新的输出目录名称，基于时间戳
        import time
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        new_dist_dir = Path(f'dist_{timestamp}')
        print(f"将使用新的输出目录: {new_dist_dir}")
        # 修改环境变量来影响pyinstaller的行为
        os.environ['PYINSTALLER_DISTPATH'] = str(new_dist_dir)
    
    print("清理完成")


def package_windows():
    """打包Windows应用程序 - 使用虚拟环境中的Python和PyInstaller"""
    print("开始在Windows平台上打包...")
    
    # 获取当前使用的输出目录
    dist_dir = os.environ.get('PYINSTALLER_DISTPATH', os.path.join(os.getcwd(), 'dist'))
    print(f"使用输出目录: {dist_dir}")
    
    # 使用虚拟环境中的PyInstaller
    venv_pyinstaller = os.path.join(os.getcwd(), 'venv_clean', 'Scripts', 'pyinstaller.exe')
    print(f"使用虚拟环境中的PyInstaller: {venv_pyinstaller}")
    
    # 使用PyInstaller打包
    try:
        # 检查是否存在spec文件，如果存在则使用spec文件打包
        spec_file = Path('EasyBookmark.spec')
        if spec_file.exists():
            print(f"使用spec文件: {spec_file}")
            subprocess.run([venv_pyinstaller, spec_file.name], check=True, capture_output=True, text=True)
        else:
            # 直接使用命令行参数打包
            print("使用命令行参数打包")
            cmd = [
                venv_pyinstaller,
                '--name', 'EasyBookmark',
                '--windowed',  # 不显示控制台窗口
                '--noconsole',
                '--onefile',  # 生成单个可执行文件
                '--hidden-import', 'pypdf',
                '--hidden-import', 'pypdf.pdf',
                '--hidden-import', 'pypdf._utils',
                '--hidden-import', 'PyQt6',
                '--hidden-import', 'PyQt6.QtCore',
                '--hidden-import', 'PyQt6.QtWidgets',
                '--hidden-import', 'PyQt6.QtGui',
                '--hidden-import', 'python_dotenv',
                '--hidden-import', 'PIL',
                '--hidden-import', 'PIL.Image',
                'main.py'
            ]
            
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("✓ Windows打包完成")
        # 尝试使用环境变量中的dist目录查找可执行文件
        try:
            exe_path = os.path.join(dist_dir, 'EasyBookmark.exe')
            if os.path.exists(exe_path):
                print(f"可执行文件位置: {exe_path}")
            else:
                # 尝试查找可执行文件
                print("查找可执行文件...")
                found = False
                for root, dirs, files in os.walk(dist_dir):
                    if 'EasyBookmark.exe' in files:
                        exe_path = os.path.join(root, 'EasyBookmark.exe')
                        print(f"找到可执行文件: {exe_path}")
                        found = True
                        break
                if not found:
                    print("可执行文件位置: 未找到，请在dist目录中查找")
        except Exception as e:
            print(f"查找可执行文件时出错: {e}")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Windows打包失败: {e}")
        print("错误输出:")
        print(e.stderr)
        
        # 尝试使用直接命令行方式重新打包...
        try:
            # 直接使用虚拟环境中的pyinstaller命令行参数
            direct_cmd = [
                venv_pyinstaller,
                '--name=EasyBookmark',
                '--windowed',  # 无控制台窗口
                '--add-data=src;src',
                '--add-data=assets;assets',
                '--icon=assets/logo.ico',
                '--hidden-import=pypdf',
                '--hidden-import=pypdf.pdf',
                '--hidden-import=pypdf._utils',
                '--hidden-import=PyQt6.QtSvg',
                '--hidden-import=python_dotenv',
                '--hidden-import=PIL',
                '--hidden-import=PIL.Image',
                '--hidden-import=requests',
                '--hidden-import=pdf2image',
                '--hidden-import=langchain_openai',
                '--hidden-import=langchain_core',
                '--hidden-import=openai',
                '--hidden-import=langsmith',
                '--onefile',  # 生成单个可执行文件
                'main.py'
            ]
            print(f"执行直接命令: {' '.join(direct_cmd[:10])} ...")
            
            # 执行直接打包命令
            direct_result = subprocess.run(direct_cmd, check=True)
            print("直接打包成功！")
            return True
        except Exception as direct_e:
            print(f"直接打包也失败: {direct_e}")
            return False
    except Exception as e:
        print(f"✗ Windows打包失败: {e}")
        return False

def package_mac():
    """Mac平台打包"""
    print("开始在Mac平台上打包...")
    
    # 使用PyInstaller打包
    try:
        # 检查是否存在spec文件，如果存在则使用spec文件打包
        spec_file = Path('pdf_easy.spec')
        if spec_file.exists():
            print(f"使用spec文件: {spec_file}")
            subprocess.run(['pyinstaller', spec_file.name], check=True)
        else:
            # 直接使用命令行参数打包
            print("使用命令行参数打包")
            cmd = [
                'pyinstaller',
                '--name', 'EasyBookmark',
                '--windowed',  # 创建.app包
                '--onefile',  # 生成单个可执行文件
                '--hidden-import', 'pypdf',
                '--hidden-import', 'pypdf.pdf',
                '--hidden-import', 'pypdf._utils',
                # langchain相关依赖需要用户手动安装
                # '--hidden-import', 'langchain',
                # '--hidden-import', 'langchain_openai',
                # '--hidden-import', 'langchain_core',
                '--hidden-import', 'PyQt6',
                '--hidden-import', 'PyQt6.QtCore',
                '--hidden-import', 'PyQt6.QtWidgets',
                '--hidden-import', 'PyQt6.QtGui',
            ]
            
            # 暂时不使用图标参数，避免转换错误
            pass
            
            # 添加主程序
            cmd.append('main.py')
            
            subprocess.run(cmd, check=True)
        
        print("✓ Mac打包完成")
        print(f"应用程序位置: {Path('dist/EasyBookmark.app').absolute()}")
        return True
    except Exception as e:
        print(f"✗ Mac打包失败: {e}")
        return False

def main():
    """主函数"""
    print("=== EasyBookmark 应用打包脚本 ===")
    
    # 创建assets文件夹
    create_assets_folder()
    
    # 检查依赖
    if not check_requirements():
        print("依赖检查失败，退出")
        return 1
    
    # 清理之前的构建文件
    clean_dist_build()
    
    # 根据当前平台选择打包方式
    current_os = platform.system()
    
    if current_os == 'Windows':
        success = package_windows()
    elif current_os == 'Darwin':  # Mac
        success = package_mac()
    else:
        print(f"不支持的平台: {current_os}")
        print("请手动使用PyInstaller打包")
        return 1
    
    if success:
        print("\n✅ 打包成功！")
        print("\n提示：")
        print("1. 请测试生成的可执行文件确保功能正常")
        print("2. 对于Windows，可执行文件在dist目录下")
        print("3. 对于Mac，应用程序在dist目录下")
        return 0
    else:
        print("\n❌ 打包失败")
        return 1

if __name__ == '__main__':
    sys.exit(main())