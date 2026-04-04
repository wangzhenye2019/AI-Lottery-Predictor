# -*- coding: utf-8 -*-
"""
注册码生成器工具 - 供客服使用
Author: BigCat
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from machine_register_system import RegisterCodeSystem, MachineCodeGenerator
from datetime import datetime
import json
import os


class RegisterCodeGeneratorApp:
    """注册码生成器应用"""
    
    def __init__(self):
        self.register_system = RegisterCodeSystem()
        
        # 创建主窗口
        self.root = ctk.CTk()
        self.root.title("🔑 注册码生成器 - 客服工具")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 设置主题
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        # 创建界面
        self.create_ui()
        
        # 绑定事件
        self.bind_events()
    
    def create_ui(self):
        """创建界面"""
        # 主框架
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 标题
        title_label = ctk.CTkLabel(
            main_frame,
            text="🔑 注册码生成器",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#1890FF"
        )
        title_label.pack(pady=(0, 20))
        
        # 选项卡
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # 创建选项卡
        self.create_generate_tab()
        self.create_validate_tab()
        self.create_batch_tab()
        self.create_settings_tab()
    
    def create_generate_tab(self):
        """创建生成选项卡"""
        generate_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(generate_frame, text="单个生成")
        
        # 机器码输入
        machine_frame = ctk.CTkFrame(generate_frame)
        machine_frame.pack(fill="x", padx=20, pady=20)
        
        machine_label = ctk.CTkLabel(
            machine_frame,
            text="🖥️ 客户机器码：",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        machine_label.pack(anchor="w", pady=(10, 5))
        
        self.machine_entry = ctk.CTkEntry(
            machine_frame,
            placeholder_text="输入客户的16位机器码",
            font=ctk.CTkFont(size=12, family="Courier New"),
            height=35
        )
        self.machine_entry.pack(fill="x", pady=(0, 10))
        
        # 套餐选择
        plan_frame = ctk.CTkFrame(generate_frame)
        plan_frame.pack(fill="x", padx=20, pady=20)
        
        plan_label = ctk.CTkLabel(
            plan_frame,
            text="📦 选择套餐：",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        plan_label.pack(anchor="w", pady=(10, 5))
        
        self.plan_var = tk.StringVar(value="monthly")
        
        plans = [
            ("试用版 (7天)", "trial"),
            ("包月会员 (30天)", "monthly"),
            ("季度会员 (90天)", "quarterly"),
            ("年度会员 (365天)", "yearly"),
            ("永久会员", "lifetime")
        ]
        
        for text, value in plans:
            radio = ctk.CTkRadioButton(
                plan_frame,
                text=text,
                variable=self.plan_var,
                value=value
            )
            radio.pack(anchor="w", pady=2)
        
        # 自定义天数
        custom_frame = ctk.CTkFrame(plan_frame)
        custom_frame.pack(fill="x", pady=(10, 0))
        
        self.use_custom_var = tk.BooleanVar(value=False)
        
        custom_check = ctk.CTkCheckBox(
            custom_frame,
            text="自定义天数：",
            variable=self.use_custom_var,
            command=self.toggle_custom_days
        )
        custom_check.pack(side="left")
        
        self.custom_days_entry = ctk.CTkEntry(
            custom_frame,
            placeholder_text="天数",
            width=100,
            height=30
        )
        self.custom_days_entry.pack(side="left", padx=(10, 0))
        self.custom_days_entry.pack_forget()  # 初始隐藏
        
        # 生成按钮
        generate_btn = ctk.CTkButton(
            generate_frame,
            text="🔑 生成注册码",
            command=self.generate_single_code,
            fg_color="#1890FF",
            hover_color="#40A9FF",
            height=40
        )
        generate_btn.pack(fill="x", pady=20)
        
        # 结果显示
        result_frame = ctk.CTkFrame(generate_frame)
        result_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        result_label = ctk.CTkLabel(
            result_frame,
            text="📋 生成结果：",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        result_label.pack(anchor="w", pady=(10, 5))
        
        self.result_text = ctk.CTkTextbox(result_frame, height=150)
        self.result_text.pack(fill="both", expand=True, pady=(0, 10))
        
        # 操作按钮
        action_frame = ctk.CTkFrame(result_frame)
        action_frame.pack(fill="x")
        
        copy_btn = ctk.CTkButton(
            action_frame,
            text="📋 复制注册码",
            command=self.copy_result,
            width=120
        )
        copy_btn.pack(side="left", padx=(0, 10))
        
        save_btn = ctk.CTkButton(
            action_frame,
            text="💾 保存记录",
            command=self.save_record,
            width=120
        )
        save_btn.pack(side="left")
    
    def create_validate_tab(self):
        """创建验证选项卡"""
        validate_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(validate_frame, text="验证注册码")
        
        # 注册码输入
        input_frame = ctk.CTkFrame(validate_frame)
        input_frame.pack(fill="x", padx=20, pady=20)
        
        input_label = ctk.CTkLabel(
            input_frame,
            text="🔑 输入注册码：",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        input_label.pack(anchor="w", pady=(10, 5))
        
        self.validate_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="格式：XXXX-XXXX-XXXX-XXXX",
            font=ctk.CTkFont(size=12, family="Courier New"),
            height=35
        )
        self.validate_entry.pack(fill="x", pady=(0, 10))
        
        # 验证按钮
        validate_btn = ctk.CTkButton(
            input_frame,
            text="🔍 验证注册码",
            command=self.validate_code,
            fg_color="#52C41A",
            hover_color="#73D13D",
            height=40
        )
        validate_btn.pack(fill="x")
        
        # 验证结果
        result_frame = ctk.CTkFrame(validate_frame)
        result_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        result_label = ctk.CTkLabel(
            result_frame,
            text="📋 验证结果：",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        result_label.pack(anchor="w", pady=(10, 5))
        
        self.validate_result_text = ctk.CTkTextbox(result_frame, height=200)
        self.validate_result_text.pack(fill="both", expand=True, pady=(0, 10))
    
    def create_batch_tab(self):
        """创建批量生成选项卡"""
        batch_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(batch_frame, text="批量生成")
        
        # 批量生成设置
        settings_frame = ctk.CTkFrame(batch_frame)
        settings_frame.pack(fill="x", padx=20, pady=20)
        
        # 数量设置
        count_label = ctk.CTkLabel(
            settings_frame,
            text="📊 生成数量：",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        count_label.pack(anchor="w", pady=(10, 5))
        
        self.count_entry = ctk.CTkEntry(
            settings_frame,
            placeholder_text="输入生成数量",
            height=35
        )
        self.count_entry.pack(fill="x", pady=(0, 10))
        
        # 批量生成按钮
        batch_btn = ctk.CTkButton(
            settings_frame,
            text="🔑 批量生成",
            command=self.generate_batch_codes,
            fg_color="#FA8C16",
            hover_color="#FFA940",
            height=40
        )
        batch_btn.pack(fill="x")
        
        # 批量结果
        batch_result_frame = ctk.CTkFrame(batch_frame)
        batch_result_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        batch_result_label = ctk.CTkLabel(
            batch_result_frame,
            text="📋 批量结果：",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        batch_result_label.pack(anchor="w", pady=(10, 5))
        
        self.batch_result_text = ctk.CTkTextbox(batch_result_frame, height=200)
        self.batch_result_text.pack(fill="both", expand=True, pady=(0, 10))
        
        # 批量操作按钮
        batch_action_frame = ctk.CTkFrame(batch_result_frame)
        batch_action_frame.pack(fill="x")
        
        export_btn = ctk.CTkButton(
            batch_action_frame,
            text="📄 导出文件",
            command=self.export_batch,
            width=120
        )
        export_btn.pack(side="left", padx=(0, 10))
        
        clear_btn = ctk.CTkButton(
            batch_action_frame,
            text="🗑️ 清空结果",
            command=self.clear_batch,
            width=120
        )
        clear_btn.pack(side="left")
    
    def create_settings_tab(self):
        """创建设置选项卡"""
        settings_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(settings_frame, text="设置")
        
        # 当前机器信息
        info_frame = ctk.CTkFrame(settings_frame)
        info_frame.pack(fill="x", padx=20, pady=20)
        
        info_label = ctk.CTkLabel(
            info_frame,
            text="🖥️ 当前机器信息：",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        info_label.pack(anchor="w", pady=(10, 5))
        
        self.info_text = ctk.CTkTextbox(info_frame, height=150)
        self.info_text.pack(fill="x", pady=(0, 10))
        
        # 显示当前机器信息
        self.update_machine_info()
        
        # 刷新按钮
        refresh_btn = ctk.CTkButton(
            info_frame,
            text="🔄 刷新信息",
            command=self.update_machine_info,
            width=120
        )
        refresh_btn.pack(anchor="w")
    
    def toggle_custom_days(self):
        """切换自定义天数输入"""
        if self.use_custom_var.get():
            self.custom_days_entry.pack(side="left", padx=(10, 0))
        else:
            self.custom_days_entry.pack_forget()
    
    def generate_single_code(self):
        """生成单个注册码"""
        try:
            machine_code = self.machine_entry.get().strip().upper()
            if not machine_code:
                messagebox.showerror("错误", "请输入机器码")
                return
            
            if len(machine_code) != 16:
                messagebox.showerror("错误", "机器码必须是16位")
                return
            
            # 获取套餐类型
            if self.use_custom_var.get():
                custom_days = self.custom_days_entry.get().strip()
                if not custom_days or not custom_days.isdigit():
                    messagebox.showerror("错误", "请输入有效的天数")
                    return
                days = int(custom_days)
                plan_type = "custom"
                plan_name = f"自定义({days}天)"
            else:
                plan_type = self.plan_var.get()
                plan_info = self.register_system.plans[plan_type]
                days = plan_info['days']
                plan_name = plan_info['name']
            
            # 临时替换机器码生成器
            original_machine_code = self.register_system.machine_code
            self.register_system.machine_code = machine_code
            
            # 生成注册码
            register_code = self.register_system.generate_register_code(plan_type, days)
            
            # 恢复原始机器码
            self.register_system.machine_code = original_machine_code
            
            # 显示结果
            result = f"""
