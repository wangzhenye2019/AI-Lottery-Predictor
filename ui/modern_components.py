# -*- coding: utf-8 -*-
"""
现代化的UI组件库
Author: BigCat
"""
import customtkinter as ctk
from typing import Dict, Any, Optional, Callable, Tuple
from config_new import config
from utils.logger_new import get_logger

logger = get_logger(__name__)


class ModernTheme:
    """现代化主题配置"""
    
    # 颜色配置
    COLORS = {
        # 基础颜色
        "bg": ("#F8FAFC", "#0A0E1A"),  # 浅色/深色背景
        "card": ("#FFFFFF", "#111827"),  # 卡片背景
        "border": ("#E2E8F0", "#1F2937"),  # 边框
        
        # 文字颜色
        "text": ("#1E293B", "#F3F4F6"),  # 主文字
        "subtext": ("#64748B", "#9CA3AF"),  # 副文字
        "muted": ("#94A3B8", "#6B7280"),  # 静音文字
        
        # 主题色
        "primary": ("#3B82F6", "#3B82F6"),  # 主色
        "primary_hover": ("#2563EB", "#2563EB"),  # 主色悬停
        "primary_light": ("#EFF6FF", "#1E3A8A"),  # 主色浅色
        
        # 功能色
        "success": ("#10B981", "#10B981"),  # 成功
        "warning": ("#F59E0B", "#F59E0B"),  # 警告
        "danger": ("#EF4444", "#EF4444"),  # 危险
        "info": ("#06B6D4", "#06B6D4"),  # 信息
        
        # 彩票专用色
        "red_ball": ("#EF4444", "#EF4444"),  # 红球
        "blue_ball": ("#3B82F6", "#3B82F6"),  # 蓝球
        
        # 状态色
        "hot": ("#EF4444", "#EF4444"),  # 热号
        "warm": ("#A78BFA", "#A78BFA"),  # 温号
        "cold": ("#3B82F6", "#3B82F6"),  # 冷号
    }
    
    # 尺寸配置
    SIZES = {
        "radius_small": 8,
        "radius_medium": 12,
        "radius_large": 16,
        "radius_card": 20,
        "radius_input": 12,
        "radius_inset": 8,
        
        "gap_small": 8,
        "gap_medium": 16,
        "gap_large": 24,
        "gap_xlarge": 32,
        
        "pad_small": 8,
        "pad_medium": 16,
        "pad_large": 24,
        "pad_card": 20,
        "pad_outer": 24,
        "pad_inner": 12,
        
        "height_small": 32,
        "height_medium": 40,
        "height_large": 48,
        "height_button": 48,
        
        "font_small": 12,
        "font_medium": 14,
        "font_large": 16,
        "font_xlarge": 18,
        "font_title": 20,
        "font_heading": 24,
    }
    
    @classmethod
    def get_color(cls, color_name: str, mode: str = None) -> str:
        """获取颜色"""
        if mode is None:
            mode = "dark" if config.ui.theme == "dark" else "light"
        
        colors = cls.COLORS.get(color_name, ("#000000", "#FFFFFF"))
        if isinstance(colors, tuple):
            return colors[0] if mode == "light" else colors[1]
        return colors
    
    @classmethod
    def get_size(cls, size_name: str) -> int:
        """获取尺寸"""
        return cls.SIZES.get(size_name, 16)


class ModernCard(ctk.CTkFrame):
    """现代化卡片组件"""
    
    def __init__(self, parent, **kwargs):
        # 默认参数
        default_kwargs = {
            "fg_color": ModernTheme.get_color("card"),
            "border_width": 1,
            "border_color": ModernTheme.get_color("border"),
            "corner_radius": ModernTheme.get_size("radius_card"),
        }
        default_kwargs.update(kwargs)
        
        super().__init__(parent, **default_kwargs)


class ModernButton(ctk.CTkButton):
    """现代化按钮组件"""
    
    def __init__(self, parent, style: str = "primary", **kwargs):
        # 样式配置
        style_config = {
            "primary": {
                "fg_color": ModernTheme.get_color("primary"),
                "hover_color": ModernTheme.get_color("primary_hover"),
                "text_color": "#FFFFFF",
            },
            "success": {
                "fg_color": ModernTheme.get_color("success"),
                "hover_color": "#059669",
                "text_color": "#FFFFFF",
            },
            "danger": {
                "fg_color": ModernTheme.get_color("danger"),
                "hover_color": "#DC2626",
                "text_color": "#FFFFFF",
            },
            "outline": {
                "fg_color": "transparent",
                "hover_color": ModernTheme.get_color("primary_light"),
                "border_width": 2,
                "border_color": ModernTheme.get_color("primary"),
                "text_color": ModernTheme.get_color("primary"),
            },
            "ghost": {
                "fg_color": "transparent",
                "hover_color": ModernTheme.get_color("primary_light"),
                "text_color": ModernTheme.get_color("primary"),
            }
        }
        
        config = style_config.get(style, style_config["primary"])
        
        # 默认参数
        default_kwargs = {
            "height": ModernTheme.get_size("height_button"),
            "corner_radius": ModernTheme.get_size("radius_input"),
            "font": ctk.CTkFont(size=ModernTheme.get_size("font_medium"), weight="bold"),
        }
        default_kwargs.update(config)
        default_kwargs.update(kwargs)
        
        super().__init__(parent, **default_kwargs)


