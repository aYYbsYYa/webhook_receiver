from logger import setup_logger
from gui import WebhookGUI
from server import run_server
from config import load_config, ensure_logs_directory
import threading

def main():
    # 初始化配置
    config = load_config()
    
    # 确保日志目录存在
    ensure_logs_directory()
    
    # 设置日志
    logger = setup_logger()
    
    # 初始化GUI
    gui = WebhookGUI(logger)
    
    # 启动Webhook服务器
    server_thread = threading.Thread(target=run_server, args=(gui,), daemon=True)
    server_thread.start()
    
    # 运行GUI主循环
    gui.run()

if __name__ == '__main__':
    main()