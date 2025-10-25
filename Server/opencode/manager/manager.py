#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SR私服管理器
基于CustomTkinter的现代化GUI私服管理工具

Version: 1.0.0
License: GNU V3 LICENSE
"""

import os
import sys
import json
import time
import threading
import subprocess
import argparse
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, Callable
from pathlib import Path

import customtkinter as ctk
import psutil
try:
    import darkdetect
except ImportError:
    darkdetect = None

# 设置CustomTkinter外观
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

def get_base_path():
    """
    智能检测当前运行环境并返回正确的基础路径
    - 如果在 opencode/manager 目录下运行，返回 ../../
    - 如果在 manager 目录下运行，返回 ../
    """
    if getattr(sys, 'frozen', False):
        # 打包后的可执行文件
        current_dir = Path(sys.executable).parent
    else:
        # 开发环境中的Python脚本
        current_dir = Path(__file__).parent
    
    # 检查当前目录结构来判断运行环境
    if current_dir.name == "manager" and current_dir.parent.name == "opencode":
        # 在 opencode/manager 目录下运行
        return "../../"
    elif current_dir.name == "manager" and current_dir.parent.name == "Server":
        # 在 Server/manager 目录下运行
        return "../"
    else:
        # 默认情况，假设在 Server/manager 目录下
        return "../"

def get_service_paths():
    """根据运行环境动态生成服务路径配置"""
    base_path = get_base_path()
    return {
        "cyrene-sr-gameserver": {
            "executable": f"{base_path}releases/pexecvelf/pexecvelf.exe",
            "args": [f"{base_path}releases/cyrene-sr/gameserver"]
        },
        "cyrene-sr-dispatch": {
            "executable": f"{base_path}releases/pexecvelf/pexecvelf.exe", 
            "args": [f"{base_path}releases/cyrene-sr/dispatch"]
        },
        "hoyo-sdk": {
            "executable": f"{base_path}releases/hoyo-sdk/hoyo-sdk.exe",
            "args": []
        }
    }

# 硬编码配置，动态适应运行环境
HARDCODED_CONFIG = {
    "version": "1.0.0",
    "theme_config": {
        "mode": "auto",
        "current_theme": "dark",
        "auto_detect": True
    },
    "service_config": {
        "startup_timeout": 10,
        "auto_restart": False,
        "service_paths": get_service_paths()
    },
    "ui_config": {
        "window_width": 800,
        "window_height": 600,
        "font_size": 14,
        "remember_position": True,
        "last_position": {
            "x": 759,
            "y": 201
        }
    }
}

class ServiceStatus(Enum):
    """服务状态枚举"""
    STOPPED = "stopped"      # 红色指示灯
    STARTING = "starting"    # 黄色指示灯  
    RUNNING = "running"      # 绿色指示灯
    ERROR = "error"          # 红色闪烁指示灯

class ThemeMode(Enum):
    """主题模式枚举"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = None):
        # 使用硬编码配置，不再依赖外部配置文件
        self.config = HARDCODED_CONFIG.copy()
    
    def save_config(self) -> bool:
        """保存配置文件 - 现在只是一个占位符，因为使用硬编码配置"""
        # 不再保存到文件，因为使用硬编码配置
        return True
    
    def get_setting(self, key: str) -> Any:
        """获取设置值"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        return value
    
    def set_setting(self, key: str, value: Any) -> None:
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

class ThemeManager:
    """主题管理器"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.current_theme = self.config_manager.get_setting("theme_config.current_theme") or "light"
        self.mode = self.config_manager.get_setting("theme_config.mode") or "auto"
        
        # 主题颜色定义
        self.colors = {
            "light": {
                "bg_primary": "#FFFFFF",
                "bg_secondary": "#F0F0F0",
                "text_primary": "#2B2B2B",
                "text_secondary": "#666666",
                "accent": "#1F6AA5",
                "success": "#4CAF50",
                "warning": "#FF9800",
                "error": "#F44336"
            },
            "dark": {
                "bg_primary": "#212121",
                "bg_secondary": "#2E2E2E",
                "text_primary": "#FFFFFF",
                "text_secondary": "#CCCCCC",
                "accent": "#1F6AA5",
                "success": "#4CAF50",
                "warning": "#FF9800",
                "error": "#F44336"
            }
        }
    
    def set_theme(self, theme: str) -> None:
        """设置主题"""
        if theme in ["light", "dark", "auto"]:
            if theme == "auto":
                self.mode = "auto"
                self.current_theme = self.detect_system_theme()
            else:
                self.mode = theme
                self.current_theme = theme
            
            # 应用主题到CustomTkinter
            ctk.set_appearance_mode(self.current_theme)
            
            # 保存配置
            self.config_manager.set_setting("theme_config.mode", self.mode)
            self.config_manager.set_setting("theme_config.current_theme", self.current_theme)
            self.config_manager.save_config()
    
    def get_current_theme(self) -> str:
        """获取当前主题"""
        return self.current_theme
    
    def detect_system_theme(self) -> str:
        """检测系统主题"""
        if darkdetect:
            try:
                system_theme = darkdetect.theme()
                return "dark" if system_theme == "Dark" else "light"
            except:
                pass
        return "light"
    
    def get_color(self, color_name: str) -> str:
        """获取主题颜色"""
        return self.colors.get(self.current_theme, {}).get(color_name, "#000000")

