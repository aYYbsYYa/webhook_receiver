import os
import json
import logging
from datetime import datetime

class DailyRotatingFileHandler(logging.FileHandler):
    def __init__(self, filename_pattern, encoding):
        self.filename_pattern = filename_pattern
        self.current_date = datetime.now().date()
        filename = self.get_current_filename()
        super().__init__(filename, encoding=encoding)
        
    def get_current_filename(self):
        return self.filename_pattern.format(self.current_date.strftime('%Y-%m-%d'))
    
    def emit(self, record):
        current_date = datetime.now().date()
        if current_date != self.current_date:
            # 日期已变更，切换到新的日志文件
            self.close()
            self.current_date = current_date
            self.baseFilename = self.get_current_filename()
            self.stream = self._open()
        super().emit(record)

class CustomFormatter(logging.Formatter):
    def format(self, record):
        # 只处理INFO级别的日志
        if record.levelno == logging.INFO:
            # 使用简化的时间格式
            dt = datetime.fromtimestamp(record.created)
            timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
            try:
                # 尝试解析消息为JSON格式
                msg = json.loads(record.msg)
                formatted_msg = json.dumps(msg, ensure_ascii=False, indent=2)
            except:
                formatted_msg = record.msg
            return f"[{timestamp}] {formatted_msg}"
        return ""

def setup_logger():
    # 确保logs目录存在
    os.makedirs('logs', exist_ok=True)
    
    # 配置日志处理器
    logger = logging.getLogger('webhook')
    logger.setLevel(logging.INFO)
    handler = DailyRotatingFileHandler('logs/{}.log', encoding='gb2312')
    handler.setFormatter(CustomFormatter())
    logger.addHandler(handler)
    
    # 禁用Flask默认日志
    logging.getLogger('werkzeug').disabled = True
    
    return logger
