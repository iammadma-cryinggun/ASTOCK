# -*- coding: utf-8 -*-
"""
===================================
A股自选股智能分析系统 - 语义分析路由器
===================================

职责：
1. 根据分析任务类型智能选择最佳模型
2. 集成专业金融模型（FinBERT、XuanYuan等）
3. 提供统一的语义分析接口
4. 支持多模型结果融合

支持的分析任务：
- news_sentiment: 新闻情绪快速打分（FinBERT，毫秒级）
- financial_report: 财报/公告深度分析（XuanYuan-70B）
- macro_analysis: 宏观新闻分析（通用LLM）
- general: 通用分析（DeepSeek/千问）
"""

import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """分析任务类型"""
    NEWS_SENTIMENT = "news_sentiment"  # 新闻情绪快速打分
    FINANCIAL_REPORT = "financial_report"  # 财报/公告深度分析
    MACRO_ANALYSIS = "macro_analysis"  # 宏观新闻分析
    GENERAL = "general"  # 通用分析


@dataclass
class SentimentResult:
    """情绪分析结果"""
    score: float  # 情绪得分 -1.0(极端负面) ~ 1.0(极端正面)
    confidence: float  # 置信度 0.0 ~ 1.0
    label: str  # 标签：positive/negative/neutral
    model_used: str  # 使用的模型
    processing_time: float  # 处理时间（秒）

    def to_dict(self) -> Dict[str, Any]:
        return {
            'score': self.score,
            'confidence': self.confidence,
            'label': self.label,
            'model_used': self.model_used,
            'processing_time': self.processing_time
        }


class FinBERTClient:
    """
    FinBERT-Chinese 客户端（通过 Hugging Face Inference API）

    特点：
    - 专门在中文金融语料上训练
    - 对"跌停"、"减持"等金融词汇敏感
    - 毫秒级响应（相比通用LLM的秒级）

    文档：https://huggingface.co/chtma/finbert-chinese
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 FinBERT 客户端

        Args:
            api_key: Hugging Face API Key（可选，免费版有限制）
        """
        self.api_key = api_key
        # 模型 URL（Transformers 模式下不需要）
        self.api_url = None
        # 使用可用的中文金融情绪分析模型
        # https://huggingface.co/yiyanghkust/finbert-tone-chinese
        self.model_id = "yiyanghkust/finbert-tone-chinese"
        self._pipeline = None
        # Transformers 模式：直接加载模型，不需要 API Key
        self.is_available = True  # 总是尝试加载

        if self.is_available:
            logger.info(f"[FinBERT] 客户端初始化成功（Transformers模式）")

    def _load_pipeline(self):
        """延迟加载 Transformers pipeline"""
        if self._pipeline is not None:
            return self._pipeline

        try:
            from transformers import pipeline
            logger.info(f"[FinBERT] 正在加载模型: {self.model_id}")
            self._pipeline = pipeline("text-classification", model=self.model_id)
            logger.info("[FinBERT] 模型加载成功")
            return self._pipeline
        except Exception as e:
            logger.error(f"[FinBERT] 模型加载失败: {e}")
            return None

    def analyze_sentiment(self, text: str) -> Optional[SentimentResult]:
        """
        分析文本情绪

        Args:
            text: 待分析文本

        Returns:
            SentimentResult 对象，失败返回 None
        """
        if not self.is_available:
            logger.warning("[FinBERT] 客户端不可用，跳过分析")
            return None

        try:
            # 延迟加载模型
            pipeline = self._load_pipeline()
            if pipeline is None:
                return None

            start_time = time.time()

            # 使用 Transformers pipeline 推理
            result = pipeline(text)

            elapsed = time.time() - start_time

            # FinBERT 返回格式: [{'label': 'positive', 'score': 0.98}, ...]
            if isinstance(result, list):
                predictions = result

                # 转换为字典便于查找
                pred_dict = {p['label']: p['score'] for p in predictions}

                # 获取各标签的置信度
                positive_conf = pred_dict.get('positive', 0.0)
                negative_conf = pred_dict.get('negative', 0.0)
                neutral_conf = pred_dict.get('neutral', 0.0)

                # 三层判断逻辑
                if neutral_conf >= positive_conf and neutral_conf >= negative_conf:
                    label = 'neutral'
                    raw_score = neutral_conf
                    score = 0.0
                elif positive_conf > neutral_conf + 0.2:
                    label = 'positive'
                    raw_score = positive_conf
                    score = positive_conf
                elif negative_conf > neutral_conf + 0.2:
                    label = 'negative'
                    raw_score = negative_conf
                    score = -negative_conf
                else:
                    label = 'neutral'
                    raw_score = neutral_conf
                    score = 0.0
                    logger.debug(f"[FinBERT] 情绪不明显（positive={positive_conf:.2f}, neutral={neutral_conf:.2f}, negative={negative_conf:.2f}），判定为中性")

                logger.info(f"[FinBERT] 分析完成: {label} ({score:.3f}), 置信度分布=[positive:{positive_conf:.2f}, neutral:{neutral_conf:.2f}, negative:{negative_conf:.2f}], 耗时 {elapsed*1000:.0f}ms")

                return SentimentResult(
                    score=score,
                    confidence=raw_score,
                    label=label,
                    model_used="FinBERT-Chinese",
                    processing_time=elapsed
                )

        except Exception as e:
            logger.error(f"[FinBERT] 分析失败: {e}")

        return None


