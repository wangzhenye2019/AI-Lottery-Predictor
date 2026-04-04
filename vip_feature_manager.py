# -*- coding: utf-8 -*-
"""
VIP功能管理系统
Author: BigCat
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class MembershipLevel(Enum):
    """会员等级"""
    TRIAL = "trial"           # 试用版
    MONTHLY = "monthly"       # 包月会员
    QUARTERLY = "quarterly"   # 季度会员
    YEARLY = "yearly"         # 年度会员
    LIFETIME = "lifetime"     # 永久会员


@dataclass
class VIPFeature:
    """VIP功能定义"""
    feature_id: str
    name: str
    description: str
    icon: str
    min_level: MembershipLevel
    is_exclusive: bool = False  # 是否专属功能


class VIPFeatureManager:
    """VIP功能管理器"""
    
    def __init__(self):
        # 定义所有VIP功能
        self.features = {
            # 基础功能（所有用户）
            "basic_prediction": VIPFeature(
                "basic_prediction", "基础预测", "使用基础算法进行预测",
                "🎯", MembershipLevel.TRIAL
            ),
            "single_lottery": VIPFeature(
                "single_lottery", "单种彩票", "每次只能预测一种彩票",
                "🎲", MembershipLevel.TRIAL
            ),
            "standard_export": VIPFeature(
                "standard_export", "标准导出", "导出结果为标准格式",
                "📄", MembershipLevel.TRIAL
            ),
            
            # 包月会员功能
            "advanced_algorithm": VIPFeature(
                "advanced_algorithm", "高级算法", "使用深度学习高级算法",
                "🧠", MembershipLevel.MONTHLY
            ),
            "batch_prediction": VIPFeature(
                "batch_prediction", "批量预测", "一次预测多期号码",
                "📊", MembershipLevel.MONTHLY
            ),
            "history_analysis": VIPFeature(
                "history_analysis", "历史分析", "查看历史数据分析",
                "📈", MembershipLevel.MONTHLY
            ),
            "trend_chart": VIPFeature(
                "trend_chart", "走势图", "查看号码走势图",
                "📉", MembershipLevel.MONTHLY
            ),
            
            # 季度会员功能
            "expert_algorithm": VIPFeature(
                "expert_algorithm", "专家算法", "使用专家级预测算法",
                "🏆", MembershipLevel.QUARTERLY
            ),
            "all_lottery_types": VIPFeature(
                "all_lottery_types", "全彩种", "支持所有彩票类型",
                "🎰", MembershipLevel.QUARTERLY
            ),
            "custom_strategy": VIPFeature(
                "custom_strategy", "自定义策略", "自定义预测策略",
                "⚙️", MembershipLevel.QUARTERLY
            ),
            "prediction_report": VIPFeature(
                "prediction_report", "预测报告", "生成详细预测报告",
                "📋", MembershipLevel.QUARTERLY
            ),
            "priority_support": VIPFeature(
                "priority_support", "优先支持", "客服优先响应",
                "🚀", MembershipLevel.QUARTERLY
            ),
            
            # 年度会员功能
            "vip_algorithm": VIPFeature(
                "vip_algorithm", "VIP算法", "使用VIP专属预测算法",
                "💎", MembershipLevel.YEARLY
            ),
            "realtime_data": VIPFeature(
                "realtime_data", "实时数据", "获取实时开奖数据",
                "⚡", MembershipLevel.YEARLY
            ),
            "winning_notification": VIPFeature(
                "winning_notification", "中奖提醒", "自动检查中奖结果",
                "🔔", MembershipLevel.YEARLY
            ),
            "advanced_export": VIPFeature(
                "advanced_export", "高级导出", "支持多种格式导出",
                "📑", MembershipLevel.YEARLY
            ),
            "cloud_sync": VIPFeature(
                "cloud_sync", "云端同步", "数据云端备份同步",
                "☁️", MembershipLevel.YEARLY
            ),
            "personal_advisor": VIPFeature(
                "personal_advisor", "专属顾问", "一对一专属顾问服务",
                "👔", MembershipLevel.YEARLY
            ),
            
            # 永久会员功能（尊享所有功能）
            "ultimate_algorithm": VIPFeature(
                "ultimate_algorithm", "至尊算法", "使用至尊级预测算法",
                "👑", MembershipLevel.LIFETIME, True
            ),
            "unlimited_predictions": VIPFeature(
                "unlimited_predictions", "无限预测", "无限制预测次数",
                "♾️", MembershipLevel.LIFETIME, True
            ),
            "early_access": VIPFeature(
                "early_access", "新功能优先", "优先体验新功能",
                "🆕", MembershipLevel.LIFETIME, True
            ),
            "vip_community": VIPFeature(
                "vip_community", "VIP社群", "加入VIP专属社群",
                "🌟", MembershipLevel.LIFETIME, True
            ),
            "lifetime_updates": VIPFeature(
                "lifetime_updates", "终身更新", "免费终身软件更新",
                "🔄", MembershipLevel.LIFETIME, True
            ),
        }
        
        # 会员等级显示配置
        self.level_config = {
            MembershipLevel.TRIAL: {
                "name": "试用用户",
                "badge": "🎯",
                "color": "#FF6B35",
                "bg_color": "#FFF7ED"
            },
            MembershipLevel.MONTHLY: {
                "name": "包月会员",
                "badge": "💎",
                "color": "#1890FF",
                "bg_color": "#F0F9FF"
            },
            MembershipLevel.QUARTERLY: {
                "name": "季度会员",
                "badge": "🏆",
                "color": "#52C41A",
                "bg_color": "#F6FFED"
            },
            MembershipLevel.YEARLY: {
                "name": "年度会员",
                "badge": "⭐",
                "color": "#722ED1",
                "bg_color": "#F9F0FF"
            },
            MembershipLevel.LIFETIME: {
                "name": "永久会员",
                "badge": "👑",
                "color": "#FFD700",
                "bg_color": "#FFFBE6"
            }
        }
    
    def get_user_level(self, is_premium: bool, days: int = None) -> MembershipLevel:
        """根据用户状态获取会员等级"""
        if not is_premium:
            return MembershipLevel.TRIAL
        
        if days is None:
            return MembershipLevel.LIFETIME  # 永久会员
        elif days <= 30:
            return MembershipLevel.MONTHLY
        elif days <= 90:
            return MembershipLevel.QUARTERLY
        else:
            return MembershipLevel.YEARLY
    
    def get_available_features(self, level: MembershipLevel) -> List[VIPFeature]:
        """获取指定等级可用的所有功能"""
        available = []
        for feature in self.features.values():
            # 检查等级是否满足要求
            level_order = list(MembershipLevel)
            user_level_index = level_order.index(level)
            feature_level_index = level_order.index(feature.min_level)
            
            if user_level_index >= feature_level_index:
                available.append(feature)
        
        return available
    
    def get_feature_by_id(self, feature_id: str) -> VIPFeature:
        """根据ID获取功能"""
        return self.features.get(feature_id)
    
    def check_feature_access(self, feature_id: str, level: MembershipLevel) -> bool:
        """检查用户是否有权限使用某功能"""
        feature = self.features.get(feature_id)
        if not feature:
            return False
        
        level_order = list(MembershipLevel)
        user_level_index = level_order.index(level)
        feature_level_index = level_order.index(feature.min_level)
        
        return user_level_index >= feature_level_index
    
    def get_level_config(self, level: MembershipLevel) -> Dict:
        """获取等级显示配置"""
        return self.level_config.get(level, self.level_config[MembershipLevel.TRIAL])
    
    def get_features_by_category(self, level: MembershipLevel) -> Dict[str, List[VIPFeature]]:
        """按类别获取功能列表"""
        features = self.get_available_features(level)
        
        categories = {
            "prediction": [],      # 预测功能
            "analysis": [],        # 分析功能
            "export": [],          # 导出功能
            "service": [],         # 服务功能
            "exclusive": []        # 专属功能
        }
        
        for feature in features:
            if feature.is_exclusive:
                categories["exclusive"].append(feature)
            elif "algorithm" in feature.feature_id:
                categories["prediction"].append(feature)
            elif "export" in feature.feature_id:
                categories["export"].append(feature)
            elif any(x in feature.feature_id for x in ["analysis", "chart", "trend", "report"]):
                categories["analysis"].append(feature)
            else:
                categories["service"].append(feature)
        
        return categories
    
    def generate_feature_description(self, level: MembershipLevel) -> str:
        """生成功能描述文本"""
        config = self.get_level_config(level)
        features = self.get_available_features(level)
        
        description = f"""
{config['badge']} {config['name']} 特权功能
═══════════════════════════════════════

