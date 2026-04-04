# -*- coding: utf-8 -*-
"""
支付系统模块
Author: BigCat
"""

import requests
import json
import time
import hashlib
import random
import string
from typing import Dict, Optional, Tuple
from datetime import datetime
import urllib.parse

# 导入配置
from payment_config import WECHAT_CONFIG, ALIPAY_CONFIG, PAYMENT_PLANS, TEST_REGISTER_CODES


class PaymentSystem:
    """支付系统管理器"""
    
    def __init__(self):
        # 使用配置文件
        self.wechat_config = WECHAT_CONFIG
        self.alipay_config = ALIPAY_CONFIG
        self.payment_plans = PAYMENT_PLANS
        self.test_register_codes = TEST_REGISTER_CODES
    
    def generate_order_id(self) -> str:
        """生成订单号"""
        timestamp = str(int(time.time()))
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return f"LOTTERY{timestamp}{random_str}"
    
    def create_wechat_qr_payment(self, amount: float, plan_type: str) -> Dict:
        """创建微信扫码支付"""
        try:
            order_id = self.generate_order_id()
            
            # 订单信息
            order_data = {
                'appid': self.wechat_config['app_id'],
                'mch_id': self.wechat_config['mch_id'],
                'nonce_str': ''.join(random.choices(string.ascii_letters + string.digits, k=32)),
                'body': f'AI智能彩票预测系统-{plan_type}会员',
                'out_trade_no': order_id,
                'total_fee': int(amount * 100),  # 分为单位
                'spbill_create_ip': '127.0.0.1',
                'notify_url': self.wechat_config['notify_url'],
                'trade_type': self.wechat_config['trade_type']
            }
            
            if self.wechat_config.get('test_mode', True):
                # 测试模式返回模拟二维码
                return {
                    'success': True,
                    'order_id': order_id,
                    'qr_code': f'weixin://wxpay/bizpayurl?pr={order_id}',
                    'amount': amount,
                    'plan_type': plan_type,
                    'payment_method': 'wechat'
                }
            
            # 生成签名
            sign = self._generate_wechat_sign(order_data)
            order_data['sign'] = sign
            
            # 发送请求到微信支付API
            xml_data = self._dict_to_xml(order_data)
            response = requests.post(
                'https://api.mch.weixin.qq.com/pay/unifiedorder',
                data=xml_data.encode('utf-8'),
                headers={'Content-Type': 'application/xml'}
            )
            
            # 解析响应
            result = self._xml_to_dict(response.text)
            
            if result.get('return_code') == 'SUCCESS' and result.get('result_code') == 'SUCCESS':
                return {
                    'success': True,
                    'order_id': order_id,
                    'qr_code': result.get('code_url'),
                    'amount': amount,
                    'plan_type': plan_type,
                    'payment_method': 'wechat'
                }
            else:
                return {
                    'success': False,
                    'error': result.get('return_msg', '未知错误')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'微信支付创建失败: {str(e)}'
            }
    
    def create_alipay_qr_payment(self, amount: float, plan_type: str) -> Dict:
        """创建支付宝扫码支付"""
        try:
            order_id = self.generate_order_id()
            
            # 订单信息
            order_data = {
                'app_id': self.alipay_config['app_id'],
                'method': 'alipay.trade.precreate',
                'format': 'json',
                'charset': 'utf-8',
                'sign_type': 'RSA2',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'version': '1.0',
                'notify_url': self.alipay_config['notify_url'],
                'biz_content': json.dumps({
                    'out_trade_no': order_id,
                    'total_amount': str(amount),
                    'subject': f'AI智能彩票预测系统-{plan_type}会员',
                    'timeout_express': '30m'
                })
            }
            
            if self.wechat_config.get('test_mode', True):
                # 测试模式返回模拟二维码
                return {
                    'success': True,
                    'order_id': order_id,
                    'qr_code': f'alipays://platformapi/startapp?saId=10000007&qrcode={order_id}',
                    'amount': amount,
                    'plan_type': plan_type,
                    'payment_method': 'alipay'
                }
            
            # 生成签名
            sign = self._generate_alipay_sign(order_data)
            order_data['sign'] = sign
            
            # 发送请求到支付宝API
            response = requests.post(
                self.alipay_config['gateway_url'],
                data=order_data
            )
            
            # 解析响应
            result = response.json()
            
            if result.get('alipay_trade_precreate_response', {}).get('code') == '10000':
                return {
                    'success': True,
                    'order_id': order_id,
                    'qr_code': result['alipay_trade_precreate_response']['qr_code'],
                    'amount': amount,
                    'plan_type': plan_type,
                    'payment_method': 'alipay'
                }
            else:
                error_msg = result.get('alipay_trade_precreate_response', {}).get('msg', '未知错误')
                return {
                    'success': False,
                    'error': f'支付宝支付创建失败: {error_msg}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'支付宝支付创建失败: {str(e)}'
            }
    
    def check_payment_status(self, order_id: str, payment_method: str) -> Dict:
        """检查支付状态"""
        try:
            if self.wechat_config.get('test_mode', True):
                # 测试模式模拟支付成功
                return {
                    'success': True,
                    'paid': True,
                    'order_id': order_id,
                    'payment_method': payment_method
                }
            
            if payment_method == 'wechat':
                return self._check_wechat_payment(order_id)
            elif payment_method == 'alipay':
                return self._check_alipay_payment(order_id)
            else:
                return {'success': False, 'error': '不支持的支付方式'}
                
        except Exception as e:
            return {
                'success': False,
                'error': f'查询支付状态失败: {str(e)}'
            }
    
    def _generate_wechat_sign(self, data: Dict) -> str:
        """生成微信支付签名"""
        # 过滤空值并按参数名排序
        filtered_data = {k: v for k, v in data.items() if v is not None and v != ''}
        sorted_data = sorted(filtered_data.items())
        
        # 拼接字符串
        string_to_sign = '&'.join([f'{k}={v}' for k, v in sorted_data])
        string_to_sign += f'&key={self.wechat_config["api_key"]}'
        
        # MD5加密并转为大写
        return hashlib.md5(string_to_sign.encode('utf-8')).hexdigest().upper()
    
    def _generate_alipay_sign(self, data: Dict) -> str:
        """生成支付宝签名"""
        # 过滤空值并按参数名排序
        filtered_data = {k: v for k, v in data.items() if k != 'sign' and v is not None and v != ''}
        sorted_data = sorted(filtered_data.items())
        
        # 拼接字符串
        string_to_sign = '&'.join([f'{k}={v}' for k, v in sorted_data])
        
        # 这里应该使用RSA私钥签名，简化处理
        return hashlib.sha256(string_to_sign.encode('utf-8')).hexdigest()
    
    def _dict_to_xml(self, data: Dict) -> str:
        """字典转XML"""
        xml = '<xml>'
        for k, v in data.items():
            xml += f'<{k}><![CDATA[{v}]]></{k}>'
        xml += '</xml>'
        return xml
    
    def _xml_to_dict(self, xml_str: str) -> Dict:
        """XML转字典"""
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_str)
        return {child.tag: child.text for child in root}
    
    def _check_wechat_payment(self, order_id: str) -> Dict:
        """查询微信支付状态"""
        # 实际实现中调用微信支付查询接口
        return {'success': True, 'paid': False}
    
    def _check_alipay_payment(self, order_id: str) -> Dict:
        """查询支付宝支付状态"""
        # 实际实现中调用支付宝查询接口
        return {'success': True, 'paid': False}


