# 私服运行管理器

一个基于Python和CustomTkinter开发的Windows应用程序，专门用于管理游戏私服的各个服务组件。

## 系统要求

- Windows 10/11
- Python 3.8+
- 管理员权限（用于进程管理）

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行程序

```bash
python manager.py
```

## 配置说明

配置文件 `config.json` 包含以下设置：

- **theme_config**：主题相关设置
- **service_config**：服务路径和启动参数
- **ui_config**：界面布局和窗口设置

## 使用说明

1. **启动管理器**：双击运行 manager.py 或可执行文件
2. **查看状态**：主界面显示各服务的实时状态
3. **控制服务**：点击启动/停止/重启按钮控制服务
4. **切换主题**：右上角下拉菜单选择主题模式
5. **修改设置**：设置页面可调整各项参数

## 快捷键

- `Ctrl+R`：重启所有服务
- `Ctrl+S`：停止所有服务
- `Ctrl+T`：切换主题
- `F5`：刷新状态