class ProcessManager:
    """进程管理器"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.service_processes: Dict[str, subprocess.Popen] = {}
        self.service_status: Dict[str, ServiceStatus] = {}
        self.status_callbacks: Dict[str, Callable] = {}
        
        # 初始化服务状态
        service_paths = self.config_manager.get_setting("service_config.service_paths") or {}
        for service_name in service_paths.keys():
            self.service_status[service_name] = ServiceStatus.STOPPED
    
    def register_status_callback(self, service_name: str, callback: Callable):
        """注册状态变化回调"""
        self.status_callbacks[service_name] = callback
    
    def _notify_status_change(self, service_name: str, status: ServiceStatus):
        """通知状态变化"""
        self.service_status[service_name] = status
        if service_name in self.status_callbacks:
            self.status_callbacks[service_name](status)
    
    def start_service(self, service_name: str) -> bool:
        """启动服务"""
        try:
            service_paths = self.config_manager.get_setting("service_config.service_paths")
            if not service_paths or service_name not in service_paths:
                return False
            
            service_config = service_paths[service_name]
            
            # 支持新的配置格式（包含executable和args）和旧格式（直接路径）
            if isinstance(service_config, dict):
                executable_path = service_config.get("executable", "")
                args = service_config.get("args", [])
            else:
                # 兼容旧格式
                executable_path = service_config
                args = []
            
            # 使用智能路径解析
            if getattr(sys, 'frozen', False):
                # 打包后的可执行文件
                base_dir = Path(sys.executable).parent
            else:
                # 开发环境中的Python脚本
                base_dir = Path(__file__).parent
            
            abs_executable_path = base_dir / executable_path
            
            if not abs_executable_path.exists():
                print(f"可执行文件不存在: {abs_executable_path}")
                self._notify_status_change(service_name, ServiceStatus.ERROR)
                return False
            
            # 检查服务是否已经在运行
            if self.is_service_running(service_name):
                return True
            
            # 设置启动状态
            self._notify_status_change(service_name, ServiceStatus.STARTING)
            
            # 构建命令行参数
            cmd = [str(abs_executable_path)]
            if args:
                # 将相对路径转换为绝对路径
                for arg in args:
                    if arg.startswith("../") or arg.startswith("./"):
                        abs_arg_path = base_dir / arg
                        cmd.append(str(abs_arg_path))
                    else:
                        cmd.append(arg)
            
            # 启动进程
            process = subprocess.Popen(
                cmd,
                cwd=abs_executable_path.parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
            )
            
            self.service_processes[service_name] = process
            
            # 启动监控线程
            threading.Thread(
                target=self._monitor_service,
                args=(service_name, process),
                daemon=True
            ).start()
            
            return True
            
        except Exception as e:
            print(f"启动服务失败 {service_name}: {e}")
            self._notify_status_change(service_name, ServiceStatus.ERROR)
            return False
    
    def stop_service(self, service_name: str) -> bool:
        """停止服务"""
        try:
            if service_name in self.service_processes:
                process = self.service_processes[service_name]
                if process and process.poll() is None:
                    process.terminate()
                    # 等待进程结束
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                
                del self.service_processes[service_name]
            
            self._notify_status_change(service_name, ServiceStatus.STOPPED)
            return True
            
        except Exception as e:
            print(f"停止服务失败 {service_name}: {e}")
            return False
    
    def restart_service(self, service_name: str) -> bool:
        """重启服务"""
        self.stop_service(service_name)
        time.sleep(1)  # 等待进程完全停止
        return self.start_service(service_name)
    
    def get_service_status(self, service_name: str) -> ServiceStatus:
        """获取服务状态"""
        return self.service_status.get(service_name, ServiceStatus.STOPPED)
    
    def is_service_running(self, service_name: str) -> bool:
        """检查服务是否运行"""
        if service_name in self.service_processes:
            process = self.service_processes[service_name]
            return process and process.poll() is None
        return False
    
    def _monitor_service(self, service_name: str, process: subprocess.Popen):
        """监控服务进程"""
        timeout = self.config_manager.get_setting("service_config.startup_timeout") or 10
        start_time = time.time()
        
        # 等待进程启动
        while time.time() - start_time < timeout:
            if process.poll() is not None:
                # 进程已退出
                self._notify_status_change(service_name, ServiceStatus.ERROR)
                return
            time.sleep(0.5)
        
        # 启动成功
        self._notify_status_change(service_name, ServiceStatus.RUNNING)
        
        # 继续监控进程
        while process.poll() is None:
            time.sleep(1)
        
        # 进程异常退出
        if service_name in self.service_processes:
            self._notify_status_change(service_name, ServiceStatus.ERROR)

class ServiceCard(ctk.CTkFrame):
    """服务状态卡片"""
    
    def __init__(self, parent, service_name: str, process_manager: ProcessManager, theme_manager: ThemeManager):
        super().__init__(parent)
        
        self.service_name = service_name
        self.process_manager = process_manager
        self.theme_manager = theme_manager
        self.status = ServiceStatus.STOPPED
        
        self.setup_ui()
        self.update_status(self.process_manager.get_service_status(service_name))
        
        # 注册状态变化回调
        self.process_manager.register_status_callback(service_name, self.update_status)
    
    def setup_ui(self):
        """设置UI"""
        self.grid_columnconfigure(1, weight=1)
        
        # 状态指示灯
        self.status_indicator = ctk.CTkLabel(
            self, 
            text="●", 
            font=ctk.CTkFont(size=20),
            width=30
        )
        self.status_indicator.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="w")
        
        # 服务名称
        self.name_label = ctk.CTkLabel(
            self,
            text=self.service_name,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.name_label.grid(row=0, column=1, padx=5, pady=10, sticky="w")
        
        # 状态文字
        self.status_label = ctk.CTkLabel(
            self,
            text="已停止",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.grid(row=1, column=1, padx=5, pady=(0, 10), sticky="w")
        
        # 控制按钮
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.grid(row=0, column=2, rowspan=2, padx=10, pady=10, sticky="e")
        
        self.start_button = ctk.CTkButton(
            self.button_frame,
            text="启动",
            width=80,
            height=32,
            fg_color="#4CAF50",
            hover_color="#45A049",
            command=self.start_service
        )
        self.start_button.grid(row=0, column=0, padx=2, pady=2)
        
        self.stop_button = ctk.CTkButton(
            self.button_frame,
            text="停止",
            width=80,
            height=32,
            fg_color="#F44336",
            hover_color="#DA190B",
            command=self.stop_service
        )
        self.stop_button.grid(row=0, column=1, padx=2, pady=2)
        
        self.restart_button = ctk.CTkButton(
            self.button_frame,
            text="重启",
            width=80,
            height=32,
            fg_color="#FF9800",
            hover_color="#F57C00",
            command=self.restart_service
        )
        self.restart_button.grid(row=0, column=2, padx=2, pady=2)
    
    def update_status(self, status: ServiceStatus):
        """更新状态显示"""
        self.status = status
        
        # 更新指示灯颜色和状态文字
        if status == ServiceStatus.STOPPED:
            self.status_indicator.configure(text_color="#F44336")
            self.status_label.configure(text="已停止")
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.restart_button.configure(state="disabled")
        elif status == ServiceStatus.STARTING:
            self.status_indicator.configure(text_color="#FF9800")
            self.status_label.configure(text="启动中...")
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.restart_button.configure(state="disabled")
        elif status == ServiceStatus.RUNNING:
            self.status_indicator.configure(text_color="#4CAF50")
            self.status_label.configure(text="运行中")
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.restart_button.configure(state="normal")
        elif status == ServiceStatus.ERROR:
            self.status_indicator.configure(text_color="#F44336")
            self.status_label.configure(text="错误")
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.restart_button.configure(state="normal")
    
    def start_service(self):
        """启动服务"""
        threading.Thread(
            target=self.process_manager.start_service,
            args=(self.service_name,),
            daemon=True
        ).start()
    
    def stop_service(self):
        """停止服务"""
        threading.Thread(
            target=self.process_manager.stop_service,
            args=(self.service_name,),
            daemon=True
        ).start()
    
    def restart_service(self):
        """重启服务"""
        threading.Thread(
            target=self.process_manager.restart_service,
            args=(self.service_name,),
            daemon=True
        ).start()

class ConfirmDialog(ctk.CTkToplevel):
    """确认对话框"""
    
    def __init__(self, parent, title: str, message: str, callback: Callable = None):
        super().__init__(parent)
        
        self.callback = callback
        self.result = False
        
        self.title(title)
        self.geometry("400x200")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # 居中显示
        self.center_window()
        
        self.setup_ui(message)
    
    def center_window(self):
        """窗口居中"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.winfo_screenheight() // 2) - (200 // 2)
        self.geometry(f"400x200+{x}+{y}")
    
    def setup_ui(self, message: str):
        """设置UI"""
        # 消息文本
        self.message_label = ctk.CTkLabel(
            self,
            text=message,
            font=ctk.CTkFont(size=14),
            wraplength=350
        )
        self.message_label.pack(pady=30, padx=20)
        
        # 按钮框架
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(pady=20)
        
        # 确认按钮
        self.confirm_button = ctk.CTkButton(
            self.button_frame,
            text="确认",
            width=100,
            command=self.confirm
        )
        self.confirm_button.pack(side="left", padx=10)
        
        # 取消按钮
        self.cancel_button = ctk.CTkButton(
            self.button_frame,
            text="取消",
            width=100,
            fg_color="gray",
            command=self.cancel
        )
        self.cancel_button.pack(side="left", padx=10)
    
    def confirm(self):
        """确认操作"""
        self.result = True
        if self.callback:
            self.callback()
        self.destroy()
    
    def cancel(self):
        """取消操作"""
        self.result = False
        self.destroy()

