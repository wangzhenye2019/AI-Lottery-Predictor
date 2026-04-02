# -*- coding:utf-8 -*-
"""
Author: BigCat
Description: AI 彩票预测系统 - Windows 可视化图形界面 (Google App / Material Design 风格)
"""
import tkinter as tk
from tkinter import messagebox
import threading
import sys
import os
import warnings
import customtkinter as ctk

# 配置外观模式为系统默认 (跟随系统亮暗色)
ctk.set_appearance_mode("System")
# 配置颜色主题，可选: "blue" (默认), "green", "dark-blue"
ctk.set_default_color_theme("blue")

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
warnings.filterwarnings('ignore', category=UserWarning, module='tensorflow')
warnings.filterwarnings('ignore', category=FutureWarning, module='tensorflow')
warnings.filterwarnings('ignore', module='keras')
import tensorflow as tf
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

from loguru import logger
from get_data import run as run_get_data
from run_train_model_optimized import run as run_train_optimized
from run_predict_enhanced import run as run_predict_enhanced

class TrainArgsMock:
    def __init__(self, name):
        self.name = name
        self.train_test_split = 0.8
        self.use_early_stopping = True
        self.patience = 10
        self.use_lr_decay = True
        self.decay_rate = 0.95
        self.save_best_only = True

class TextRedirector(object):
    """将 stdout 和 stderr 重定向到 CTkTextbox"""
    def __init__(self, text_widget, tag="stdout"):
        self.text_widget = text_widget
        self.tag = tag

    def write(self, string):
        self.text_widget.configure(state='normal')
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)
        self.text_widget.configure(state='disabled')
        self.text_widget.update_idletasks()

    def flush(self):
        pass

class LotteryPredictorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AI 彩票预测系统 v2.0 - Material Design")
        self.geometry("900x650")
        self.minsize(800, 600)
        
        # 配置网格自适应
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # ----------------------------------------
        # 顶部：控制卡片面板 (Google Material 风格)
        # ----------------------------------------
        self.control_frame = ctk.CTkFrame(self, corner_radius=15)
        self.control_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        # 内部网格布局
        self.control_frame.grid_columnconfigure((1, 3, 5), weight=1)
        
        # 标题
        self.lbl_title = ctk.CTkLabel(
            self.control_frame, 
            text="🎯 AI 智能预测参数配置", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.lbl_title.grid(row=0, column=0, columnspan=6, padx=20, pady=(20, 10), sticky="w")
        
        # 玩法选择
        self.lbl_game = ctk.CTkLabel(self.control_frame, text="🎲 彩票玩法:", font=ctk.CTkFont(size=14))
        self.lbl_game.grid(row=1, column=0, padx=(20, 5), pady=10, sticky="w")
        self.game_var = ctk.StringVar(value="ssq (双色球)")
        self.game_combo = ctk.CTkOptionMenu(
            self.control_frame, 
            variable=self.game_var, 
            values=["ssq (双色球)", "dlt (大乐透)", "qlc (七乐彩)", "fc3d (福彩3D)"],
            font=ctk.CTkFont(size=13),
            dynamic_resizing=False,
            width=140
        )
        self.game_combo.grid(row=1, column=1, padx=(0, 20), pady=10, sticky="w")
        
        # 策略选择
        self.lbl_strategy = ctk.CTkLabel(self.control_frame, text="🧠 预测策略:", font=ctk.CTkFont(size=14))
        self.lbl_strategy.grid(row=1, column=2, padx=(10, 5), pady=10, sticky="w")
        self.strategy_var = ctk.StringVar(value="hybrid (混合分析)")
        self.strategy_combo = ctk.CTkOptionMenu(
            self.control_frame, 
            variable=self.strategy_var, 
            values=["hybrid (混合分析)", "model_only (仅AI模型)", "strategy_only (仅统计算法)"],
            font=ctk.CTkFont(size=13),
            dynamic_resizing=False,
            width=180
        )
        self.strategy_combo.grid(row=1, column=3, padx=(0, 20), pady=10, sticky="w")
        
        # 生成组数
        self.lbl_combo = ctk.CTkLabel(self.control_frame, text="🔢 生成组数:", font=ctk.CTkFont(size=14))
        self.lbl_combo.grid(row=1, column=4, padx=(10, 5), pady=10, sticky="w")
        self.combo_num_var = ctk.StringVar(value="5")
        self.combo_entry = ctk.CTkOptionMenu(
            self.control_frame, 
            variable=self.combo_num_var, 
            values=[str(i) for i in range(1, 21)],
            font=ctk.CTkFont(size=13),
            dynamic_resizing=False,
            width=80
        )
        self.combo_entry.grid(row=1, column=5, padx=(0, 20), pady=10, sticky="w")
        
        # 是否训练模型 (使用 Switch 开关，更符合现代 App 风格)
        self.train_var = ctk.BooleanVar(value=False)
        self.sw_train = ctk.CTkSwitch(
            self.control_frame, 
            text="预测前重新训练模型 (耗时较长)", 
            variable=self.train_var,
            font=ctk.CTkFont(size=14)
        )
        self.sw_train.grid(row=2, column=0, columnspan=3, padx=20, pady=(15, 20), sticky="w")
        
        # 运行按钮 (突出显示的 Primary Button)
        self.run_btn = ctk.CTkButton(
            self.control_frame, 
            text="▶ 一键开始执行", 
            font=ctk.CTkFont(size=15, weight="bold"),
            height=40,
            corner_radius=8,
            command=self.start_thread
        )
        self.run_btn.grid(row=2, column=4, columnspan=2, padx=20, pady=(15, 20), sticky="e")
        
        # ----------------------------------------
        # 底部：日志面板 (Card Style)
        # ----------------------------------------
        self.log_frame = ctk.CTkFrame(self, corner_radius=15)
        self.log_frame.grid(row=1, column=0, padx=20, pady=(10, 20), sticky="nsew")
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(1, weight=1)
        
        self.lbl_log_title = ctk.CTkLabel(
            self.log_frame, 
            text="📝 执行日志", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.lbl_log_title.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")
        
        # 文本框使用固定等宽字体，背景稍微暗一点，更像终端
        self.log_text = ctk.CTkTextbox(
            self.log_frame, 
            font=ctk.CTkFont(family="Consolas", size=13),
            state='disabled', 
            wrap="word",
            corner_radius=8
        )
        self.log_text.grid(row=1, column=0, padx=20, pady=(5, 20), sticky="nsew")
        
        # ----------------------------------------
        # 日志重定向
        # ----------------------------------------
        sys.stdout = TextRedirector(self.log_text, "stdout")
        sys.stderr = TextRedirector(self.log_text, "stderr")
        logger.remove()
        logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="INFO")
        
        self.is_running = False

    def start_thread(self):
        if self.is_running:
            messagebox.showwarning("警告", "任务正在执行中，请耐心等待！")
            return
            
        self.is_running = True
        self.run_btn.configure(state="disabled", text="⏳ 执行中...")
        self.log_text.configure(state='normal')
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state='disabled')
        
        t = threading.Thread(target=self.run_workflow)
        t.daemon = True
        t.start()

    def run_workflow(self):
        try:
            game_name = self.game_var.get().split()[0]
            strategy = self.strategy_var.get().split()[0]
            n_combinations = int(self.combo_num_var.get())
            do_train = self.train_var.get()
            
            game_names = {'ssq': '双色球', 'dlt': '大乐透', 'qlc': '七乐彩', 'fc3d': '福彩3D'}
            
            print("="*60)
            print(f"🚀 开始执行 AI 智能彩票预测系统 ({game_names.get(game_name, game_name)})")
            print("="*60 + "\n")
            
            print(f"[1/3] 正在获取 {game_name} 最新开奖数据...\n" + "-"*40)
            run_get_data(game_name)
            
            if do_train:
                print(f"\n[2/3] 正在重新训练 AI 模型 (请耐心等待)...\n" + "-"*40)
                run_train_optimized(TrainArgsMock(game_name))
            else:
                print("\n[2/3] 跳过模型训练，使用已有模型权重...\n" + "-"*40)
                
            print(f"\n[3/3] 正在执行智能预测 (策略: {strategy})...\n" + "-"*40)
            run_predict_enhanced(game_name, strategy, n_combinations)
            
            print("\n" + "="*60)
            print("🎉 全部流程执行完毕，祝您好运！")
            print("="*60 + "\n")
            
            # 使用 after 确保 messagebox 在主线程弹出
            self.after(0, lambda: messagebox.showinfo("成功", "流程执行完毕！请查看日志框内的预测结果。"))
            
        except Exception as e:
            print(f"\n❌ 执行过程中发生错误: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            self.after(0, lambda: messagebox.showerror("错误", f"执行失败:\n{str(e)}"))
        finally:
            self.is_running = False
            self.after(0, lambda: self.run_btn.configure(state="normal", text="▶ 一键开始执行"))

def main():
    app = LotteryPredictorApp()
    try:
        if os.path.exists("icon.ico"):
            app.iconbitmap("icon.ico")
    except:
        pass
        
    def on_closing():
        if app.is_running:
            if messagebox.askokcancel("退出", "预测任务正在执行，确定要强制退出吗？"):
                app.destroy()
                os._exit(0)
        else:
            app.destroy()
            
    app.protocol("WM_DELETE_WINDOW", on_closing)
    app.mainloop()

if __name__ == "__main__":
    main()