# 植物大战僵尸2 1.7.5 失落之城 · WSA 单文件直装版

## 特点

- 程序名：植物大战僵尸2
- 单文件安装，首次启动显示“正在进行首次解压”（黑底 EA logo + 绿色进度条 + PVZ 字体）
- 资源约 2.6 GB，内置在 APK 中，释放到 `Android/data/com.popcap.pvz2cthd/files/`
- 解压完自动进入游戏，无启动器/工具箱，无需第二个 APK
- 跳过“服务器通讯中”
- WSA GL shim：RGBA4444 / ETC1 / ASTC → RGBA8888
- **全分辨率 ASTC**：4 线程分条并行解码 + 内部缓存，不缩放贴图、不降画质

## 安装

```bat
adb install -r PvZ2-LostCity-1.7.5.apk
```

首次启动请允许存储权限。WSA 建议把 **窗口焦点** 设置为 **独立**。

## 性能说明

WSA 不支持游戏使用的压缩纹理，shim 在 GL 线程同步解码。首次启动要解码大量 4096/2048 ASTC，可能 1–2 分钟；不是死机。
本版用 4 线程分条并行解码，并把结果缓存到 `/data/data/com.popcap.pvz2cthd/cache/glcache/`；第二次启动直接读缓存，会快很多。缓存不改变分辨率或颜色。

## SHA-256

```
736C55E3FDE70374E96DAECE4ECA7D15C1479B36A11E7F15B59098D814212B86
```

## 免责声明

仅供学习、研究和个人备份。游戏及素材版权归 PopCap / EA 所有，请支持正版。
