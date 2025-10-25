#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SR客户端启动器
一键启动客户端并在客户端关闭时自动清理补丁文件

Version: 1.1.0
License: GNU V3 LICENSE
"""

import os
import sys
import time
import shutil
import subprocess
import psutil
import ctypes
from pathlib import Path

def is_admin():
    """检查是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """以管理员权限重新启动程序
    
    TODO: 修复UAC权限申请逻辑问题
    当前问题：
    - 权限申请成功后程序调用sys.exit(0)退出，导致无法继续执行主要逻辑
    - 需要确保权限申请成功后程序继续运行，而不是退出
    
    正确逻辑：
    1. 如果已经有管理员权限，直接返回True继续执行
    2. 如果没有权限，申请权限并重新启动程序，当前进程退出
    3. 权限申请失败时，进行清理并退出
    """
    if is_admin():
        return True
    else:
        print("检测到需要管理员权限才能正常运行客户端")
        print("正在申请管理员权限...")
        print("请在UAC提示框中点击'是'以继续")
        
        try:
            # 构建命令行参数
            if getattr(sys, 'frozen', False):
                # 打包后的可执行文件
                executable = sys.executable
            else:
                # Python脚本
                executable = sys.executable
                sys.argv.insert(0, __file__)
            
            # 重新以管理员权限启动
            result = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", executable, " ".join(sys.argv), None, 1
            )
            
            if result > 32:  # 成功
                print("管理员权限申请成功，程序将重新启动...")
                # TODO: 修复 - 权限申请成功后，当前进程应该退出，让新的管理员进程继续
                # 这是正确的行为，因为新进程会以管理员权限重新运行整个程序
                sys.exit(0)
            else:
                print("管理员权限申请失败或被用户取消")
                # TODO: 权限申请失败时，应该进行清理操作
                try:
                    # 尝试清理可能已经复制的补丁文件
                    launcher = ClientLauncher()
                    launcher.cleanup_patch_files()
                except:
                    pass  # 如果清理失败，忽略错误
                input("按回车键退出...")
                sys.exit(1)
                
        except Exception as e:
            print(f"申请管理员权限时出错: {e}")
            # TODO: 异常情况下也要进行清理
            try:
                launcher = ClientLauncher()
                launcher.cleanup_patch_files()
            except:
                pass
            input("按回车键退出...")
            sys.exit(1)