class ModernInput(ctk.CTkEntry):
    """现代化输入框组件"""
    
    def __init__(self, parent, **kwargs):
        default_kwargs = {
            "height": ModernTheme.get_size("height_medium"),
            "corner_radius": ModernTheme.get_size("radius_input"),
            "border_width": 1,
            "border_color": ModernTheme.get_color("border"),
            "font": ctk.CTkFont(size=ModernTheme.get_size("font_medium")),
        }
        default_kwargs.update(kwargs)
        
        super().__init__(parent, **default_kwargs)


class ModernLabel(ctk.CTkLabel):
    """现代化标签组件"""
    
    def __init__(self, parent, style: str = "body", **kwargs):
        # 样式配置
        style_config = {
            "heading": {
                "font": ctk.CTkFont(size=ModernTheme.get_size("font_heading"), weight="bold"),
                "text_color": ModernTheme.get_color("text"),
            },
            "title": {
                "font": ctk.CTkFont(size=ModernTheme.get_size("font_title"), weight="bold"),
                "text_color": ModernTheme.get_color("text"),
            },
            "body": {
                "font": ctk.CTkFont(size=ModernTheme.get_size("font_medium")),
                "text_color": ModernTheme.get_color("text"),
            },
            "caption": {
                "font": ctk.CTkFont(size=ModernTheme.get_size("font_small")),
                "text_color": ModernTheme.get_color("subtext"),
            },
            "muted": {
                "font": ctk.CTkFont(size=ModernTheme.get_size("font_small")),
                "text_color": ModernTheme.get_color("muted"),
            }
        }
        
        config = style_config.get(style, style_config["body"])
        default_kwargs = kwargs
        default_kwargs.update(config)
        
        super().__init__(parent, **default_kwargs)


class ModernProgressBar(ctk.CTkProgressBar):
    """现代化进度条组件"""
    
    def __init__(self, parent, **kwargs):
        default_kwargs = {
            "height": 12,
            "corner_radius": ModernTheme.get_size("radius_small"),
        }
        default_kwargs.update(kwargs)
        
        super().__init__(parent, **default_kwargs)
        
        # 设置颜色
        try:
            self.configure(
                progress_color=ModernTheme.get_color("primary"),
                fg_color=ModernTheme.get_color("border")
            )
        except Exception:
            pass


class ModernScrollableFrame(ctk.CTkScrollableFrame):
    """现代化滚动框架组件"""
    
    def __init__(self, parent, **kwargs):
        default_kwargs = {
            "fg_color": "transparent",
            "corner_radius": ModernTheme.get_size("radius_card"),
            "border_width": 1,
            "border_color": ModernTheme.get_color("border"),
        }
        default_kwargs.update(kwargs)
        
        super().__init__(parent, **default_kwargs)


class BallDisplay(ctk.CTkFrame):
    """彩票号码显示组件"""
    
    def __init__(self, parent, numbers: list, ball_type: str = "red", **kwargs):
        self.numbers = numbers
        self.ball_type = ball_type
        
        # 设置颜色
        if ball_type == "red":
            color = ModernTheme.get_color("red_ball")
        elif ball_type == "blue":
            color = ModernTheme.get_color("blue_ball")
        else:
            color = ModernTheme.get_color("primary")
        
        default_kwargs = {
            "fg_color": "transparent",
        }
        default_kwargs.update(kwargs)
        
        super().__init__(parent, **default_kwargs)
        
        self._create_balls(color)
    
    def _create_balls(self, color: str):
        """创建号码球"""
        for i, number in enumerate(self.numbers):
            ball_frame = ctk.CTkFrame(
                self,
                fg_color=color,
                corner_radius=20,
                width=40,
                height=40
            )
            ball_frame.grid(row=0, column=i, padx=4)
            ball_frame.grid_propagate(False)
            
            label = ctk.CTkLabel(
                ball_frame,
                text=str(number),
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#FFFFFF"
            )
            label.pack(expand=True)


