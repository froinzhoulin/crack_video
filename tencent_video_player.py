#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
腾讯视频播放器 - 图形界面版
输入视频链接，直接播放VIP视频（需要VIP账号Cookie）
仅供个人学习研究使用，请尊重版权
"""

import os
import sys
import json
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import webbrowser
from datetime import datetime


class TencentVideoPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("腾讯视频播放器")
        self.root.geometry("750x850")
        self.root.resizable(True, True)
        
        # 设置窗口图标（如果有的话）
        self.script_dir = Path(__file__).parent
        self.cookie_file = self.script_dir / "cookies.txt"
        self.download_dir = self.script_dir / "downloads"
        
        # 当前视频信息
        self.current_video_info = None
        self.video_formats = []
        
        self.setup_ui()
        self.check_dependencies()
    
    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(
            main_frame, 
            text="腾讯视频VIP/SVIP解析播放器", 
            font=("Microsoft YaHei", 16, "bold")
        )
        title_label.pack(pady=(0, 5))
        
        # 提示标签
        hint_label = ttk.Label(
            main_frame,
            text="ℹ️ 输入链接 → 点击解析播放 → 自动在浏览器中播放VIP/SVIP视频",
            foreground="#1E90FF",
            font=("Microsoft YaHei", 10)
        )
        hint_label.pack(pady=(0, 10))
        
        # URL输入区域
        url_frame = ttk.LabelFrame(main_frame, text="视频链接", padding="10")
        url_frame.pack(fill=tk.X, pady=10)
        
        self.url_entry = ttk.Entry(url_frame, font=("Consolas", 11))
        self.url_entry.pack(fill=tk.X, pady=(0, 10))
        self.url_entry.bind('<Return>', lambda e: self.one_click_parse())
        
        # 按钮区域
        btn_frame = ttk.Frame(url_frame)
        btn_frame.pack(fill=tk.X)
        
        # 一键解析播放按钮（主按钮）
        self.parse_play_btn = ttk.Button(
            btn_frame, 
            text="🔓 一键解析播放", 
            command=self.one_click_parse
        )
        self.parse_play_btn.pack(side=tk.LEFT, padx=5)
        
        # 选择接口按钮
        self.select_api_btn = ttk.Button(
            btn_frame, 
            text="⚙️ 选择解析接口", 
            command=self.vip_free_parse
        )
        self.select_api_btn.pack(side=tk.LEFT, padx=5)
        
        # 测速按钮
        self.speed_test_btn = ttk.Button(
            btn_frame, 
            text="⚡ 测速选最快", 
            command=self.speed_test_and_play
        )
        self.speed_test_btn.pack(side=tk.LEFT, padx=5)
        
        # 当前接口显示
        self.current_api_var = tk.StringVar(value="当前接口: 💎 SVIP-快搞 (默认)")
        current_api_label = ttk.Label(btn_frame, textvariable=self.current_api_var, foreground="green")
        current_api_label.pack(side=tk.RIGHT, padx=10)
        
        # 解析接口列表
        self.parse_apis = [
            ("💎 SVIP-快搞", "https://kuaigao.cc/jx/?url="),
            ("💎 SVIP-万能", "https://www.ckmov.vip/api.php?url="),
            ("💎 SVIP-人人", "https://jx.rrdynb.com/index.php?url="),
            ("💎 SVIP-解析la", "https://api.jiexi.la/?url="),
            ("💎 SVIP-快看", "https://jx.kuaikk.cn/?url="),
            ("💎 SVIP-极速", "https://jx.bwcxy.com/?url="),
            ("🚀 VIP-爱豆", "https://jx.aidouer.net/?url="),
            ("🚀 VIP-虾米", "https://jx.xmflv.com/?url="),
            ("🚀 VIP-M3U8", "https://jx.m3u8.tv/jiexi/?url="),
            ("🚀 VIP-OK", "https://okjx.cc/?url="),
        ]
        self.current_api_index = 0  # 默认使用第一个接口
        
        # 进度显示
        self.progress_var = tk.StringVar(value="")
        progress_label = ttk.Label(main_frame, textvariable=self.progress_var, font=("Microsoft YaHei", 9))
        progress_label.pack(anchor=tk.W, pady=5)
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="执行日志", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_text = tk.Text(log_frame, height=12, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # 底部说明
        footer_frame = ttk.Frame(main_frame)
        footer_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(
            footer_frame,
            text="💡 支持: 腾讯视频、爱奇艺、优酷、芒果、B站等平台的VIP/SVIP视频",
            foreground="gray"
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            footer_frame, 
            text="❓ 帮助", 
            command=self.show_help
        ).pack(side=tk.RIGHT)
    
    def one_click_parse(self):
        """一键解析播放 - 直接在浏览器中打开"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("提示", "请先输入视频链接\n\n支持: 腾讯视频、爱奇艺、优酷、芒果、B站等")
            return
        
        # 获取当前选中的解析接口
        api_name, api_url = self.parse_apis[self.current_api_index]
        
        # 构建解析URL
        full_url = api_url + url
        
        self.log(f"开始解析视频...", "PARSE")
        self.log(f"使用接口: {api_name}", "INFO")
        self.log(f"原始链接: {url[:50]}{'...' if len(url) > 50 else ''}", "DEBUG")
        
        self.progress_var.set("正在打开浏览器播放...")
        self.progress_bar.start()
        
        # 在浏览器中打开
        webbrowser.open(full_url)
        
        self.progress_bar.stop()
        self.progress_var.set("✓ 已在浏览器中打开播放页面")
        self.log(f"已在浏览器中打开解析页面", "SUCCESS")
        self.log(f"如播放失败，请点击'选择解析接口'换一个试试", "INFO")
    
    def speed_test_and_play(self):
        """测速并使用最快接口播放"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("提示", "请先输入视频链接")
            return
        
        import urllib.request
        import time
        
        self.log("开始测试接口速度...", "INFO")
        self.progress_var.set("正在测试接口速度...")
        self.progress_bar.start()
        
        def test_and_play():
            results = []
            
            for i, (name, api) in enumerate(self.parse_apis):
                try:
                    start = time.time()
                    test_url = api.split('?')[0]
                    
                    req = urllib.request.Request(
                        test_url,
                        headers={'User-Agent': 'Mozilla/5.0'}
                    )
                    urllib.request.urlopen(req, timeout=5)
                    
                    elapsed = (time.time() - start) * 1000
                    results.append((i, name, elapsed, True))
                    
                    self.root.after(0, lambda n=name, e=elapsed: 
                        self.log(f"{n}: {e:.0f}ms", "SUCCESS"))
                    
                except Exception:
                    results.append((i, name, 9999, False))
            
            # 按速度排序
            results.sort(key=lambda x: x[2])
            
            if results and results[0][3]:
                fastest_idx = results[0][0]
                fastest_name = results[0][1]
                fastest_time = results[0][2]
                
                self.current_api_index = fastest_idx
                self.root.after(0, lambda: 
                    self.current_api_var.set(f"当前接口: {fastest_name} ({fastest_time:.0f}ms)"))
                
                self.root.after(0, lambda: 
                    self.log(f"最快接口: {fastest_name} ({fastest_time:.0f}ms)", "SUCCESS"))
                
                # 自动播放
                self.root.after(100, self.one_click_parse)
            else:
                self.root.after(0, lambda: self.log("所有接口均不可用", "ERROR"))
            
            self.root.after(0, lambda: self.progress_bar.stop())
        
        threading.Thread(target=test_and_play, daemon=True).start()
    
    def log(self, message, level="INFO"):
        """添加日志
        level: INFO, SUCCESS, ERROR, WARNING, DEBUG
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 日志级别图标
        level_icons = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️",
            "DEBUG": "🔧",
            "DOWNLOAD": "⬇️",
            "PLAY": "▶️",
            "PARSE": "🔍"
        }
        
        icon = level_icons.get(level, "•")
        log_entry = f"[{timestamp}] {icon} {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        
        # 根据级别设置颜色标签
        line_start = self.log_text.index("end-2l")
        line_end = self.log_text.index("end-1l")
        
        if level == "ERROR":
            self.log_text.tag_add("error", line_start, line_end)
            self.log_text.tag_config("error", foreground="red")
        elif level == "SUCCESS":
            self.log_text.tag_add("success", line_start, line_end)
            self.log_text.tag_config("success", foreground="green")
        elif level == "WARNING":
            self.log_text.tag_add("warning", line_start, line_end)
            self.log_text.tag_config("warning", foreground="orange")
        
        self.log_text.see(tk.END)
        self.root.update()
    
    def update_cookie_status(self):
        """更新Cookie状态显示"""
        if self.cookie_file.exists():
            self.cookie_status.config(
                text="✓ Cookie已配置 (可播放VIP视频)", 
                foreground="green"
            )
        else:
            self.cookie_status.config(
                text="✗ 未配置Cookie (仅能播放免费视频)", 
                foreground="orange"
            )
    
    def check_dependencies(self):
        """检查依赖"""
        self.log("正在检查运行环境...", "INFO")
        try:
            result = subprocess.run(
                ['yt-dlp', '--version'], 
                capture_output=True, 
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            self.log(f"yt-dlp 版本: {result.stdout.strip()}", "SUCCESS")
            self.log(f"Python 版本: {sys.version.split()[0]}", "SUCCESS")
            self.log("环境检查完成，可以开始使用！", "SUCCESS")
        except FileNotFoundError:
            self.log("未检测到 yt-dlp，正在自动安装...", "WARNING")
            self.install_ytdlp()
    
    def install_ytdlp(self):
        """安装 yt-dlp"""
        def install():
            try:
                self.log("正在下载 yt-dlp...", "DOWNLOAD")
                subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', '-U', 'yt-dlp'],
                    check=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
                self.log("yt-dlp 安装成功!", "SUCCESS")
            except Exception as e:
                self.log(f"安装失败: {e}", "ERROR")
                messagebox.showerror("错误", "yt-dlp 安装失败，请手动执行: pip install yt-dlp")
        
        threading.Thread(target=install, daemon=True).start()
    
    def get_video_info(self):
        """获取视频信息"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("提示", "请输入视频链接")
            return
        
        self.parse_btn.config(state=tk.DISABLED)
        self.progress_bar.start()
        self.progress_var.set("正在解析视频...")
        self.log(f"开始解析视频链接...", "PARSE")
        self.log(f"URL: {url[:50]}{'...' if len(url) > 50 else ''}", "DEBUG")
        
        def fetch():
            try:
                cmd = ['yt-dlp', '-J', '--no-warnings']
                
                if self.cookie_file.exists():
                    cmd.extend(['--cookies', str(self.cookie_file)])
                
                cmd.append(url)
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
                
                if result.returncode != 0:
                    raise Exception(result.stderr)
                
                info = json.loads(result.stdout)
                self.current_video_info = info
                
                # 更新UI
                self.root.after(0, lambda: self.update_video_info(info))
                
            except json.JSONDecodeError as e:
                self.root.after(0, lambda: self.on_parse_error(f"解析响应失败: {e}"))
            except Exception as e:
                self.root.after(0, lambda: self.on_parse_error(str(e)))
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def update_video_info(self, info):
        """更新视频信息显示"""
        self.progress_bar.stop()
        self.parse_btn.config(state=tk.NORMAL)
        
        title = info.get('title', '未知标题')
        duration = info.get('duration', 0)
        
        self.title_var.set(f"标题: {title}")
        
        if duration:
            minutes = duration // 60
            seconds = duration % 60
            self.duration_var.set(f"时长: {minutes}分{seconds}秒")
        
        # 获取可用格式
        formats = info.get('formats', [])
        self.video_formats = []
        
        format_options = []
        for f in formats:
            format_id = f.get('format_id', '')
            ext = f.get('ext', '')
            resolution = f.get('resolution', 'unknown')
            filesize = f.get('filesize', 0)
            
            if filesize:
                size_mb = filesize / (1024 * 1024)
                desc = f"{format_id} - {resolution} ({ext}) [{size_mb:.1f}MB]"
            else:
                desc = f"{format_id} - {resolution} ({ext})"
            
            format_options.append(desc)
            self.video_formats.append(f)
        
        if format_options:
            self.quality_combo['values'] = format_options
            self.quality_combo.current(len(format_options) - 1)  # 默认选最高质量
        
        # 启用按钮
        self.play_btn.config(state=tk.NORMAL)
        self.download_btn.config(state=tk.NORMAL)
        self.copy_btn.config(state=tk.NORMAL)
        
        self.progress_var.set("✓ 解析成功！")
        self.log(f"解析成功!", "SUCCESS")
        self.log(f"视频标题: {title}", "INFO")
        self.log(f"可用格式: {len(formats)}种", "INFO")
    
    def on_parse_error(self, error):
        """解析错误处理"""
        self.progress_bar.stop()
        self.parse_btn.config(state=tk.NORMAL)
        self.progress_var.set("✗ 解析失败")
        self.log(f"解析失败!", "ERROR")
        self.log(f"错误详情: {str(error)[:100]}", "DEBUG")
        
        if "VIP" in str(error) or "会员" in str(error) or "login" in str(error).lower():
            messagebox.showerror(
                "需要VIP权限", 
                "该视频需要VIP权限观看\n请配置您的VIP账号Cookie后重试"
            )
        else:
            messagebox.showerror("解析失败", f"无法解析视频:\n{error[:200]}")
    
    def get_stream_url(self):
        """获取视频流地址"""
        if not self.current_video_info:
            return None
        
        # 获取选中的格式
        selected_idx = self.quality_combo.current()
        if selected_idx >= 0 and selected_idx < len(self.video_formats):
            format_info = self.video_formats[selected_idx]
            return format_info.get('url')
        
        # 默认返回最佳质量
        return self.current_video_info.get('url')
    
    def play_video(self):
        """播放视频"""
        url = self.url_entry.get().strip()
        if not url:
            return
        
        self.log("正在启动播放...", "PLAY")
        self.log("正在获取视频流地址...", "INFO")
        self.progress_var.set("正在获取播放地址...")
        
        def play():
            try:
                # 获取选中的格式ID
                selected_idx = self.quality_combo.current()
                format_id = None
                if selected_idx >= 0 and selected_idx < len(self.video_formats):
                    format_id = self.video_formats[selected_idx].get('format_id')
                
                # 使用 yt-dlp 获取直接播放URL
                cmd = ['yt-dlp', '-g', '--no-warnings']
                
                if format_id:
                    cmd.extend(['-f', format_id])
                
                if self.cookie_file.exists():
                    cmd.extend(['--cookies', str(self.cookie_file)])
                
                cmd.append(url)
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
                
                if result.returncode != 0:
                    raise Exception(result.stderr)
                
                stream_url = result.stdout.strip().split('\n')[0]
                
                if stream_url:
                    self.root.after(0, lambda: self.open_player(stream_url))
                else:
                    raise Exception("未能获取播放地址")
                    
            except Exception as e:
                self.root.after(0, lambda: self.log(f"播放失败: {e}", "ERROR"))
                self.root.after(0, lambda: self.progress_var.set("播放失败"))
        
        threading.Thread(target=play, daemon=True).start()
    
    def open_player(self, stream_url):
        """打开播放器播放"""
        self.log(f"播放地址获取成功!", "SUCCESS")
        self.log(f"正在查找可用播放器...", "INFO")
        self.progress_var.set("正在打开播放器...")
        
        # 尝试使用不同的播放器
        players = [
            # Windows Media Player
            ('C:/Program Files/Windows Media Player/wmplayer.exe', [stream_url]),
            # PotPlayer
            ('C:/Program Files/DAUM/PotPlayer/PotPlayerMini64.exe', [stream_url]),
            ('C:/Program Files (x86)/DAUM/PotPlayer/PotPlayerMini.exe', [stream_url]),
            # VLC
            ('C:/Program Files/VideoLAN/VLC/vlc.exe', [stream_url]),
            ('C:/Program Files (x86)/VideoLAN/VLC/vlc.exe', [stream_url]),
        ]
        
        for player_path, args in players:
            if os.path.exists(player_path):
                try:
                    subprocess.Popen([player_path] + args)
                    player_name = os.path.basename(player_path)
                    self.log(f"已使用 {player_name} 打开视频", "SUCCESS")
                    self.progress_var.set("✓ 播放器已启动")
                    return
                except Exception as e:
                    self.log(f"播放器 {player_path} 启动失败", "WARNING")
                    continue
        
        # 如果没有找到播放器，使用默认浏览器打开
        self.log("未找到本地播放器，使用浏览器打开", "WARNING")
        webbrowser.open(stream_url)
        self.log("已在默认浏览器中打开视频", "SUCCESS")
        self.progress_var.set("已在浏览器中打开")
    
    def download_video(self):
        """下载视频"""
        url = self.url_entry.get().strip()
        if not url:
            return
        
        # 选择保存目录
        save_dir = filedialog.askdirectory(
            title="选择保存目录",
            initialdir=str(self.download_dir)
        )
        
        if not save_dir:
            return
        
        self.download_btn.config(state=tk.DISABLED)
        self.progress_bar.start()
        self.progress_var.set("正在下载...")
        
        def download():
            try:
                # 获取选中的格式ID
                selected_idx = self.quality_combo.current()
                format_id = None
                if selected_idx >= 0 and selected_idx < len(self.video_formats):
                    format_id = self.video_formats[selected_idx].get('format_id')
                
                cmd = [
                    'yt-dlp',
                    '-o', os.path.join(save_dir, '%(title)s.%(ext)s'),
                    '--no-warnings',
                    '--newline',
                ]
                
                if format_id:
                    cmd.extend(['-f', format_id])
                
                if self.cookie_file.exists():
                    cmd.extend(['--cookies', str(self.cookie_file)])
                
                cmd.append(url)
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
                
                for line in process.stdout:
                    line = line.strip()
                    if line:
                        self.root.after(0, lambda l=line: self.progress_var.set(l[:60]))
                
                process.wait()
                
                if process.returncode == 0:
                    self.root.after(0, lambda: self.on_download_complete(save_dir))
                else:
                    raise Exception("下载过程出错")
                    
            except Exception as e:
                self.root.after(0, lambda: self.on_download_error(str(e)))
        
        threading.Thread(target=download, daemon=True).start()
    
    def on_download_complete(self, save_dir):
        """下载完成"""
        self.progress_bar.stop()
        self.download_btn.config(state=tk.NORMAL)
        self.progress_var.set("✓ 下载完成！")
        self.log(f"下载完成!", "SUCCESS")
        self.log(f"保存位置: {save_dir}", "INFO")
        
        if messagebox.askyesno("下载完成", "视频下载完成！\n是否打开保存目录？"):
            os.startfile(save_dir)
    
    def on_download_error(self, error):
        """下载错误"""
        self.progress_bar.stop()
        self.download_btn.config(state=tk.NORMAL)
        self.progress_var.set("✗ 下载失败")
        self.log(f"下载失败!", "ERROR")
        self.log(f"错误详情: {str(error)[:100]}", "DEBUG")
        messagebox.showerror("下载失败", f"下载过程出错:\n{error[:200]}")
    
    def copy_stream_url(self):
        """复制播放地址到剪贴板"""
        url = self.url_entry.get().strip()
        if not url:
            return
        
        self.log("正在获取播放地址...", "INFO")
        
        def get_url():
            try:
                selected_idx = self.quality_combo.current()
                format_id = None
                if selected_idx >= 0 and selected_idx < len(self.video_formats):
                    format_id = self.video_formats[selected_idx].get('format_id')
                
                cmd = ['yt-dlp', '-g', '--no-warnings']
                
                if format_id:
                    cmd.extend(['-f', format_id])
                
                if self.cookie_file.exists():
                    cmd.extend(['--cookies', str(self.cookie_file)])
                
                cmd.append(url)
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
                
                stream_url = result.stdout.strip().split('\n')[0]
                
                if stream_url:
                    self.root.after(0, lambda: self.do_copy(stream_url))
                else:
                    raise Exception("获取失败")
                    
            except Exception as e:
                self.root.after(0, lambda: self.log(f"获取播放地址失败: {e}", "ERROR"))
        
        threading.Thread(target=get_url, daemon=True).start()
    
    def do_copy(self, text):
        """复制到剪贴板"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.log("播放地址已复制到剪贴板", "SUCCESS")
        self.log(f"地址长度: {len(text)} 字符", "DEBUG")
        self.progress_var.set("✓ 已复制到剪贴板")
    
    def set_cookie(self):
        """设置Cookie文件 - 显示向导"""
        self.show_cookie_wizard()
    
    def show_cookie_wizard(self):
        """显示Cookie设置向导"""
        wizard = tk.Toplevel(self.root)
        wizard.title("Cookie设置向导")
        wizard.geometry("600x550")
        wizard.resizable(False, False)
        wizard.transient(self.root)
        wizard.grab_set()
        
        # 主框架
        main_frame = ttk.Frame(wizard, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title = ttk.Label(
            main_frame, 
            text="🍪 Cookie设置向导", 
            font=("Microsoft YaHei", 14, "bold")
        )
        title.pack(pady=(0, 15))
        
        # 说明文字
        intro = ttk.Label(
            main_frame,
            text="Cookie是您的登录凭证，用于访问VIP视频。\n请按以下步骤获取您的腾讯视频Cookie：",
            justify=tk.CENTER
        )
        intro.pack(pady=(0, 15))
        
        # 步骤框架
        steps_frame = ttk.LabelFrame(main_frame, text="获取步骤", padding="15")
        steps_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        steps = [
            ("步骤1️⃣", "安装浏览器扩展", 
             "在Chrome/Edge浏览器中安装扩展:\n'Get cookies.txt LOCALLY'\n(在浏览器扩展商店搜索即可)"),
            ("步骤2️⃣", "登录腾讯视频", 
             "打开 v.qq.com\n使用您的VIP账号登录\n确保登录状态正常"),
            ("步骤3️⃣", "导出Cookie", 
             "点击扩展图标\n选择 'Export' 或 '导出'\n保存为 cookies.txt 文件"),
            ("步骤4️⃣", "导入Cookie", 
             "点击下方'选择Cookie文件'按钮\n选择刚才保存的文件")
        ]
        
        for i, (step_num, step_title, step_desc) in enumerate(steps):
            step_frame = ttk.Frame(steps_frame)
            step_frame.pack(fill=tk.X, pady=5)
            
            # 步骤编号
            num_label = ttk.Label(
                step_frame, 
                text=step_num, 
                font=("Microsoft YaHei", 10, "bold"),
                foreground="#1E90FF"
            )
            num_label.pack(side=tk.LEFT, padx=(0, 10))
            
            # 步骤内容
            content_frame = ttk.Frame(step_frame)
            content_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            title_label = ttk.Label(
                content_frame, 
                text=step_title, 
                font=("Microsoft YaHei", 9, "bold")
            )
            title_label.pack(anchor=tk.W)
            
            desc_label = ttk.Label(
                content_frame, 
                text=step_desc, 
                foreground="gray",
                justify=tk.LEFT
            )
            desc_label.pack(anchor=tk.W)
        
        # 当前状态
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=10)
        
        if self.cookie_file.exists():
            status_text = "✅ Cookie已配置"
            status_color = "green"
        else:
            status_text = "❌ Cookie未配置"
            status_color = "red"
        
        status_label = ttk.Label(
            status_frame, 
            text=f"当前状态: {status_text}",
            foreground=status_color,
            font=("Microsoft YaHei", 10)
        )
        status_label.pack()
        
        # 按钮区域
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=15)
        
        def select_cookie_file():
            file_path = filedialog.askopenfilename(
                title="选择Cookie文件",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialdir=str(self.script_dir)
            )
            
            if file_path:
                import shutil
                try:
                    shutil.copy(file_path, self.cookie_file)
                    self.update_cookie_status()
                    self.log(f"Cookie文件已导入", "SUCCESS")
                    self.log(f"文件路径: {file_path}", "DEBUG")
                    status_label.config(text="当前状态: ✅ Cookie已配置", foreground="green")
                    messagebox.showinfo("成功", "Cookie文件设置成功！\n现在可以播放VIP视频了。")
                except Exception as e:
                    self.log(f"Cookie导入失败: {e}", "ERROR")
                    messagebox.showerror("错误", f"设置失败: {e}")
        
        def open_tencent_video():
            webbrowser.open("https://v.qq.com")
            self.log("已打开腾讯视频网站", "INFO")
        
        ttk.Button(
            btn_frame, 
            text="🌐 打开腾讯视频网站", 
            command=open_tencent_video
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame, 
            text="📁 选择Cookie文件", 
            command=select_cookie_file
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame, 
            text="关闭", 
            command=wizard.destroy
        ).pack(side=tk.RIGHT, padx=5)
        
        # 提示信息
        tip_label = ttk.Label(
            main_frame,
            text="💡 提示: Cookie有效期通常为30天，过期后需要重新导出",
            foreground="gray"
        )
        tip_label.pack(pady=(10, 0))
    
    def vip_free_parse(self):
        """VIP免费解析 - 使用第三方解析接口"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("提示", "请先输入视频链接")
            return
        
        # 显示解析接口选择窗口
        self.show_vip_parse_window(url)
    
    def show_vip_parse_window(self, video_url):
        """显示VIP解析接口选择窗口"""
        parse_win = tk.Toplevel(self.root)
        parse_win.title("VIP免费解析")
        parse_win.geometry("500x400")
        parse_win.resizable(False, False)
        parse_win.transient(self.root)
        parse_win.grab_set()
        
        main_frame = ttk.Frame(parse_win, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title = ttk.Label(
            main_frame, 
            text="🔓 VIP/SVIP视频免费解析", 
            font=("Microsoft YaHei", 12, "bold")
        )
        title.pack(pady=(0, 10))
        
        # 说明
        desc = ttk.Label(
            main_frame,
            text="💎 SVIP接口支持4K/蓝光高清 | 🚀 VIP接口支持1080P\n无需Cookie即可观看，选择接口后在浏览器中播放",
            justify=tk.CENTER
        )
        desc.pack(pady=(0, 15))
        
        # 解析接口列表 - 支持VIP/SVIP
        parse_apis = [
            # SVIP高清接口（优先）
            ("💎 SVIP-快搞", "https://kuaigao.cc/jx/?url="),
            ("💎 SVIP-万能", "https://www.ckmov.vip/api.php?url="),
            ("💎 SVIP-人人", "https://jx.rrdynb.com/index.php?url="),
            ("💎 SVIP-解析la", "https://api.jiexi.la/?url="),
            ("💎 SVIP-快看", "https://jx.kuaikk.cn/?url="),
            ("💎 SVIP-极速", "https://jx.bwcxy.com/?url="),
            # VIP高速接口
            ("🚀 VIP-爱豆", "https://jx.aidouer.net/?url="),
            ("🚀 VIP-虾米", "https://jx.xmflv.com/?url="),
            ("🚀 VIP-M3U8", "https://jx.m3u8.tv/jiexi/?url="),
            ("🚀 VIP-OK", "https://okjx.cc/?url="),
            ("🚀 VIP-YT", "https://jx.yangtu.top/?url="),
            ("🚀 VIP-8090", "https://www.8090g.cn/?url="),
        ]
        
        # 列表框架
        list_frame = ttk.LabelFrame(main_frame, text="选择解析接口", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 创建列表
        listbox_frame = ttk.Frame(list_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.api_listbox = tk.Listbox(
            listbox_frame, 
            font=("Microsoft YaHei", 10),
            selectmode=tk.SINGLE,
            yscrollcommand=scrollbar.set
        )
        self.api_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.api_listbox.yview)
        
        for name, api in parse_apis:
            self.api_listbox.insert(tk.END, f"  {name}")
        
        self.api_listbox.select_set(0)  # 默认选中第一个
        
        # 保存接口列表供后续使用
        self.parse_apis = parse_apis
        self.current_video_url = video_url
        
        # 按钮区域
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        def open_parse():
            selection = self.api_listbox.curselection()
            if not selection:
                messagebox.showwarning("提示", "请选择一个解析接口")
                return
            
            idx = selection[0]
            api_name, api_url = self.parse_apis[idx]
            
            # 构建解析URL
            full_url = api_url + video_url
            
            self.log(f"使用 {api_name} 解析视频", "INFO")
            self.log(f"正在打开浏览器...", "PLAY")
            
            # 在浏览器中打开
            webbrowser.open(full_url)
            
            self.log(f"已在浏览器中打开解析页面", "SUCCESS")
            parse_win.destroy()
        
        def copy_all_links():
            """复制所有解析链接"""
            links = []
            for name, api in self.parse_apis:
                links.append(f"{name}: {api}{video_url}")
            
            all_links = "\n".join(links)
            self.root.clipboard_clear()
            self.root.clipboard_append(all_links)
            
            self.log("已复制所有解析链接到剪贴板", "SUCCESS")
            messagebox.showinfo("成功", "已复制所有解析链接到剪贴板！\n可以粘贴到浏览器中尝试。")
        
        ttk.Button(
            btn_frame, 
            text="▶ 打开播放", 
            command=open_parse
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame, 
            text="⚡ 测速选择", 
            command=lambda: self.test_api_speed(parse_win)
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame, 
            text="📋 复制链接", 
            command=copy_all_links
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame, 
            text="关闭", 
            command=parse_win.destroy
        ).pack(side=tk.RIGHT, padx=5)
        
        # 双击打开
        def on_double_click(event):
            open_parse()
        
        self.api_listbox.bind('<Double-Button-1>', on_double_click)
        
        # 提示信息
        tip = ttk.Label(
            main_frame,
            text="💡 提示: 💎标记的支持SVIP高清 | 点击'测速选择'自动选最快接口",
            foreground="gray"
        )
        tip.pack(pady=(5, 0))
    
    def test_api_speed(self, parent_window):
        """测试解析接口速度"""
        import urllib.request
        import time
        
        self.log("开始测试接口速度...", "INFO")
        
        def test_speed():
            results = []
            
            for i, (name, api) in enumerate(self.parse_apis):
                try:
                    # 测试接口响应时间
                    start = time.time()
                    
                    # 只获取域名部分测试
                    test_url = api.split('?')[0]
                    
                    req = urllib.request.Request(
                        test_url,
                        headers={'User-Agent': 'Mozilla/5.0'}
                    )
                    urllib.request.urlopen(req, timeout=5)
                    
                    elapsed = (time.time() - start) * 1000  # 转换为毫秒
                    results.append((i, name, elapsed, True))
                    
                    # 修复闭包变量问题
                    def log_success(n, e):
                        self.log(f"{n}: {e:.0f}ms", "SUCCESS")
                    self.root.after(0, lambda n=name, e=elapsed: log_success(n, e))
                    
                except Exception:
                    results.append((i, name, 9999, False))
                    def log_warning(n):
                        self.log(f"{n}: 超时/不可用", "WARNING")
                    self.root.after(0, lambda n=name: log_warning(n))
            
            # 按速度排序，选择最快的
            results.sort(key=lambda x: x[2])
            
            if results and results[0][3]:  # 如果有可用的接口
                fastest_idx = results[0][0]
                fastest_name = results[0][1]
                fastest_time = results[0][2]
                
                self.root.after(0, lambda: self.api_listbox.select_clear(0, tk.END))
                self.root.after(0, lambda: self.api_listbox.select_set(fastest_idx))
                self.root.after(0, lambda: self.api_listbox.see(fastest_idx))
                
                self.root.after(0, lambda: 
                    self.log(f"最快接口: {fastest_name} ({fastest_time:.0f}ms)", "SUCCESS"))
                
                self.root.after(0, lambda: 
                    messagebox.showinfo("测速完成", 
                        f"最快接口: {fastest_name}\n响应时间: {fastest_time:.0f}ms\n\n已自动选中，点击'打开播放'即可"))
            else:
                self.root.after(0, lambda: 
                    self.log("所有接口均不可用", "ERROR"))
        
        threading.Thread(target=test_speed, daemon=True).start()
    
    def show_help(self):
        """显示帮助信息"""
        help_text = """
【腾讯视频播放器使用说明】

1. 获取Cookie（播放VIP视频必须）
   - 安装浏览器扩展 "Get cookies.txt LOCALLY"
   - 登录腾讯视频VIP账号
   - 导出Cookie文件
   - 点击"设置Cookie"按钮导入

2. 播放视频
   - 粘贴腾讯视频链接
   - 点击"解析视频"
   - 选择清晰度
   - 点击"在线播放"

3. 下载视频
   - 解析后点击"下载视频"
   - 选择保存目录即可

4. 支持的播放器
   - PotPlayer（推荐）
   - VLC Player
   - Windows Media Player
   - 或使用浏览器播放

⚠ 本工具仅供个人学习研究使用
   请尊重版权，勿用于商业用途
"""
        messagebox.showinfo("帮助", help_text)


def main():
    root = tk.Tk()
    app = TencentVideoPlayer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