class ErrorDialog(ctk.CTkToplevel):
    """错误提示对话框"""
    
    def __init__(self, parent, title: str, message: str):
        super().__init__(parent)
        
        self.title(title)
        self.geometry("400x200")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # 居中显示
        self.center_window()
        
        self.setup_ui(message)
    
    def center_window(self):
        """窗口居中"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.winfo_screenheight() // 2) - (200 // 2)
        self.geometry(f"400x200+{x}+{y}")
    
    def setup_ui(self, message: str):
        """设置UI"""
        # 错误图标和消息
        self.message_label = ctk.CTkLabel(
            self,
            text=f"❌ {message}",
            font=ctk.CTkFont(size=14),
            wraplength=350
        )
        self.message_label.pack(pady=30, padx=20)
        
        # 确定按钮
        self.ok_button = ctk.CTkButton(
            self,
            text="确定",
            width=100,
            command=self.destroy
        )
        self.ok_button.pack(pady=20)

class MainWindow(ctk.CTk):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化管理器
        self.config_manager = ConfigManager()
        self.theme_manager = ThemeManager(self.config_manager)
        self.process_manager = ProcessManager(self.config_manager)
        
        self.setup_window()
        self.setup_ui()
        self.setup_bindings()
        
        # 应用主题
        self.theme_manager.set_theme(self.theme_manager.mode)
    
    def setup_window(self):
        """设置窗口"""
        self.title("SR测试服私服管理器 - Open and Free")
        
        # 获取窗口配置
        width = self.config_manager.get_setting("ui_config.window_width") or 800
        height = self.config_manager.get_setting("ui_config.window_height") or 600
        
        self.geometry(f"{width}x{height}")
        self.minsize(800, 600)
        
        # 设置窗口位置
        if self.config_manager.get_setting("ui_config.remember_position"):
            pos = self.config_manager.get_setting("ui_config.last_position")
            if pos:
                self.geometry(f"{width}x{height}+{pos['x']}+{pos['y']}")
        
        # 设置窗口图标（如果有的话）
        try:
            self.iconbitmap("icon.ico")
        except:
            pass
    
    def setup_ui(self):
        """设置UI"""
        # 主框架
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 顶部框架（标题和主题切换）
        self.top_frame = ctk.CTkFrame(self.main_frame)
        self.top_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # 标题
        self.title_label = ctk.CTkLabel(
            self.top_frame,
            text="私服服务管理",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.pack(side="left", padx=10, pady=10)
        
        # 主题切换
        self.theme_var = ctk.StringVar(value=self.theme_manager.mode)
        self.theme_menu = ctk.CTkOptionMenu(
            self.top_frame,
            values=["light", "dark", "auto"],
            variable=self.theme_var,
            command=self.change_theme
        )
        self.theme_menu.pack(side="right", padx=10, pady=10)
        
        self.theme_label = ctk.CTkLabel(
            self.top_frame,
            text="主题:",
            font=ctk.CTkFont(size=12)
        )
        self.theme_label.pack(side="right", padx=(10, 5), pady=10)
        
        # 服务卡片容器
        self.services_frame = ctk.CTkScrollableFrame(self.main_frame)
        self.services_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 创建服务卡片
        self.service_cards = {}
        service_paths = self.config_manager.get_setting("service_config.service_paths") or {}
        
        for i, service_name in enumerate(service_paths.keys()):
            card = ServiceCard(
                self.services_frame,
                service_name,
                self.process_manager,
                self.theme_manager
            )
            card.pack(fill="x", padx=5, pady=5)
            self.service_cards[service_name] = card
        
        # 底部控制框架
        self.bottom_frame = ctk.CTkFrame(self.main_frame)
        self.bottom_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        # 全局控制按钮
        self.start_all_button = ctk.CTkButton(
            self.bottom_frame,
            text="启动全部",
            width=120,
            height=40,
            fg_color="#4CAF50",
            hover_color="#45A049",
            command=self.start_all_services
        )
        self.start_all_button.pack(side="left", padx=10, pady=10)
        
        self.stop_all_button = ctk.CTkButton(
            self.bottom_frame,
            text="停止全部",
            width=120,
            height=40,
            fg_color="#F44336",
            hover_color="#DA190B",
            command=self.stop_all_services
        )
        self.stop_all_button.pack(side="left", padx=5, pady=10)
        
        self.restart_all_button = ctk.CTkButton(
            self.bottom_frame,
            text="重启全部",
            width=120,
            height=40,
            fg_color="#FF9800",
            hover_color="#F57C00",
            command=self.restart_all_services
        )
        self.restart_all_button.pack(side="left", padx=5, pady=10)
        
        # 刷新按钮
        self.refresh_button = ctk.CTkButton(
            self.bottom_frame,
            text="刷新状态",
            width=120,
            height=40,
            command=self.refresh_status
        )
        self.refresh_button.pack(side="right", padx=10, pady=10)
    
    def setup_bindings(self):
        """设置快捷键绑定"""
        self.bind("<Control-r>", lambda e: self.restart_all_services())
        self.bind("<Control-s>", lambda e: self.stop_all_services())
        self.bind("<Control-t>", lambda e: self.toggle_theme())
        self.bind("<F5>", lambda e: self.refresh_status())
        
        # 窗口关闭事件
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def change_theme(self, theme: str):
        """切换主题"""
        self.theme_manager.set_theme(theme)
    
    def toggle_theme(self):
        """切换主题（快捷键）"""
        current = self.theme_manager.get_current_theme()
        new_theme = "dark" if current == "light" else "light"
        self.theme_var.set(new_theme)
        self.theme_manager.set_theme(new_theme)
    
    def start_all_services(self):
        """启动全部服务"""
        def start_all():
            for service_name in self.service_cards.keys():
                self.process_manager.start_service(service_name)
                time.sleep(0.5)  # 避免同时启动太多进程
        
        ConfirmDialog(
            self,
            "确认操作",
            "确定要启动所有服务吗？",
            lambda: threading.Thread(target=start_all, daemon=True).start()
        )
    
    def stop_all_services(self):
        """停止全部服务"""
        def stop_all():
            for service_name in self.service_cards.keys():
                self.process_manager.stop_service(service_name)
        
        ConfirmDialog(
            self,
            "确认操作",
            "确定要停止所有服务吗？",
            lambda: threading.Thread(target=stop_all, daemon=True).start()
        )
    
    def restart_all_services(self):
        """重启全部服务"""
        def restart_all():
            for service_name in self.service_cards.keys():
                self.process_manager.restart_service(service_name)
                time.sleep(1)  # 重启需要更多时间
        
        ConfirmDialog(
            self,
            "确认操作",
            "确定要重启所有服务吗？",
            lambda: threading.Thread(target=restart_all, daemon=True).start()
        )
    
    def refresh_status(self):
        """刷新状态"""
        for service_name, card in self.service_cards.items():
            status = self.process_manager.get_service_status(service_name)
            card.update_status(status)
    
    def on_closing(self):
        """窗口关闭事件"""
        # 保存窗口位置和大小
        if self.config_manager.get_setting("ui_config.remember_position"):
            self.config_manager.set_setting("ui_config.window_width", self.winfo_width())
            self.config_manager.set_setting("ui_config.window_height", self.winfo_height())
            self.config_manager.set_setting("ui_config.last_position.x", self.winfo_x())
            self.config_manager.set_setting("ui_config.last_position.y", self.winfo_y())
            self.config_manager.save_config()
        
        # 停止所有服务
        for service_name in self.service_cards.keys():
            self.process_manager.stop_service(service_name)
        
        self.destroy()

def run_cli_command(args):
    """运行命令行命令"""
    config_manager = ConfigManager()
    process_manager = ProcessManager(config_manager)
    
    if args.command == 'run':
        print("正在启动所有服务端...")
        service_paths = config_manager.get_setting("service_config.service_paths") or {}
        success_count = 0
        
        for service_name in service_paths.keys():
            print(f"启动 {service_name}...")
            if process_manager.start_service(service_name):
                success_count += 1
                print(f"✓ {service_name} 启动成功")
            else:
                print(f"✗ {service_name} 启动失败")
        
        print(f"\n启动完成: {success_count}/{len(service_paths)} 个服务启动成功")
        
        if success_count > 0:
            print("服务正在后台运行，可以安全关闭此命令行窗口。")
            # 保持进程运行，让服务在后台继续
            try:
                while True:
                    time.sleep(60)  # 每分钟检查一次
                    # 检查是否还有服务在运行
                    running_count = sum(1 for name in service_paths.keys() 
                                      if process_manager.is_service_running(name))
                    if running_count == 0:
                        print("所有服务已停止，退出管理器。")
                        break
            except KeyboardInterrupt:
                print("\n收到中断信号，停止所有服务...")
                for service_name in service_paths.keys():
                    process_manager.stop_service(service_name)
                print("所有服务已停止。")
    
    elif args.command == 'status':
        print("服务端运行状态:")
        print("-" * 50)
        service_paths = config_manager.get_setting("service_config.service_paths") or {}
        
        for service_name in service_paths.keys():
            status = process_manager.get_service_status(service_name)
            is_running = process_manager.is_service_running(service_name)
            
            if is_running:
                status_text = "运行中 ✓"
                status_color = "绿色"
            else:
                status_text = "已停止 ✗"
                status_color = "红色"
            
            print(f"{service_name:<25} {status_text}")
        
        print("-" * 50)
    
    elif args.command == 'stop':
        print("正在停止所有服务端...")
        service_paths = config_manager.get_setting("service_config.service_paths") or {}
        
        for service_name in service_paths.keys():
            print(f"停止 {service_name}...")
            if process_manager.stop_service(service_name):
                print(f"✓ {service_name} 已停止")
            else:
                print(f"✗ {service_name} 停止失败")
        
        print("所有服务已停止。")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='SR私服管理器')
    parser.add_argument('--run', dest='command', action='store_const', const='run',
                       help='启动所有服务端')
    parser.add_argument('--status', dest='command', action='store_const', const='status',
                       help='查看当前服务端运行状态')
    parser.add_argument('--stop', dest='command', action='store_const', const='stop',
                       help='停止所有服务端')
    
    args = parser.parse_args()
    
    if args.command:
        # 命令行模式
        run_cli_command(args)
    else:
        # GUI模式
        try:
            app = MainWindow()
            app.mainloop()
        except Exception as e:
            print(f"应用程序启动失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()