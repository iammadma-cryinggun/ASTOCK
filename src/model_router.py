# -*- coding: utf-8 -*-
"""
===================================
多模型管理器 - 智能路由和负载均衡
===================================

职责：
1. 管理多个云端API模型
2. 智能选择最佳模型
3. 自动故障切换
4. 成本优化

支持模型：
- DeepSeek（主力）
- 通义千问
- Kimi（Moonshot）
- 智谱GLM
- Gemini（免费兜底）
"""

import logging
import random
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """模型配置"""
    name: str                    # 模型名称
    api_key: str                 # API Key
    base_url: str                # API地址
    model: str                   # 模型标识
    priority: int = 0            # 优先级（0最高）
    cost_per_million: float = 0  # 每百万tokens价格（人民币）
    free_quota: int = 0          # 免费额度（tokens）
    speed: str = "medium"        # 速度：fast/medium/slow
    strengths: List[str] = None   # 专长
    available: bool = True       # 是否可用

    def __post_init__(self):
        if self.strengths is None:
            self.strengths = []


class ModelRouter:
    """
    多模型路由器

    策略：
    1. 优先使用免费额度
    2. 按优先级选择
    3. 自动故障切换
    4. 成本优化
    """

    def __init__(self):
        self.models: Dict[str, ModelConfig] = {}
        self.failure_count: Dict[str, int] = {}
        self.last_failure_time: Dict[str, datetime] = {}
        self.cooldown_period = timedelta(minutes=5)  # 故障冷却期

    def register_model(self, config: ModelConfig) -> None:
        """注册模型"""
        self.models[config.name] = config
        self.failure_count[config.name] = 0
        logger.info(f"[ModelRouter] 注册模型: {config.name} (优先级: {config.priority})")

    def get_best_model(self, task_type: str = "general") -> Optional[ModelConfig]:
        """
        智能选择最佳模型

        Args:
            task_type: 任务类型（general/analysis/sentiment/long_text）

        Returns:
            最佳模型配置，或None
        """
        available_models = []

        for name, config in self.models.items():
            # 检查是否可用
            if not config.available:
                continue

            # 检查是否在冷却期
            if name in self.last_failure_time:
                if datetime.now() - self.last_failure_time[name] < self.cooldown_period:
                    continue

            # 检查失败次数
            if self.failure_count.get(name, 0) >= 3:
                continue

            # 任务匹配度评分
            score = self._calculate_score(config, task_type)
            available_models.append((score, config))

        if not available_models:
            logger.warning("[ModelRouter] 没有可用的模型")
            return None

        # 按评分排序，返回最高分
        available_models.sort(key=lambda x: x[0], reverse=True)
        best_model = available_models[0][1]

        logger.debug(f"[ModelRouter] 选择模型: {best_model.name} (评分: {available_models[0][0]:.2f})")
        return best_model

    def _calculate_score(self, config: ModelConfig, task_type: str) -> float:
        """
        计算模型适配度评分

        评分因素：
        1. 优先级（权重30%）
        2. 成本（权重30%）
        3. 任务匹配（权重20%）
        4. 速度（权重10%）
        5. 免费额度（权重10%）
        """
        score = 0.0

        # 1. 优先级（0-100分，优先级越高分越高）
        priority_score = 100 - (config.priority * 10)
        score += priority_score * 0.3

        # 2. 成本（越便宜分越高）
        if config.cost_per_million == 0:
            cost_score = 100
        elif config.cost_per_million <= 1:
            cost_score = 90
        elif config.cost_per_million <= 5:
            cost_score = 70
        elif config.cost_per_million <= 20:
            cost_score = 50
        else:
            cost_score = 30
        score += cost_score * 0.3

        # 3. 任务匹配度
        if config.strengths:
            if task_type in config.strengths:
                match_score = 100
            elif "general" in config.strengths:
                match_score = 80
            else:
                match_score = 50
        else:
            match_score = 60
        score += match_score * 0.2

        # 4. 速度
        speed_scores = {"fast": 100, "medium": 70, "slow": 40}
        speed_score = speed_scores.get(config.speed, 70)
        score += speed_score * 0.1

        # 5. 免费额度加分
        if config.free_quota > 0:
            score += 10 * 0.1

        return score

    def mark_failure(self, model_name: str, error: str) -> None:
        """标记模型失败"""
        self.failure_count[model_name] = self.failure_count.get(model_name, 0) + 1
        self.last_failure_time[model_name] = datetime.now()

        logger.warning(
            f"[ModelRouter] 模型 {model_name} 失败 "
            f"(第{self.failure_count[model_name]}次): {error[:100]}"
        )

        # 如果失败次数过多，暂时禁用
        if self.failure_count[model_name] >= 5:
            if model_name in self.models:
                self.models[model_name].available = False
                logger.error(f"[ModelRouter] 模型 {model_name} 已被暂时禁用")

    def mark_success(self, model_name: str) -> None:
        """标记模型成功，重置失败计数"""
        if model_name in self.failure_count:
            self.failure_count[model_name] = 0

        if model_name in self.models:
            self.models[model_name].available = True

        logger.debug(f"[ModelRouter] 模型 {model_name} 调用成功")

    def get_available_models(self) -> List[str]:
        """获取所有可用模型列表"""
        return [name for name, config in self.models.items() if config.available]

    def reset_all(self) -> None:
        """重置所有模型状态（用于定期恢复）"""
        for name in self.models:
            self.failure_count[name] = 0
            self.models[name].available = True
        logger.info("[ModelRouter] 已重置所有模型状态")


