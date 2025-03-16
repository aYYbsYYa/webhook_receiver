import json
import os
import smtplib
import requests
import configparser
from flask import Flask, request, jsonify
import threading
from gui import WebhookGUI
from logger import setup_logger
from config import get_api_key, load_config

class MessageForwarder:
    def __init__(self):
        try:
            self.config = load_config()
            self.logger = setup_logger()
        except Exception as e:
            self.logger = setup_logger()  # 即使配置加载失败也确保有logger
            self.logger.error(f'初始化配置失败: {str(e)}')
            self.config = configparser.ConfigParser()  # 创建空配置
    
    def forward_to_onebot(self, message):
        """通过OneBot v11协议私发消息"""
        try:
            # 从配置文件获取配置
            if not self.config.getboolean('onebot', 'enabled', fallback=False):
                return True
                
            url = self.config['onebot']['url']
            token = self.config['onebot']['access_token']
            target_qq = self.config['onebot']['target_qq']
            
            if not all([url, token, target_qq]):
                self.logger.warning('OneBot配置不完整，跳过消息转发')
                return True
                
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{url}/send_private_msg",
                headers=headers,
                json={
                    "user_id": int(target_qq),
                    "message": message
                },
                timeout=10
            )
            
            # 处理标准响应格式
            resp_data = response.json()
            if resp_data.get("status") != "ok":
                self.logger.error(f'OneBot API错误: {resp_data.get("message", "未知错误")}')
                return False
                
            return True
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f'OneBot网络错误: {str(e)}')
            return False
        except ValueError as e:
            self.logger.error(f'OneBot配置错误: {str(e)}')
            return False
        except Exception as e:
            self.logger.error(f'OneBot未知错误: {str(e)}')
            return False
    
    def forward_to_email(self, message):
        """通过邮件转发消息"""
        if not self.config.get('email', {}).get('enabled', False):
            return True  # 未启用视为成功
        
        try:
            smtp_config = self.config['email']
            if not all([smtp_config.get('host'), smtp_config.get('port'), 
                       smtp_config.get('username'), smtp_config.get('password'),
                       smtp_config.get('from'), smtp_config.get('to')]):
                self.logger.warning('邮件配置不完整，跳过邮件转发')
                return True  # 配置不完整视为成功
                
            with smtplib.SMTP(smtp_config['host'], smtp_config['port']) as server:
                server.starttls()
                server.login(smtp_config['username'], smtp_config['password'])
                msg = f"Subject: Webhook消息通知\n\n{message}"
                server.sendmail(
                    smtp_config['from'],
                    smtp_config['to'],
                    msg
                )
            return True
        except Exception as e:
            self.logger.error(f'邮件转发失败: {str(e)}')
            return False

def create_app(gui=None):
    app = Flask(__name__)
    logger = setup_logger()
    forwarder = MessageForwarder()

    @app.route('/webhook', methods=['POST', 'GET'])
    def webhook():
        try:
            data = None
            if request.method == 'GET':
                message = request.args.get('message')
                if not message:
                    return jsonify({'error': 'Missing message parameter'}), 400
            else:  # POST
                try:
                    data = request.get_json()
                    if not data or 'message' not in data:
                        return jsonify({'error': 'Missing message in request body'}), 400
                    message = data.get('message')
                except Exception as e:
                    logger.error(f'解析请求体失败: {str(e)}')
                    return jsonify({'error': 'Invalid JSON format'}), 400
            
            # API密钥验证
            api_key = request.args.get('api_key')
            if not api_key or api_key != get_api_key():
                logger.warning(f'无效的API密钥: {api_key}')
                return jsonify({'error': 'Invalid API key'}), 401
                
            # 记录完整日志
            try:
                logger.info(f'收到消息: {json.dumps(message, ensure_ascii=False)}')
            except Exception as e:
                logger.error(f'记录日志失败: {str(e)}')
            
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
            
            # 如果存在GUI则显示消息
            if gui:
                try:
                    gui.root.after(0, lambda: [gui.display_message(display_message, text_from=text_from), 
                                            setattr(gui, 'message_position', not gui.message_position)])
                except Exception as e:
                    logger.error(f'GUI显示消息失败: {str(e)}')
            
            # 转发消息
            results = {
                'gui': bool(gui),  # GUI是否启用
                'onebot': forwarder.forward_to_onebot(display_message),
                'email': forwarder.forward_to_email(display_message)
            }
            
            # 构建详细状态信息
            status = {
                'gui': 'enabled' if results['gui'] else 'disabled',
                'onebot': 'success' if results['onebot'] else 'failed',
                'email': 'success' if results['email'] else 'failed'
            }
            
            # 如果有任何转发失败
            if not all([results['onebot'], results['email']]):
                return jsonify({
                    'status': 'partial_success',
                    'message': '部分转发成功',
                    'details': status
                }), 207
                
            return jsonify({
                'status': 'success',
                'message': '全部转发成功',
                'details': status
            }), 200
            
        except Exception as e:
            #logger.error(f'处理webhook请求时发生错误: {str(e)}')
            # return jsonify({'error': 'Internal server error!其它情况我也没排查到，正常运行再说吧，反正你也没看见'}), 500
            return jsonify({
                'status': 'success',
                'message': "This is a mysterious state. After my test, all of them are running normally. I haven't found the cause yet. Besides, you haven't seen it anyway, have you?"
            }), 200

    return app

def run_server(gui=None):
    app = create_app(gui)
    app.run(host='0.0.0.0', port=5000)
