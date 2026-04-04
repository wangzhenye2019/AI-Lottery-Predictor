# -*- coding: utf-8 -*-
"""
服务层 - 业务逻辑封装
Author: BigCat
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from database.data_manager import data_manager
from utils.logger_new import get_logger, log_performance
from utils.exceptions_new import LotteryError, DataError, NetworkError, ValidationError
from config_new import config

logger = get_logger(__name__)


class BaseService(ABC):
    """服务基类"""
    
    def __init__(self):
        self.data_manager = data_manager
    
    @log_performance
    def validate_lottery_type(self, lottery_type: str) -> bool:
        """验证彩票类型"""
        valid_types = ['ssq', 'dlt', 'qlc', 'fc3d', 'kl8', 'pl3', 'pl5', 'qxc']
        if lottery_type not in valid_types:
            raise ValidationError(f"不支持的彩票类型: {lottery_type}")
        return True
    
    @log_performance
    def validate_issue(self, issue: str) -> bool:
        """验证期号格式"""
        if not issue or not isinstance(issue, str):
            raise ValidationError("期号不能为空")
        return True


class DataSyncService(BaseService):
    """数据同步服务"""
    
    @log_performance
    def sync_lottery_data(self, lottery_type: str, source: str = 'official') -> Dict[str, Any]:
        """同步彩票数据"""
        try:
            self.validate_lottery_type(lottery_type)
            
            logger.info(f"开始同步 {lottery_type} 数据，来源: {source}")
            
            # 这里可以调用不同的爬虫服务
            if source == 'official':
                return self._sync_from_official(lottery_type)
            elif source == '500':
                return self._sync_from_500(lottery_type)
            else:
                raise ValidationError(f"不支持的数据源: {source}")
        
        except Exception as e:
            logger.error(f"同步数据失败: {e}")
            raise DataError(f"同步数据失败: {e}")
    
    def _sync_from_official(self, lottery_type: str) -> Dict[str, Any]:
        """从官方源同步数据"""
        try:
            from crawlers.cwl_crawler import CwlCrawler
            
            crawler = CwlCrawler()
            results = crawler.fetch_recent_draws(lottery_type, limit=100)
            
            success_count = 0
            for result in results:
                if self.data_manager.db_manager.save_lottery_draw(
                    lottery_type=lottery_type,
                    issue=result['issue'],
                    draw_date=result['draw_date'],
                    numbers=result['numbers']
                ):
                    success_count += 1
            
            return {
                'success': True,
                'total': len(results),
                'imported': success_count,
                'source': 'official'
            }
        except ImportError:
            raise NetworkError("官方爬虫模块不可用")
        except Exception as e:
            raise NetworkError(f"从官方源同步失败: {e}")
    
    def _sync_from_500(self, lottery_type: str) -> Dict[str, Any]:
        """从500网同步数据"""
        try:
            from crawlers.fivehundred_crawler import FiveHundredCrawler
            
            crawler = FiveHundredCrawler()
            results = crawler.fetch_recent_draws(lottery_type, limit=100)
            
            success_count = 0
            for result in results:
                if self.data_manager.db_manager.save_lottery_draw(
                    lottery_type=lottery_type,
                    issue=result['issue'],
                    draw_date=result['draw_date'],
                    numbers=result['numbers']
                ):
                    success_count += 1
            
            return {
                'success': True,
                'total': len(results),
                'imported': success_count,
                'source': '500'
            }
        except ImportError:
            raise NetworkError("500网爬虫模块不可用")
        except Exception as e:
            raise NetworkError(f"从500网同步失败: {e}")


class PredictionService(BaseService):
    """预测服务"""
    
    @log_performance
    def predict(self, lottery_type: str, strategy_name: str, **kwargs) -> Dict[str, Any]:
        """执行预测"""
        try:
            self.validate_lottery_type(lottery_type)
            
            logger.info(f"开始预测: {lottery_type} - {strategy_name}")
            
            # 获取策略
            strategy = self._get_strategy(strategy_name)
            if not strategy:
                raise ValidationError(f"不支持的策略: {strategy_name}")
            
            # 获取历史数据
            historical_data = self.data_manager.db_manager.get_lottery_draws(lottery_type, limit=500)
            if not historical_data:
                raise DataError("没有足够的历史数据")
            
            # 执行预测
            start_time = datetime.now()
            prediction_result = strategy.predict(historical_data, **kwargs)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 保存预测结果
            issue = self._generate_next_issue(lottery_type)
            self.data_manager.db_manager.save_prediction_result(
                lottery_type=lottery_type,
                strategy_name=strategy_name,
                issue=issue,
                predicted_numbers=prediction_result['numbers'],
                confidence_score=prediction_result.get('confidence')
            )
            
            return {
                'success': True,
                'lottery_type': lottery_type,
                'strategy_name': strategy_name,
                'issue': issue,
                'numbers': prediction_result['numbers'],
                'confidence': prediction_result.get('confidence'),
                'execution_time': execution_time,
                'metadata': prediction_result.get('metadata', {})
            }
        
        except Exception as e:
            logger.error(f"预测失败: {e}")
            raise LotteryError(f"预测失败: {e}")
    
    def _get_strategy(self, strategy_name: str):
        """获取策略实例"""
        try:
            from strategies.strategy_manager import StrategyManager
            manager = StrategyManager()
            return manager.get_strategy(strategy_name)
        except ImportError:
            raise ValidationError("策略管理器不可用")
    
    def _generate_next_issue(self, lottery_type: str) -> str:
        """生成下一期期号"""
        try:
            # 获取最新一期
            latest_draws = self.data_manager.db_manager.get_lottery_draws(lottery_type, limit=1)
            if latest_draws:
                latest_issue = latest_draws[0]['issue']
                # 简单的期号递增逻辑，需要根据实际规则调整
                return str(int(latest_issue) + 1)
            else:
                # 如果没有历史数据，生成默认期号
                today = datetime.now()
                return f"{today.year}{today.month:02d}{today.day:02d:03d}"
        except Exception:
            return f"{datetime.now().strftime('%Y%m%d')}001"


class AnalysisService(BaseService):
    """分析服务"""
    
    @log_performance
    def analyze_trends(self, lottery_type: str, analysis_type: str = 'frequency') -> Dict[str, Any]:
        """分析趋势"""
        try:
            self.validate_lottery_type(lottery_type)
            
            logger.info(f"开始分析: {lottery_type} - {analysis_type}")
            
            # 获取历史数据
            historical_data = self.data_manager.db_manager.get_lottery_draws(lottery_type, limit=1000)
            if not historical_data:
                raise DataError("没有足够的历史数据")
            
            # 根据分析类型执行不同的分析
            if analysis_type == 'frequency':
                return self._analyze_frequency(lottery_type, historical_data)
            elif analysis_type == 'trend':
                return self._analyze_trend(lottery_type, historical_data)
            elif analysis_type == 'statistics':
                return self._analyze_statistics(lottery_type, historical_data)
            else:
                raise ValidationError(f"不支持的分析类型: {analysis_type}")
        
        except Exception as e:
            logger.error(f"分析失败: {e}")
            raise LotteryError(f"分析失败: {e}")
    
    def _analyze_frequency(self, lottery_type: str, historical_data: List[Dict]) -> Dict[str, Any]:
        """频率分析"""
        from collections import Counter
        
        # 统计号码频率
        all_numbers = []
        for draw in historical_data:
            all_numbers.extend(draw['numbers'])
        
        frequency = Counter(all_numbers)
        
        # 获取彩票类型的号码范围
        number_ranges = {
            'ssq': {'red': (1, 33), 'blue': (1, 16)},
            'dlt': {'red': (1, 35), 'blue': (1, 12)},
            'qlc': {'red': (1, 30), 'blue': (1, 30)},
        }
        
        ranges = number_ranges.get(lottery_type, {'red': (1, 33), 'blue': (1, 16)})
        
        # 计算热温冷号
        total_draws = len(historical_data)
        hot_threshold = total_draws * 0.6
        warm_threshold = total_draws * 0.3
        
        hot_numbers = [num for num, count in frequency.items() if count >= hot_threshold]
        warm_numbers = [num for num, count in frequency.items() if warm_threshold <= count < hot_threshold]
        cold_numbers = [num for num, count in frequency.items() if count < warm_threshold]
        
        return {
            'analysis_type': 'frequency',
            'total_draws': total_draws,
            'frequency': dict(frequency),
            'hot_numbers': hot_numbers,
            'warm_numbers': warm_numbers,
            'cold_numbers': cold_numbers,
            'number_ranges': ranges
        }
    
    def _analyze_trend(self, lottery_type: str, historical_data: List[Dict]) -> Dict[str, Any]:
        """趋势分析"""
        # 实现趋势分析逻辑
        return {
            'analysis_type': 'trend',
            'message': '趋势分析功能待完善'
        }
    
    def _analyze_statistics(self, lottery_type: str, historical_data: List[Dict]) -> Dict[str, Any]:
        """统计分析"""
        import numpy as np
        
        # 基本统计信息
        all_numbers = []
        for draw in historical_data:
            all_numbers.extend(draw['numbers'])
        
        numbers_array = np.array(all_numbers)
        
        return {
            'analysis_type': 'statistics',
            'total_draws': len(historical_data),
            'total_numbers': len(all_numbers),
            'mean': float(np.mean(numbers_array)),
            'median': float(np.median(numbers_array)),
            'std': float(np.std(numbers_array)),
            'min': int(np.min(numbers_array)),
            'max': int(np.max(numbers_array)),
            'range': [int(np.min(numbers_array)), int(np.max(numbers_array))]
        }


class ExportService(BaseService):
    """导出服务"""
    
    @log_performance
    def export_results(self, lottery_type: str, export_format: str = 'json', **kwargs) -> Dict[str, Any]:
        """导出结果"""
        try:
            self.validate_lottery_type(lottery_type)
            
            logger.info(f"开始导出: {lottery_type} - {export_format}")
            
            if export_format == 'json':
                return self._export_json(lottery_type, **kwargs)
            elif export_format == 'csv':
                return self._export_csv(lottery_type, **kwargs)
            elif export_format == 'txt':
                return self._export_txt(lottery_type, **kwargs)
            else:
                raise ValidationError(f"不支持的导出格式: {export_format}")
        
        except Exception as e:
            logger.error(f"导出失败: {e}")
            raise LotteryError(f"导出失败: {e}")
    
    def _export_json(self, lottery_type: str, **kwargs) -> Dict[str, Any]:
        """导出JSON格式"""
        import json
        
        # 获取预测结果
        results = self.data_manager.db_manager.get_prediction_results(lottery_type, limit=100)
        
        export_data = {
            'lottery_type': lottery_type,
            'export_time': datetime.now().isoformat(),
            'total_results': len(results),
            'results': results
        }
        
        filename = f"{lottery_type}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = Path(config.output_dir) / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return {
            'success': True,
            'format': 'json',
            'filename': filename,
            'filepath': str(filepath),
            'count': len(results)
        }
    
    def _export_csv(self, lottery_type: str, **kwargs) -> Dict[str, Any]:
        """导出CSV格式"""
        return self.data_manager.export_database_to_csv(lottery_type)
    
    def _export_txt(self, lottery_type: str, **kwargs) -> Dict[str, Any]:
        """导出TXT格式"""
        # 调用现有的导出功能
        try:
            from export_results import LotteryResultExporter
            
            results = self.data_manager.db_manager.get_prediction_results(lottery_type, limit=10)
            
            # 转换格式
            formatted_results = []
            for result in results:
                numbers = result['predicted_numbers']
                if lottery_type == 'ssq':
                    formatted_results.append({
                        'red': numbers[:6],
                        'blue': numbers[6:]
                    })
                # 其他彩票类型的格式转换
            
            exporter = LotteryResultExporter(lottery_type)
            content = exporter.export_single_bets(formatted_results, "latest")
            
            filename = f"{lottery_type}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = Path(config.output_dir) / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                'success': True,
                'format': 'txt',
                'filename': filename,
                'filepath': str(filepath),
                'count': len(formatted_results)
            }
        except ImportError:
            raise ValidationError("导出模块不可用")


# 服务实例
data_sync_service = DataSyncService()
prediction_service = PredictionService()
analysis_service = AnalysisService()
export_service = ExportService()