class ClientLauncher:
    """客户端启动器"""
    
    def __init__(self):
        # 获取当前脚本所在目录
        if getattr(sys, 'frozen', False):
            # 打包后的可执行文件 (d:\Games\SR\Patch\manager\client_launcher.exe)
            self.script_dir = Path(sys.executable).parent
            # 打包环境：script_dir = d:\Games\SR\Patch\manager
            self.patch_dir = self.script_dir.parent  # d:\Games\SR\Patch
        else:
            # 开发环境中的Python脚本 (d:\Games\SR\Patch\opencode\manager\client_launcher.py)
            self.script_dir = Path(__file__).parent
            # 开发环境：script_dir = d:\Games\SR\Patch\opencode\manager
            self.patch_dir = self.script_dir.parent.parent  # d:\Games\SR\Patch
        
        # 设置路径（两种环境下都相同）
        self.client_dir = self.patch_dir.parent / "Client"  # d:\Games\SR\Client
        self.releases_dir = self.patch_dir / "releases"  # d:\Games\SR\Patch\releases
        
        # 补丁文件
        self.patch_files = [
            "cyrene.exe",
            "cyrene.dll"
        ]
        
        print(f"补丁目录: {self.patch_dir}")
        print(f"客户端目录: {self.client_dir}")
        print(f"补丁文件目录: {self.releases_dir}")
    
    def check_files(self):
        """检查必要文件是否存在"""
        print("检查文件...")
        
        # 检查客户端目录
        if not self.client_dir.exists():
            print(f"错误: 客户端目录不存在: {self.client_dir}")
            return False
        
        # 检查StarRail.exe
        starrail_exe = self.client_dir / "StarRail.exe"
        if not starrail_exe.exists():
            print(f"错误: 客户端可执行文件不存在: {starrail_exe}")
            return False
        
        # 检查补丁文件
        missing_files = []
        for patch_file in self.patch_files:
            patch_path = self.releases_dir / patch_file
            if not patch_path.exists():
                missing_files.append(str(patch_path))
        
        if missing_files:
            print("错误: 以下补丁文件不存在:")
            for file in missing_files:
                print(f"  - {file}")
            return False
        
        print("✓ 所有必要文件检查通过")
        return True
    
    def copy_patch_files(self):
        """复制补丁文件到客户端目录"""
        print("复制补丁文件...")
        
        try:
            for patch_file in self.patch_files:
                src_path = self.releases_dir / patch_file
                dst_path = self.client_dir / patch_file
                
                print(f"复制 {patch_file}...")
                shutil.copy2(src_path, dst_path)
                print(f"✓ {patch_file} 复制成功")
            
            print("✓ 所有补丁文件复制完成")
            return True
            
        except Exception as e:
            print(f"错误: 复制补丁文件失败: {e}")
            return False
    
    def launch_client(self):
        """启动客户端"""
        print("启动客户端...")
        
        try:
            # 使用cyrene.exe启动客户端
            cyrene_exe = self.client_dir / "cyrene.exe"
            
            print(f"执行: {cyrene_exe}")
            process = subprocess.Popen(
                [str(cyrene_exe)],
                cwd=str(self.client_dir),
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
            )
            
            print(f"✓ 客户端已启动 (PID: {process.pid})")
            return process
            
        except Exception as e:
            print(f"错误: 启动客户端失败: {e}")
            return None
    
    def wait_for_client_exit(self, process):
        """等待客户端退出"""
        print("等待客户端退出...")
        print("提示: 您可以安全地关闭此窗口，补丁文件会在客户端退出时自动清理")
        
        try:
            # 等待进程结束
            process.wait()
            print("客户端已退出")
            
        except KeyboardInterrupt:
            print("收到中断信号，但会继续监控客户端...")
            # 即使用户中断，也要继续监控客户端进程
            try:
                while process.poll() is None:
                    time.sleep(1)
                print("客户端已退出")
            except:
                pass
        
        except Exception as e:
            print(f"监控客户端时出错: {e}")
    
    def cleanup_patch_files(self):
        """清理补丁文件"""
        print("清理补丁文件...")
        
        try:
            for patch_file in self.patch_files:
                file_path = self.client_dir / patch_file
                
                if file_path.exists():
                    print(f"删除 {patch_file}...")
                    file_path.unlink()
                    print(f"✓ {patch_file} 已删除")
                else:
                    print(f"- {patch_file} 不存在，跳过")
            
            print("✓ 补丁文件清理完成")
            return True
            
        except Exception as e:
            print(f"错误: 清理补丁文件失败: {e}")
            return False
    
    def run(self):
        """运行启动器"""
        print("=" * 50)
        print("SR客户端启动器")
        print("=" * 50)
        
        # 检查文件
        if not self.check_files():
            print("启动失败，请检查文件完整性")
            input("按回车键退出...")
            return False
        
        # 复制补丁文件
        if not self.copy_patch_files():
            print("启动失败，无法复制补丁文件")
            input("按回车键退出...")
            return False
        
        # 启动客户端
        process = self.launch_client()
        if not process:
            print("启动失败，无法启动客户端")
            # 清理已复制的文件
            self.cleanup_patch_files()
            input("按回车键退出...")
            return False
        
        print("客户端启动成功！")
        print("注意: 请不要手动删除补丁文件，启动器会在客户端退出时自动清理")
        
        # 等待客户端退出
        self.wait_for_client_exit(process)
        
        # 清理补丁文件
        self.cleanup_patch_files()
        
        print("客户端已关闭，补丁文件已清理")
        print("感谢使用SR客户端启动器！")
        
        return True

def main():
    """主函数"""
    # 检查并申请管理员权限
    # 如果没有权限，run_as_admin()会申请权限并重新启动程序，当前进程会退出
    # 如果已有权限，run_as_admin()返回True，程序继续执行
    run_as_admin()
    
    # 执行到这里说明已经有管理员权限了
    print("✓ 已获得管理员权限")
    
    try:
        launcher = ClientLauncher()
        success = launcher.run()
        
        if not success:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("用户中断操作")
        # 确保在异常情况下也清理补丁文件
        try:
            launcher = ClientLauncher()
            launcher.cleanup_patch_files()
        except:
            pass
        sys.exit(0)
    except Exception as e:
        print(f"启动器运行时出错: {e}")
        import traceback
        traceback.print_exc()
        # 确保在异常情况下也清理补丁文件
        try:
            launcher = ClientLauncher()
            launcher.cleanup_patch_files()
        except:
            pass
        input("按回车键退出...")
        sys.exit(1)

if __name__ == "__main__":
    main()