class PaymentQRDialog:
    """支付二维码对话框"""
    
    def __init__(self, parent, payment_info, trial_manager):
        self.parent = parent
        self.payment_info = payment_info
        self.trial_manager = trial_manager
        self.payment_system = PaymentSystem()
        self.checking_payment = False
        
        # 创建对话框窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("💳 扫码支付")
        
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
        
        # 开始检查支付状态
        self.start_payment_check()
    
    def create_ui(self):
        """创建界面"""
        # 主框架
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 标题
        title_label = ctk.CTkLabel(
            main_frame,
            text="💳 扫码支付",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#1890FF"
        )
        title_label.pack(pady=(0, 15))
        
        # 订单信息
        order_frame = ctk.CTkFrame(main_frame, fg_color="#F0F9FF")
        order_frame.pack(fill="x", pady=(0, 20))
        
        plan_name = "永久会员" if self.payment_info['plan_type'] == 'lifetime' else "包月会员"
        payment_method = "微信支付" if self.payment_info['payment_method'] == 'wechat' else "支付宝"
        
        order_info = ctk.CTkLabel(
            order_frame,
            text=f"📦 套餐：{plan_name}\n💰 价格：¥{self.payment_info['amount']}\n💳 支付方式：{payment_method}\n📋 订单号：{self.payment_info['order_id']}",
            font=ctk.CTkFont(size=12),
            text_color=AntDesignColors.TEXT_PRIMARY,
            justify="left"
        )
        order_info.pack(pady=15, padx=20)
        
        # 二维码区域
        qr_frame = ctk.CTkFrame(main_frame)
        qr_frame.pack(fill="x", pady=(0, 20))
        
        qr_label = ctk.CTkLabel(
            qr_frame,
            text="📱 请使用手机扫码支付",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=AntDesignColors.TEXT_PRIMARY
        )
        qr_label.pack(pady=(10, 5))
        
        # 这里应该显示真实的二维码，简化处理显示文本
        qr_code_label = ctk.CTkLabel(
            qr_frame,
            text="[二维码区域]\n请使用微信或支付宝扫码\n支付完成后自动激活",
            font=ctk.CTkFont(size=10),
            text_color=AntDesignColors.TEXT_SECONDARY,
            justify="center"
        )
        qr_code_label.pack(pady=10)
        
        # 支付状态
        self.status_label = ctk.CTkLabel(
            qr_frame,
            text="⏳ 等待支付中...",
            font=ctk.CTkFont(size=12),
            text_color="#FF6B35"
        )
        self.status_label.pack(pady=(10, 15))
        
        # 按钮区域
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x")
        
        # 刷新状态按钮
        refresh_btn = ctk.CTkButton(
            button_frame,
            text="🔄 刷新支付状态",
            command=self.manual_check_payment,
            fg_color="#1890FF",
            hover_color="#40A9FF",
            height=40
        )
        refresh_btn.pack(fill="x", pady=(10, 5))
        
        # 取消支付按钮
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="取消支付",
            command=self.on_close,
            fg_color=AntDesignColors.BORDER,
            hover_color=AntDesignColors.TEXT_SECONDARY,
            text_color=AntDesignColors.TEXT_PRIMARY,
            height=35
        )
        cancel_btn.pack(fill="x")
    
    def start_payment_check(self):
        """开始检查支付状态"""
        if not self.checking_payment:
            self.checking_payment = True
            self.check_payment_status()
    
    def check_payment_status(self):
        """检查支付状态"""
        if not self.checking_payment:
            return
        
        try:
            result = self.payment_system.check_payment_status(
                self.payment_info['order_id'],
                self.payment_info['payment_method']
            )
            
            if result['success'] and result['paid']:
                # 支付成功，激活会员
                self.activate_membership()
            else:
                # 继续检查
                self.status_label.configure(text="⏳ 等待支付中...点击刷新按钮检查状态")
                self.dialog.after(3000, self.check_payment_status)  # 3秒后再次检查
                
        except Exception as e:
            self.status_label.configure(text=f"❌ 检查失败: {str(e)}")
            self.dialog.after(5000, self.check_payment_status)  # 5秒后再次检查
    
    def manual_check_payment(self):
        """手动检查支付状态"""
        self.status_label.configure(text="🔄 正在检查支付状态...")
        self.check_payment_status()
    
    def activate_membership(self):
        """激活会员"""
        try:
            self.checking_payment = False
            
            # 激活会员
            if self.payment_info['plan_type'] == 'lifetime':
                self.trial_manager.config['is_premium'] = True
                self.trial_manager.config['premium_expire'] = None
                success_msg = "🎉 恭喜您成为永久会员！\n\n已解锁永久无限使用权限"
            else:
                self.trial_manager.activate_premium(30)
                success_msg = "🎉 恭喜您成为会员！\n\n已解锁30天无限使用权限"
            
            self.trial_manager._save_config()
            
            # 显示成功消息
            messagebox.showinfo("支付成功", success_msg)
            
            # 关闭所有对话框
            self.on_close()
            if self.parent:
                self.parent.destroy()
            
            # 刷新主界面状态
            if hasattr(self.parent, 'parent') and hasattr(self.parent.parent, 'update_trial_status'):
                self.parent.parent.update_trial_status()
                
        except Exception as e:
            messagebox.showerror("激活失败", f"会员激活失败: {str(e)}")
    
    def on_close(self):
        """关闭对话框"""
        self.checking_payment = False
        self.dialog.destroy()
