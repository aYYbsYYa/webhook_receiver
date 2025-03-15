import configparser
import os

def load_config():
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    return config

def ensure_logs_directory():
    os.makedirs('logs', exist_ok=True)

def get_api_key():
    config = load_config()
    return config['security'].get('api_key', '')
