# -*- coding: utf-8 -*-
"""
机器码注册码生成器
Author: BigCat
"""

import hashlib
import base64
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import uuid
import platform


class MachineCodeGenerator:
    """机器码生成器"""
    
    @staticmethod
    def get_machine_code() -> str:
        """获取机器唯一标识码"""
        try:
            # 获取系统信息
            machine_info = []
            
            # 1. 计算机名
            machine_info.append(platform.node())
            
            # 2. 处理器信息
            try:
                processor = platform.processor()
                if processor:
                    machine_info.append(processor)
            except:
                pass
            
            # 3. 系统类型
            machine_info.append(platform.system())
            
            # 4. MAC地址（如果可用）
            try:
                import psutil
                net_interfaces = psutil.net_if_addrs()
                for interface_name, interface_addresses in net_interfaces.items():
                    for address in interface_addresses:
                        if address.family.name == 'AF_LINK' and address.address:
                            machine_info.append(address.address.replace(':', '').upper()[:8])
                            break
                    if len(machine_info) > 3:
                        break
            except:
                pass
            
            # 5. 硬盘序列号（简化版本）
            try:
                import os
                if platform.system() == 'Windows':
                    import winreg
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                      r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as key:
                        product_id = winreg.QueryValueEx(key, "ProductId")[0]
                        machine_info.append(product_id[:8])
                else:
                    # Linux/Mac 使用其他标识
                    machine_info.append(str(uuid.getnode())[:8])
            except:
                pass
            
            # 6. 如果信息不足，添加随机数确保唯一性
            if len(machine_info) < 3:
                machine_info.append(str(uuid.uuid4())[:8])
            
            # 组合所有信息
            combined_info = '|'.join(machine_info)
            
            # 生成MD5哈希
            machine_hash = hashlib.md5(combined_info.encode('utf-8')).hexdigest()
            
            # 取前16位作为机器码
            machine_code = machine_hash[:16].upper()
            
            return machine_code
            
        except Exception as e:
            # 如果获取失败，使用随机生成的唯一ID
            fallback_id = f"{platform.node()}_{uuid.uuid4().hex[:8]}"
            return hashlib.md5(fallback_id.encode('utf-8')).hexdigest()[:16].upper()
    
    @staticmethod
    def get_machine_info() -> Dict[str, str]:
        """获取机器详细信息"""
        try:
            info = {
                'computer_name': platform.node(),
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
            }
            
            # 添加MAC地址
            try:
                import psutil
                net_interfaces = psutil.net_if_addrs()
                mac_addresses = []
                for interface_name, interface_addresses in net_interfaces.items():
                    for address in interface_addresses:
                        if address.family.name == 'AF_LINK' and address.address:
                            mac_addresses.append(address.address)
                info['mac_addresses'] = mac_addresses[:3]  # 只取前3个
            except:
                info['mac_addresses'] = []
            
            return info
            
        except Exception:
            return {'error': '无法获取机器信息'}