可用功能 ({len(features)}项):
"""
        
        for feature in features:
            exclusive_mark = " [专属]" if feature.is_exclusive else ""
            description += f"  {feature.icon} {feature.name}: {feature.description}{exclusive_mark}\n"
        
        # 显示下一等级功能预告
        level_order = list(MembershipLevel)
        current_index = level_order.index(level)
        
        if current_index < len(level_order) - 1:
            next_level = level_order[current_index + 1]
            next_config = self.get_level_config(next_level)
            next_features = self.get_available_features(next_level)
            new_features = [f for f in next_features if f not in features]
            
            if new_features:
                description += f"\n\n升级 {next_config['badge']} {next_config['name']} 解锁:\n"
                for feature in new_features[:5]:  # 只显示前5个
                    description += f"  ✨ {feature.name}\n"
        
        return description


# 使用示例
if __name__ == "__main__":
    # 创建VIP功能管理器
    vip_manager = VIPFeatureManager()
    
    # 测试不同等级的功能
    levels = [
        MembershipLevel.TRIAL,
        MembershipLevel.MONTHLY,
        MembershipLevel.QUARTERLY,
        MembershipLevel.YEARLY,
        MembershipLevel.LIFETIME
    ]
    
    for level in levels:
        config = vip_manager.get_level_config(level)
        features = vip_manager.get_available_features(level)
        
        print(f"\n{config['badge']} {config['name']} ({len(features)}项功能)")
        print("=" * 50)
        
        categories = vip_manager.get_features_by_category(level)
        for category, category_features in categories.items():
            if category_features:
                print(f"\n{category.upper()}:")
                for feature in category_features:
                    exclusive = " [专属]" if feature.is_exclusive else ""
                    print(f"  {feature.icon} {feature.name}{exclusive}")
        
        # 显示功能描述
        print("\n" + vip_manager.generate_feature_description(level))
        print("\n" + "=" * 80)
