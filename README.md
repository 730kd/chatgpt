# chatgpt

一个简单的 USB 音频描述符解析示例。

## 文件

- `usb_audio_parser.py`：解析 USB 标准描述符 + 音频类相关描述符（重点支持 Interface / Endpoint / CS_INTERFACE / CS_ENDPOINT）。

## 用法

### 1) 直接输入十六进制

```bash
python usb_audio_parser.py --hex "09 04 00 00 00 01 01 00 00"
```

### 2) 从二进制文件读取

```bash
python usb_audio_parser.py --file descriptors.bin
```

## 说明

- 该代码偏向 **UAC1/UAC2 的通用解析框架**，适合作为你项目里的基础版本。
- 如果你有具体设备抓包（比如 `lsusb -v` 或原始描述符字节流），可以继续补充更完整的 subtype 字段解析。
