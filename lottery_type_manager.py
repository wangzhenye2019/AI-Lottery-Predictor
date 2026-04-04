# -*- coding: utf-8 -*-
"""
彩票类型配置管理器
支持所有中国常见彩种
Author: BigCat
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class LotteryConfig:
    """彩票配置类"""
    name: str  # 彩种名称
    code: str  # 彩种代码
    red_pool: int  # 红球/前区池大小
    red_count: int  # 红球/前区选择个数
    blue_pool: int  # 蓝球/后区池大小
    blue_count: int  # 蓝球/后区选择个数
    description: str  # 描述
    

class LotteryTypeManager:
    """彩票类型管理器 - 支持所有彩种"""
    
    # 定义所有支持的彩种
    LOTTERY_TYPES = {
        # 双色球系列
        "ssq": LotteryConfig(
            name="双色球",
            code="ssq",
            red_pool=33,
            red_count=6,
            blue_pool=16,
            blue_count=1,
            description="6红球(1-33) + 1蓝球(1-16)"
        ),
        
        # 大乐透系列
        "dlt": LotteryConfig(
            name="大乐透",
            code="dlt",
            red_pool=35,
            red_count=5,
            blue_pool=12,
            blue_count=2,
            description="5前区(1-35) + 2后区(1-12)"
        ),
        
        # 福彩3D
        "fc3d": LotteryConfig(
            name="福彩3D",
            code="fc3d",
            red_pool=10,
            red_count=3,
            blue_pool=0,
            blue_count=0,
            description="3位数字(0-9)"
        ),
        
        # 排列3
        "pl3": LotteryConfig(
            name="排列3",
            code="pl3",
            red_pool=10,
            red_count=3,
            blue_pool=0,
            blue_count=0,
            description="3位数字(0-9)，每位不重复"
        ),
        
        # 排列5
        "pl5": LotteryConfig(
            name="排列5",
            code="pl5",
            red_pool=10,
            red_count=5,
            blue_pool=0,
            blue_count=0,
            description="5位数字(0-9)，每位不重复"
        ),
        
        # 七星彩
        "qxc": LotteryConfig(
            name="七星彩",
            code="qxc",
            red_pool=10,
            red_count=7,
            blue_pool=15,
            blue_count=1,
            description="7位数字(0-9) + 1特别号(1-15)"
        ),
        
        # 七乐彩
        "qlc": LotteryConfig(
            name="七乐彩",
            code="qlc",
            red_pool=30,
            red_count=7,
            blue_pool=0,
            blue_count=0,
            description="7个号码(1-30)"
        ),
        
        # 快乐8
        "kl8": LotteryConfig(
            name="快乐8",
            code="kl8",
            red_pool=80,
            red_count=20,
            blue_pool=0,
            blue_count=0,
            description="选1-10个号码(1-80)，开奖20个"
        ),
        
        # 11选5 - 广东
        "gd115": LotteryConfig(
            name="广东11选5",
            code="gd115",
            red_pool=11,
            red_count=5,
            blue_pool=0,
            blue_count=0,
            description="5个号码(1-11)"
        ),
        
        # 快3 - 江苏
        "jsk3": LotteryConfig(
            name="江苏快3",
            code="jsk3",
            red_pool=6,
            red_count=3,
            blue_pool=0,
            blue_count=0,
            description="3个骰子(1-6)，和值3-18"
        ),
        
        # 时时彩 - 重庆
        "cqssc": LotteryConfig(
            name="重庆时时彩",
            code="cqssc",
            red_pool=10,
            red_count=5,
            blue_pool=0,
            blue_count=0,
            description="5位数字(0-9)"
        ),
    }
    
    @classmethod
    def get_config(cls, lottery_type: str) -> LotteryConfig:
        """获取彩票配置"""
        return cls.LOTTERY_TYPES.get(lottery_type, cls.LOTTERY_TYPES["ssq"])
    
    @classmethod
    def get_all_types(cls) -> List[str]:
        """获取所有彩票类型代码"""
        return list(cls.LOTTERY_TYPES.keys())
    
    @classmethod
    def get_all_configs(cls) -> Dict[str, LotteryConfig]:
        """获取所有彩票配置"""
        return cls.LOTTERY_TYPES.copy()
    
    @classmethod
    def get_name(cls, lottery_type: str) -> str:
        """获取彩票名称"""
        config = cls.get_config(lottery_type)
        return config.name
    
    @classmethod
    def is_valid(cls, lottery_type: str) -> bool:
        """检查彩票类型是否有效"""
        return lottery_type in cls.LOTTERY_TYPES
    
    @classmethod
    def get_categories(cls) -> Dict[str, List[str]]:
        """按类别获取彩票类型"""
        return {
            "数字彩": ["ssq", "dlt", "qlc"],
            "高频彩": ["gd115", "jsk3", "cqssc", "kl8"],
            "排列彩": ["fc3d", "pl3", "pl5", "qxc"]
        }
    
    @classmethod
    def generate_random_numbers(cls, lottery_type: str) -> Dict:
        """生成随机号码"""
        import numpy as np
        
        config = cls.get_config(lottery_type)
        
        # 生成红球/前区/主号码
        if config.red_count > 0:
            if lottery_type in ["fc3d", "cqssc"]:
                # 数字彩，可以有重复
                main_numbers = [np.random.randint(0, config.red_pool) 
                                for _ in range(config.red_count)]
            else:
                # 乐透彩，不重复
                main_numbers = sorted(np.random.choice(
                    range(1, config.red_pool + 1),
                    config.red_count,
                    replace=False
                ).tolist())
        else:
            main_numbers = []
        
        # 生成蓝球/后区/特别号码
        if config.blue_count > 0:
            if lottery_type == "qxc":
                # 七星彩特别号
                special_numbers = [np.random.randint(1, config.blue_pool + 1)]
            else:
                # 普通蓝球
                special_numbers = sorted(np.random.choice(
                    range(1, config.blue_pool + 1),
                    config.blue_count,
                    replace=False
                ).tolist())
        else:
            special_numbers = []
        
        return {
            "lottery_type": lottery_type,
            "lottery_name": config.name,
            "main_numbers": main_numbers,
            "special_numbers": special_numbers,
            "description": config.description
        }
    
    @classmethod
    def format_numbers(cls, lottery_type: str, numbers: Dict) -> str:
        """格式化号码显示"""
        if lottery_type in ["ssq", "qlc"]:
            # 双色球、七乐彩格式
            main = ' '.join([f'{n:02d}' for n in numbers['main_numbers']])
            if numbers.get('special_numbers'):
                special = f" + {numbers['special_numbers'][0]:02d}"
                return f"{main}{special}"
            return main
        
        elif lottery_type == "dlt":
            # 大乐透格式
            front = ' '.join([f'{n:02d}' for n in numbers['main_numbers']])
            back = ' '.join([f'{n:02d}' for n in numbers['special_numbers']])
            return f"{front} | {back}"
        
        elif lottery_type in ["fc3d", "pl3", "pl5", "cqssc"]:
            # 数字彩格式
            return ''.join([str(n) for n in numbers['main_numbers']])
        
        elif lottery_type == "qxc":
            # 七星彩格式
            main = ''.join([str(n) for n in numbers['main_numbers']])
            special = f" + {numbers['special_numbers'][0]:02d}"
            return f"{main}{special}"
        
        elif lottery_type == "kl8":
            # 快乐8格式
            return ' '.join([f'{n:02d}' for n in numbers['main_numbers']])
        
        elif lottery_type in ["gd115", "jsk3"]:
            # 11选5、快3格式
            return ' '.join([f'{n:02d}' for n in numbers['main_numbers']])
        
        else:
            return str(numbers)


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("彩票类型管理器测试")
    print("=" * 60)
    
    # 测试所有彩种
    for lottery_type in LotteryTypeManager.get_all_types():
        config = LotteryTypeManager.get_config(lottery_type)
        numbers = LotteryTypeManager.generate_random_numbers(lottery_type)
        formatted = LotteryTypeManager.format_numbers(lottery_type, numbers)
        
        print(f"\n【{config.name}】({lottery_type})")
        print(f"  规则: {config.description}")
        print(f"  随机号码: {formatted}")
    
    print("\n" + "=" * 60)
    print("按类别分类:")
    for category, types in LotteryTypeManager.get_categories().items():
        names = [LotteryTypeManager.get_name(t) for t in types]
        print(f"{category}: {', '.join(names)}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
