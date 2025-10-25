> 一个完整的管理第三方服务端的脚本，包含客户端、补丁和服务端组件。

## 📁 项目结构

```
SR/
├── Client/                   # 客户端文件
├── Patch/                    # 客户端补丁
├── Server/                   # 服务端组件
├── Start.bat                 # 快速启动脚本
└── README.md                 # 使用文档
```

## 🚀 快速开始

0. 克隆本仓库或下载`zip`包
1. 下载客户端并解压到`Client`目录下： [OneDrive](https://1drv.ronova.me/s/qgHw) [Google Drive](https://drive.google.com/drive/folders/1ZbWkpmQXIXXM_81MJW7vmsEZGy1uye6v?usp=sharing) [Gofile](https://gofile.io/d/ynqge5) [Transfer](https://transfer.it/t/fc2coF9FTJ6Z)
2. 运行`Start.bat`脚本
3. 别管打开的乱七八糟的弹窗和游戏，先打开浏览器
- 访问: http://127.0.0.1:20100/account/register
- 注册你的游戏账户和密码
4. 游戏客户端使用你刚刚注册的账密登录。

## 🛠️ 高级：手动启动

### 1.启动服务端

- `Server/releases/`目录中的三个服务端启动。`

> `hoyo-sdk.exe`服务端双击即可。
>
> `cyrene-sr/`目录下的两个服务端要通过`pexecvelf.exe`启动。
> 详见`cyrene-sr/`目录下的`README.md`。

### 2. 注册账户

- 访问: http://127.0.0.1:20100/account/register
- 注册你的游戏账户，后面凭此登录

### 3.应用客户端补丁并启动客户端

1. 将`Patch/releases/ `中的两个补丁文件复制到`Client/`中
2. 右键单击`cyrene.exe`，选择以管理员身份运行，客户端将自动启动
3. 使用你前面注册的游戏账户登录

## ⚠️ 重要提醒

- **仅供学习和娱乐**: 此项目仅用于学习和娱乐目的
- **不建议生产环境使用**: 当前版本不适合在生产环境中运行
- **功能不完整**: 部分游戏功能可能尚未实现
- **版本兼容性**: 仅支持特定的客户端版本 (CNBETAWin3.6.51)

## 📞 获取帮助 & 鸣谢

- 请自行查看各组件的详细文档:
  - [cyrene-sr 文档](Server/cyrene-sr/README.md)
  - [hoyo-sdk 文档](Server/hoyo-sdk/README.md)
  - [pexecvelf 文档](https://git.xeondev.com/xeon/pexecvelf)
  - [cyrene-patch 文档](https://git.xeondev.com/cyrene-sr/cyrene-patch)

## 📄 许可证

GNU V3 LICENSE

---

**注意**: 请确保遵守相关法律法规和游戏服务条款。项目本身开源，为作学习交流之用。用户不当使用所造成的一切后果自负。