class XuanYuanClient:
    """
    轩辕-70B 客户端（通过云端 API）

    特点：
    - 70B参数，逻辑推理能力强
    - 专门针对金融文档训练
    - 能看懂财报里的陷阱

    注意：需要确认轩辕大模型的 API 地址和调用方式
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        初始化轩辕客户端

        Args:
            api_key: API Key
            base_url: API 基础地址
        """
        self.api_key = api_key
        self.base_url = base_url or "https://api.xuanyuan.ai/v1"  # 需确认
        self.is_available = bool(api_key and base_url)

        if self.is_available:
            logger.info(f"[轩辕] 客户端初始化成功")
        else:
            logger.info("[轩辕] 未配置，将使用通用 LLM 替代")

    def analyze_financial_report(self, content: str) -> Optional[Dict[str, Any]]:
        """
        分析财报/公告

        Args:
            content: 财报/公告内容

        Returns:
            分析结果字典
        """
        if not self.is_available:
            return None

        # TODO: 实现轩辕 API 调用逻辑
        # 目前返回 None，会回退到通用 LLM
        logger.warning("[轩辕] API 调用尚未实现，使用通用 LLM 替代")
        return None


class SemanticRouter:
    """
    语义分析路由器

    根据任务类型智能选择最佳模型：

    任务类型                    | 最佳模型          | 响应时间   | 成本
    ---------------------------|-------------------|-----------|--------
    news_sentiment (新闻情绪)  | FinBERT           | 毫秒级    | 低
    financial_report (财报)    | XuanYuan-70B      | 秒级      | 中
    macro_analysis (宏观)      | DeepSeek/千问     | 秒级      | 低
    general (通用)             | DeepSeek/千问     | 秒级      | 低
    """

    def __init__(
        self,
        finbert_api_key: Optional[str] = None,
        xuanyuan_api_key: Optional[str] = None,
        xuanyuan_base_url: Optional[str] = None,
    ):
        """
        初始化语义分析路由器

        Args:
            finbert_api_key: Hugging Face API Key（用于 FinBERT）
            xuanyuan_api_key: 轩辕 API Key
            xuanyuan_base_url: 轩辕 API 地址
        """
        # 初始化专业模型客户端
        self.finbert = FinBERTClient(api_key=finbert_api_key)
        self.xuanyuan = XuanYuanClient(
            api_key=xuanyuan_api_key,
            base_url=xuanyuan_base_url
        )

        # 通用 LLM（从现有的 model_router 获取）
        self._general_llm = None

        logger.info("[语义路由] 初始化完成")
        self._log_available_models()

    def _log_available_models(self):
        """记录可用模型"""
        available = []
        if self.finbert.is_available:
            available.append("FinBERT-Chinese")
        if self.xuanyuan.is_available:
            available.append("XuanYuan-70B")

        logger.info(f"[语义路由] 可用专业模型: {', '.join(available) if available else '无'}")

    def set_general_llm(self, analyzer):
        """
        设置通用 LLM 分析器

        Args:
            analyzer: GeminiAnalyzer 实例
        """
        self._general_llm = analyzer

    def analyze(
        self,
        task_type: TaskType,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[SentimentResult]:
        """
        路由分析请求到最佳模型

        Args:
            task_type: 任务类型
            content: 待分析内容
            context: 附加上下文（可选）

        Returns:
            分析结果
        """
        logger.info(f"[语义路由] 任务类型: {task_type.value}")

        # 1. 新闻情绪快速打分 → FinBERT
        if task_type == TaskType.NEWS_SENTIMENT:
            result = self.finbert.analyze_sentiment(content)

            if result:
                logger.info(f"[语义路由] 使用 FinBERT: {result.label} ({result.score:.3f})")
                return result
            else:
                logger.warning("[语义路由] FinBERT 不可用，回退到通用 LLM")

        # 2. 财报深度分析 → XuanYuan
        elif task_type == TaskType.FINANCIAL_REPORT:
            result = self.xuanyuan.analyze_financial_report(content)

            if result:
                logger.info(f"[语义路由] 使用轩辕: 深度分析完成")
                return self._convert_to_sentiment_result(result)
            else:
                logger.warning("[语义路由] 轩辕不可用，回退到通用 LLM")

        # 3. 回退到通用 LLM
        if self._general_llm:
            logger.info(f"[语义路由] 使用通用 LLM 分析")
            return self._analyze_with_general_llm(content, context)
        else:
            logger.error("[语义路由] 通用 LLM 未配置")
            return None

    def _analyze_with_general_llm(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[SentimentResult]:
        """
        使用通用 LLM 分析情绪

        Args:
            content: 待分析内容
            context: 上下文

        Returns:
            SentimentResult
        """
        # 构建简化的 prompt
        prompt = f"""请分析以下金融文本的情绪，返回 JSON 格式：

文本：{content[:500]}

请返回：
{{
    "label": "positive/negative/neutral",
    "score": 0.0~1.0 (置信度),
    "reason": "简要理由"
}}
"""

        try:
            # 调用通用 LLM（复用现有的 analyzer）
            # 注意：这里需要调用 OpenAI 兼容接口
            from src.model_router import get_model_router

            router = get_model_router()
            model = router.get_best_model()

            if not model:
                return None

            # 使用 OpenAI 兼容接口调用
            # TODO: 实现通用 LLM 调用逻辑
            logger.warning("[语义路由] 通用 LLM 调用尚未完整实现")

        except Exception as e:
            logger.error(f"[语义路由] 通用 LLM 分析失败: {e}")

        return None

    def _convert_to_sentiment_result(self, result: Dict[str, Any]) -> SentimentResult:
        """将字典结果转换为 SentimentResult"""
        # TODO: 实现转换逻辑
        return SentimentResult(
            score=0.0,
            confidence=0.0,
            label="neutral",
            model_used="Unknown",
            processing_time=0.0
        )

    def batch_analyze_news(
        self,
        news_list: List[str],
        use_finbert: bool = True
    ) -> List[SentimentResult]:
        """
        批量分析新闻情绪

        Args:
            news_list: 新闻文本列表
            use_finbert: 是否使用 FinBERT（更快）

        Returns:
            情绪结果列表
        """
        results = []

        for i, news in enumerate(news_list):
            logger.info(f"[语义路由] 批量分析 {i+1}/{len(news_list)}")

            if use_finbert and self.finbert.is_available:
                result = self.finbert.analyze_sentiment(news)
            else:
                result = self.analyze(TaskType.NEWS_SENTIMENT, news)

            if result:
                results.append(result)
            else:
                # 失败时添加中性结果
                results.append(SentimentResult(
                    score=0.0,
                    confidence=0.0,
                    label="neutral",
                    model_used="fallback",
                    processing_time=0.0
                ))

        return results


# === 全局单例 ===
_semantic_router: Optional[SemanticRouter] = None


def get_semantic_router() -> SemanticRouter:
    """获取语义分析路由器单例"""
    global _semantic_router

    if _semantic_router is None:
        from src.config import get_config
        config = get_config()

        _semantic_router = SemanticRouter(
            finbert_api_key=config.huggingface_api_key,  # 复用 HF API Key
            xuanyuan_api_key=None,  # TODO: 添加到配置
            xuanyuan_base_url=None,
        )

    return _semantic_router


def reset_semantic_router():
    """重置路由器（用于测试）"""
    global _semantic_router
    _semantic_router = None


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s | %(levelname)-8s | %(message)s'
    )

    router = get_semantic_router()

    # 测试新闻情绪分析
    test_news = [
        "宁德时代发布业绩预告，净利润同比增长50%，超市场预期",
        "某公司公告控股股东减持5%股份",
        "证监会发布新规，加强对上市公司监管"
    ]

    print("\n=== 测试新闻情绪分析 ===")
    results = router.batch_analyze_news(test_news)

    for news, result in zip(test_news, results):
        print(f"\n新闻: {news}")
        if result:
            print(f"  情绪: {result.label} ({result.score:.3f})")
            print(f"  置信度: {result.confidence:.3f}")
            print(f"  模型: {result.model_used}")
            print(f"  耗时: {result.processing_time*1000:.0f}ms")
