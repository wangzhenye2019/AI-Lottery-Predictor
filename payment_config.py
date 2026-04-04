# -*- coding: utf-8 -*-
"""
支付系统配置文件
"""

# 微信支付配置（测试环境）
WECHAT_CONFIG = {
    'app_id': 'wx1234567890abcdef',  # 测试公众号ID
    'mch_id': '1234567890',          # 测试商户号
    'api_key': 'your_api_key_here',   # API密钥
    'notify_url': 'https://your-domain.com/payment/notify/wechat',
    'trade_type': 'NATIVE',  # 扫码支付
    'test_mode': True  # 测试模式
}

# 支付宝配置（测试环境）
ALIPAY_CONFIG = {
    'app_id': '2021001234567890',     # 测试应用ID
    'private_key': 'your_private_key', # 应用私钥
    'public_key': 'your_public_key',   # 支付宝公钥
    'notify_url': 'https://your-domain.com/payment/notify/alipay',
    'gateway_url': 'https://openapi.alipay.com/gateway.do',
    'test_mode': True  # 测试模式
}

# 支付套餐配置
PAYMENT_PLANS = {
    'monthly': {
        'name': '包月会员',
        'price': 10.0,
        'duration': '30天',
        'description': '30天无限使用所有功能'
    },
    'lifetime': {
        'name': '永久会员',
        'price': 99.0,
        'duration': '永久',
        'description': '一次付费，永久使用'
    }
}

# 客服信息
CUSTOMER_SERVICE = {
    'wechat': 'LotterySupport',
    'email': 'support@lottery.com',
    'phone': '400-123-4567'
}

# 测试注册码
TEST_REGISTER_CODES = {
    'LOTTERY-2024-LIFETIME-001': ('lifetime', None),
    'LOTTERY-2024-MONTHLY-001': ('monthly', 30),
    'LOTTERY-2024-LIFETIME-002': ('lifetime', None),
    'LOTTERY-2024-MONTHLY-002': ('monthly', 30),
    'DEMO-LIFETIME-CODE-2024': ('lifetime', None),
    'DEMO-MONTHLY-CODE-2024': ('monthly', 30),
}
