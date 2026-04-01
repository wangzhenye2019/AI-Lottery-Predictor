# -*- coding:utf-8 -*-
"""
Author: BigCat
Description: 双色球数据统计分析工具
"""
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from collections import Counter
from config import name_path, data_file_name
from loguru import logger

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class LotteryAnalyzer:
    """彩票数据分析类"""
    
    def __init__(self, data, name='ssq'):
        self.data = data
        self.name = name
        self.red_balls = [col for col in data.columns if '红球' in col]
        self.blue_balls = [col for col in data.columns if '蓝球' in col]
        
    def plot_frequency(self, ball_type='red', save_path=None):
        """
        绘制号码频率分布图
        :param ball_type: 球类型
        :param save_path: 保存路径
        """
        if ball_type == 'red':
            balls = self.red_balls
            max_num = 33
            title = "红球号码频率分布"
        else:
            balls = self.blue_balls
            max_num = 16 if len(self.blue_balls) == 1 else 12
            title = "蓝球号码频率分布"
            
        all_balls = self.data[balls].values.flatten().astype(int)
        counter = Counter(all_balls)
        
        numbers = list(range(1, max_num + 1))
        frequencies = [counter.get(num, 0) for num in numbers]
        
        plt.figure(figsize=(15, 6))
        bars = plt.bar(numbers, frequencies, color='coral' if ball_type == 'red' else 'skyblue')
        
        plt.xlabel('号码', fontsize=12)
        plt.ylabel('出现次数', fontsize=12)
        plt.title(title, fontsize=14)
        plt.grid(axis='y', alpha=0.3)
        
        # 在柱子上标注数值
        for bar, freq in zip(bars, frequencies):
            if freq > 0:
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                        str(freq), ha='center', va='bottom', fontsize=8)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"图表已保存到：{save_path}")
        
        plt.show()
        
    def plot_sum_trend(self, save_path=None):
        """
        绘制和值趋势图
        :param save_path: 保存路径
        """
        red_data = self.data[self.red_balls].values
        sums = red_data.sum(axis=1)
        
        plt.figure(figsize=(15, 6))
        plt.plot(sums, marker='o', markersize=3, linewidth=1, color='blue')
        
        # 添加移动平均线
        if len(sums) > 10:
            ma10 = pd.Series(sums).rolling(window=10).mean()
            plt.plot(ma10, '--', label='10 期均线', linewidth=2)
        
        # 添加理论均值线
        if self.name == 'ssq':
            theoretical_mean = 102  # (1+33)*6/2
        else:
            theoretical_mean = 90   # (1+35)*5/2
            
        plt.axhline(y=theoretical_mean, color='r', linestyle='--', 
                   label=f'理论均值 ({theoretical_mean})')
        plt.axhline(y=sums.mean(), color='g', linestyle='--', 
                   label=f'实际均值 ({sums.mean():.1f})')
        
        plt.xlabel('期数', fontsize=12)
        plt.ylabel('红球和值', fontsize=12)
        plt.title('红球和值趋势图', fontsize=14)
        plt.legend()
        plt.grid(alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"图表已保存到：{save_path}")
        
        plt.show()
        
    def plot_omission_trend(self, ball_type='red', top_n=10, save_path=None):
        """
        绘制遗漏趋势图（前 N 个高遗漏号码）
        :param ball_type: 球类型
        :param top_n: 显示前 N 个号码
        :param save_path: 保存路径
        """
        if ball_type == 'red':
            balls = self.red_balls
            max_num = 33
        else:
            balls = self.blue_balls
            max_num = 16 if len(self.blue_balls) == 1 else 12
            
        # 计算每个号码的当前遗漏
        omission = {num: 0 for num in range(1, max_num + 1)}
        for idx in range(len(self.data)):
            row = self.data.iloc[idx][balls].values.astype(int)
            for num in range(1, max_num + 1):
                if num in row:
                    omission[num] = 0
                else:
                    omission[num] += 1
        
        # 获取遗漏最大的 N 个号码
        sorted_omission = sorted(omission.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        numbers = [item[0] for item in sorted_omission]
        omissions = [item[1] for item in sorted_omission]
        
        plt.figure(figsize=(12, 6))
        bars = plt.bar(numbers, omissions, color='orange')
        
        plt.xlabel('号码', fontsize=12)
        plt.ylabel('遗漏期数', fontsize=12)
        plt.title(f'{ball_type}球遗漏 Top{top_n}', fontsize=14)
        plt.grid(axis='y', alpha=0.3)
        
        # 标注数值
        for bar, omi in zip(bars, omissions):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                    str(omi), ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"图表已保存到：{save_path}")
        
        plt.show()
        
    def plot_distribution_stats(self, save_path=None):
        """
        绘制分布统计图（和值分布、AC 指数分布等）
        :param save_path: 保存路径
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 1. 和值分布
        red_data = self.data[self.red_balls].values
        sums = red_data.sum(axis=1)
        axes[0, 0].hist(sums, bins=30, edgecolor='black', alpha=0.7, color='lightblue')
        axes[0, 0].axvline(sums.mean(), color='red', linestyle='--', 
                          label=f'均值：{sums.mean():.1f}')
        axes[0, 0].set_xlabel('和值')
        axes[0, 0].set_ylabel('频数')
        axes[0, 0].set_title('红球和值分布')
        axes[0, 0].legend()
        axes[0, 0].grid(alpha=0.3)
        
        # 2. AC 指数分布
        ac_values = []
        for row in red_data:
            diffs = []
            for i in range(len(row)):
                for j in range(i+1, len(row)):
                    diffs.append(abs(int(row[i]) - int(row[j])))
            unique_diffs = len(set(diffs))
            ac = unique_diffs - (len(row) - 1)
            ac_values.append(ac)
            
        axes[0, 1].hist(ac_values, bins=range(min(ac_values), max(ac_values)+2), 
                       edgecolor='black', alpha=0.7, color='lightgreen')
        axes[0, 1].axvline(np.mean(ac_values), color='red', linestyle='--',
                          label=f'均值：{np.mean(ac_values):.2f}')
        axes[0, 1].set_xlabel('AC 指数')
        axes[0, 1].set_ylabel('频数')
        axes[0, 1].set_title('AC 指数分布')
        axes[0, 1].legend()
        axes[0, 1].grid(alpha=0.3)
        
        # 3. 首尾间距分布
        spans = red_data[:, -1] - red_data[:, 0]
        axes[1, 0].hist(spans, bins=20, edgecolor='black', alpha=0.7, color='salmon')
        axes[1, 0].axvline(spans.mean(), color='red', linestyle='--',
                          label=f'均值：{spans.mean():.1f}')
        axes[1, 0].set_xlabel('首尾间距')
        axes[1, 0].set_ylabel('频数')
        axes[1, 0].set_title('首尾间距分布')
        axes[1, 0].legend()
        axes[1, 0].grid(alpha=0.3)
        
        # 4. 连号数量分布
        consecutive_counts = []
        for row in red_data:
            count = 0
            sorted_row = sorted([int(x) for x in row])
            for i in range(len(sorted_row) - 1):
                if sorted_row[i+1] - sorted_row[i] == 1:
                    count += 1
            consecutive_counts.append(count)
            
        axes[1, 1].hist(consecutive_counts, bins=range(max(consecutive_counts)+2), 
                       edgecolor='black', alpha=0.7, color='plum')
        axes[1, 1].axvline(np.mean(consecutive_counts), color='red', linestyle='--',
                          label=f'均值：{np.mean(consecutive_counts):.2f}')
        axes[1, 1].set_xlabel('连号数量')
        axes[1, 1].set_ylabel('频数')
        axes[1, 1].set_title('连号数量分布')
        axes[1, 1].legend()
        axes[1, 1].grid(alpha=0.3)
        
        plt.suptitle('双色球数据统计分析', fontsize=16, y=1.02)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"图表已保存到：{save_path}")
        
        plt.show()
        
    def generate_report(self, save_path=None):
        """
        生成统计分析报告
        :param save_path: 保存路径
        """
        report = []
        report.append("=" * 60)
        report.append("双色球数据统计分析报告")
        report.append("=" * 60)
        report.append(f"\n数据期间：第 {self.data['期数'].min()} 期 - 第 {self.data['期数'].max()} 期")
        report.append(f"总期数：{len(self.data)}\n")
        
        # 1. 基本统计
        report.append("\n【一】基本统计】")
        red_data = self.data[self.red_balls].values
        sums = red_data.sum(axis=1)
        
        report.append(f"\n1. 和值统计:")
        report.append(f"   最小值：{sums.min()}")
        report.append(f"   最大值：{sums.max()}")
        report.append(f"   平均值：{sums.mean():.2f}")
        report.append(f"   中位数：{np.median(sums):.2f}")
        report.append(f"   标准差：{sums.std():.2f}")
        
        # 2. 冷热号
        report.append(f"\n2. 冷热号分析 (最近 50 期):")
        all_red = self.data.tail(50)[self.red_balls].values.flatten().astype(int)
        counter = Counter(all_red)
        sorted_items = sorted(counter.items(), key=lambda x: x[1], reverse=True)
        
        hot = sorted_items[:11]
        cold = sorted_items[-11:]
        
        report.append(f"   热号 (出现最多): {[num for num, _ in hot]}")
        report.append(f"   冷号 (出现最少): {[num for num, _ in cold]}")
        
        # 3. 遗漏分析
        report.append(f"\n3. 遗漏分析:")
        omission = {num: 0 for num in range(1, 34)}
        for idx in range(len(self.data)):
            row = self.data.iloc[idx][self.red_balls].values.astype(int)
            for num in range(1, 34):
                if num in row:
                    omission[num] = 0
                else:
                    omission[num] += 1
        
        sorted_omission = sorted(omission.items(), key=lambda x: x[1], reverse=True)[:10]
        report.append(f"   遗漏 Top10: {[(num, cnt) for num, cnt in sorted_omission]}")
        
        # 4. AC 指数
        report.append(f"\n4. AC 指数分析:")
        ac_values = []
        for row in red_data:
            diffs = []
            for i in range(len(row)):
                for j in range(i+1, len(row)):
                    diffs.append(abs(int(row[i]) - int(row[j])))
            ac = len(set(diffs)) - 5
            ac_values.append(ac)
            
        report.append(f"   最小值：{min(ac_values)}")
        report.append(f"   最大值：{max(ac_values)}")
        report.append(f"   平均值：{np.mean(ac_values):.2f}")
        
        # 5. 连号分析
        report.append(f"\n5. 连号分析:")
        consecutive_counts = []
        for row in red_data:
            count = 0
            sorted_row = sorted([int(x) for x in row])
            for i in range(len(sorted_row) - 1):
                if sorted_row[i+1] - sorted_row[i] == 1:
                    count += 1
            consecutive_counts.append(count)
        
        report.append(f"   无连号期数：{consecutive_counts.count(0)} ({consecutive_counts.count(0)/len(consecutive_counts)*100:.1f}%)")
        report.append(f"   1 组连号期数：{consecutive_counts.count(1)} ({consecutive_counts.count(1)/len(consecutive_counts)*100:.1f}%)")
        report.append(f"   2 组及以上：{sum(1 for c in consecutive_counts if c >= 2)} ({sum(1 for c in consecutive_counts if c >= 2)/len(consecutive_counts)*100:.1f}%)")
        
        # 6. 蓝球分析
        if len(self.blue_balls) == 1:
            report.append(f"\n6. 蓝球分析:")
            blue_data = self.data[self.blue_balls].values.flatten().astype(int)
            blue_counter = Counter(blue_data)
            blue_sorted = sorted(blue_counter.items(), key=lambda x: x[1], reverse=True)
            
            report.append(f"   最热蓝球：{blue_sorted[0][0]} (出现{blue_sorted[0][1]}次)")
            report.append(f"   最冷蓝球：{blue_sorted[-1][0]} (出现{blue_sorted[-1][1]}次)")
        
        report_str = "\n".join(report)
        print(report_str)
        
        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(report_str)
            logger.info(f"报告已保存到：{save_path}")
            
        return report_str


def run_analysis(name='ssq', plot=False, report=False, output_dir='./analysis_output/'):
    """
    运行分析
    :param name: 玩法名称
    :param plot: 是否生成图表
    :param report: 是否生成报告
    :param output_dir: 输出目录
    """
    import os
    
    data_path = "{}{}".format(name_path[name]["path"], data_file_name)
    
    if not os.path.exists(data_path):
        logger.error("数据文件不存在，请先执行 get_data.py 获取数据！")
        return
        
    data = pd.read_csv(data_path)
    logger.info(f"加载历史数据：{len(data)}期")
    
    # 创建输出目录
    if plot or report:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    analyzer = LotteryAnalyzer(data, name)
    
    if plot:
        logger.info("正在生成图表...")
        analyzer.plot_frequency('red', save_path=f"{output_dir}红球频率分布.png")
        analyzer.plot_frequency('blue', save_path=f"{output_dir}蓝球频率分布.png")
        analyzer.plot_sum_trend(save_path=f"{output_dir}和值趋势.png")
        analyzer.plot_omission_trend('red', save_path=f"{output_dir}红球遗漏.png")
        analyzer.plot_distribution_stats(save_path=f"{output_dir}统计分布.png")
        logger.info(f"图表已保存到：{output_dir}")
    
    if report:
        logger.info("正在生成报告...")
        analyzer.generate_report(save_path=f"{output_dir}统计分析报告.txt")
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', default="ssq", type=str, help="选择分析数据：双色球/大乐透")
    parser.add_argument('--plot', action='store_true', help="是否生成图表")
    parser.add_argument('--report', action='store_true', help="是否生成报告")
    parser.add_argument('--output', default='./analysis_output/', type=str, help="输出目录")
    args = parser.parse_args()
    
    run_analysis(args.name, args.plot, args.report, args.output)
