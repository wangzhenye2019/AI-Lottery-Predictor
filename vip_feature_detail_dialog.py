# -*- coding: utf-8 -*-
"""
VIP功能详情对话框 - 展示各功能的实际实现
Author: BigCat
"""

import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time


class VIPFeatureDetailDialog:
    """VIP功能详情对话框"""
    
    def __init__(self, parent, feature_id: str, vip_impl, user_level, is_available: bool):
        self.parent = parent
        self.feature_id = feature_id
        self.vip_impl = vip_impl
        self.user_level = user_level
        self.is_available = is_available
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"功能详情 - {feature_id}")
        self.dialog.geometry("800x600")
        self.dialog.transient(parent)
        
        # 创建界面
        self.create_ui()
    
    def create_ui(self):
        """创建功能详情界面"""
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 功能标题
        title_frame = ctk.CTkFrame(main_frame, fg_color="#F0F9FF")
        title_frame.pack(fill="x", pady=(0, 20))
        
        feature_names = {
            "basic_prediction": ("🎯 基础预测", "基础算法预测"),
            "advanced_prediction": ("🧠 高级预测", "深度学习算法预测"),
            "expert_prediction": ("🏆 专家预测", "多模型融合预测"),
            "vip_prediction": ("💎 VIP预测", "实时数据+个性化预测"),
            "ultimate_prediction": ("👑 至尊预测", "终极策略预测"),
            "batch_prediction": ("📊 批量预测", "一次预测多期"),
            "history_analysis": ("📈 历史分析", "历史数据分析"),
            "trend_chart": ("📉 走势图", "可视化走势图"),
            "prediction_report": ("📋 预测报告", "详细预测报告"),
            "advanced_export": ("📑 高级导出", "多种格式导出"),
            "check_winning": ("🔔 中奖检查", "自动检查中奖"),
            "realtime_data": ("⚡ 实时数据", "获取实时数据")
        }
        
        name, desc = feature_names.get(self.feature_id, (self.feature_id, ""))
        
        title_label = ctk.CTkLabel(
            title_frame,
            text=name,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#1890FF"
        )
        title_label.pack(pady=(15, 5))
        
        desc_label = ctk.CTkLabel(
            title_frame,
            text=desc,
            font=ctk.CTkFont(size=12),
            text_color="#666"
        )
        desc_label.pack(pady=(0, 15))
        
        # 权限状态
        if not self.is_available:
            lock_frame = ctk.CTkFrame(main_frame, fg_color="#FFF7ED")
            lock_frame.pack(fill="x", pady=(0, 20))
            
            lock_label = ctk.CTkLabel(
                lock_frame,
                text="🔒 此功能需要更高等级会员\n请升级会员解锁此功能",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#FF6B35"
            )
            lock_label.pack(pady=20)
            
            upgrade_btn = ctk.CTkButton(
                lock_frame,
                text="🚀 升级会员",
                command=self.on_upgrade,
                fg_color="#FFD700",
                hover_color="#FFC107",
                text_color="#333",
                height=40
            )
            upgrade_btn.pack(pady=(0, 20))
            
            return
        
        # 功能演示区域
        demo_frame = ctk.CTkFrame(main_frame)
        demo_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        self.create_feature_demo(demo_frame)
        
        # 关闭按钮
        close_btn = ctk.CTkButton(
            main_frame,
            text="关闭",
            command=self.on_close,
            fg_color="#E0E0E0",
            hover_color="#BDBDBD",
            text_color="#333",
            height=40
        )
        close_btn.pack()
    
    def create_feature_demo(self, parent):
        """创建功能演示界面"""
        if self.feature_id == "basic_prediction":
            self.create_prediction_demo(parent, "basic")
        elif self.feature_id == "advanced_prediction":
            self.create_prediction_demo(parent, "advanced")
        elif self.feature_id == "expert_prediction":
            self.create_prediction_demo(parent, "expert")
        elif self.feature_id == "vip_prediction":
            self.create_prediction_demo(parent, "vip")
        elif self.feature_id == "ultimate_prediction":
            self.create_prediction_demo(parent, "ultimate")
        elif self.feature_id == "batch_prediction":
            self.create_batch_prediction_demo(parent)
        elif self.feature_id == "history_analysis":
            self.create_history_analysis_demo(parent)
        elif self.feature_id == "trend_chart":
            self.create_trend_chart_demo(parent)
        elif self.feature_id == "prediction_report":
            self.create_report_demo(parent)
        elif self.feature_id == "advanced_export":
            self.create_export_demo(parent)
        else:
            # 默认显示
            default_label = ctk.CTkLabel(
                parent,
                text="功能演示区域\n\n点击'开始演示'查看功能效果",
                font=ctk.CTkFont(size=14),
                text_color="#666"
            )
            default_label.pack(expand=True)
            
            demo_btn = ctk.CTkButton(
                parent,
                text="▶️ 开始演示",
                command=lambda: self.run_demo(),
                fg_color="#1890FF",
                hover_color="#40A9FF",
                height=40
            )
            demo_btn.pack(pady=20)
    
    def create_prediction_demo(self, parent, algorithm_type):
        """创建预测演示界面 - 支持所有彩种"""
        from lottery_type_manager import LotteryTypeManager
        
        # 参数设置
        settings_frame = ctk.CTkFrame(parent)
        settings_frame.pack(fill="x", pady=10, padx=10)
        
        settings_label = ctk.CTkLabel(
            settings_frame,
            text="预测设置",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        settings_label.pack(anchor="w", pady=(10, 5))
        
        # 彩票类型选择 - 使用下拉菜单支持所有彩种
        type_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        type_frame.pack(fill="x", pady=5)
        
        type_label = ctk.CTkLabel(type_frame, text="彩票类型:")
        type_label.pack(side="left", padx=(0, 10))
        
        # 获取所有彩种
        all_types = LotteryTypeManager.get_all_types()
        categories = LotteryTypeManager.get_categories()
        
        # 构建下拉选项
        type_options = []
        for category, types in categories.items():
            for t in types:
                name = LotteryTypeManager.get_name(t)
                type_options.append(f"{name} ({t})")
        
        self.lottery_type_var = ctk.StringVar(value="双色球 (ssq)")
        
        type_dropdown = ctk.CTkOptionMenu(
            type_frame,
            values=type_options,
            variable=self.lottery_type_var,
            width=200,
            height=28
        )
        type_dropdown.pack(side="left")
        
        # 预测数量
        count_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        count_frame.pack(fill="x", pady=5)
        
        count_label = ctk.CTkLabel(count_frame, text="预测组数:")
        count_label.pack(side="left", padx=(0, 10))
        
        self.count_var = ctk.StringVar(value="5")
        count_entry = ctk.CTkEntry(count_frame, textvariable=self.count_var, width=50)
        count_entry.pack(side="left")
        
        # 开始按钮
        algo_names = {
            "basic": "基础",
            "advanced": "高级",
            "expert": "专家",
            "vip": "VIP",
            "ultimate": "至尊"
        }
        algo_name = algo_names.get(algorithm_type, algorithm_type)
        
        start_btn = ctk.CTkButton(
            settings_frame,
            text=f"▶️ 使用{algo_name}算法预测",
            command=lambda: self.run_prediction(algorithm_type),
            fg_color="#1890FF",
            hover_color="#40A9FF",
            height=40
        )
        start_btn.pack(fill="x", pady=10)
        
        # 结果区域
        result_frame = ctk.CTkFrame(parent)
        result_frame.pack(fill="both", expand=True, pady=10, padx=10)
        
        result_label = ctk.CTkLabel(
            result_frame,
            text="预测结果",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        result_label.pack(anchor="w", pady=(10, 5))
        
        self.result_text = ctk.CTkTextbox(result_frame, height=200)
        self.result_text.pack(fill="both", expand=True, pady=(0, 10))
        
        # 导出按钮
        export_btn = ctk.CTkButton(
            result_frame,
            text="📄 导出结果",
            command=self.export_prediction_result,
            fg_color="#52C41A",
            hover_color="#73D13D",
            height=35
        )
        export_btn.pack(fill="x")
    
    def create_batch_prediction_demo(self, parent):
        """创建批量预测演示 - 支持所有彩种"""
        from lottery_type_manager import LotteryTypeManager
        
        settings_frame = ctk.CTkFrame(parent)
        settings_frame.pack(fill="x", pady=10, padx=10)
        
        settings_label = ctk.CTkLabel(
            settings_frame,
            text="批量预测设置",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        settings_label.pack(anchor="w", pady=(10, 5))
        
        # 彩票类型选择
        type_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        type_frame.pack(fill="x", pady=5)
        
        type_label = ctk.CTkLabel(type_frame, text="彩票类型:")
        type_label.pack(side="left", padx=(0, 10))
        
        # 构建下拉选项
        categories = LotteryTypeManager.get_categories()
        type_options = []
        for category, types in categories.items():
            for t in types:
                name = LotteryTypeManager.get_name(t)
                type_options.append(f"{name} ({t})")
        
        self.lottery_type_var = ctk.StringVar(value="双色球 (ssq)")
        
        type_dropdown = ctk.CTkOptionMenu(
            type_frame,
            values=type_options,
            variable=self.lottery_type_var,
            width=200,
            height=28
        )
        type_dropdown.pack(side="left")
        
        # 期数设置
        period_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        period_frame.pack(fill="x", pady=5)
        
        period_label = ctk.CTkLabel(period_frame, text="预测期数:")
        period_label.pack(side="left", padx=(0, 10))
        
        self.period_var = ctk.StringVar(value="10")
        period_entry = ctk.CTkEntry(period_frame, textvariable=self.period_var, width=50)
        period_entry.pack(side="left")
        
        # 算法选择
        algo_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        algo_frame.pack(fill="x", pady=5)
        
        algo_label = ctk.CTkLabel(algo_frame, text="预测算法:")
        algo_label.pack(side="left", padx=(0, 10))
        
        self.algo_var = ctk.StringVar(value="advanced")
        
        algorithms = [
            ("高级算法", "advanced"),
            ("专家算法", "expert"),
            ("VIP算法", "vip"),
            ("至尊算法", "ultimate")
        ]
        
        for text, value in algorithms:
            radio = ctk.CTkRadioButton(algo_frame, text=text, variable=self.algo_var, value=value)
            radio.pack(side="left", padx=(0, 10))
        
        # 开始按钮
        start_btn = ctk.CTkButton(
            settings_frame,
            text="📊 开始批量预测",
            command=self.run_batch_prediction,
            fg_color="#1890FF",
            hover_color="#40A9FF",
            height=40
        )
        start_btn.pack(fill="x", pady=10)
        
        # 结果区域
        result_frame = ctk.CTkFrame(parent)
        result_frame.pack(fill="both", expand=True, pady=10, padx=10)
        
        self.batch_result_text = ctk.CTkTextbox(result_frame)
        self.batch_result_text.pack(fill="both", expand=True)
    
    def create_history_analysis_demo(self, parent):
        """创建历史分析演示 - 支持所有彩种"""
        from lottery_type_manager import LotteryTypeManager
        
        # 分析设置
        settings_frame = ctk.CTkFrame(parent)
        settings_frame.pack(fill="x", pady=10, padx=10)
        
        settings_label = ctk.CTkLabel(
            settings_frame,
            text="历史分析设置",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        settings_label.pack(anchor="w", pady=(10, 5))
        
        # 彩票类型选择
        type_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        type_frame.pack(fill="x", pady=5)
        
        type_label = ctk.CTkLabel(type_frame, text="彩票类型:")
        type_label.pack(side="left", padx=(0, 10))
        
        categories = LotteryTypeManager.get_categories()
        type_options = []
        for category, types in categories.items():
            for t in types:
                name = LotteryTypeManager.get_name(t)
                type_options.append(f"{name} ({t})")
        
        self.lottery_type_var = ctk.StringVar(value="双色球 (ssq)")
        
        type_dropdown = ctk.CTkOptionMenu(
            type_frame,
            values=type_options,
            variable=self.lottery_type_var,
            width=200,
            height=28
        )
        type_dropdown.pack(side="left")
        
        # 分析期数
        period_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        period_frame.pack(fill="x", pady=5)
        
        period_label = ctk.CTkLabel(period_frame, text="分析期数:")
        period_label.pack(side="left", padx=(0, 10))
        
        self.analysis_period_var = ctk.StringVar(value="100")
        
        for text, value in [("50期", "50"), ("100期", "100"), ("200期", "200")]:
            radio = ctk.CTkRadioButton(
                period_frame, text=text, variable=self.analysis_period_var, value=value
            )
            radio.pack(side="left", padx=(0, 10))
        
        # 开始分析按钮
        start_btn = ctk.CTkButton(
            settings_frame,
            text="📈 开始历史分析",
            command=self.run_history_analysis,
            fg_color="#1890FF",
            hover_color="#40A9FF",
            height=40
        )
        start_btn.pack(fill="x", pady=10)
        
        # 结果显示区域
        result_frame = ctk.CTkScrollableFrame(parent)
        result_frame.pack(fill="both", expand=True, pady=10, padx=10)
        
        self.analysis_result_frame = result_frame
    
    def create_trend_chart_demo(self, parent):
        """创建走势图演示 - 支持所有彩种"""
        from lottery_type_manager import LotteryTypeManager
        
        # 图表设置
        settings_frame = ctk.CTkFrame(parent)
        settings_frame.pack(fill="x", pady=10, padx=10)
        
        settings_label = ctk.CTkLabel(
            settings_frame,
            text="走势图设置",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        settings_label.pack(anchor="w", pady=(10, 5))
        
        # 彩票类型选择
        type_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        type_frame.pack(fill="x", pady=5)
        
        type_label = ctk.CTkLabel(type_frame, text="彩票类型:")
        type_label.pack(side="left", padx=(0, 10))
        
        categories = LotteryTypeManager.get_categories()
        type_options = []
        for category, types in categories.items():
            for t in types:
                name = LotteryTypeManager.get_name(t)
                type_options.append(f"{name} ({t})")
        
        self.lottery_type_var = ctk.StringVar(value="双色球 (ssq)")
        
        type_dropdown = ctk.CTkOptionMenu(
            type_frame,
            values=type_options,
            variable=self.lottery_type_var,
            width=200,
            height=28
        )
        type_dropdown.pack(side="left")
        
        # 期数选择
        period_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        period_frame.pack(fill="x", pady=5)
        
        period_label = ctk.CTkLabel(period_frame, text="显示期数:")
        period_label.pack(side="left", padx=(0, 10))
        
        self.chart_period_var = ctk.StringVar(value="50")
        
        for text, value in [("30期", "30"), ("50期", "50"), ("100期", "100")]:
            radio = ctk.CTkRadioButton(
                period_frame, text=text, variable=self.chart_period_var, value=value
            )
            radio.pack(side="left", padx=(0, 10))
        
        # 生成按钮
        start_btn = ctk.CTkButton(
            settings_frame,
            text="📉 生成走势图",
            command=self.run_trend_chart,
            fg_color="#1890FF",
            hover_color="#40A9FF",
            height=40
        )
        start_btn.pack(fill="x", pady=10)
        
        # 图表显示区域
        self.chart_frame = ctk.CTkFrame(parent)
        self.chart_frame.pack(fill="both", expand=True, pady=10, padx=10)
    
    def create_report_demo(self, parent):
        """创建预测报告演示 - 支持所有彩种"""
        from lottery_type_manager import LotteryTypeManager
        
        # 报告设置
        settings_frame = ctk.CTkFrame(parent)
        settings_frame.pack(fill="x", pady=10, padx=10)
        
        settings_label = ctk.CTkLabel(
            settings_frame,
            text="预测报告设置",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        settings_label.pack(anchor="w", pady=(10, 5))
        
        # 彩票类型选择
        type_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        type_frame.pack(fill="x", pady=5)
        
        type_label = ctk.CTkLabel(type_frame, text="彩票类型:")
        type_label.pack(side="left", padx=(0, 10))
        
        categories = LotteryTypeManager.get_categories()
        type_options = []
        for category, types in categories.items():
            for t in types:
                name = LotteryTypeManager.get_name(t)
                type_options.append(f"{name} ({t})")
        
        self.lottery_type_var = ctk.StringVar(value="双色球 (ssq)")
        
        type_dropdown = ctk.CTkOptionMenu(
            type_frame,
            values=type_options,
            variable=self.lottery_type_var,
            width=200,
            height=28
        )
        type_dropdown.pack(side="left")
        
        generate_btn = ctk.CTkButton(
            settings_frame,
            text="📋 生成详细报告",
            command=self.generate_report,
            fg_color="#1890FF",
            hover_color="#40A9FF",
            height=40
        )
        generate_btn.pack(fill="x", pady=10)
        
        # 报告显示区域
        report_frame = ctk.CTkFrame(parent)
        report_frame.pack(fill="both", expand=True, pady=10, padx=10)
        
        self.report_text = ctk.CTkTextbox(report_frame)
        self.report_text.pack(fill="both", expand=True)
        
        # 导出按钮
        export_frame = ctk.CTkFrame(parent, fg_color="transparent")
        export_frame.pack(fill="x", pady=10)
        
        for format_type, format_name in [("txt", "TXT格式"), ("pdf", "PDF格式")]:
            btn = ctk.CTkButton(
                export_frame,
                text=f"📄 导出为{format_name}",
                command=lambda f=format_type: self.export_report(f),
                width=120,
                height=35
            )
            btn.pack(side="left", padx=5)
    
    def create_export_demo(self, parent):
        """创建高级导出演示"""
        # 导出设置
        settings_frame = ctk.CTkFrame(parent)
        settings_frame.pack(fill="x", pady=10, padx=10)
        
        settings_label = ctk.CTkLabel(
            settings_frame,
            text="高级导出设置",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        settings_label.pack(anchor="w", pady=(10, 5))
        
        export_label = ctk.CTkLabel(
            settings_frame,
            text="选择导出格式:",
            font=ctk.CTkFont(size=12)
        )
        export_label.pack(anchor="w", pady=5)
        
        # 格式选择
        formats_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        formats_frame.pack(fill="x", pady=5)
        
        export_formats = [
            ("JSON", "json", "结构化数据格式"),
            ("CSV", "csv", "表格数据格式"),
            ("Excel", "excel", "电子表格格式"),
            ("TXT", "txt", "纯文本格式")
        ]
        
        for name, value, desc in export_formats:
            format_frame = ctk.CTkFrame(formats_frame, fg_color="transparent")
            format_frame.pack(fill="x", pady=2)
            
            btn = ctk.CTkButton(
                format_frame,
                text=f"📑 {name}",
                command=lambda v=value: self.export_data(v),
                width=100,
                height=30
            )
            btn.pack(side="left", padx=(0, 10))
            
            desc_label = ctk.CTkLabel(format_frame, text=desc, font=ctk.CTkFont(size=10))
            desc_label.pack(side="left")
        
        # 说明
        info_frame = ctk.CTkFrame(parent, fg_color="#F0F9FF")
        info_frame.pack(fill="x", pady=10, padx=10)
        
        info_text = """
💡 导出说明:
• JSON格式 - 适合程序处理和数据分析
• CSV格式 - 适合Excel和表格软件打开
• Excel格式 - 适合复杂数据和多表格
• TXT格式 - 适合文本编辑和打印
        """
        
        info_label = ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=ctk.CTkFont(size=11),
            text_color="#666",
            justify="left"
        )
        info_label.pack(pady=15, padx=10)
    
    # ==================== 功能执行方法 ====================
    
    def run_prediction(self, algorithm_type):
        """运行预测 - 支持所有彩种"""
        # 从下拉菜单值中提取彩票代码 (如 "双色球 (ssq)" -> "ssq")
        lottery_type_full = self.lottery_type_var.get()
        lottery_type = lottery_type_full.split("(")[-1].rstrip(")")
        
        count = int(self.count_var.get())
        
        # 显示加载状态
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", f"🔄 正在使用 {lottery_type_full} 生成预测结果，请稍候...\n")
        self.dialog.update()
        
        # 模拟处理时间
        time.sleep(1)
        
        # 调用对应算法
        try:
            if algorithm_type == "basic":
                results = self.vip_impl.basic_prediction(lottery_type, count)
            elif algorithm_type == "advanced":
                results = self.vip_impl.advanced_prediction(lottery_type, count)
            elif algorithm_type == "expert":
                results = self.vip_impl.expert_prediction(lottery_type, count)
            elif algorithm_type == "vip":
                results = self.vip_impl.vip_prediction(lottery_type, count)
            else:  # ultimate
                results = self.vip_impl.ultimate_prediction(lottery_type, count)
            
            # 显示结果
            self._display_prediction_results(results, algorithm_type)
            
        except Exception as e:
            self.result_text.delete("1.0", "end")
            self.result_text.insert("1.0", f"❌ 预测失败: {str(e)}\n")
    
    def _display_prediction_results(self, results, algorithm_type):
        """显示预测结果 - 通用格式支持所有彩种"""
        algo_names = {
            "basic": "基础算法",
            "advanced": "高级算法",
            "expert": "专家算法",
            "vip": "VIP算法",
            "ultimate": "至尊算法"
        }
        algo_name = algo_names.get(algorithm_type, algorithm_type)
        
        self.result_text.delete("1.0", "end")
        
        # 获取彩票类型名称
        lottery_name = results[0].get('lottery_name', '未知') if results else '未知'
        
        self.result_text.insert("1.0", f"🎯 {algo_name} - {lottery_name} 预测结果\n")
        self.result_text.insert("end", "=" * 50 + "\n\n")
        
        for i, result in enumerate(results, 1):
            self.result_text.insert("end", f"【预测组 {i}】\n")
            
            # 显示格式化后的号码
            formatted = result.get('formatted', 'N/A')
            self.result_text.insert("end", f"号码: {formatted}\n")
            
            # 显示置信度
            confidence = result.get('confidence', 0)
            self.result_text.insert("end", f"置信度: {confidence:.1%}\n")
            
            # 显示算法信息
            algo = result.get('algorithm', algo_name)
            self.result_text.insert("end", f"算法: {algo}\n")
            
            # 显示分析说明（如果有）
            if 'analysis' in result:
                self.result_text.insert("end", f"分析: {result['analysis']}\n")
            
            self.result_text.insert("end", "-" * 40 + "\n")
    
    def run_batch_prediction(self):
        """运行批量预测 - 支持所有彩种"""
        # 获取彩票类型
        lottery_type_full = self.lottery_type_var.get() if hasattr(self, 'lottery_type_var') else "双色球 (ssq)"
        lottery_type = lottery_type_full.split("(")[-1].rstrip(")")
        
        periods = int(self.period_var.get())
        algorithm = self.algo_var.get()
        
        self.batch_result_text.delete("1.0", "end")
        self.batch_result_text.insert("1.0", f"🔄 正在生成 {lottery_type_full} 批量预测，请稍候...\n")
        self.dialog.update()
        
        # 模拟处理
        time.sleep(2)
        
        try:
            result = self.vip_impl.batch_prediction(lottery_type, periods, algorithm)
            
            # 显示结果
            self.batch_result_text.delete("1.0", "end")
            self.batch_result_text.insert("1.0", f"📊 {result['lottery_name']} 批量预测结果 ({periods}期)\n")
            self.batch_result_text.insert("end", "=" * 50 + "\n\n")
            
            for pred in result['predictions']:
                self.batch_result_text.insert("end", f"期数{pred['period']}: {pred['expected_date']}\n")
                prediction = pred['prediction']
                formatted = prediction.get('formatted', 'N/A')
                self.batch_result_text.insert("end", f"  号码: {formatted}\n")
                self.batch_result_text.insert("end", f"  置信度: {prediction.get('confidence', 0):.1%}\n")
                self.batch_result_text.insert("end", "-" * 40 + "\n")
                
        except Exception as e:
            self.batch_result_text.delete("1.0", "end")
            self.batch_result_text.insert("1.0", f"❌ 批量预测失败: {str(e)}\n")
    
    def run_history_analysis(self):
        """运行历史分析 - 支持所有彩种"""
        # 获取彩票类型
        lottery_type_full = self.lottery_type_var.get() if hasattr(self, 'lottery_type_var') else "双色球 (ssq)"
        lottery_type = lottery_type_full.split("(")[-1].rstrip(")")
        
        periods = int(self.analysis_period_var.get())
        
        # 清除旧结果
        for widget in self.analysis_result_frame.winfo_children():
            widget.destroy()
        
        # 执行分析
        analysis = self.vip_impl.historical_analysis(lottery_type, periods)
        
        # 显示彩票名称
        name_label = ctk.CTkLabel(
            self.analysis_result_frame,
            text=f"📊 {analysis['lottery_name']} 历史分析 ({periods}期)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#1890FF"
        )
        name_label.pack(anchor="w", pady=(10, 5), padx=10)
        
        # 显示结果
        sections = [
            ("📊 频率分析", analysis['frequency']),
            ("📈 间隔分析", analysis['gap_analysis']),
            ("🔥 热冷号分析", analysis['hot_cold']),
            ("❄️ 遗漏分析", analysis['missing'])
        ]
        
        for title, data in sections:
            section_frame = ctk.CTkFrame(self.analysis_result_frame)
            section_frame.pack(fill="x", pady=5)
            
            title_label = ctk.CTkLabel(
                section_frame,
                text=title,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#1890FF"
            )
            title_label.pack(anchor="w", pady=(5, 3), padx=10)
            
            data_text = str(data)
            data_label = ctk.CTkLabel(
                section_frame,
                text=data_text,
                font=ctk.CTkFont(size=10),
                text_color="#666",
                justify="left"
            )
            data_label.pack(anchor="w", pady=(0, 5), padx=10)
    
    def run_trend_chart(self):
        """生成走势图 - 支持所有彩种"""
        # 获取彩票类型
        lottery_type_full = self.lottery_type_var.get() if hasattr(self, 'lottery_type_var') else "双色球 (ssq)"
        lottery_type = lottery_type_full.split("(")[-1].rstrip(")")
        
        periods = int(self.chart_period_var.get())
        
        # 清除旧图表
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        try:
            # 生成图表
            fig = self.vip_impl.generate_trend_chart(lottery_type, periods)
            
            # 嵌入到Tkinter
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
        except Exception as e:
            error_label = ctk.CTkLabel(
                self.chart_frame,
                text=f"❌ 生成走势图失败: {str(e)}",
                text_color="#FF6B35"
            )
            error_label.pack(pady=20)
    
    def generate_report(self):
        """生成报告 - 支持所有彩种"""
        # 获取彩票类型
        lottery_type_full = self.lottery_type_var.get() if hasattr(self, 'lottery_type_var') else "双色球 (ssq)"
        lottery_type = lottery_type_full.split("(")[-1].rstrip(")")
        
        try:
            # 先生成预测结果
            prediction = self.vip_impl.vip_prediction(lottery_type, 1)[0]
            
            # 生成报告
            report = self.vip_impl.generate_prediction_report(prediction)
            
            # 显示报告
            self.report_text.delete("1.0", "end")
            self.report_text.insert("1.0", report)
        except Exception as e:
            self.report_text.delete("1.0", "end")
            self.report_text.insert("1.0", f"❌ 生成报告失败: {str(e)}\n")
    
    def export_prediction_result(self):
        """导出预测结果"""
        result_text = self.result_text.get("1.0", "end").strip()
        if not result_text:
            messagebox.showwarning("导出失败", "没有预测结果可导出")
            return
        
        filename = filedialog.asksaveasfilename(
            title="导出预测结果",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(result_text)
            messagebox.showinfo("导出成功", f"结果已保存到：{filename}")
    
    def export_report(self, format_type):
        """导出报告"""
        report_text = self.report_text.get("1.0", "end").strip()
        if not report_text or "=" not in report_text:
            messagebox.showwarning("导出失败", "请先生成预测报告")
            return
        
        filename = self.vip_impl.advanced_export({"report": report_text}, "txt")
        messagebox.showinfo("导出成功", f"报告已导出为：{filename}")
    
    def export_data(self, format_type):
        """导出数据"""
        # 示例数据
        data = {
            "lottery_type": "ssq",
            "predictions": 5,
            "algorithm": "vip",
            "generated_at": "2024-01-01"
        }
        
        filename = self.vip_impl.advanced_export(data, format_type)
        messagebox.showinfo("导出成功", f"数据已导出为：{filename}")
    
    def run_demo(self):
        """运行默认演示"""
        messagebox.showinfo("功能演示", "该功能的具体演示正在开发中...")
    
    def on_upgrade(self):
        """升级会员"""
        messagebox.showinfo("升级会员", "请联系客服升级会员以解锁此功能")
        self.on_close()
    
    def on_close(self):
        """关闭对话框"""
        self.dialog.destroy()


# 测试代码
if __name__ == "__main__":
    import tkinter as tk
    from vip_feature_implementation import VIPFeatureImplementation
    
    root = tk.Tk()
    root.title("测试")
    root.geometry("400x300")
    
    vip_impl = VIPFeatureImplementation()
    
    def show_demo():
        dialog = VIPFeatureDetailDialog(
            root, "advanced_prediction", vip_impl, "monthly", True
        )
    
    btn = ctk.CTkButton(root, text="显示功能详情", command=show_demo)
    btn.pack(pady=50)
    
    root.mainloop()
