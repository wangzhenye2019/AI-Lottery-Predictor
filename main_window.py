#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
优化后的主窗口 - 整合用户体验改进
Author: BigCat
"""
import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Optional, Callable, Dict, Any, List
from pathlib import Path
from datetime import datetime
import threading

import customtkinter as ctk
from loguru import logger

from app_state import AppStateManager, AppStatus, OperationContext, PredictionResult
from user_interface import ErrorHandler, UserNotifier, show_progress
from main_optimized import app_config, error_boundary


class ModernTheme:
    """现代化主题配置"""

    # 颜色配置
    COLORS = {
        "primary": "#1890FF",
        "primary_hover": "#40A9FF",
        "success": "#52C41A",
        "warning": "#FAAD14",
        "error": "#F5222D",
        "red_ball": "#F5222D",
        "blue_ball": "#1890FF",
        "text_primary": "#262626",
        "text_secondary": "#595959",
        "border": "#D9D9D9",
        "background": "#F0F2F5",
        "component_bg": "#FFFFFF",
        "hover": "#F5F5F5",
    }

    @classmethod
    def get_color(cls, name: str) -> str:
        return cls.COLORS.get(name, "#000000")


class StatusBar(ctk.CTkFrame):
    """状态栏组件"""

    def __init__(self, parent, app_state: AppStateManager, **kwargs):
        super().__init__(parent, height=30, fg_color=ModernTheme.get_color("component_bg"), **kwargs)

        self.app_state = app_state

        # 状态标签
        self.status_label = ctk.CTkLabel(
            self, text="就绪", font=ctk.CTkFont(size=11),
            text_color=ModernTheme.get_color("text_secondary")
        )
        self.status_label.pack(side="left", padx=10)

        # 进度条
        self.progress_bar = ctk.CTkProgressBar(self, width=150, height=6)
        self.progress_bar.pack(side="left", padx=10)
        self.progress_bar.set(0)
        self.progress_bar.pack_forget()  # 默认隐藏

        # 时间显示
        self.time_label = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=11),
            text_color=ModernTheme.get_color("text_secondary")
        )
        self.time_label.pack(side="right", padx=10)

        # 注册状态监听
        self.app_state.on_status_change(self._on_status_change)
        self.app_state.on_progress_update(self._on_progress_update)

        # 更新时间
        self._update_time()

    def _on_status_change(self, status: AppStatus):
        """状态变更回调"""
        status_texts = {
            AppStatus.IDLE: ("就绪", ModernTheme.get_color("success")),
            AppStatus.INITIALIZING: ("初始化中...", ModernTheme.get_color("primary")),
            AppStatus.LOADING_DATA: ("加载数据中...", ModernTheme.get_color("primary")),
            AppStatus.TRAINING: ("训练中...", ModernTheme.get_color("warning")),
            AppStatus.PREDICTING: ("预测中...", ModernTheme.get_color("warning")),
            AppStatus.ANALYZING: ("分析中...", ModernTheme.get_color("warning")),
            AppStatus.EXPORTING: ("导出中...", ModernTheme.get_color("warning")),
            AppStatus.ERROR: ("发生错误", ModernTheme.get_color("error")),
        }

        text, color = status_texts.get(status, ("未知状态", ModernTheme.get_color("text_secondary")))
        self.status_label.configure(text=text, text_color=color)

    def _on_progress_update(self, progress: float, message: str):
        """进度更新回调"""
        if progress > 0 and progress < 1:
            self.progress_bar.pack(side="left", padx=10)
            self.progress_bar.set(progress)
        else:
            self.progress_bar.pack_forget()

    def _update_time(self):
        """更新时间显示"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.configure(text=current_time)
        self.after(1000, self._update_time)