# 全局路由器实例
_router: Optional[ModelRouter] = None


def get_model_router() -> ModelRouter:
    """获取全局模型路由器"""
    global _router
    if _router is None:
        _router = ModelRouter()
        _initialize_default_models()
    return _router


def _initialize_default_models() -> None:
    """初始化默认模型配置（从环境变量读取）"""
    import os
    from src.config import get_config
    config = get_config()

    router = get_model_router()

    # 1. DeepSeek（主力，便宜）
    if config.openai_api_key and "deepseek" in config.openai_base_url.lower():
        router.register_model(ModelConfig(
            name="deepseek",
            api_key=config.openai_api_key,
            base_url=config.openai_base_url,
            model=config.openai_model or "deepseek-chat",
            priority=0,
            cost_per_million=1.0,
            free_quota=0,
            speed="fast",
            strengths=["general", "analysis"],
            available=True
        ))

    # 2. 通义千问（备选，便宜）
    qwen_key = os.getenv("QWEN_API_KEY")
    if qwen_key:
        router.register_model(ModelConfig(
            name="qwen",
            api_key=qwen_key,
            base_url=os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            model=os.getenv("QWEN_MODEL", "qwen-turbo"),
            priority=1,
            cost_per_million=0.5,
            free_quota=0,
            speed="fast",
            strengths=["sentiment", "fast_analysis"],
            available=True
        ))

    # 3. Kimi（长文本）
    kimi_key = os.getenv("KIMI_API_KEY")
    if kimi_key:
        router.register_model(ModelConfig(
            name="kimi",
            api_key=kimi_key,
            base_url="https://api.moonshot.cn/v1",
            model=os.getenv("KIMI_MODEL", "moonshot-v1-8k"),
            priority=2,
            cost_per_million=12.0,
            free_quota=0,
            speed="medium",
            strengths=["long_text", "deep_analysis"],
            available=True
        ))

    # 4. Gemini（免费兜底）
    if config.gemini_api_key:
        router.register_model(ModelConfig(
            name="gemini",
            api_key=config.gemini_api_key,
            base_url="",  # Gemini使用SDK
            model=config.gemini_model,
            priority=10,
            cost_per_million=0,
            free_quota=15,  # 15次/天
            speed="medium",
            strengths=["general", "free"],
            available=True
        ))

    # 5. Groq（超快推理）
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        router.register_model(ModelConfig(
            name="groq",
            api_key=groq_key,
            base_url="https://api.groq.com/openai/v1",
            model=os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile"),
            priority=5,
            cost_per_million=0,
            free_quota=0,
            speed="fast",
            strengths=["fast", "inference"],
            available=True
        ))

    logger.info(f"[ModelRouter] 已初始化 {len(router.models)} 个模型")


def get_model_stats() -> Dict[str, Any]:
    """获取模型统计信息"""
    router = get_model_router()
    return {
        "total_models": len(router.models),
        "available_models": router.get_available_models(),
        "failure_counts": router.failure_count,
        "models": {
            name: {
                "priority": config.priority,
                "cost": config.cost_per_million,
                "speed": config.speed,
                "available": config.available
            }
            for name, config in router.models.items()
        }
    }