生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
机器码：{machine_code}
套餐类型：{plan_name}
注册码：{register_code}

请将注册码发送给客户进行激活。
"""
            
            self.result_text.delete("1.0", "end")
            self.result_text.insert("1.0", result.strip())
            
            messagebox.showinfo("成功", "注册码生成成功！")
            
        except Exception as e:
            messagebox.showerror("错误", f"生成注册码失败：{str(e)}")
    
    def validate_code(self):
        """验证注册码"""
        try:
            code = self.validate_entry.get().strip()
            if not code:
                messagebox.showerror("错误", "请输入注册码")
                return
            
            # 验证注册码
            is_valid, result = self.register_system.validate_register_code(code)
            
            if is_valid:
                validation_result = f"""
✅ 验证成功！

注册码：{code}
套餐类型：{result['plan_name']}
使用时长：{result['days']}天
价格：¥{result['price']}
生成时间：{datetime.fromtimestamp(result['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}

状态：有效
"""
            else:
                validation_result = f"""
❌ 验证失败！

注册码：{code}
错误信息：{result['error']}

状态：无效
"""
            
            self.validate_result_text.delete("1.0", "end")
            self.validate_result_text.insert("1.0", validation_result.strip())
            
        except Exception as e:
            messagebox.showerror("错误", f"验证注册码失败：{str(e)}")
    
    def generate_batch_codes(self):
        """批量生成注册码"""
        try:
            count_str = self.count_entry.get().strip()
            if not count_str or not count_str.isdigit():
                messagebox.showerror("错误", "请输入有效的生成数量")
                return
            
            count = int(count_str)
            if count < 1 or count > 100:
                messagebox.showerror("错误", "生成数量必须在1-100之间")
                return
            
            plan_type = self.plan_var.get()
            plan_info = self.register_system.plans[plan_type]
            
            # 批量生成
            batch_results = []
            current_time = datetime.now()
            
            for i in range(count):
                # 生成临时机器码（实际使用时应该输入客户机器码）
                temp_machine_code = f"BATCH{i:03d}{hash(str(i)) % 10000:04d}"[:16].upper()
                
                # 临时替换机器码
                original_machine_code = self.register_system.machine_code
                self.register_system.machine_code = temp_machine_code
                
                # 生成注册码
                register_code = self.register_system.generate_register_code(plan_type)
                
                # 恢复原始机器码
                self.register_system.machine_code = original_machine_code
                
                batch_results.append({
                    'index': i + 1,
                    'machine_code': temp_machine_code,
                    'register_code': register_code,
                    'plan': plan_info['name'],
                    'days': plan_info['days'],
                    'price': plan_info['price']
                })
            
            # 显示结果
            result_text = f"批量生成时间：{current_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            result_text += f"套餐类型：{plan_info['name']}\n"
            result_text += f"生成数量：{count}\n"
            result_text += "=" * 80 + "\n\n"
            
            for result in batch_results:
                result_text += f"序号：{result['index']:03d}\n"
                result_text += f"机器码：{result['machine_code']}\n"
                result_text += f"注册码：{result['register_code']}\n"
                result_text += f"套餐：{result['plan']} ({result['days']}天)\n"
                result_text += f"价格：¥{result['price']}\n"
                result_text += "-" * 40 + "\n"
            
            self.batch_result_text.delete("1.0", "end")
            self.batch_result_text.insert("1.0", result_text)
            
            messagebox.showinfo("成功", f"成功生成 {count} 个注册码！")
            
        except Exception as e:
            messagebox.showerror("错误", f"批量生成失败：{str(e)}")
    
    def copy_result(self):
        """复制结果"""
        try:
            result = self.result_text.get("1.0", "end").strip()
            if result:
                self.root.clipboard_clear()
                self.root.clipboard_append(result)
                messagebox.showinfo("成功", "结果已复制到剪贴板")
        except Exception as e:
            messagebox.showerror("错误", f"复制失败：{str(e)}")
    
    def save_record(self):
        """保存记录"""
        try:
            result = self.result_text.get("1.0", "end").strip()
            if not result:
                messagebox.showerror("错误", "没有可保存的内容")
                return
            
            filename = filedialog.asksaveasfilename(
                title="保存注册码记录",
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(result)
                messagebox.showinfo("成功", f"记录已保存到：{filename}")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败：{str(e)}")
    
    def export_batch(self):
        """导出批量结果"""
        try:
            result = self.batch_result_text.get("1.0", "end").strip()
            if not result:
                messagebox.showerror("错误", "没有可导出的内容")
                return
            
            filename = filedialog.asksaveasfilename(
                title="导出批量注册码",
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("CSV文件", "*.csv"), ("所有文件", "*.*")]
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(result)
                messagebox.showinfo("成功", f"批量结果已导出到：{filename}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败：{str(e)}")
    
    def clear_batch(self):
        """清空批量结果"""
        self.batch_result_text.delete("1.0", "end")
        messagebox.showinfo("成功", "批量结果已清空")
    
    def update_machine_info(self):
        """更新机器信息"""
        try:
            info = MachineCodeGenerator.get_machine_info()
            current_machine_code = self.register_system.machine_code
            
            info_text = f"""
当前机器码：{current_machine_code}

详细信息：
- 计算机名：{info.get('computer_name', '未知')}
- 操作系统：{info.get('system', '未知')} {info.get('release', '未知')}
- 处理器：{info.get('processor', '未知')}
- Python版本：{info.get('python_version', '未知')}
- MAC地址：{', '.join(info.get('mac_addresses', ['未知']))}

生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            self.info_text.delete("1.0", "end")
            self.info_text.insert("1.0", info_text.strip())
            
        except Exception as e:
            error_text = f"获取机器信息失败：{str(e)}"
            self.info_text.delete("1.0", "end")
            self.info_text.insert("1.0", error_text)
    
    def bind_events(self):
        """绑定事件"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def on_closing(self):
        """关闭窗口"""
        if messagebox.askokcancel("退出", "确定要退出注册码生成器吗？"):
            self.root.destroy()
    
    def run(self):
        """运行应用"""
        self.root.mainloop()


if __name__ == "__main__":
    app = RegisterCodeGeneratorApp()
    app.run()
