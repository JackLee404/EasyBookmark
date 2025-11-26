import os
import shutil
import time
import subprocess
from pathlib import Path

def force_clean():
    print("开始强制清理构建文件...")
    
    # 先尝试终止所有相关进程
    print("尝试终止相关进程...")
    try:
        subprocess.run(["taskkill", "/F", "/IM", "EasyBookmark.exe"], check=False)
    except Exception as e:
        print(f"终止进程时出错: {e}")
    
    # 等待一下让进程完全结束
    time.sleep(2)
    
    # 尝试删除dist目录
    dist_dir = Path("dist")
    if dist_dir.exists():
        print(f"尝试删除dist目录: {dist_dir}")
        try:
            # 先尝试删除单个可执行文件
            exe_file = dist_dir / "EasyBookmark.exe"
            if exe_file.exists():
                print(f"尝试删除可执行文件: {exe_file}")
                try:
                    # 更改文件权限
                    os.chmod(exe_file, 0o777)
                    # 尝试使用PowerShell删除
                    subprocess.run(["powershell", "Remove-Item", str(exe_file), "-Force"], check=True)
                    print("✓ 成功删除可执行文件")
                except Exception as e:
                    print(f"删除可执行文件时出错: {e}")
            
            # 尝试重命名dist目录
            try:
                backup_name = f"dist_backup_{int(time.time())}"
                dist_dir.rename(backup_name)
                print(f"✓ 成功将dist目录重命名为: {backup_name}")
                # 然后尝试删除重命名后的目录
                shutil.rmtree(backup_name, ignore_errors=True)
                print(f"✓ 成功删除备份目录: {backup_name}")
            except Exception as e:
                print(f"重命名dist目录时出错: {e}")
        except Exception as e:
            print(f"处理dist目录时出错: {e}")
    
    # 尝试删除build目录
    build_dir = Path("build")
    if build_dir.exists():
        print(f"尝试删除build目录: {build_dir}")
        try:
            shutil.rmtree(build_dir, ignore_errors=True)
            if not build_dir.exists():
                print("✓ 成功删除build目录")
        except Exception as e:
            print(f"删除build目录时出错: {e}")
    
    print("清理完成！")

if __name__ == "__main__":
    force_clean()