import customtkinter as ctk
from tkinter import messagebox, scrolledtext
import threading
import logging
import ctypes
from typing import TYPE_CHECKING
import os
import sys
from PIL import Image, ImageDraw, ImageFont

# 尝试导入pystray，如果不存在则稍后处理
try:
    from pystray import Icon as TrayIcon, MenuItem as TrayMenuItem
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False

if TYPE_CHECKING:
    from main import AnanSketchbookApp

class AnanSketchbookUI:
    def __init__(self, app: 'AnanSketchbookApp'):
        self.app = app
        
        # 启用高DPI支持
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # 设置高DPI感知
        except:
            pass
            
        ctk.set_appearance_mode("System")  # 跟随系统主题
        ctk.set_default_color_theme("blue")  # 使用蓝色主题
        
        self.root = ctk.CTk()
        self.root.title("安安的素描本聊天框")
        self.root.geometry("650x500")
        self.root.minsize(500, 400)  # 设置最小尺寸
        self.root.resizable(True, True)  # 允许调整窗口大小
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 设置窗口图标
        self.setup_window_icon()
        
        # 在创建窗口之后初始化字体
        self.init_fonts()
        
        # 创建日志处理器
        self.log_handler = UITextHandler(self)
        self.log_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        )
        
        # 设置UI元素
        self.setup_ui()
        
        # 最小化状态
        self.is_minimized = False
        
    def setup_window_icon(self):
        """设置窗口图标"""
        try:
            # 创建一个简单的图标
            icon = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))  # 透明背景
            draw = ImageDraw.Draw(icon)
            
            # 绘制一个简洁的笔记本图标
            draw.rectangle([8, 8, 56, 56], fill=(30, 144, 255, 255), outline=(25, 25, 112, 255), width=2)  # 笔记本封面
            draw.rectangle([15, 15, 20, 50], fill=(255, 255, 255, 200))  # 装订线
            
            # 添加代表"安安"的图案
            draw.ellipse([30, 20, 50, 40], fill=(255, 182, 193, 200))  # 简单的头部轮廓
            
            self.root.iconphoto(False, icon)
        except Exception as e:
            print(f"设置窗口图标失败: {e}")
        
    def init_fonts(self):
        """初始化字体，在窗口创建后调用"""
        # 从配置中获取UI设置
        ui_settings = self.app.config.ui_settings
        # 设置更清晰的字体
        self.custom_font = ctk.CTkFont(family=ui_settings.font_family, size=ui_settings.font_size)
        self.title_font = ctk.CTkFont(family=ui_settings.font_family, size=ui_settings.title_font_size, weight="bold")
        self.header_font = ctk.CTkFont(family=ui_settings.font_family, size=ui_settings.font_size + 1, weight="bold")
        
    def setup_ui(self):
        # 创建顶部标题栏
        self.create_header()
        
        # 创建notebook用于分隔配置和日志
        self.notebook = ctk.CTkTabview(self.root, segmented_button_selected_color=("#3a7ebf", "#1f538d"))
        self.notebook.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # 添加标签页
        self.config_tab = self.notebook.add("配置")
        self.log_tab = self.notebook.add("日志")
        
        # 配置界面元素
        self.setup_config_ui()
        
        # 日志界面元素
        self.setup_log_ui()
        
        # 创建底部状态栏
        self.create_status_bar()
        
    def create_header(self):
        """创建顶部标题栏"""
        header_frame = ctk.CTkFrame(self.root, height=60, corner_radius=0)
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header_frame, 
            text="安安的素描本聊天框", 
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("gray10", "gray90")
        )
        title_label.pack(side="left", padx=20, pady=10)
        
        # 添加版本信息
        version_label = ctk.CTkLabel(
            header_frame,
            text="v1.0",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60")
        )
        version_label.pack(side="right", padx=20, pady=10)
        
    def setup_config_ui(self):
        # 创建滚动框架以适应高DPI下的内容
        config_canvas = ctk.CTkScrollableFrame(self.config_tab, corner_radius=10)
        config_canvas.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 添加欢迎信息
        welcome_frame = ctk.CTkFrame(config_canvas, corner_radius=10)
        welcome_frame.pack(fill="x", padx=5, pady=5)
        
        welcome_label = ctk.CTkLabel(
            welcome_frame,
            text="欢迎使用安安的素描本聊天框！\n在这里配置您的个性化设置",
            font=self.header_font,
            wraplength=500,
            justify="center"
        )
        welcome_label.pack(pady=15)
        
        # 主配置框架
        main_config_frame = ctk.CTkFrame(config_canvas, corner_radius=10)
        main_config_frame.pack(fill="x", padx=5, pady=10)
        
        ctk.CTkLabel(main_config_frame, text="基础设置", font=self.header_font).pack(pady=(15, 10))
        
        # 热键配置
        hotkey_frame = ctk.CTkFrame(main_config_frame, corner_radius=8)
        hotkey_frame.pack(fill="x", pady=5, padx=20)
        ctk.CTkLabel(hotkey_frame, text="全局热键:", font=self.custom_font).pack(side="left", padx=10, pady=10)
        self.hotkey_var = ctk.StringVar(value=self.app.config.hotkey)
        hotkey_entry = ctk.CTkEntry(hotkey_frame, textvariable=self.hotkey_var, width=200, font=self.custom_font)
        hotkey_entry.pack(side="right", padx=10, pady=10)
        
        # 延迟配置
        delay_frame = ctk.CTkFrame(main_config_frame, corner_radius=8)
        delay_frame.pack(fill="x", pady=5, padx=20)
        ctk.CTkLabel(delay_frame, text="操作延迟(秒):", font=self.custom_font).pack(side="left", padx=10, pady=10)
        self.delay_var = ctk.DoubleVar(value=self.app.config.delay)
        delay_entry = ctk.CTkEntry(delay_frame, textvariable=self.delay_var, width=200, font=self.custom_font)
        delay_entry.pack(side="right", padx=10, pady=10)
        
        # 坐标配置框架
        coord_frame = ctk.CTkFrame(config_canvas, corner_radius=10)
        coord_frame.pack(fill="x", padx=5, pady=10)
        
        ctk.CTkLabel(coord_frame, text="坐标设置", font=self.header_font).pack(pady=(15, 10))
        
        # 文本框坐标说明
        text_coord_desc = ctk.CTkLabel(
            coord_frame, 
            text="设置文本在素描本上的显示区域", 
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60")
        )
        text_coord_desc.pack(pady=(0, 10))
        
        # 左上角坐标
        topleft_frame = ctk.CTkFrame(coord_frame, corner_radius=8)
        topleft_frame.pack(fill="x", pady=5, padx=20)
        ctk.CTkLabel(topleft_frame, text="左上角坐标(X,Y):", font=self.custom_font).pack(side="left", padx=10, pady=10)
        self.topleft_x_var = ctk.IntVar(value=self.app.config.text_box_topleft[0])
        self.topleft_y_var = ctk.IntVar(value=self.app.config.text_box_topleft[1])
        topleft_x_entry = ctk.CTkEntry(topleft_frame, textvariable=self.topleft_x_var, width=100, font=self.custom_font)
        topleft_x_entry.pack(side="right", padx=(0, 10), pady=10)
        topleft_y_entry = ctk.CTkEntry(topleft_frame, textvariable=self.topleft_y_var, width=100, font=self.custom_font)
        topleft_y_entry.pack(side="right", padx=(0, 10), pady=10)
        
        # 右下角坐标
        bottomright_frame = ctk.CTkFrame(coord_frame, corner_radius=8)
        bottomright_frame.pack(fill="x", pady=5, padx=20)
        ctk.CTkLabel(bottomright_frame, text="右下角坐标(X,Y):", font=self.custom_font).pack(side="left", padx=10, pady=10)
        self.bottomright_x_var = ctk.IntVar(value=self.app.config.image_box_bottomright[0])
        self.bottomright_y_var = ctk.IntVar(value=self.app.config.image_box_bottomright[1])
        bottomright_x_entry = ctk.CTkEntry(bottomright_frame, textvariable=self.bottomright_x_var, width=100, font=self.custom_font)
        bottomright_x_entry.pack(side="right", padx=(0, 10), pady=10)
        bottomright_y_entry = ctk.CTkEntry(bottomright_frame, textvariable=self.bottomright_y_var, width=100, font=self.custom_font)
        bottomright_y_entry.pack(side="right", padx=(0, 10), pady=10)
        
        # 功能开关框架
        switches_frame = ctk.CTkFrame(config_canvas, corner_radius=10)
        switches_frame.pack(fill="x", padx=5, pady=10)
        
        ctk.CTkLabel(switches_frame, text="功能开关", font=self.header_font).pack(pady=(15, 10))
        
        # 自动粘贴开关
        self.auto_paste_var = ctk.BooleanVar(value=self.app.config.auto_paste_image)
        auto_paste_switch = ctk.CTkSwitch(
            switches_frame, 
            text="自动粘贴图片", 
            variable=self.auto_paste_var,
            font=self.custom_font,
            onvalue=True,
            offvalue=False
        )
        auto_paste_switch.pack(anchor="w", pady=5, padx=20)
        
        # 自动发送开关
        self.auto_send_var = ctk.BooleanVar(value=self.app.config.auto_send_image)
        auto_send_switch = ctk.CTkSwitch(
            switches_frame, 
            text="自动发送图片", 
            variable=self.auto_send_var,
            font=self.custom_font,
            onvalue=True,
            offvalue=False
        )
        auto_send_switch.pack(anchor="w", pady=5, padx=20)
        
        # 阻塞热键开关
        self.block_hotkey_var = ctk.BooleanVar(value=self.app.config.block_hotkey)
        block_hotkey_switch = ctk.CTkSwitch(
            switches_frame, 
            text="阻塞热键", 
            variable=self.block_hotkey_var,
            font=self.custom_font,
            onvalue=True,
            offvalue=False
        )
        block_hotkey_switch.pack(anchor="w", pady=5, padx=20)
        
        # 控制按钮框架
        button_frame = ctk.CTkFrame(config_canvas, corner_radius=10)
        button_frame.pack(fill="x", padx=5, pady=(15, 10))
        
        ctk.CTkButton(
            button_frame, 
            text="保存配置", 
            command=self.save_config, 
            font=self.custom_font,
            corner_radius=8,
            height=35
        ).pack(side="left", padx=(20, 10), pady=15)
        
        ctk.CTkButton(
            button_frame, 
            text="应用配置", 
            command=self.apply_config, 
            font=self.custom_font,
            corner_radius=8,
            height=35
        ).pack(side="left", padx=10, pady=15)
        
        ctk.CTkButton(
            button_frame, 
            text="折叠到托盘", 
            command=self.minimize, 
            font=self.custom_font,
            corner_radius=8,
            height=35,
            fg_color=("gray60", "gray20"),
            hover_color=("gray50", "gray30")
        ).pack(side="right", padx=(10, 20), pady=15)
        
    def setup_log_ui(self):
        # 日志显示区域
        log_text_frame = ctk.CTkFrame(self.log_tab, corner_radius=10)
        log_text_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 添加日志标题
        log_header_frame = ctk.CTkFrame(log_text_frame, corner_radius=8)
        log_header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(log_header_frame, text="运行日志", font=self.header_font).pack(side="left", padx=10, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(
            log_text_frame, 
            state='disabled', 
            wrap='word',
            height=10,
            bg="#202020" if ctk.get_appearance_mode() == "Dark" else "#ffffff",
            fg="#ffffff" if ctk.get_appearance_mode() == "Dark" else "#000000",
            font=(self.app.config.ui_settings.font_family, 9)
        )
        self.log_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # 日志控制按钮
        log_control_frame = ctk.CTkFrame(self.log_tab, corner_radius=10)
        log_control_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            log_control_frame, 
            text="清空日志", 
            command=self.clear_log, 
            font=self.custom_font,
            corner_radius=8,
            height=35
        ).pack(side="left", padx=(20, 10), pady=15)
        
        ctk.CTkButton(
            log_control_frame, 
            text="折叠到托盘", 
            command=self.minimize, 
            font=self.custom_font,
            corner_radius=8,
            height=35,
            fg_color=("gray60", "gray20"),
            hover_color=("gray50", "gray30")
        ).pack(side="right", padx=(10, 20), pady=15)
        
    def create_status_bar(self):
        """创建底部状态栏"""
        self.status_frame = ctk.CTkFrame(self.root, height=30, corner_radius=0)
        self.status_frame.pack(fill="x", side="bottom", padx=0, pady=0)
        self.status_frame.pack_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame, 
            text="就绪", 
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60")
        )
        self.status_label.pack(side="left", padx=15, pady=5)
        
        # 显示当前热键
        hotkey_info = ctk.CTkLabel(
            self.status_frame,
            text=f"热键: {self.app.config.hotkey}",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60")
        )
        hotkey_info.pack(side="right", padx=15, pady=5)
        
    def update_status(self, message: str):
        """更新状态栏信息"""
        self.status_label.configure(text=message)
        self.root.update_idletasks()
        
    def save_config(self):
        """保存配置到文件"""
        try:
            # TODO: 实现配置保存到文件
            messagebox.showinfo("提示", "配置保存功能将在后续实现")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置时发生错误: {str(e)}")
            
    def apply_config(self):
        """应用配置到运行时"""
        try:
            self.update_status("正在应用配置...")
            
            # 更新应用配置
            self.app.config.hotkey = self.hotkey_var.get()
            self.app.config.delay = self.delay_var.get()
            self.app.config.text_box_topleft = (self.topleft_x_var.get(), self.topleft_y_var.get())
            self.app.config.image_box_bottomright = (self.bottomright_x_var.get(), self.bottomright_y_var.get())
            self.app.config.auto_paste_image = self.auto_paste_var.get()
            self.app.config.auto_send_image = self.auto_send_var.get()
            self.app.config.block_hotkey = self.block_hotkey_var.get()
            
            # 重新注册热键
            self.app.rebind_hotkey()
            
            # 更新状态栏
            self.update_status("配置已应用")
            
            messagebox.showinfo("提示", "配置已应用")
        except Exception as e:
            self.update_status("配置应用失败")
            messagebox.showerror("错误", f"应用配置时发生错误: {str(e)}")
            
    def minimize(self):
        """最小化窗口到系统托盘"""
        self.update_status("正在最小化到系统托盘...")
        self.is_minimized = True
        # 隐藏主窗口
        self.root.withdraw()
        
        # 如果pystray可用，则创建系统托盘图标
        if PYSTRAY_AVAILABLE:
            self.create_tray_icon()
        else:
            # 如果pystray不可用，则使用标准的窗口最小化方法
            self.root.iconify()
            self.update_status("已最小化到任务栏")

    def create_tray_icon(self):
        """创建系统托盘图标"""
        # 创建托盘图标菜单
        menu = (
            TrayMenuItem('显示', self.restore),
            TrayMenuItem('退出', self.confirm_exit_from_tray),
        )
        
        # 尝试加载图标，如果没有则使用默认图标
        icon_image = self.create_default_icon()
        
        # 创建并运行托盘图标
        self.tray_icon = TrayIcon(
            "安安的素描本聊天框",
            icon_image,
            "安安的素描本聊天框",
            menu
        )
        
        # 添加双击事件处理
        def on_tray_icon_click(icon, query):
            if query == TrayIcon.DoubleClick:
                self.restore()
        
        self.tray_icon.on_click = on_tray_icon_click
        
        # 在单独的线程中运行托盘图标
        self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        self.tray_thread.start()
        self.update_status("已最小化到系统托盘")

    def create_default_icon(self):
        """创建默认的托盘图标"""
        # 创建一个更美观的图标
        icon = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))  # 透明背景
        draw = ImageDraw.Draw(icon)
        
        # 绘制一个更精美的笔记本图标
        draw.rectangle([8, 8, 56, 56], fill=(30, 144, 255), outline=(25, 25, 112), width=2)  # 笔记本封面
        draw.rectangle([15, 15, 20, 50], fill=(255, 255, 255))  # 装订线
        
        # 添加代表"安安"的图案
        draw.ellipse([30, 20, 50, 40], fill=(255, 182, 193))  # 头部
        draw.ellipse([35, 25, 38, 28], fill=(0, 0, 0))  # 眼睛
        draw.ellipse([42, 25, 45, 28], fill=(0, 0, 0))  # 眼睛
        
        return icon

    def restore(self):
        """恢复窗口"""
        self.is_minimized = False
        
        # 停止托盘图标（如果存在）
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        
        # 恢复主窗口
        self.root.deiconify()
        self.root.lift()
        self.update_status("就绪")

    def confirm_exit_from_tray(self):
        """托盘退出确认"""
        # 停止托盘图标（如果存在）
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
            
        self.app.stop()
        self.root.destroy()

    def on_closing(self):
        """处理窗口关闭事件"""
        # 显示选项对话框
        from tkinter import messagebox
        
        # 创建一个顶层窗口作为对话框的父窗口
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("确认操作")
        dialog.geometry("350x180")
        dialog.resizable(False, False)
        dialog.transient(self.root)  # 设置为瞬态窗口
        dialog.grab_set()  # 模态对话框
        
        # 居中显示对话框
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (350 // 2)
        y = (dialog.winfo_screenheight() // 2) - (180 // 2)
        dialog.geometry(f"350x180+{x}+{y}")
        
        # 对话框内容
        label = ctk.CTkLabel(dialog, text="确定要退出安安的素描本聊天框吗？", font=self.header_font)
        label.pack(pady=20)
        
        desc_label = ctk.CTkLabel(
            dialog, 
            text="选择“隐藏”可以最小化到系统托盘继续运行", 
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60")
        )
        desc_label.pack(pady=(0, 10))
        
        # 按钮框架
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=10)
        
        def hide_window():
            dialog.destroy()
            self.minimize()
            
        def close_app():
            dialog.destroy()
            # 停止托盘图标（如果存在）
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.stop()
                
            self.app.stop()
            self.root.destroy()
            
        def cancel_action():
            dialog.destroy()
            
        # 创建三个按钮
        hide_btn = ctk.CTkButton(
            button_frame, 
            text="隐藏到托盘", 
            command=hide_window,
            fg_color=("gray60", "gray20"),
            hover_color=("gray50", "gray30"),
            width=80
        )
        hide_btn.pack(side="left", padx=5)
        
        close_btn = ctk.CTkButton(
            button_frame, 
            text="退出程序", 
            command=close_app, 
            fg_color="#d32f2f",
            hover_color="#b71c1c",
            width=80
        )
        close_btn.pack(side="left", padx=5)
        
        cancel_btn = ctk.CTkButton(
            button_frame, 
            text="取消", 
            command=cancel_action,
            width=80
        )
        cancel_btn.pack(side="left", padx=5)
        
        # 确保对话框获得焦点
        dialog.focus_force()
        
    def append_log(self, message: str):
        """添加日志消息到UI"""
        self.log_text.config(state='normal')
        self.log_text.insert(ctk.END, message + '\n')
        self.log_text.config(state='disabled')
        self.log_text.see(ctk.END)
        
    def clear_log(self):
        """清空日志"""
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, ctk.END)
        self.log_text.config(state='disabled')


class UITextHandler(logging.Handler):
    """自定义日志处理器，将日志输出到UI"""
    
    def __init__(self, ui: AnanSketchbookUI):
        super().__init__()
        self.ui = ui
        
    def emit(self, record):
        msg = self.format(record)
        # 使用线程安全的方式更新UI
        if self.ui.root:
            self.ui.root.after(0, self.ui.append_log, msg)