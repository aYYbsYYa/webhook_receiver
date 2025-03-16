import os
import tkinter as tk
from tkinter import ttk
import json
from datetime import datetime
import logging

class WebhookGUI:
    def __init__(self, logger):
        self.logger = logger
        self.root = tk.Tk()
        self.root.title("Webhook 消息接收器")
        self.root.geometry("1000x700")
        self.root.configure(bg="#ededed")
        
        self.message_position = True
        self.message_count = 0
        
        self.setup_ui()
        self.root.after(0, self.load_today_logs)

    def setup_ui(self):
        # 顶部工具栏
        toolbar = tk.Frame(self.root, bg="#f6f6f6", height=50)
        toolbar.pack(fill=tk.X)
        
        title_label = tk.Label(
            toolbar,
            text="Webhook 消息接收器",
            font=("Microsoft YaHei UI", 14, "bold"),
            bg="#f6f6f6",
            fg="#000000"
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # 消息显示区域
        self.messages_frame = tk.Frame(self.root, bg="#ededed")
        self.messages_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(self.messages_frame, bg="#ededed", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.messages_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#ededed")
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=self.canvas.winfo_reqwidth())
        
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

    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_frame, width=event.width)

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def load_today_logs(self):
        try:
            log_file = f"logs/{datetime.now().strftime('%Y-%m-%d')}.log"
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='gb2312') as f:
                    for line in f:
                        try:
                            if line.startswith('['):
                                timestamp = line[1:20]
                                message = line[22:].strip()
                                try:
                                    msg_json = json.loads(message)
                                    message = json.dumps(msg_json, ensure_ascii=False, indent=2)
                                    message = message.replace('\\n', '\n')
                                except:
                                    pass
                                dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                                display_time = dt.strftime('%H:%M:%S')
                                self.display_message(message, custom_timestamp=display_time)
                                self.message_position = not self.message_position
                        except Exception as e:
                            self.logger.error(f"解析日志行失败: {e}")
                            continue
            else:
                self.logger.warning(f"日志文件不存在: {log_file}")
        except Exception as e:
            self.logger.error(f"读取日志文件失败: {e}")

    def create_message_bubble(self, message, timestamp, is_left=True, text_from="aYYbsYYa"):
        msg_frame = tk.Frame(self.scrollable_frame, bg="#ededed")
        msg_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 时间戳
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
        
        # 消息气泡
        bubble_frame = tk.Frame(msg_frame, bg="#ededed")
        bubble_frame.pack(fill=tk.X, pady=2)
        
        # 昵称
        name_label = tk.Label(
            bubble_frame,
            text=text_from,
            font=("Microsoft YaHei UI", 10),
            fg="#666666",
            bg="#ededed"
        )
        if is_left:
            name_label.pack(anchor="w", padx=(93, 0), pady=(0, 1))
        else:
            name_label.pack(anchor="e", padx=(0, 93), pady=(0, 1))
        
        bubble_bg = "#ffffff" if is_left else "#95ec69"
        message_frame = tk.Frame(
            bubble_frame,
            bg=bubble_bg,
            padx=8,
            pady=6,
        )
        
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
        
        message_text.insert("1.0", message)
        message_text.configure(state="disabled")
        
        # 计算合适的大小
        lines = message.split('\n')
        width = min(max(len(line) for line in lines) + 4, 50)
        height = min(len(lines), 20)
        message_text.configure(width=width, height=height)
        
        # 右键菜单
        menu = tk.Menu(message_frame, tearoff=0)
        
        def show_menu(event):
            menu.delete(0, tk.END)
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
            self.show_copy_tooltip(widget)
            
        def select_all(widget):
            widget.configure(state="normal")
            widget.tag_add("sel", "1.0", "end")
            widget.configure(state="disabled")
            
        message_text.bind("<Button-3>", show_menu)
        message_text.bind("<Control-c>", lambda e: copy_text(message_text))
        message_text.bind("<Control-a>", lambda e: select_all(message_text))
        message_text.bind("<Enter>", lambda e: message_text.configure(cursor="ibeam"))
        message_text.bind("<Leave>", lambda e: message_text.configure(cursor="arrow"))
        
        message_text.pack(expand=True, fill=tk.BOTH)
        
        # 头像
        avatar = tk.Label(
            bubble_frame,
            text="Y",
            font=("Microsoft YaHei UI", 12, "bold"),
            fg="#ffffff",
            bg="#1aad19",
            width=2,
            height=1
        )
        
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
        tooltip = tk.Toplevel()
        tooltip.overrideredirect(True)
        tooltip.attributes('-topmost', True)
        
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
        
        x = widget.winfo_rootx() + widget.winfo_width() // 2 - label.winfo_reqwidth() // 2
        y = widget.winfo_rooty() - 30
        tooltip.geometry(f"+{x}+{y}")
        self.root.after(1000, tooltip.destroy)
        
    def display_message(self, message, custom_timestamp=None, text_from="aYYbsYYa"):
        timestamp = custom_timestamp if custom_timestamp else datetime.now().strftime('%H:%M')
        
        if isinstance(message, str):
            try:
                parsed = json.loads(message)
                if isinstance(parsed, str):
                    message = parsed
            except:
                pass
        
        msg_frame = self.create_message_bubble(message, timestamp, self.message_position, text_from)
        
        self.message_count += 1
        self.status_bar.config(text=f"收到新消息 · 共 {self.message_count} 条消息")
        
        self.root.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def run(self):
        self.root.mainloop()
