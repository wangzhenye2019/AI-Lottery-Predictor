# -*- coding:utf-8 -*-
"""
Author: BigCat
Description: AI 彩票预测系统 - Windows 可视化图形界面
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import sys
import os

import warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # 屏蔽TF C++层面的INFO和WARNING
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0' # 屏蔽 oneDNN 提示
warnings.filterwarnings('ignore', category=UserWarning, module='tensorflow')
warnings.filterwarnings('ignore', category=FutureWarning, module='tensorflow')
warnings.filterwarnings('ignore', module='keras')
import tensorflow as tf
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

from loguru import logger

# 导入各模块的主函数
from get_data import run as run_get_data
from run_train_model_optimized import run as run_train_optimized
from run_predict_enhanced import run as run_predict_enhanced

class TrainArgsMock:
    """模拟 argparse 解析后的对象，传递给训练模块"""
    def __init__(self, name):
        self.name = name
        self.train_test_split = 0.8
        self.use_early_stopping = True
        self.patience = 10
        self.use_lr_decay = True
        self.decay_rate = 0.95
        self.save_best_only = True

class TextRedirector(object):
    """将 stdout 和 stderr 重定向到 Tkinter 文本框"""
    def __init__(self, text_widget, tag="stdout"):
        self.text_widget = text_widget
        self.tag = tag

    def write(self, string):
        self.text_widget.configure(state='normal')
        self.text_widget.insert(tk.END, string, (self.tag,))
        self.text_widget.see(tk.END)
        self.text_widget.configure(state='disabled')
        # 强制更新界面
        self.text_widget.update_idletasks()

    def flush(self):
        pass


class LotteryPredictorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI 彩票预测系统 v1.0")
        self.root.geometry("800x600")
        self.root.configure(padx=10, pady=10)
        
        # 定义样式
        style = ttk.Style()
        style.configure('TButton', font=('微软雅黑', 10), padding=5)
        style.configure('TLabel', font=('微软雅黑', 10))
        style.configure('TCombobox', font=('微软雅黑', 10))
        
        # 顶部的控制面板
        control_frame = ttk.LabelFrame(self.root, text="设置与控制", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # --- 玩法选择 ---
        ttk.Label(control_frame, text="彩票玩法:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.game_var = tk.StringVar(value="ssq")
        game_combo = ttk.Combobox(control_frame, textvariable=self.game_var, state="readonly", width=15)
        game_combo['values'] = ("ssq (双色球)", "dlt (大乐透)", "qlc (七乐彩)", "fc3d (福彩3D)")
        game_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # --- 预测策略选择 ---
        ttk.Label(control_frame, text="预测策略:").grid(row=0, column=2, padx=15, pady=5, sticky=tk.W)
        self.strategy_var = tk.StringVar(value="hybrid")
        strategy_combo = ttk.Combobox(control_frame, textvariable=self.strategy_var, state="readonly", width=15)
        strategy_combo['values'] = ("hybrid (混合分析)", "model_only (仅AI模型)", "strategy_only (仅统计算法)")
        strategy_combo.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        # --- 预测组合数量 ---
        ttk.Label(control_frame, text="生成组数:").grid(row=0, column=4, padx=15, pady=5, sticky=tk.W)
        self.combo_num_var = tk.IntVar(value=5)
        ttk.Spinbox(control_frame, from_=1, to=20, textvariable=self.combo_num_var, width=5).grid(row=0, column=5, padx=5, pady=5, sticky=tk.W)
        
        # --- 是否重新训练模型选项 ---
        self.train_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(control_frame, text="预测前重新训练模型 (耗时较长)", variable=self.train_var).grid(row=1, column=0, columnspan=3, padx=5, pady=10, sticky=tk.W)
        
        # --- 运行按钮 ---
        self.run_btn = ttk.Button(control_frame, text="▶ 一键开始执行", command=self.start_thread, width=20)
        self.run_btn.grid(row=1, column=4, columnspan=2, padx=5, pady=10)
        
        # 日志输出区域
        log_frame = ttk.LabelFrame(self.root, text="执行日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, font=('Consolas', 10), bg="#1e1e1e", fg="#d4d4d4", state='disabled')
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置日志颜色标签
        self.log_text.tag_configure("stdout", foreground="#d4d4d4")
        self.log_text.tag_configure("stderr", foreground="#f44747")
        
        # 重定向标准输出
        sys.stdout = TextRedirector(self.log_text, "stdout")
        sys.stderr = TextRedirector(self.log_text, "stderr")
        
        # 重定向 loguru 到 stdout
        logger.remove()
        logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="INFO")
        
        self.is_running = False

    def start_thread(self):
        """防止阻塞主界面，在后台线程执行耗时任务"""
        if self.is_running:
            messagebox.showwarning("警告", "任务正在执行中，请耐心等待！")
            return
            
        self.is_running = True
        self.run_btn.config(state=tk.DISABLED, text="⏳ 执行中...")
        self.log_text.configure(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state='disabled')
        
        # 启动线程
        t = threading.Thread(target=self.run_workflow)
        t.daemon = True
        t.start()

    def run_workflow(self):
        """执行完整流程"""
        try:
            # 提取真实的值 (去掉描述)
            game_name = self.game_var.get().split()[0]
            strategy = self.strategy_var.get().split()[0]
            n_combinations = self.combo_num_var.get()
            do_train = self.train_var.get()
            
            game_names = {'ssq': '双色球', 'dlt': '大乐透', 'qlc': '七乐彩', 'fc3d': '福彩3D'}
            
            print("="*60)
            print(f"🚀 开始执行 AI 智能彩票预测系统 ({game_names.get(game_name, game_name)})")
            print("="*60 + "\n")
            
            # 1. 获取数据
            print(f"[1/3] 正在获取 {game_name} 最新开奖数据...\n" + "-"*40)
            run_get_data(game_name)
            
            # 2. 训练模型 (可选)
            if do_train:
                print(f"\n[2/3] 正在重新训练 AI 模型 (请耐心等待)...\n" + "-"*40)
                run_train_optimized(TrainArgsMock(game_name))
            else:
                print("\n[2/3] 跳过模型训练，使用已有模型权重...\n" + "-"*40)
                
            # 3. 执行预测
            print(f"\n[3/3] 正在执行智能预测 (策略: {strategy})...\n" + "-"*40)
            run_predict_enhanced(game_name, strategy, n_combinations)
            
            print("\n" + "="*60)
            print("🎉 全部流程执行完毕，祝您好运！")
            print("="*60 + "\n")
            messagebox.showinfo("成功", "流程执行完毕！请查看日志框内的预测结果。")
            
        except Exception as e:
            print(f"\n❌ 执行过程中发生错误: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            messagebox.showerror("错误", f"执行失败:\n{str(e)}")
        finally:
            self.is_running = False
            # 在主线程中恢复按钮状态
            self.root.after(0, lambda: self.run_btn.config(state=tk.NORMAL, text="▶ 一键开始执行"))

def main():
    root = tk.Tk()
    
    # 尝试设置 Windows 应用图标 (忽略错误)
    try:
        # 如果你未来有图标，可以把 icon.ico 放在根目录
        if os.path.exists("icon.ico"):
            root.iconbitmap("icon.ico")
    except:
        pass
        
    app = LotteryPredictorApp(root)
    
    # 捕获窗口关闭事件
    def on_closing():
        if app.is_running:
            if messagebox.askokcancel("退出", "预测任务正在执行，确定要强制退出吗？"):
                root.destroy()
                os._exit(0)
        else:
            root.destroy()
            
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
