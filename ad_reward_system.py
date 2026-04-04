# -*- coding: utf-8 -*-
"""
广告奖励系统
Author: BigCat
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import hashlib


class AdRewardSystem:
    """广告奖励系统"""
    
    def __init__(self, config_file='ad_config.json'):
        self.config_file = config_file
        self.config = self._load_config()
        
        # 广告配置
        self.ad_config = {
            'daily_limit': 5,              # 每日广告观看上限
            'reward_per_ad': 2,            # 每次广告获得的次数
            'cooldown_seconds': 300,       # 广告间隔冷却时间（5分钟）
            'ad_duration_seconds': 30,       # 广告播放时长（30秒）
            'double_reward_chance': 0.1    # 双倍奖励概率（10%）
        }
    
    def _load_config(self) -> Dict:
        """加载配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            'total_ads_watched': 0,
            'total_rewards_earned': 0,
            'daily_records': {},
            'last_ad_time': None,
            'ad_history': []
        }
    
    def _save_config(self):
        """保存配置"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
    
    def get_today_key(self) -> str:
        """获取今天的日期键"""
        return datetime.now().strftime('%Y-%m-%d')
    
    def get_today_stats(self) -> Dict:
        """获取今日统计"""
        today_key = self.get_today_key()
        if today_key not in self.config['daily_records']:
            self.config['daily_records'][today_key] = {
                'ads_watched': 0,
                'rewards_earned': 0,
                'last_ad_time': None
            }
        return self.config['daily_records'][today_key]
    
    def can_watch_ad(self) -> Tuple[bool, str]:
        """检查是否可以观看广告"""
        today_stats = self.get_today_stats()
        
        # 检查每日上限
        if today_stats['ads_watched'] >= self.ad_config['daily_limit']:
            return False, f"今日广告次数已用完，明天再来吧！"
        
        # 检查冷却时间
        if today_stats['last_ad_time']:
            last_time = datetime.fromisoformat(today_stats['last_ad_time'])
            cooldown = timedelta(seconds=self.ad_config['cooldown_seconds'])
            next_available = last_time + cooldown
            
            if datetime.now() < next_available:
                remaining = next_available - datetime.now()
                minutes = int(remaining.total_seconds() // 60)
                seconds = int(remaining.total_seconds() % 60)
                return False, f"广告冷却中，{minutes}分{seconds}秒后可再次观看"
        
        return True, "可以观看广告"
    
    def watch_ad(self) -> Dict:
        """观看广告并获取奖励"""
        can_watch, message = self.can_watch_ad()
        
        if not can_watch:
            return {
                'success': False,
                'message': message,
                'rewards': 0
            }
        
        # 模拟广告观看过程
        # 实际应用中这里会调用广告SDK
        ad_result = self._simulate_ad_watch()
        
        if ad_result['completed']:
            # 计算奖励
            base_reward = self.ad_config['reward_per_ad']
            is_double = self._check_double_reward()
            total_reward = base_reward * (2 if is_double else 1)
            
            # 更新今日统计
            today_stats = self.get_today_stats()
            today_stats['ads_watched'] += 1
            today_stats['rewards_earned'] += total_reward
            today_stats['last_ad_time'] = datetime.now().isoformat()
            
            # 更新总统计
            self.config['total_ads_watched'] += 1
            self.config['total_rewards_earned'] += total_reward
            self.config['last_ad_time'] = datetime.now().isoformat()
            
            # 记录历史
            ad_record = {
                'timestamp': datetime.now().isoformat(),
                'reward': total_reward,
                'is_double': is_double,
                'ad_type': ad_result['ad_type']
            }
            self.config['ad_history'].append(ad_record)
            
            # 保存配置
            self._save_config()
            
            return {
                'success': True,
                'message': f"🎉 恭喜获得 {total_reward} 次免费预测！" + 
                          (" 双倍奖励！" if is_double else ""),
                'rewards': total_reward,
                'is_double': is_double,
                'ads_remaining': self.ad_config['daily_limit'] - today_stats['ads_watched']
            }
        else:
            return {
                'success': False,
                'message': "广告观看未完成，请重新尝试",
                'rewards': 0
            }
    
    def _simulate_ad_watch(self) -> Dict:
        """模拟广告观看"""
        import random
        
        ad_types = ['video', 'banner', 'interstitial', 'rewarded_video']
        
        return {
            'completed': True,
            'ad_type': random.choice(ad_types),
            'duration': self.ad_config['ad_duration_seconds']
        }
    
    def _check_double_reward(self) -> bool:
        """检查是否获得双倍奖励"""
        import random
        return random.random() < self.ad_config['double_reward_chance']
    
    def get_ad_status(self) -> Dict:
        """获取广告状态"""
        today_stats = self.get_today_stats()
        can_watch, message = self.can_watch_ad()
        
        return {
            'can_watch': can_watch,
            'message': message,
            'today_ads_watched': today_stats['ads_watched'],
            'daily_limit': self.ad_config['daily_limit'],
            'ads_remaining': self.ad_config['daily_limit'] - today_stats['ads_watched'],
            'reward_per_ad': self.ad_config['reward_per_ad'],
            'cooldown_seconds': self.ad_config['cooldown_seconds'],
            'total_ads_watched': self.config['total_ads_watched'],
            'total_rewards_earned': self.config['total_rewards_earned']
        }
    
    def get_reward_summary(self) -> str:
        """获取奖励摘要"""
        status = self.get_ad_status()
        
        summary = f"""
