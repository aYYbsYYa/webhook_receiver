import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
import tkinter as tk
from tkinter import scrolledtext, ttk
from PIL import Image, ImageTk
import io
import base64
import configparser
import random

# 确保logs目录存在
os.makedirs('logs', exist_ok=True)

# 初始化配置
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

# 配置日志记录器
log_file = f"logs/{datetime.now().strftime('%Y-%m-%d')}.log"

# 创建自定义的日志格式化器
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

# 配置日志处理器
logger = logging.getLogger('webhook')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(log_file, encoding='gb2312')
handler.setFormatter(CustomFormatter())
logger.addHandler(handler)

# 禁用Flask默认日志
logging.getLogger('werkzeug').disabled = True

app = Flask(__name__)

# GUI界面
class WebhookGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Webhook 消息接收器")
        self.root.geometry("1000x700")
        self.root.configure(bg="#ededed")  # 微信经典灰色背景
        
        # 初始化消息位置标志（True为左边，False为右边）
        self.message_position = True
        
        # 初始化消息计数
        self.message_count = 0
        
        # 设置窗口图标
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
            
        # 顶部工具栏
        toolbar = tk.Frame(self.root, bg="#f6f6f6", height=50)
        toolbar.pack(fill=tk.X)
        
        # 标题
        title_label = tk.Label(
            toolbar,
            text="Webhook 消息接收器",
            font=("Microsoft YaHei UI", 14, "bold"),
            bg="#f6f6f6",
            fg="#000000"
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # 创建自定义的消息框架
        self.messages_frame = tk.Frame(self.root, bg="#ededed")
        self.messages_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建画布和滚动条
        self.canvas = tk.Canvas(self.messages_frame, bg="#ededed", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.messages_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#ededed")
        
        # 配置画布滚动区域
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # 打包滚动条和画布
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 创建窗口来显示滚动框架
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=self.canvas.winfo_reqwidth())
        
        # 绑定事件
        self.scrollable_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        
        # 状态栏
        self.status_bar = tk.Label(
            self.root,
            text="就绪",
            bd=0,
            anchor=tk.W,
            bg="#f6f6f6",
            fg="#666666",
            font=("Microsoft YaHei UI", 10)
        )
        self.status_bar.pack(fill=tk.X, padx=10, pady=8)
        
        # GUI初始化完成后，读取当天的日志文件
        self.root.after(0, self.load_today_logs)

    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        # 更新画布窗口的宽度以适应画布
        self.canvas.itemconfig(self.canvas_frame, width=event.width)

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def load_today_logs(self):
        """读取当天的日志文件"""
        try:
            log_file = f"logs/{datetime.now().strftime('%Y-%m-%d')}.log"
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='gb2312') as f:
                    for line in f:
                        # 解析日志行
                        try:
                            if line.startswith('['):
                                timestamp = line[1:20]  # 提取时间戳
                                message = line[22:].strip()  # 提取消息内容
                                # 如果是JSON格式，保持格式化并处理换行符
                                try:
                                    msg_json = json.loads(message)
                                    message = json.dumps(msg_json, ensure_ascii=False, indent=2)
                                    # 将字符串形式的\n转换为实际的换行符
                                    message = message.replace('\\n', '\n')
                                except:
                                    pass
                                # 转换时间戳格式
                                dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                                display_time = dt.strftime('%H:%M')
                                self.display_message(message, custom_timestamp=display_time)
                                self.message_position = not self.message_position
                        except Exception as e:
                            print(f"解析日志行失败: {e}")
                            continue
            else:
                print(f"日志文件不存在: {log_file}")
        except Exception as e:
            print(f"读取日志文件失败: {e}")

    def create_message_bubble(self, message, timestamp, is_left=True):
        # 创建消息框架
        msg_frame = tk.Frame(self.scrollable_frame, bg="#ededed")
        msg_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 时间戳标签
        time_frame = tk.Frame(msg_frame, bg="#ededed")
        time_frame.pack(fill=tk.X)
        time_label = tk.Label(
            time_frame,
            text=timestamp,
            font=("Microsoft YaHei UI", 10),
            fg="#999999",
            bg="#ededed"
        )
        time_label.pack(anchor="center", pady=(5, 0))
        
        # 创建气泡框架
        bubble_frame = tk.Frame(msg_frame, bg="#ededed")
        bubble_frame.pack(fill=tk.X, pady=5)
        
        # 消息气泡
        bubble_bg = "#ffffff" if is_left else "#95ec69"
        # 创建消息气泡框架
        message_frame = tk.Frame(
            bubble_frame,
            bg=bubble_bg,
            padx=8,
            pady=6,
        )
        
        # 创建可选择的文本区域
        message_text = tk.Text(
            message_frame,
            font=("Microsoft YaHei UI", 11),
            bg=bubble_bg,
            fg="#000000",
            wrap=tk.WORD,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            cursor="arrow",
            height=1,
            width=1,
            padx=2,
            pady=2
        )
        
        # 插入文本并禁用编辑
        message_text.insert("1.0", message)
        message_text.configure(state="disabled")
        
        # 禁用滚动条
        message_text.configure(yscrollcommand=None)
        
        # 计算所需的大小
        message_text.update_idletasks()
        lines = message.split('\n')
        width = min(max(len(line) for line in lines) + 4, 50)  # 限制最大宽度
        height = min(len(lines), 20)  # 限制最大高度
        message_text.configure(width=width, height=height)
        
        # 创建右键菜单
        menu = tk.Menu(message_frame, tearoff=0)
        menu.configure(
            font=("Microsoft YaHei UI", 10),
            bg="white",
            activebackground="#f0f0f0",
            activeforeground="black",
            relief="flat",
            bd=1
        )
        
        def show_menu(event):
            menu.delete(0, tk.END)  # 清除旧菜单项
            menu.add_command(
                label="全选",
                command=lambda: select_all(message_text),
                accelerator="Ctrl+A"
            )
            menu.add_command(
                label="复制",
                command=lambda: copy_text(message_text),
                accelerator="Ctrl+C"
            )
            menu.post(event.x_root, event.y_root)
            
        def copy_text(widget):
            widget.configure(state="normal")
            if not widget.tag_ranges("sel"):
                widget.tag_add("sel", "1.0", "end")
            widget.event_generate("<<Copy>>")
            widget.tag_remove("sel", "1.0", "end")
            widget.configure(state="disabled")
            
            # 显示复制成功提示
            self.show_copy_tooltip(widget)
            
        def select_all(widget):
            widget.configure(state="normal")
            widget.tag_add("sel", "1.0", "end")
            widget.configure(state="disabled")
            
        # 绑定事件
        message_text.bind("<Button-3>", show_menu)  # 右键菜单
        message_text.bind("<Control-c>", lambda e: copy_text(message_text))  # Ctrl+C
        message_text.bind("<Control-a>", lambda e: select_all(message_text))  # Ctrl+A
        message_text.bind("<Enter>", lambda e: message_text.configure(cursor="ibeam"))  # 鼠标进入
        message_text.bind("<Leave>", lambda e: message_text.configure(cursor="arrow"))  # 鼠标离开
        
        message_text.pack(expand=True, fill=tk.BOTH)
        
        # 头像（使用文本代替）
        avatar = tk.Label(
            bubble_frame,
            text="Y",
            font=("Microsoft YaHei UI", 12, "bold"),
            fg="#ffffff",
            bg="#1aad19",  # 微信绿色
            width=2,
            height=1
        )
        
        # 创建左右两侧的空白框架以实现对齐
        left_space = tk.Frame(bubble_frame, bg="#ededed", width=50)
        right_space = tk.Frame(bubble_frame, bg="#ededed", width=50)
        
        if is_left:
            left_space.pack(side=tk.LEFT, padx=(0, 10))
            avatar.pack(side=tk.LEFT, padx=(0, 10))
            message_frame.pack(side=tk.LEFT, anchor="w")
            right_space.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        else:
            right_space.pack(side=tk.RIGHT, padx=(10, 0))
            avatar.pack(side=tk.RIGHT, padx=(10, 0))
            message_frame.pack(side=tk.RIGHT, anchor="e")
            left_space.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        return msg_frame

    def show_copy_tooltip(self, widget):
        # 创建提示窗口
        tooltip = tk.Toplevel()
        tooltip.overrideredirect(True)
        tooltip.attributes('-topmost', True)
        
        # 设置提示文本
        label = tk.Label(
            tooltip,
            text="已复制",
            font=("Microsoft YaHei UI", 10),
            fg="#ffffff",
            bg="#1aad19",
            padx=10,
            pady=5
        )
        label.pack()
        
        # 计算提示窗口位置
        x = widget.winfo_rootx() + widget.winfo_width() // 2 - label.winfo_reqwidth() // 2
        y = widget.winfo_rooty() - 30
        tooltip.geometry(f"+{x}+{y}")
        
        # 1秒后自动关闭
        self.root.after(1000, tooltip.destroy)
        
    def display_message(self, message, custom_timestamp=None):
        # 使用自定义时间戳或当前时间
        timestamp = custom_timestamp if custom_timestamp else datetime.now().strftime('%H:%M')
        
        # 如果消息是JSON字符串，需要去除外层引号
        if isinstance(message, str):
            try:
                # 尝试解析JSON字符串
                parsed = json.loads(message)
                if isinstance(parsed, str):
                    message = parsed
            except:
                pass
        
        # 创建新的消息气泡
        msg_frame = self.create_message_bubble(message, timestamp, self.message_position)
        
        # 更新消息计数
        self.message_count += 1
        
        # 更新状态栏
        self.status_bar.config(text=f"收到新消息 · 共 {self.message_count} 条消息")
        
        # 滚动到底部
        self.root.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def run(self):
        self.root.mainloop()

# 初始化GUI
gui = WebhookGUI()

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
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
    #if request.args.get('api_key') != 'sk-aYYbsYYa':
    #    return jsonify({'error': 'Invalid API key'}), 401
        
    # 记录完整日志
    logger.info(json.dumps(message, ensure_ascii=False))
    
    # 显示消息（不包含日期时间前缀）
    # 如果消息是JSON字符串，需要去除外层引号
    display_message = message
    if isinstance(message, str):
        try:
            # 尝试解析JSON字符串
            parsed = json.loads(message)
            if isinstance(parsed, str):
                display_message = parsed
        except:
            pass
    
    # 使用after方法确保在主线程中更新GUI
    gui.root.after(0, lambda: [gui.display_message(display_message), setattr(gui, 'message_position', not gui.message_position)])
    
    return jsonify({'status': 'success'}), 200

def run_server():
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    import threading
    threading.Thread(target=run_server, daemon=True).start()
    gui.run()