class BallDisplay(ctk.CTkFrame):
    """号码球显示组件"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.red_canvas_list: List[tk.Canvas] = []
        self.blue_canvas_list: List[tk.Canvas] = []

    def create_balls(self, red_count: int, blue_count: int):
        """创建号码球"""
        # 清空现有
        for widget in self.winfo_children():
            widget.destroy()
        self.red_canvas_list = []
        self.blue_canvas_list = []

        # 主容器
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(expand=True)

        # 红球区域
        if red_count > 0:
            red_frame = ctk.CTkFrame(container, fg_color="transparent")
            red_frame.pack(side="left", padx=10)

            red_label = ctk.CTkLabel(
                red_frame, text="🔴 红球",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=ModernTheme.get_color("text_primary")
            )
            red_label.pack(pady=(0, 5))

            balls_frame = ctk.CTkFrame(red_frame, fg_color="transparent")
            balls_frame.pack()

            for i in range(red_count):
                canvas = tk.Canvas(
                    balls_frame, width=40, height=40,
                    highlightthickness=0, bg=ModernTheme.get_color("component_bg")
                )
                canvas.pack(side="left", padx=2)

                canvas.create_oval(2, 2, 38, 38, fill=ModernTheme.get_color("red_ball"), outline="")
                canvas.create_text(20, 20, text="--", font=("Microsoft YaHei", 12, "bold"), fill="white")
                self.red_canvas_list.append(canvas)

        # 分隔符
        if blue_count > 0:
            separator = ctk.CTkLabel(
                container, text="+",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=ModernTheme.get_color("text_secondary")
            )
            separator.pack(side="left", padx=10)

        # 蓝球区域
        if blue_count > 0:
            blue_frame = ctk.CTkFrame(container, fg_color="transparent")
            blue_frame.pack(side="left", padx=10)

            blue_label = ctk.CTkLabel(
                blue_frame, text="🔵 蓝球",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=ModernTheme.get_color("text_primary")
            )
            blue_label.pack(pady=(0, 5))

            balls_frame = ctk.CTkFrame(blue_frame, fg_color="transparent")
            balls_frame.pack()

            for i in range(blue_count):
                canvas = tk.Canvas(
                    balls_frame, width=40, height=40,
                    highlightthickness=0, bg=ModernTheme.get_color("component_bg")
                )
                canvas.pack(side="left", padx=2)

                canvas.create_oval(2, 2, 38, 38, fill=ModernTheme.get_color("blue_ball"), outline="")
                canvas.create_text(20, 20, text="--", font=("Microsoft YaHei", 12, "bold"), fill="white")
                self.blue_canvas_list.append(canvas)

    def update_numbers(self, red_numbers: List[int], blue_numbers: List[int]):
        """更新号码显示"""
        for i, canvas in enumerate(self.red_canvas_list):
            if i < len(red_numbers):
                canvas.itemconfig(2, text=str(red_numbers[i]))

        for i, canvas in enumerate(self.blue_canvas_list):
            if i < len(blue_numbers):
                canvas.itemconfig(2, text=str(blue_numbers[i]))

    def clear(self):
        """清空显示"""
        for canvas in self.red_canvas_list:
            canvas.itemconfig(2, text="--")
        for canvas in self.blue_canvas_list:
            canvas.itemconfig(2, text="--")


class MainWindow:
    """优化后的主窗口"""

    # 彩票类型配置
    LOTTERY_TYPES = {
        "双色球": {"code": "ssq", "red": 6, "blue": 1},
        "大乐透": {"code": "dlt", "red": 5, "blue": 2},
        "七乐彩": {"code": "qlc", "red": 7, "blue": 0},
        "福彩3D": {"code": "fc3d", "red": 3, "blue": 0},
        "快乐8": {"code": "kl8", "red": 20, "blue": 0},
        "排列3": {"code": "pl3", "red": 3, "blue": 0},
        "排列5": {"code": "pl5", "red": 5, "blue": 0},
        "七星彩": {"code": "qxc", "red": 7, "blue": 0},
    }

    STRATEGIES = [
        "XGBoost梯度提升",
        "ARIMA时间序列",
        "聚类分析",
        "集成学习",
        "Apriori关联规则",
        "遗传算法"
    ]

    def __init__(self):
        self.app_state = AppStateManager()
        self.error_handler = ErrorHandler()
        self.notifier = UserNotifier()

        self.root: Optional[ctk.CTk] = None
        self.ball_display: Optional[BallDisplay] = None
        self.status_bar: Optional[StatusBar] = None

        self._setup_ui()
        self._bind_events()

    def _setup_ui(self):
        """设置UI"""
        # 配置主题
        ctk.set_appearance_mode(app_config.theme)
        ctk.set_default_color_theme("blue")

        # 创建主窗口
        self.root = ctk.CTk()
        self.root.title("AI智能彩票预测系统 - 优化版")
        self.root.geometry(f"{app_config.window_width}x{app_config.window_height}")
        self.root.minsize(app_config.min_width, app_config.min_height)

        # 主框架
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 创建标题栏
        self._create_header(main_frame)

        # 创建控制面板
        self._create_control_panel(main_frame)

        # 创建结果显示区
        self._create_result_area(main_frame)

        # 创建状态栏
        self.status_bar = StatusBar(main_frame, self.app_state)
        self.status_bar.pack(side="bottom", fill="x", pady=(10, 0))

    def _create_header(self, parent):
        """创建标题栏"""
        header = ctk.CTkFrame(parent, height=60, fg_color=ModernTheme.get_color("component_bg"))
        header.pack(fill="x", pady=(0, 10))
        header.pack_propagate(False)

        # 标题
        title = ctk.CTkLabel(
            header, text="🎯 AI智能彩票预测系统",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=ModernTheme.get_color("text_primary")
        )
        title.pack(side="left", padx=20, pady=10)

        # 版本
        version = ctk.CTkLabel(
            header, text="v2.0 优化版",
            font=ctk.CTkFont(size=11),
            text_color=ModernTheme.get_color("text_secondary")
        )
        version.pack(side="left", pady=10)

    def _create_control_panel(self, parent):
        """创建控制面板"""
        panel = ctk.CTkFrame(parent, fg_color=ModernTheme.get_color("component_bg"))
        panel.pack(fill="x", pady=(0, 10))

        # 彩票类型选择
        type_frame = ctk.CTkFrame(panel, fg_color="transparent")
        type_frame.pack(side="left", padx=15, pady=15)

        ctk.CTkLabel(
            type_frame, text="🎲 彩票类型",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w")

        self.lottery_combo = ctk.CTkComboBox(
            type_frame,
            values=list(self.LOTTERY_TYPES.keys()),
            width=150,
            command=self._on_lottery_change
        )
        self.lottery_combo.set("双色球")
        self.lottery_combo.pack(pady=(5, 0))

        # 策略选择
        strategy_frame = ctk.CTkFrame(panel, fg_color="transparent")
        strategy_frame.pack(side="left", padx=15, pady=15)

        ctk.CTkLabel(
            strategy_frame, text="🧠 预测策略",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w")

        self.strategy_combo = ctk.CTkComboBox(
            strategy_frame,
            values=self.STRATEGIES,
            width=150
        )
        self.strategy_combo.set(self.STRATEGIES[0])
        self.strategy_combo.pack(pady=(5, 0))

        # 操作按钮
        btn_frame = ctk.CTkFrame(panel, fg_color="transparent")
        btn_frame.pack(side="right", padx=15, pady=15)

        self.predict_btn = ctk.CTkButton(
            btn_frame,
            text="🚀 开始预测",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=120,
            height=35,
            command=self._start_prediction,
            fg_color=ModernTheme.get_color("primary"),
            hover_color=ModernTheme.get_color("primary_hover")
        )
        self.predict_btn.pack(side="left", padx=5)

        self.refresh_btn = ctk.CTkButton(
            btn_frame,
            text="🔄 刷新数据",
            font=ctk.CTkFont(size=12),
            width=100,
            height=35,
            command=self._refresh_data,
            fg_color=ModernTheme.get_color("component_bg"),
            hover_color=ModernTheme.get_color("hover"),
            text_color=ModernTheme.get_color("text_primary"),
            border_width=1,
            border_color=ModernTheme.get_color("border")
        )
        self.refresh_btn.pack(side="left", padx=5)

    def _create_result_area(self, parent):
        """创建结果显示区"""
        result_frame = ctk.CTkFrame(parent, fg_color=ModernTheme.get_color("component_bg"))
        result_frame.pack(fill="both", expand=True)

        # 标题
        ctk.CTkLabel(
            result_frame,
            text="🎯 预测结果",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(15, 10))

        # 号码显示
        self.ball_display = BallDisplay(result_frame)
        self.ball_display.pack(pady=20)

        # 初始显示
        self._update_ball_display("双色球")

        # 置信度
        self.confidence_frame = ctk.CTkFrame(result_frame, fg_color="transparent")
        self.confidence_frame.pack(fill="x", padx=20, pady=10)

        self.confidence_label = ctk.CTkLabel(
            self.confidence_frame,
            text="等待预测...",
            font=ctk.CTkFont(size=12)
        )
        self.confidence_label.pack()

        # 统计信息
        self.stats_text = ctk.CTkTextbox(result_frame, height=150)
        self.stats_text.pack(fill="x", padx=20, pady=10)
        self.stats_text.insert("1.0", "欢迎使用AI智能彩票预测系统\n请选择彩票类型并开始预测...")
        self.stats_text.configure(state="disabled")

    def _bind_events(self):
        """绑定事件"""
        self.app_state.on_notification(self._on_notification)

    def _on_notification(self, message: str, title: str, level: str):
        """通知回调"""
        if level == "error":
            messagebox.showerror(title, message)
        elif level == "warning":
            messagebox.showwarning(title, message)
        elif level == "success":
            messagebox.showinfo(title, message)

    def _on_lottery_change(self, choice):
        """彩票类型变更"""
        self._update_ball_display(choice)
        self.ball_display.clear()

    def _update_ball_display(self, lottery_name: str):
        """更新号码显示"""
        config = self.LOTTERY_TYPES.get(lottery_name, self.LOTTERY_TYPES["双色球"])
        self.ball_display.create_balls(config["red"], config["blue"])

    def _start_prediction(self):
        """开始预测"""
        if not self.app_state.can_start_operation():
            messagebox.showwarning("提示", "当前有操作正在进行，请等待完成")
            return

        lottery_name = self.lottery_combo.get()
        strategy = self.strategy_combo.get()

        # 在后台线程执行预测
        thread = threading.Thread(
            target=self._do_prediction,
            args=(lottery_name, strategy),
            daemon=True
        )
        thread.start()

    def _do_prediction(self, lottery_name: str, strategy: str):
        """执行预测（后台线程）"""
        try:
            with OperationContext("预测", AppStatus.PREDICTING) as ctx:
                ctx.update_progress(0.1, "加载模型...")

                # TODO: 调用实际的预测服务
                import time
                time.sleep(1)  # 模拟加载

                ctx.update_progress(0.5, "分析数据...")
                time.sleep(1)  # 模拟分析

                ctx.update_progress(0.8, "生成预测...")
                time.sleep(0.5)  # 模拟预测

                ctx.update_progress(1.0, "完成")

                # 生成模拟结果
                import random
                lottery_config = self.LOTTERY_TYPES[lottery_name]

                red_numbers = sorted(random.sample(range(1, 34), lottery_config["red"]))
                blue_numbers = []
                if lottery_config["blue"] > 0:
                    blue_max = 17 if lottery_config["code"] == "ssq" else 13
                    blue_numbers = sorted(random.sample(range(1, blue_max), lottery_config["blue"]))

                # 更新UI（必须在主线程）
                self.root.after(0, lambda: self._update_prediction_result(
                    red_numbers, blue_numbers, 0.85, strategy
                ))

        except Exception as e:
            logger.error(f"预测失败: {e}")
            self.root.after(0, lambda: messagebox.showerror("预测失败", str(e)))

    def _update_prediction_result(self, red: List[int], blue: List[int],
                                   confidence: float, strategy: str):
        """更新预测结果到UI"""
        self.ball_display.update_numbers(red, blue)

        self.confidence_label.configure(
            text=f"预测置信度: {confidence*100:.1f}% | 策略: {strategy}"
        )

        # 更新统计
        self.stats_text.configure(state="normal")
        self.stats_text.delete("1.0", "end")
        self.stats_text.insert("1.0",
            f"预测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"使用策略: {strategy}\n"
            f"红球号码: {', '.join(map(str, red))}\n"
            f"蓝球号码: {', '.join(map(str, blue)) if blue else '无'}\n"
            f"置信度: {confidence*100:.1f}%"
        )
        self.stats_text.configure(state="disabled")

        # 记录结果
        result = PredictionResult(
            red_balls=red,
            blue_balls=blue,
            confidence=confidence,
            strategy=strategy
        )
        self.app_state.record_prediction(result)

        messagebox.showinfo("预测完成", "预测结果已生成！")

    def _refresh_data(self):
        """刷新数据"""
        if not self.app_state.can_start_operation():
            messagebox.showwarning("提示", "当前有操作正在进行")
            return

        def do_refresh():
            try:
                with OperationContext("数据刷新", AppStatus.LOADING_DATA) as ctx:
                    ctx.update_progress(0.3, "连接数据源...")
                    import time
                    time.sleep(0.5)

                    ctx.update_progress(0.7, "同步数据...")
                    time.sleep(0.5)

                    ctx.update_progress(1.0, "完成")

                self.root.after(0, lambda: messagebox.showinfo("刷新完成", "数据已更新到最新！"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("刷新失败", str(e)))

        threading.Thread(target=do_refresh, daemon=True).start()

    def run(self):
        """运行主循环"""
        self.root.mainloop()


if __name__ == "__main__":
    app = MainWindow()
    app.run()
