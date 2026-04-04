# -*- coding: utf-8 -*-
"""
遗传算法策略
使用遗传算法优化号码组合
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from deap import base, creator, tools, algorithms
import random
from .base_strategy import BaseStrategy
from loguru import logger


class GeneticStrategy(BaseStrategy):
    """遗传算法优化策略"""

    def __init__(self, name: str = "genetic", config: Dict[str, Any] = None):
        """
        初始化遗传算法策略

        Args:
            config: {
                'population_size': 100,
                'generations': 50,
                'crossover_prob': 0.7,
                'mutation_prob': 0.2,
                'tournament_size': 3,
                'window_size': 50  # 统计窗口大小
            }
        """
        default_config = {
            'population_size': 100,
            'generations': 50,
            'crossover_prob': 0.7,
            'mutation_prob': 0.2,
            'tournament_size': 3,
            'window_size': 50
        }
        config = {**default_config, **(config or {})}
        super().__init__(name, config)

        # 定义适应度函数（最大化）
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)

        self.toolbox = base.Toolbox()
        self.historical_stats: Dict[str, Any] = {}
        self._setup_deap()

    def _setup_deap(self):
        """设置 DEAP 工具箱"""
        # 注册个体生成（6个不重复的红球，范围1-33）
        self.toolbox.register("individual", tools.initIterate, creator.Individual, self._generate_individual)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)

        # 注册评估函数
        self.toolbox.register("evaluate", self._evaluate_individual)

        # 注册遗传操作
        self.toolbox.register("mate", tools.cxTwoPoint)
        self.toolbox.register("mutate", self._mutate_individual)
        self.toolbox.register("select", tools.selTournament, tournsize=self.config['tournament_size'])

    def _generate_individual(self) -> List[int]:
        """生成一个有效个体（6个不重复红球）"""
        return sorted(random.sample(range(1, 34), 6))

    def _mutate_individual(self, individual: List[int]) -> Tuple[List[int]]:
        """变异操作：随机替换一个号码"""
        if random.random() < 0.5:
            # 替换一个号码
            idx = random.randint(0, 5)
            available = [n for n in range(1, 34) if n not in individual]
            if available:
                individual[idx] = random.choice(available)
        else:
            # 交换两个号码
            idx1, idx2 = random.sample(range(6), 2)
            individual[idx1], individual[idx2] = individual[idx2], individual[idx1]

        individual.sort()
        return (individual,)

    def _calculate_frequency_weights(self, data: pd.DataFrame) -> Dict[int, float]:
        """计算号码频率权重"""
        red_cols = [col for col in data.columns if '红球' in col]
        all_reds = data[red_cols].values.flatten().astype(int)
        from collections import Counter
        counter = Counter(all_reds)
        total = len(all_reds)

        weights = {}
        for num in range(1, 34):
            weights[num] = counter.get(num, 0) / total if total > 0 else 0
        return weights

    def _calculate_omission_weights(self, data: pd.DataFrame) -> Dict[int, float]:
        """计算遗漏权重（遗漏越久权重越高）"""
        red_cols = sorted([col for col in data.columns if '红球' in col])
        max_num = 33

        # 计算每个号码的当前遗漏
        omission = {i: 0 for i in range(1, max_num + 1)}

        for idx in range(len(data) - 1, -1, -1):
            row = data.iloc[idx]
            reds = [int(row[col]) for col in red_cols]
            for num in range(1, max_num + 1):
                if num in reds:
                    break
                omission[num] += 1

        # 归一化
        max_omission = max(omission.values()) if omission.values() else 1
        weights = {num: omission[num] / max_omission for num in range(1, 34)}
        return weights

    def _evaluate_individual(self, individual: List[int]) -> Tuple[float]:
        """
        评估个体适应度

        Args:
            individual: 6个红球号码列表

        Returns:
            适应度分数
        """
        score = 0.0

        # 1. 频率权重
        for ball in individual:
            score += self.historical_stats['frequency_weights'].get(ball, 0) * 10

        # 2. 遗漏权重
        for ball in individual:
            score += self.historical_stats['omission_weights'].get(ball, 0) * 8

        # 3. 和值约束（双色球和值通常在 90-120 之间）
        sum_value = sum(individual)
        sum_mean = self.historical_stats.get('sum_mean', 105)
        sum_std = self.historical_stats.get('sum_std', 15)
        if sum_mean - sum_std <= sum_value <= sum_mean + sum_std:
            score += 5
        else:
            score -= 2

        # 4. AC 指数约束（4-10）
        diffs = []
        for i in range(len(individual)):
            for j in range(i+1, len(individual)):
                diffs.append(abs(individual[i] - individual[j]))
        ac = len(set(diffs)) - (len(individual) - 1)
        if 4 <= ac <= 10:
            score += 3

        # 5. 奇偶比例（通常3:3或2:4或4:2）
        odd_count = sum(1 for b in individual if b % 2 == 1)
        if odd_count in [3, 2, 4]:
            score += 2

        # 6. 大小分布（大小定义：1-16为小，17-33为大）
        small_count = sum(1 for b in individual if b <= 16)
        if small_count in [2, 3, 4]:
            score += 2

        return (score,)

    def train(self, data: pd.DataFrame) -> None:
        """
        训练遗传算法（计算历史统计特征）

        Args:
            data: 历史数据
        """
        logger.info(f"开始训练 {self.name} 策略...")
        self.history_data = data.copy()

        window_size = self.config['window_size']
        recent_data = data.iloc[-window_size:] if len(data) > window_size else data

        # 计算统计特征
        self.historical_stats['frequency_weights'] = self._calculate_frequency_weights(recent_data)
        self.historical_stats['omission_weights'] = self._calculate_omission_weights(recent_data)

        red_cols = [col for col in recent_data.columns if '红球' in col]
        all_reds = recent_data[red_cols].values.flatten().astype(int)
        sums = recent_data[red_cols].astype(int).sum(axis=1)

        self.historical_stats['sum_mean'] = np.mean(sums)
        self.historical_stats['sum_std'] = np.std(sums)

        self.is_trained = True
        logger.info(f"{self.name} 策略训练完成（统计特征已计算）")

    def predict(
        self,
        recent_data: pd.DataFrame,
        n_predictions: int = 1
    ) -> Dict[str, List[int]]:
        """
        使用遗传算法生成预测

        Args:
            recent_data: 最近N期数据
            n_predictions: 预测期数

        Returns:
            {'red': [...], 'blue': [...]}
        """
        if not self.is_trained:
            raise RuntimeError("模型未训练，请先调用 train()")

        # 更新统计权重（基于最新数据）
        window_size = self.config['window_size']
        recent_window = recent_data.iloc[-window_size:] if len(recent_data) > window_size else recent_data
        self.historical_stats['frequency_weights'] = self._calculate_frequency_weights(recent_window)
        self.historical_stats['omission_weights'] = self._calculate_omission_weights(recent_window)

        red_cols = [col for col in recent_window.columns if '红球' in col]
        sums = recent_window[red_cols].astype(int).sum(axis=1)
        self.historical_stats['sum_mean'] = np.mean(sums)
        self.historical_stats['sum_std'] = np.std(sums)

        # 初始化种群
        pop_size = self.config['population_size']
        population = self.toolbox.population(n=pop_size)

        # 评估初始种群
        fitnesses = list(map(self.toolbox.evaluate, population))
        for ind, fit in zip(population, fitnesses):
            ind.fitness.values = fit

        # 进化
        generations = self.config['generations']
        cxpb = self.config['crossover_prob']
        mutpb = self.config['mutation_prob']

        for gen in range(generations):
            # 选择
            offspring = self.toolbox.select(population, len(population))
            offspring = list(map(self.toolbox.clone, offspring))

            # 交叉
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < cxpb:
                    self.toolbox.mate(child1, child2)
                    del child1.fitness.values
                    del child2.fitness.values

            # 变异
            for mutant in offspring:
                if random.random() < mutpb:
                    self.toolbox.mutate(mutant)
                    del mutant.fitness.values

            # 重新评估
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = map(self.toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit

            # 替换种群
            population[:] = offspring

            # 日志
            if (gen + 1) % 10 == 0:
                best_fit = max(ind.fitness.values[0] for ind in population)
                logger.debug(f"  第 {gen+1} 代，最佳适应度: {best_fit:.2f}")

        # 选择最佳个体
        best_individual = tools.selBest(population, 1)[0]
        predicted_red = sorted(best_individual)

        # 蓝球预测
        predicted_blue = self._predict_blue(recent_data)

        logger.info(f"{self.name} 策略完成，适应度: {best_individual.fitness.values[0]:.2f}")

        return {
            'red': predicted_red,
            'blue': predicted_blue
        }

    def _predict_blue(self, recent_data: pd.DataFrame) -> List[int]:
        """预测蓝球"""
        blue_cols = [col for col in recent_data.columns if '蓝球' in col]
        if not blue_cols:
            return [6]

        blue_series = recent_data[blue_cols[0]].astype(int)
        from collections import Counter
        counter = Counter(blue_series)
        most_common = counter.most_common(3)
        if most_common:
            return [most_common[0][0]]
        else:
            return [int(blue_series.mode()[0]) if len(blue_series.mode()) > 0 else 6]
