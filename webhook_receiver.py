import argparse
from logger import setup_logger
from gui import WebhookGUI
from server import run_server
from config import load_config, ensure_logs_directory
import threading

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-gui', action='store_true', help='以无GUI模式运行')
    args = parser.parse_args()

    # 初始化配置
    config = load_config()
    
    # 确保日志目录存在
    ensure_logs_directory()
    
    # 设置日志
    logger = setup_logger()
    
    # 初始化GUI（如果未禁用）
    gui = WebhookGUI(logger) if not args.no_gui else None
    
    # 启动Webhook服务器
    server_thread = threading.Thread(target=run_server, args=(gui,), daemon=True)
    server_thread.start()
    
    # 如果有GUI则运行主循环
    if gui:
        gui.run()
    else:
        logger.info("以无GUI模式运行，按Ctrl+C退出")
        try:
            while True:
                pass
        except KeyboardInterrupt:
            logger.info("正在关闭服务器...")

if __name__ == '__main__':
    main()
