#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应用初始化模块 - 统一处理启动检查和资源准备
Author: BigCat
"""
import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class CheckResult:
    """检查结果数据类"""
    name: str
    passed: bool
    message: str
    fixable: bool = False
    fix_action: Optional[str] = None


class AppInitializer:
    """应用初始化器 - 检查环境并准备资源"""

    def __init__(self):
        self.checks: List[CheckResult] = []
        self.config_dir = Path("config")
        self.data_dir = Path("data")
        self.models_dir = Path("data/models")

    def run_all_checks(self) -> Tuple[bool, List[CheckResult]]:
        """运行所有检查"""
        logger.info("🔍 开始应用初始化检查...")

        checks = [
            self._check_python_version,
            self._check_dependencies,
            self._check_directories,
            self._check_config_files,
            self._check_model_files,
            self._check_database,
        ]

        for check in checks:
            try:
                result = check()
                self.checks.append(result)
                if result.passed:
                    logger.info(f"✅ {result.name}: {result.message}")
                else:
                    logger.warning(f"⚠️ {result.name}: {result.message}")
            except Exception as e:
                logger.error(f"❌ {check.__name__} 执行失败: {e}")
                self.checks.append(CheckResult(
                    name=check.__name__,
                    passed=False,
                    message=f"检查失败: {e}",
                    fixable=False
                ))

        all_passed = all(c.passed for c in self.checks)

        if all_passed:
            logger.info("✅ 所有检查通过，应用可以正常启动")
        else:
            failed = [c for c in self.checks if not c.passed]
            logger.warning(f"⚠️ {len(failed)} 项检查未通过")

        return all_passed, self.checks

    def _check_python_version(self) -> CheckResult:
        """检查Python版本"""
        version = sys.version_info
        min_version = (3, 8)

        if version >= min_version:
            return CheckResult(
                name="Python版本",
                passed=True,
                message=f"Python {version.major}.{version.minor}.{version.micro}"
            )
        else:
            return CheckResult(
                name="Python版本",
                passed=False,
                message=f"需要Python {min_version[0]}.{min_version[1]}+，当前 {version.major}.{version.minor}",
                fixable=False
            )

    def _check_dependencies(self) -> CheckResult:
        """检查依赖包"""
        required = [
            "customtkinter",
            "loguru",
            "pandas",
            "numpy",
            "tensorflow",
            "requests",
            "bs4",
        ]

        missing = []
        for package in required:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)

        if not missing:
            return CheckResult(
                name="依赖包",
                passed=True,
                message="所有依赖包已安装"
            )
        else:
            return CheckResult(
                name="依赖包",
                passed=False,
                message=f"缺少依赖: {', '.join(missing)}",
                fixable=True,
                fix_action=f"pip install {' '.join(missing)}"
            )

    def _check_directories(self) -> CheckResult:
        """检查目录结构"""
        dirs = ["data", "data/models", "data/logs", "outputs", "config"]
        created = []

        for d in dirs:
            path = Path(d)
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                created.append(d)

        return CheckResult(
            name="目录结构",
            passed=True,
            message=f"目录检查完成{'，已创建: ' + ', '.join(created) if created else ''}"
        )

    def _check_config_files(self) -> CheckResult:
        """检查配置文件"""
        config_file = Path("config/app_config.json")

        if config_file.exists():
            return CheckResult(
                name="配置文件",
                passed=True,
                message="配置文件存在"
            )

        # 创建默认配置
        default_config = {
            "theme": "light",
            "auto_update": True,
            "data_sources": {
                "primary": "cwl",
                "fallback": "500"
            },
            "prediction": {
                "default_strategy": "XGBoost梯度提升",
                "confidence_threshold": 0.7
            },
            "notifications": {
                "enabled": True,
                "sound": False
            }
        }

        try:
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)

            return CheckResult(
                name="配置文件",
                passed=True,
                message="已创建默认配置文件",
                fixable=True
            )
        except Exception as e:
            return CheckResult(
                name="配置文件",
                passed=False,
                message=f"创建配置文件失败: {e}",
                fixable=False
            )

    def _check_model_files(self) -> CheckResult:
        """检查模型文件"""
        lottery_types = ["ssq", "dlt", "qlc", "fc3d"]
        missing_models = []

        for lt in lottery_types:
            model_path = self.models_dir / lt
            if not model_path.exists() or not any(model_path.iterdir()):
                missing_models.append(lt)

        if not missing_models:
            return CheckResult(
                name="模型文件",
                passed=True,
                message="模型文件已就绪"
            )
        else:
            return CheckResult(
                name="模型文件",
                passed=False,
                message=f"缺少模型: {', '.join(missing_models)}，请先训练模型",
                fixable=True,
                fix_action="运行训练脚本: python scripts/train.py"
            )

    def _check_database(self) -> CheckResult:
        """检查数据库"""
        db_file = self.data_dir / "lottery.db"

        try:
            if not db_file.exists():
                # 数据库将在首次使用时自动创建
                return CheckResult(
                    name="数据库",
                    passed=True,
                    message="数据库将在首次使用时创建"
                )

            # 检查数据库可访问
            import sqlite3
            conn = sqlite3.connect(str(db_file))
            conn.execute("SELECT 1")
            conn.close()

            return CheckResult(
                name="数据库",
                passed=True,
                message="数据库连接正常"
            )
        except Exception as e:
            return CheckResult(
                name="数据库",
                passed=False,
                message=f"数据库检查失败: {e}",
                fixable=True,
                fix_action="删除 data/lottery.db 后重试"
            )

    def generate_report(self) -> str:
        """生成检查报告"""
        lines = ["=" * 50, "应用初始化检查报告", "=" * 50, ""]

        passed = sum(1 for c in self.checks if c.passed)
        total = len(self.checks)

        lines.append(f"检查结果: {passed}/{total} 通过\n")

        for check in self.checks:
            status = "✅" if check.passed else "⚠️"
            lines.append(f"{status} {check.name}")
            lines.append(f"   {check.message}")
            if not check.passed and check.fix_action:
                lines.append(f"   修复: {check.fix_action}")
            lines.append("")

        return "\n".join(lines)


def initialize_app() -> bool:
    """便捷函数: 初始化应用"""
    initializer = AppInitializer()
    passed, checks = initializer.run_all_checks()

    print(initializer.generate_report())

    return passed


if __name__ == "__main__":
    success = initialize_app()
    sys.exit(0 if success else 1)