class StatusIndicator(ctk.CTkFrame):
    """状态指示器组件"""
    
    def __init__(self, parent, status: str = "running", **kwargs):
        self.status = status
        
        # 状态配置
        status_config = {
            "running": {"color": ModernTheme.get_color("success"), "text": "运行中"},
            "stopped": {"color": ModernTheme.get_color("danger"), "text": "已停止"},
            "warning": {"color": ModernTheme.get_color("warning"), "text": "警告"},
            "idle": {"color": ModernTheme.get_color("muted"), "text": "空闲"},
        }
        
        config = status_config.get(status, status_config["idle"])
        
        default_kwargs = {
            "fg_color": "transparent",
        }
        default_kwargs.update(kwargs)
        
        super().__init__(parent, **default_kwargs)
        
        # 创建指示器
        self._create_indicator(config["color"], config["text"])
    
    def _create_indicator(self, color: str, text: str):
        """创建状态指示器"""
        # 状态点
        dot = ctk.CTkLabel(
            self,
            text="●",
            font=ctk.CTkFont(size=16),
            text_color=color
        )
        dot.grid(row=0, column=0, padx=(0, 6))
        
        # 状态文字
        label = ctk.CTkLabel(
            self,
            text=text,
            font=ctk.CTkFont(size=ModernTheme.get_size("font_small")),
            text_color=ModernTheme.get_color("subtext")
        )
        label.grid(row=0, column=1)
    
    def update_status(self, status: str):
        """更新状态"""
        self.status = status
        
        # 清空现有组件
        for widget in self.winfo_children():
            widget.destroy()
        
        # 重新创建指示器
        status_config = {
            "running": {"color": ModernTheme.get_color("success"), "text": "运行中"},
            "stopped": {"color": ModernTheme.get_color("danger"), "text": "已停止"},
            "warning": {"color": ModernTheme.get_color("warning"), "text": "警告"},
            "idle": {"color": ModernTheme.get_color("muted"), "text": "空闲"},
        }
        
        config = status_config.get(status, status_config["idle"])
        self._create_indicator(config["color"], config["text"])


class StatsCard(ModernCard):
    """统计卡片组件"""
    
    def __init__(self, parent, title: str, value: str, subtitle: str = None, **kwargs):
        default_kwargs = {
            "fg_color": ModernTheme.get_color("card"),
        }
        default_kwargs.update(kwargs)
        
        super().__init__(parent, **default_kwargs)
        
        self._create_content(title, value, subtitle)
    
    def _create_content(self, title: str, value: str, subtitle: str = None):
        """创建内容"""
        # 标题
        title_label = ModernLabel(
            self,
            text=title,
            style="caption"
        )
        title_label.grid(row=0, column=0, sticky="w", padx=ModernTheme.get_size("pad_card"), pady=(ModernTheme.get_size("pad_card"), 4))
        
        # 数值
        value_label = ModernLabel(
            self,
            text=value,
            style="title"
        )
        value_label.grid(row=1, column=0, sticky="w", padx=ModernTheme.get_size("pad_card"), pady=(0, 4))
        
        # 副标题
        if subtitle:
            subtitle_label = ModernLabel(
                self,
                text=subtitle,
                style="muted"
            )
            subtitle_label.grid(row=2, column=0, sticky="w", padx=ModernTheme.get_size("pad_card"), pady=(0, ModernTheme.get_size("pad_card")))


class HeatmapCanvas(ctk.CTkCanvas):
    """热力图画布组件"""
    
    def __init__(self, parent, **kwargs):
        default_kwargs = {
            "highlightthickness": 0,
            "bg": ModernTheme.get_color("card"),
        }
        default_kwargs.update(kwargs)
        
        super().__init__(parent, **default_kwargs)
        
        self.heatmap_data = {}
        self.cell_size = 30
        self.padding = 20
    
    def draw_heatmap(self, data: Dict[int, int], max_value: int = None):
        """绘制热力图"""
        self.delete("all")
        
        if not data:
            return
        
        # 计算最大值
        if max_value is None:
            max_value = max(data.values()) if data else 1
        
        # 绘制热力图
        for number, frequency in data.items():
            # 计算颜色
            ratio = frequency / max_value if max_value > 0 else 0
            
            if ratio >= 0.6:
                color = ModernTheme.get_color("hot")
            elif ratio >= 0.3:
                color = ModernTheme.get_color("warm")
            else:
                color = ModernTheme.get_color("cold")
            
            # 计算位置
            row = (number - 1) // 10
            col = (number - 1) % 10
            
            x = self.padding + col * self.cell_size
            y = self.padding + row * self.cell_size
            
            # 绘制方块
            self.create_rectangle(
                x, y,
                x + self.cell_size - 2,
                y + self.cell_size - 2,
                fill=color,
                outline=ModernTheme.get_color("border")
            )
            
            # 绘制数字
            self.create_text(
                x + self.cell_size // 2,
                y + self.cell_size // 2,
                text=str(number),
                fill="#FFFFFF",
                font=("Arial", 10, "bold")
            )
    
    def get_cell_position(self, number: int) -> Tuple[int, int]:
        """获取号码位置"""
        row = (number - 1) // 10
        col = (number - 1) % 10
        
        x = self.padding + col * self.cell_size + self.cell_size // 2
        y = self.padding + row * self.cell_size + self.cell_size // 2
        
        return x, y
