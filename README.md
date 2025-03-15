# Webhook 消息接收器

一个简单的Webhook消息接收器，提供GUI界面显示接收到的消息。支持通过POST或GET方式发送消息，并保存历史记录。

## 功能特点

- 美观的GUI界面，类似微信风格
- 支持POST和GET两种请求方式
- 自动保存消息历史
- 支持消息换行显示
- 自动加载历史消息
- 支持滚动查看历史消息

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

1. 启动服务器：

```bash
python webhook_receiver.py
```

2. 发送消息：

### POST方式

```bash
curl -X POST http://localhost:5000/webhook?api_key=your-api-key-here \
  -H "Content-Type: application/json" \
  -d '{"message": "你好\n这是一条测试消息"}'
```

### GET方式

```bash
curl "http://localhost:5000/webhook?api_key=your-api-key-here&message=你好，这是一条测试消息"
```

### GET参数说明

- `api_key`：API密钥，用于验证发送者身份，可选参数，默认值`your-api-key-here`
- `message`：消息内容，必填参数
- `text_from`: 发送者来源，可选参数，默认值`aYYbsYYa`

### POST参数说明
- `message`：消息内容，必填参数

## 配置说明

### config.ini

可以在config.ini中配置以下参数：
- API密钥验证（默认your-api-key-here）
- 端口号（默认5000）
- 其他自定义配置

## 日志

所有接收到的消息都会保存在`logs`目录下，按日期生成日志文件（格式：YYYY-MM-DD.log）。

## 系统要求

- Python 3.6+
- 支持图形界面的操作系统（Windows/Linux/MacOS）

## 注意事项

1. 确保5000端口未被占用
2. 如需外网访问，请配置相应的防火墙规则
3. 建议在使用API密钥验证的情况下使用

## 待添加功能
- [ ] TTS语音生成（决定是否进行语音提醒）
  - 栗云AI API提供支持
  - GET参数是否决定开启tts-type
  - GET参数传递具体内容tts-text
- [ ] 通知转发功能
  - 邮箱
  - QQ消息（OneBot）
    - 附带监听消息，若监听到回复关键词，则执行cmd操作
- [ ] web同时显示界面
