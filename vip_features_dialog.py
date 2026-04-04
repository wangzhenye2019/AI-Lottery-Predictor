# -*- coding: utf-8 -*-
"""
VIP特权功能对话框
Author: BigCat
"""

import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
from typing import Dict, List
from vip_feature_manager import VIPFeatureManager, MembershipLevel
from vip_feature_implementation import VIPFeatureImplementation
from vip_feature_detail_dialog import VIPFeatureDetailDialog


class VIPFeaturesDialog:
    """VIP特权功能对话框"""
    
    def __init__(self, parent, vip_manager: VIPFeatureManager, 
                 is_premium: bool, days: int = None, trial_manager=None):
        self.parent = parent
        self.vip_manager = vip_manager
        self.trial_manager = trial_manager
        
        # 初始化VIP功能实现
        self.vip_impl = VIPFeatureImplementation()
        
        # 获取用户VIP等级
        self.user_level = self.vip_manager.get_user_level(is_premium, days)
        self.level_config = self.vip_manager.get_level_config(self.user_level)
        
        # 创建对话框窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"{self.level_config['badge']} VIP特权中心")
        
        # 获取屏幕尺寸并计算窗口大小和位置
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        
        window_width = 700
        window_height = 600
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        
        # 创建界面
        self.create_ui()
        
        # 绑定关闭事件
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_ui(self):
        """创建界面"""
        # 主框架
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 标题区域
        title_frame = ctk.CTkFrame(main_frame, fg_color=self.level_config['bg_color'])
        title_frame.pack(fill="x", pady=(0, 20))
        
        # VIP等级标识
        level_badge = ctk.CTkLabel(
            title_frame,
            text=f"{self.level_config['badge']}",
            font=ctk.CTkFont(size=40),
            text_color=self.level_config['color']
        )
        level_badge.pack(pady=(15, 5))
        
        # 等级名称
        level_name = ctk.CTkLabel(
            title_frame,
            text=self.level_config['name'],
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.level_config['color']
        )
        level_name.pack()
        
        # 功能数量
        features = self.vip_manager.get_available_features(self.user_level)
        feature_count = ctk.CTkLabel(
            title_frame,
            text=f"尊享 {len(features)} 项特权功能",
            font=ctk.CTkFont(size=12),
            text_color="#666"
        )
        feature_count.pack(pady=(5, 15))
        
        # 功能列表区域
        features_frame = ctk.CTkScrollableFrame(main_frame)
        features_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # 按类别显示功能
        categories = self.vip_manager.get_features_by_category(self.user_level)
        
        category_names = {
            "prediction": "🎯 预测功能",
            "analysis": "📊 分析功能", 
            "export": "📄 导出功能",
            "service": "🎁 服务功能",
            "exclusive": "👑 专属特权"
        }
        
        for category, category_features in categories.items():
            if category_features:
                # 类别标题
                category_frame = ctk.CTkFrame(features_frame, fg_color="transparent")
                category_frame.pack(fill="x", pady=(10, 5))
                
                category_label = ctk.CTkLabel(
                    category_frame,
                    text=category_names.get(category, category),
                    font=ctk.CTkFont(size=14, weight="bold"),
                    text_color="#333"
                )
                category_label.pack(anchor="w")
                
                # 功能列表
                for feature in category_features:
                    self.create_feature_item(features_frame, feature)
        
        # 底部按钮区域
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))
        
        # 升级按钮（如果不是永久会员）
        if self.user_level != MembershipLevel.LIFETIME:
            upgrade_btn = ctk.CTkButton(
                button_frame,
                text="🚀 升级会员",
                command=self.on_upgrade,
                fg_color="#FFD700",
                hover_color="#FFC107",
                text_color="#333",
                height=40
            )
            upgrade_btn.pack(side="left", padx=(0, 10))
        
        # 关闭按钮
        close_btn = ctk.CTkButton(
            button_frame,
            text="关闭",
            command=self.on_close,
            fg_color="#E0E0E0",
            hover_color="#BDBDBD",
            text_color="#333",
            height=40
        )
        close_btn.pack(side="right")
    
    def create_feature_item(self, parent, feature):
        """创建功能项"""
        # 检查用户是否有权限使用此功能
        is_available = self.vip_manager.check_feature_access(
            feature.feature_id, self.user_level
        )
        
        # 根据权限设置不同的背景色
        bg_color = "transparent" if is_available else "#FFF7ED"
        
        item_frame = ctk.CTkFrame(parent, fg_color=bg_color)
        item_frame.pack(fill="x", pady=2)
        
        # 功能图标
        icon_label = ctk.CTkLabel(
            item_frame,
            text=feature.icon,
            font=ctk.CTkFont(size=16)
        )
        icon_label.pack(side="left", padx=(10, 5))
        
        # 功能信息
        info_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, padx=5)
        
        # 功能名称
        name_label = ctk.CTkLabel(
            info_frame,
            text=feature.name,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#333" if is_available else "#999"
        )
        name_label.pack(anchor="w")
        
        # 功能描述
        desc_label = ctk.CTkLabel(
            info_frame,
            text=feature.description,
            font=ctk.CTkFont(size=10),
            text_color="#666" if is_available else "#999"
        )
        desc_label.pack(anchor="w")
        
        # 右侧按钮/标识
        if is_available:
            # 有权限，显示"立即体验"按钮
            try_btn = ctk.CTkButton(
                item_frame,
                text="▶️ 体验",
                command=lambda f=feature: self.on_try_feature(f),
                fg_color="#1890FF",
                hover_color="#40A9FF",
                width=70,
                height=25,
                font=ctk.CTkFont(size=9)
            )
            try_btn.pack(side="right", padx=10)
        else:
            # 无权限，显示锁定标识
            lock_label = ctk.CTkLabel(
                item_frame,
                text="🔒",
                font=ctk.CTkFont(size=14),
                text_color="#FF6B35"
            )
            lock_label.pack(side="right", padx=10)
        
        # 专属标识
        if feature.is_exclusive:
            exclusive_label = ctk.CTkLabel(
                item_frame,
                text="👑 专属",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="#FFD700"
            )
            exclusive_label.pack(side="right", padx=5)
    
    def on_try_feature(self, feature):
        """点击体验功能"""
        # 打开功能详情对话框
        detail_dialog = VIPFeatureDetailDialog(
            self.dialog,
            feature.feature_id,
            self.vip_impl,
            self.user_level,
            True  # 有权限
        )
    
    def on_upgrade(self):
        """升级会员"""
        self.on_close()
        # 触发付费对话框
        if self.trial_manager and hasattr(self.parent, 'on_payment_click'):
            self.parent.on_payment_click()
    
    def on_close(self):
        """关闭对话框"""
        self.dialog.destroy()


# 简单测试
if __name__ == "__main__":
    import tkinter as tk
    
    root = tk.Tk()
    root.title("测试")
    root.geometry("400x300")
    
    vip_manager = VIPFeatureManager()
    
    def show_vip():
        dialog = VIPFeaturesDialog(root, vip_manager, True, None)
    
    btn = ctk.CTkButton(root, text="显示VIP特权", command=show_vip)
    btn.pack(pady=50)
    
    root.mainloop()