class RegisterCodeSystem:
    """注册码系统"""
    
    def __init__(self):
        self.machine_code = MachineCodeGenerator.get_machine_code()
        self.secret_key = "LOTTERY_2024_SECRET_KEY"  # 密钥，实际部署时应该更复杂
        
        # 套餐配置
        self.plans = {
            'trial': {'name': '试用版', 'days': 7, 'price': 0},
            'monthly': {'name': '包月会员', 'days': 30, 'price': 10},
            'quarterly': {'name': '季度会员', 'days': 90, 'price': 25},
            'yearly': {'name': '年度会员', 'days': 365, 'price': 88},
            'lifetime': {'name': '永久会员', 'days': -1, 'price': 99}
        }
    
    def generate_register_code(self, plan_type: str, custom_days: int = None) -> str:
        """生成注册码"""
        try:
            # 获取套餐信息
            if plan_type not in self.plans:
                raise ValueError(f"不支持的套餐类型: {plan_type}")
            
            plan = self.plans[plan_type]
            days = custom_days if custom_days is not None else plan['days']
            
            # 构建注册码数据
            code_data = {
                'machine_code': self.machine_code,
                'plan_type': plan_type,
                'days': days,
                'timestamp': int(time.time()),
                'version': '1.0'
            }
            
            # 生成签名
            signature = self._generate_signature(code_data)
            code_data['signature'] = signature
            
            # 转换为JSON字符串
            json_str = json.dumps(code_data, separators=(',', ':'), sort_keys=True)
            
            # Base64编码
            encoded_bytes = base64.b64encode(json_str.encode('utf-8'))
            encoded_str = encoded_bytes.decode('utf-8')
            
            # 格式化为注册码格式：XXXX-XXXX-XXXX-XXXX
            register_code = self._format_register_code(encoded_str)
            
            return register_code
            
        except Exception as e:
            raise Exception(f"生成注册码失败: {str(e)}")
    
    def validate_register_code(self, register_code: str) -> Tuple[bool, Dict]:
        """验证注册码"""
        try:
            # 移除格式分隔符和空格，保留所有Base64字符
            clean_code = register_code.replace('-', '').replace(' ', '')
            
            # 长度检查
            if len(clean_code) < 16:
                return False, {'error': '注册码长度不足'}
            
            # 补齐Base64 padding
            padding_needed = 4 - (len(clean_code) % 4)
            if padding_needed != 4:
                clean_code += '=' * padding_needed
            
            # Base64解码
            try:
                decoded_bytes = base64.b64decode(clean_code)
                json_str = decoded_bytes.decode('utf-8')
            except Exception as e:
                return False, {'error': f'注册码解码失败: 格式错误或已损坏'}
            
            # 解析JSON
            try:
                code_data = json.loads(json_str)
            except:
                return False, {'error': '注册码数据格式错误'}
            
            # 验证必要字段
            required_fields = ['machine_code', 'plan_type', 'days', 'timestamp', 'signature', 'version']
            for field in required_fields:
                if field not in code_data:
                    return False, {'error': f'注册码缺少必要字段: {field}'}
            
            # 验证机器码
            if code_data['machine_code'] != self.machine_code:
                return False, {'error': '注册码与当前机器不匹配'}
            
            # 验证套餐类型
            if code_data['plan_type'] not in self.plans:
                return False, {'error': f'不支持的套餐类型: {code_data["plan_type"]}'}
            
            # 验证签名
            if not self._verify_signature(code_data):
                return False, {'error': '注册码签名验证失败'}
            
            # 验证时间戳（防止过期注册码）
            timestamp = code_data['timestamp']
            current_time = int(time.time())
            if current_time - timestamp > 365 * 24 * 3600:  # 一年有效期
                return False, {'error': '注册码已过期'}
            
            # 返回验证成功信息
            plan = self.plans[code_data['plan_type']]
            return True, {
                'plan_type': code_data['plan_type'],
                'plan_name': plan['name'],
                'days': code_data['days'],
                'price': plan['price'],
                'timestamp': timestamp
            }
            
        except Exception as e:
            return False, {'error': f'验证注册码失败: {str(e)}'}
    
    def _generate_signature(self, data: Dict) -> str:
        """生成签名"""
        # 移除签名字段
        sign_data = {k: v for k, v in data.items() if k != 'signature'}
        
        # 按键排序
        sorted_data = sorted(sign_data.items())
        
        # 构建签名字符串
        sign_str = '|'.join([f'{k}={v}' for k, v in sorted_data])
        sign_str += f'|key={self.secret_key}'
        
        # 生成MD5签名
        signature = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
        
        return signature
    
    def _verify_signature(self, data: Dict) -> bool:
        """验证签名"""
        if 'signature' not in data:
            return False
        
        # 生成预期签名
        expected_signature = self._generate_signature(data)
        
        # 比较签名
        return data['signature'] == expected_signature
    
    def _format_register_code(self, encoded_str: str) -> str:
        """格式化注册码为可读的带分隔符格式"""
        # 移除Base64中的=（padding）
        clean_str = encoded_str.replace('=', '')
        
        # 不截断，保留完整长度，只添加分隔符便于阅读
        # 每8个字符添加一个分隔符
        parts = []
        for i in range(0, len(clean_str), 8):
            parts.append(clean_str[i:i+8])
        
        # 用-连接各部分
        formatted = '-'.join(parts)
        
        return formatted
    
    def get_machine_info_for_support(self) -> str:
        """获取用于客服支持的机器信息"""
        machine_info = MachineCodeGenerator.get_machine_info()
        machine_code = self.machine_code
        
        support_info = f"""
机器码: {machine_code}

机器信息:
- 计算机名: {machine_info.get('computer_name', '未知')}
- 操作系统: {machine_info.get('system', '未知')} {machine_info.get('release', '未知')}
- 处理器: {machine_info.get('processor', '未知')}
- Python版本: {machine_info.get('python_version', '未知')}

MAC地址: {', '.join(machine_info.get('mac_addresses', ['未知']))}

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

请将此信息发送给客服以获取对应的注册码。
"""
        return support_info.strip()


# 使用示例
if __name__ == "__main__":
    # 创建注册码系统
    reg_system = RegisterCodeSystem()
    
    # 获取机器码
    machine_code = reg_system.machine_code
    print(f"机器码: {machine_code}")
    
    # 生成不同套餐的注册码
    plans = ['trial', 'monthly', 'quarterly', 'yearly', 'lifetime']
    
    print("\n生成的注册码:")
    print("=" * 50)
    
    for plan in plans:
        try:
            code = reg_system.generate_register_code(plan)
            plan_info = reg_system.plans[plan]
            print(f"{plan_info['name']:8} - {code} - ¥{plan_info['price']}")
        except Exception as e:
            print(f"{plan:8} - 生成失败: {e}")
    
    # 验证注册码示例
    print("\n验证注册码示例:")
    print("=" * 50)
    
    test_code = reg_system.generate_register_code('monthly')
    is_valid, result = reg_system.validate_register_code(test_code)
    
    print(f"注册码: {test_code}")
    print(f"验证结果: {'成功' if is_valid else '失败'}")
    
    if is_valid:
        print(f"套餐: {result['plan_name']}")
        print(f"时长: {result['days']}天")
        print(f"价格: ¥{result['price']}")
    else:
        print(f"错误: {result['error']}")
    
    # 获取客服支持信息
    print("\n客服支持信息:")
    print("=" * 50)
    print(reg_system.get_machine_info_for_support())