📺 广告奖励系统
═══════════════════════════════════════

今日状态：
• 已观看广告：{status['today_ads_watched']}/{status['daily_limit']} 次
• 剩余次数：{status['ads_remaining']} 次
• 每次奖励：{status['reward_per_ad']} 次预测

累计统计：
• 总观看广告：{status['total_ads_watched']} 次
• 总获得奖励：{status['total_rewards_earned']} 次预测

说明：
💡 每天可观看 {status['daily_limit']} 次广告
🎁 每次广告可获得 {status['reward_per_ad']} 次免费预测
⭐ 有 {int(self.ad_config['double_reward_chance']*100)}% 概率获得双倍奖励
⏰ 广告间隔需要等待 {self.ad_config['cooldown_seconds']//60} 分钟
"""
        return summary.strip()


class AdRewardDialog:
    """广告奖励对话框"""
    
    def __init__(self, parent, ad_system, trial_manager):
        self.parent = parent
        self.ad_system = ad_system
        self.trial_manager = trial_manager
        
        # 创建对话框窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("📺 看广告赚次数")
        
        # 获取屏幕尺寸并计算窗口大小和位置
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        
        window_width = 500
        window_height = 600
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.dialog.resizable(False, False)
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
        
        # 标题
        title_label = ctk.CTkLabel(
            main_frame,
            text="📺 看广告赚免费次数",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#1890FF"
        )
        title_label.pack(pady=(0, 20))
        
        # 状态显示
        self.status_frame = ctk.CTkFrame(main_frame, fg_color="#F0F9FF")
        self.status_frame.pack(fill="x", pady=(0, 20))
        
        self.update_status_display()
        
        # 广告观看区域
        ad_frame = ctk.CTkFrame(main_frame, fg_color="#FFF7ED")
        ad_frame.pack(fill="x", pady=(0, 20))
        
        ad_title = ctk.CTkLabel(
            ad_frame,
            text="🎬 观看广告",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#FF6B35"
        )
        ad_title.pack(pady=(15, 10))
        
        # 广告说明
        ad_info = ctk.CTkLabel(
            ad_frame,
            text="💡 观看30秒广告即可获得免费预测次数\n🎁 每次可获得2次免费预测\n⭐ 有10%概率获得双倍奖励（4次）",
            font=ctk.CTkFont(size=12),
            text_color=AntDesignColors.TEXT_SECONDARY,
            justify="center"
        )
        ad_info.pack(pady=(0, 15))
        
        # 观看广告按钮
        self.watch_btn = ctk.CTkButton(
            ad_frame,
            text="📺 观看广告",
            command=self.watch_ad,
            fg_color="#FF6B35",
            hover_color="#E55A2B",
            height=50
        )
        self.watch_btn.pack(fill="x", padx=20, pady=(0, 15))
        
        # 冷却时间显示
        self.cooldown_label = ctk.CTkLabel(
            ad_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=AntDesignColors.TEXT_SECONDARY
        )
        self.cooldown_label.pack(pady=(0, 10))
        
        # 规则说明
        rules_frame = ctk.CTkFrame(main_frame)
        rules_frame.pack(fill="x", pady=(0, 20))
        
        rules_title = ctk.CTkLabel(
            rules_frame,
            text="📋 活动规则",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=AntDesignColors.TEXT_PRIMARY
        )
        rules_title.pack(pady=(10, 5))
        
        rules_text = ctk.CTkLabel(
            rules_frame,
            text="• 每天最多可观看5次广告\n• 每次广告间隔需要等待5分钟\n• 广告时长约30秒\n• 奖励次数可以累积使用\n• 双倍奖励随机触发",
            font=ctk.CTkFont(size=11),
            text_color=AntDesignColors.TEXT_SECONDARY,
            justify="left"
        )
        rules_text.pack(pady=(0, 10), padx=15)
        
        # 按钮区域
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x")
        
        close_btn = ctk.CTkButton(
            button_frame,
            text="关闭",
            command=self.on_close,
            fg_color=AntDesignColors.BORDER,
            hover_color=AntDesignColors.TEXT_SECONDARY,
            text_color=AntDesignColors.TEXT_PRIMARY,
            height=40
        )
        close_btn.pack(pady=10)
    
    def update_status_display(self):
        """更新状态显示"""
        # 清除旧的状态显示
        for widget in self.status_frame.winfo_children():
            widget.destroy()
        
        status = self.ad_system.get_ad_status()
        
        # 今日进度
        progress_label = ctk.CTkLabel(
            self.status_frame,
            text=f"今日进度：{status['today_ads_watched']}/{status['daily_limit']} 次",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=AntDesignColors.TEXT_PRIMARY
        )
        progress_label.pack(pady=(10, 5))
        
        # 进度条
        progress_bar = ctk.CTkProgressBar(self.status_frame, width=300)
        progress_bar.pack(pady=(0, 10))
        progress_bar.set(status['today_ads_watched'] / status['daily_limit'])
        
        # 剩余次数
        remaining_label = ctk.CTkLabel(
            self.status_frame,
            text=f"剩余 {status['ads_remaining']} 次机会",
            font=ctk.CTkFont(size=12),
            text_color="#52C41A" if status['ads_remaining'] > 0 else AntDesignColors.TEXT_SECONDARY
        )
        remaining_label.pack(pady=(0, 10))
        
        # 更新按钮状态
        if not status['can_watch']:
            self.watch_btn.configure(state="disabled", text="⏰ 冷却中")
            self.cooldown_label.configure(text=status['message'])
        else:
            self.watch_btn.configure(state="normal", text="📺 观看广告")
            self.cooldown_label.configure(text="✅ 可以观看广告")
    
    def watch_ad(self):
        """观看广告"""
        # 模拟广告观看过程
        self.watch_btn.configure(state="disabled", text="▶️ 广告播放中...")
        self.dialog.update()
        
        # 模拟广告播放（实际应用中这里会调用广告SDK）
        import time
        time.sleep(3)  # 模拟3秒广告
        
        # 获取奖励
        result = self.ad_system.watch_ad()
        
        if result['success']:
            # 添加奖励到试用系统
            self.trial_manager.add_trial_attempts(result['rewards'])
            
            # 显示成功消息
            messagebox.showinfo(
                "获得奖励",
                f"{result['message']}\n\n您现在有 {self.trial_manager.get_remaining_attempts()} 次免费预测机会"
            )
        else:
            # 显示错误消息
            messagebox.showwarning(
                "观看失败",
                result['message']
            )
        
        # 更新状态显示
        self.update_status_display()
    
    def on_close(self):
        """关闭对话框"""
        self.dialog.destroy()


# 使用示例
if __name__ == "__main__":
    # 创建广告奖励系统
    ad_system = AdRewardSystem()
    
    # 打印状态
    print(ad_system.get_reward_summary())
    
    # 检查是否可以观看广告
    can_watch, message = ad_system.can_watch_ad()
    print(f"\n是否可以观看广告: {can_watch}")
    print(f"消息: {message}")
    
    # 模拟观看广告
    if can_watch:
        result = ad_system.watch_ad()
        print(f"\n广告观看结果:")
        print(f"成功: {result['success']}")
        print(f"消息: {result['message']}")
        print(f"获得奖励: {result['rewards']} 次")
        if result.get('is_double'):
            print("🎉 双倍奖励！")
