import json
from flask import Flask, request, jsonify
import threading
from gui import WebhookGUI
from logger import setup_logger
from config import get_api_key

def create_app(gui):
    app = Flask(__name__)
    logger = setup_logger()

    @app.route('/webhook', methods=['POST', 'GET'])
    def webhook():
        data = None
        if request.method == 'GET':
            message = request.args.get('message')
            if not message:
                return jsonify({'error': 'Missing message parameter'}), 400
        else:  # POST
            data = request.json
            if not data or 'message' not in data:
                return jsonify({'error': 'Missing message in request body'}), 400
            message = data.get('message')
        
        # API密钥验证
        if request.args.get('api_key') != get_api_key():
            return jsonify({'error': 'Invalid API key'}), 401
            
        # 记录完整日志
        logger.info(json.dumps(message, ensure_ascii=False))
        
        # 显示消息（不包含日期时间前缀）
        display_message = message
        if isinstance(message, str):
            try:
                parsed = json.loads(message)
                if isinstance(parsed, str):
                    display_message = parsed
            except:
                pass
        
        # 获取text_from参数，如果未提供则使用默认值
        text_from = request.args.get('text_from') or (data.get('text_from') if data else None)
        text_from = text_from or "aYYbsYYa"
        
        # 使用after方法确保在主线程中更新GUI
        gui.root.after(0, lambda: [gui.display_message(display_message, text_from=text_from), 
                                setattr(gui, 'message_position', not gui.message_position)])
        
        return jsonify({'status': 'success'}), 200

    return app

def run_server(gui):
    app = create_app(gui)
    app.run(host='0.0.0.0', port=5000)
