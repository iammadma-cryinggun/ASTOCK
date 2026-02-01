# -*- coding: utf-8 -*-
"""
===================================
Web 处理器层 - 请求处理
===================================

职责：
1. 处理各类 HTTP 请求
2. 调用服务层执行业务逻辑
3. 返回响应数据

处理器分类：
- PageHandler: 页面请求处理
- ApiHandler: API 接口处理
"""

from __future__ import annotations

import json
import re
import logging
from http import HTTPStatus
from datetime import datetime
from typing import Dict, Any, TYPE_CHECKING

from web.services import get_config_service, get_analysis_service
from web.templates import render_config_page, render_futures_page, render_subscription_page
# 延迟导入 render_history_page，避免循环导入
from src.enums import ReportType

if TYPE_CHECKING:
    from http.server import BaseHTTPRequestHandler

logger = logging.getLogger(__name__)


# ============================================================
# 响应辅助类
# ============================================================

class Response:
    """HTTP 响应封装"""
    
    def __init__(
        self,
        body: bytes,
        status: HTTPStatus = HTTPStatus.OK,
        content_type: str = "text/html; charset=utf-8"
    ):
        self.body = body
        self.status = status
        self.content_type = content_type
    
    def send(self, handler: 'BaseHTTPRequestHandler') -> None:
        """发送响应到客户端"""
        handler.send_response(self.status)
        handler.send_header("Content-Type", self.content_type)
        handler.send_header("Content-Length", str(len(self.body)))
        handler.end_headers()
        handler.wfile.write(self.body)


class JsonResponse(Response):
    """JSON 响应封装"""
    
    def __init__(
        self,
        data: Dict[str, Any],
        status: HTTPStatus = HTTPStatus.OK
    ):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        super().__init__(
            body=body,
            status=status,
            content_type="application/json; charset=utf-8"
        )


class HtmlResponse(Response):
    """HTML 响应封装"""
    
    def __init__(
        self,
        body: bytes,
        status: HTTPStatus = HTTPStatus.OK
    ):
        super().__init__(
            body=body,
            status=status,
            content_type="text/html; charset=utf-8"
        )


# ============================================================
# 页面处理器
# ============================================================

class PageHandler:
    """页面请求处理器"""

    def __init__(self):
        self.config_service = get_config_service()

    def handle_index(self) -> Response:
        """处理首页请求 GET /"""
        stock_list = self.config_service.get_stock_list()
        env_filename = self.config_service.get_env_filename()
        body = render_config_page(stock_list, env_filename)
        return HtmlResponse(body)

    def handle_history(self) -> Response:
        """处理历史记录页面 GET /history"""
        from src.storage import DatabaseManager
        from web.templates import render_history_page  # 延迟导入

        db = DatabaseManager.get_instance()

        # 获取历史记录和已分析股票列表
        history_list = db.get_analysis_history(limit=50)
        stock_codes = db.get_unique_analyzed_stocks()

        # 转换为字典列表
        history_dicts = [h.to_dict() for h in history_list]

        body = render_history_page(history_dicts, stock_codes)
        return HtmlResponse(body)

    def handle_futures(self) -> Response:
        """处理期货波动率监控页面 GET /futures"""
        from src.volatility_index import get_volatility_fetcher
        from src.futures_monitor import FuturesVolatilityMonitor

        try:
            # 获取波动率获取器（使用 CBOE 官方数据）
            fetcher = get_volatility_fetcher()

            # 获取默认监控标的列表
            monitor = FuturesVolatilityMonitor(data_provider=None)
            default_symbols = monitor.DEFAULT_SYMBOLS

            results = []
            extreme_dicts = []
            data_unavailable = False

            # 尝试获取第一个标的的数据来检查数据源是否可用
            first_symbol = list(default_symbols.keys())[0]
            test_iv = fetcher.get_volatility_index(first_symbol)

            if test_iv is None:
                # 数据源不可用（可能是 Yahoo Finance 403 错误）
                data_unavailable = True
                logger.warning("[PageHandler] 波动率数据源不可用（可能是网络问题）")
            else:
                # 获取每个标的的真实波动率数据
                for symbol, name in default_symbols.items():
                    try:
                        # 获取当前 IV（隐含波动率）
                        iv_current = fetcher.get_volatility_index(symbol)

                        if iv_current is None:
                            logger.warning(f"[PageHandler] 无法获取 {symbol} 的 IV 数据")
                            continue

                        # 获取历史 IV 数据用于计算分位数
                        historical_data = fetcher.get_historical_volatility_index(symbol, days=252)

                        if not historical_data:
                            logger.warning(f"[PageHandler] 无法获取 {symbol} 的历史数据")
                            continue

                        # 计算 IV 分位数
                        iv_percentile = fetcher.calculate_iv_percentile(symbol)
                        if iv_percentile is None:
                            iv_percentile = 50.0

                        # 获取历史 IV 值
                        iv_values = [d['value'] for d in historical_data]
                        iv_min = min(iv_values)
                        iv_max = max(iv_values)

                        # 计算 IV Rank
                        if iv_max > iv_min:
                            iv_rank = (iv_current - iv_min) / (iv_max - iv_min) * 100
                        else:
                            iv_rank = 50.0

                        # 获取当前价格（从历史数据的最新条目）
                        current_price = 0.0
                        if historical_data and len(historical_data) > 0:
                            latest = historical_data[-1]
                            current_price = latest.get('close', 0.0)

                        # 计算 HV（历史波动率）- 简化计算
                        import numpy as np
                        if len(iv_values) >= 20:
                            # 使用最近20个IV值的标准差作为HV的近似
                            hv_20d = float(np.std(iv_values[-20:]))
                        else:
                            hv_20d = iv_current * 0.8  # 简化估计

                        # 计算 IV-HV 背离度
                        iv_hv_divergence = iv_current - hv_20d

                        # 判断风险等级
                        if iv_percentile >= 95 or iv_hv_divergence >= 0.30:
                            risk_level = 'extreme'
                        elif iv_percentile >= 90 or iv_hv_divergence >= 0.20:
                            risk_level = 'high'
                        elif iv_percentile >= 80 or iv_hv_divergence >= 0.15:
                            risk_level = 'medium'
                        else:
                            risk_level = 'low'

                        # 检查是否为极端风险
                        if risk_level in ['high', 'extreme']:
                            results.append({
                                'symbol': symbol,
                                'name': name,
                                'current_price': current_price,
                                'iv_current': iv_current,
                                'iv_percentile': iv_percentile,
                                'hv_20d': hv_20d,
                                'iv_hv_divergence': iv_hv_divergence,
                                'risk_level': risk_level,
                                'timestamp': historical_data[-1].get('date', '') if historical_data else ''
                            })

                            if risk_level == 'extreme':
                                extreme_dicts.append({
                                    'symbol': symbol,
                                    'name': name,
                                    'current_price': current_price,
                                    'iv_current': iv_current,
                                    'iv_percentile': iv_percentile,
                                    'hv_20d': hv_20d,
                                    'iv_hv_divergence': iv_hv_divergence,
                                    'risk_level': risk_level,
                                    'timestamp': historical_data[-1].get('date', '') if historical_data else ''
                                })
                        else:
                            # 正常风险也添加到结果中
                            results.append({
                                'symbol': symbol,
                                'name': name,
                                'current_price': current_price,
                                'iv_current': iv_current,
                                'iv_percentile': iv_percentile,
                                'hv_20d': hv_20d,
                                'iv_hv_divergence': iv_hv_divergence,
                                'risk_level': risk_level,
                                'timestamp': historical_data[-1].get('date', '') if historical_data else ''
                            })

                    except Exception as e:
                        logger.warning(f"[PageHandler] 处理 {symbol} 失败: {e}")
                        continue

            logger.info(f"[PageHandler] 期货监控页面已加载，共 {len(results)} 个标的")

            body = render_futures_page(results, extreme_dicts, data_unavailable)
            return HtmlResponse(body)

        except Exception as e:
            logger.error(f"[PageHandler] 获取期货监控数据失败: {e}")
            import traceback
            traceback.print_exc()
            # 返回空页面（标记为数据不可用）
            body = render_futures_page([], [], True)
            return HtmlResponse(body)

    def handle_subscription(self) -> Response:
        """处理订阅监控页面 GET /subscription"""
        from src.storage import DatabaseManager

        try:
            db = DatabaseManager.get_instance()

            # 获取订阅列表（从配置中获取）
            stock_list = self.config_service.get_stock_list()
            subscription_list = []

            # 获取每只股票的最新分析结果
            for code in stock_list.split(',')[:20]:  # 最多20只
                code = code.strip()
                if not code:
                    continue

                # 获取最新的分析记录
                latest = db.get_latest_analysis_by_code(code)
                if latest:
                    # 判断建议类型
                    advice = latest.operation_advice or '观望'
                    if '买' in advice:
                        advice_class = 'buy'
                    elif '卖' in advice:
                        advice_class = 'sell'
                    elif '持有' in advice:
                        advice_class = 'hold'
                    else:
                        advice_class = 'wait'

                    subscription_list.append({
                        'code': code,
                        'name': latest.name or f'股票{code}',
                        'active': True,
                        'last_update': latest.analysis_time.strftime('%Y-%m-%d %H:%M') if latest.analysis_time else '-',
                        'advice': advice,
                        'advice_class': advice_class,
                        'score': latest.sentiment_score or 0
                    })

            body = render_subscription_page(subscription_list)
            return HtmlResponse(body)

        except Exception as e:
            logger.error(f"[PageHandler] 获取订阅数据失败: {e}")
            # 返回空列表
            body = render_subscription_page([])
            return HtmlResponse(body)

    def handle_update(self, form_data: Dict[str, list]) -> Response:
        """
        处理配置更新 POST /update

        Args:
            form_data: 表单数据
        """
        stock_list = form_data.get("stock_list", [""])[0]
        normalized = self.config_service.set_stock_list(stock_list)
        env_filename = self.config_service.get_env_filename()
        body = render_config_page(normalized, env_filename, message="已保存")
        return HtmlResponse(body)


# ============================================================
# API 处理器
# ============================================================

class ApiHandler:
    """API 请求处理器"""
    
    def __init__(self):
        self.analysis_service = get_analysis_service()
    
    def handle_health(self) -> Response:
        """
        健康检查 GET /health
        
        返回:
            {
                "status": "ok",
                "timestamp": "2026-01-19T10:30:00",
                "service": "stock-analysis-webui"
            }
        """
        data = {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "service": "stock-analysis-webui"
        }
        return JsonResponse(data)
    
    def handle_analysis(self, query: Dict[str, list]) -> Response:
        """
        触发股票分析 GET /analysis?code=xxx
        
        Args:
            query: URL 查询参数
            
        返回:
            {
                "success": true,
                "message": "分析任务已提交",
                "code": "600519",
                "task_id": "600519_20260119_103000"
            }
        """
        # 获取股票代码参数
        code_list = query.get("code", [])
        if not code_list or not code_list[0].strip():
            return JsonResponse(
                {"success": False, "error": "缺少必填参数: code (股票代码)"},
                status=HTTPStatus.BAD_REQUEST
            )
        
        code = code_list[0].strip()

        # 验证股票代码格式：A股(6位数字) / 港股(HK+5位数字) / 美股(1-5个大写字母+.+2个后缀字母)
        code = code.upper()
        is_a_stock = re.match(r'^\d{6}$', code)
        is_hk_stock = re.match(r'^HK\d{5}$', code)
        is_us_stock = re.match(r'^[A-Z]{1,5}(\.[A-Z]{1,2})?$', code.upper())

        if not (is_a_stock or is_hk_stock or is_us_stock):
            return JsonResponse(
                {"success": False, "error": f"无效的股票代码格式: {code} (A股6位数字 / 港股HK+5位数字 / 美股1-5个字母)"},
                status=HTTPStatus.BAD_REQUEST
            )
        
        # 获取报告类型参数（默认精简报告）
        report_type_str = query.get("report_type", ["simple"])[0]
        report_type = ReportType.from_str(report_type_str)
        
        # 提交异步分析任务
        try:
            result = self.analysis_service.submit_analysis(code, report_type=report_type)
            return JsonResponse(result)
        except Exception as e:
            logger.error(f"[ApiHandler] 提交分析任务失败: {e}")
            return JsonResponse(
                {"success": False, "error": f"提交任务失败: {str(e)}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR
            )
    
    def handle_tasks(self, query: Dict[str, list]) -> Response:
        """
        查询任务列表 GET /tasks
        
        Args:
            query: URL 查询参数 (可选 limit)
            
        返回:
            {
                "success": true,
                "tasks": [...]
            }
        """
        limit_list = query.get("limit", ["20"])
        try:
            limit = int(limit_list[0])
        except ValueError:
            limit = 20
        
        tasks = self.analysis_service.list_tasks(limit=limit)
        return JsonResponse({"success": True, "tasks": tasks})
    
    def handle_task_status(self, query: Dict[str, list]) -> Response:
        """
        查询单个任务状态 GET /task?id=xxx

        Args:
            query: URL 查询参数
        """
        task_id_list = query.get("id", [])
        if not task_id_list or not task_id_list[0].strip():
            return JsonResponse(
                {"success": False, "error": "缺少必填参数: id (任务ID)"},
                status=HTTPStatus.BAD_REQUEST
            )

        task_id = task_id_list[0].strip()
        task = self.analysis_service.get_task_status(task_id)

        if task is None:
            return JsonResponse(
                {"success": False, "error": f"任务不存在: {task_id}"},
                status=HTTPStatus.NOT_FOUND
            )

        return JsonResponse({"success": True, "task": task})

    def handle_detail(self, query: Dict[str, list]) -> Response:
        """
        查询分析详情 GET /detail?id=xxx

        Args:
            query: URL 查询参数
        """
        from src.storage import DatabaseManager

        id_list = query.get("id", [])
        if not id_list or not id_list[0].strip():
            return JsonResponse(
                {"success": False, "error": "缺少必填参数: id (分析记录ID)"},
                status=HTTPStatus.BAD_REQUEST
            )

        try:
            analysis_id = int(id_list[0].strip())
        except ValueError:
            return JsonResponse(
                {"success": False, "error": "无效的 ID 格式"},
                status=HTTPStatus.BAD_REQUEST
            )

        db = DatabaseManager.get_instance()
        detail = db.get_analysis_by_id(analysis_id)

        if detail is None:
            return JsonResponse(
                {"success": False, "error": f"分析记录不存在: {analysis_id}"},
                status=HTTPStatus.NOT_FOUND
            )

        return JsonResponse({"success": True, "detail": detail.to_dict()})

    def handle_futures_volatility(self, query: Dict[str, list]) -> Response:
        """
        获取期货波动率监控数据 GET /api/futures/volatility

        Args:
            query: URL 查询参数 (可选 symbols)

        Returns:
            {
                "success": true,
                "metrics": [...],
                "extreme_count": 2
            }
        """
        from src.futures_monitor import get_volatility_monitor
        from web.services import get_data_provider_service

        try:
            # 获取数据提供者
            data_service = get_data_provider_service()
            data_provider = data_service.get_provider()

            # 获取要监控的标的
            symbols_list = query.get("symbols", [])
            if symbols_list and symbols_list[0]:
                symbols = [s.strip().upper() for s in symbols_list[0].split(',')]
            else:
                monitor = get_volatility_monitor(data_provider)
                symbols = list(monitor.DEFAULT_SYMBOLS.keys())

            # 创建监控器并获取指标
            monitor = get_volatility_monitor(data_provider)
            results = []
            for symbol in symbols:
                name = monitor.DEFAULT_SYMBOLS.get(symbol, symbol)
                metrics = monitor.analyze_symbol(symbol, name)
                if metrics:
                    results.append(metrics.to_dict())

            # 获取极端风险标的
            extreme_symbols = monitor.get_extreme_risk_symbols(symbols)

            return JsonResponse({
                "success": True,
                "metrics": results,
                "extreme_count": len(extreme_symbols),
                "total_count": len(results)
            })

        except Exception as e:
            logger.error(f"[ApiHandler] 获取期货波动率数据失败: {e}")
            return JsonResponse(
                {"success": False, "error": str(e)},
                status=HTTPStatus.INTERNAL_SERVER_ERROR
            )

    def handle_futures_extreme_risk(self, query: Dict[str, list]) -> Response:
        """
        获取极端风险标的 GET /api/futures/extreme-risk

        Returns:
            {
                "success": true,
                "extreme_symbols": [...],
                "count": 2
            }
        """
        from src.futures_monitor import get_volatility_monitor
        from web.services import get_data_provider_service

        try:
            # 获取数据提供者
            data_service = get_data_provider_service()
            data_provider = data_service.get_provider()

            # 创建监控器
            monitor = get_volatility_monitor(data_provider)
            symbols = list(monitor.DEFAULT_SYMBOLS.keys())

            # 获取极端风险标的
            extreme_symbols = monitor.get_extreme_risk_symbols(symbols)
            extreme_dicts = [m.to_dict() for m in extreme_symbols]

            return JsonResponse({
                "success": True,
                "extreme_symbols": extreme_dicts,
                "count": len(extreme_dicts)
            })

        except Exception as e:
            logger.error(f"[ApiHandler] 获取极端风险标的失败: {e}")
            return JsonResponse(
                {"success": False, "error": str(e)},
                status=HTTPStatus.INTERNAL_SERVER_ERROR
            )

    def handle_futures_report(self, query: Dict[str, list]) -> Response:
        """
        生成期货波动率风险报告 GET /api/futures/report

        Returns:
            {
                "success": true,
                "report": "文本报告"
            }
        """
        from src.futures_monitor import get_volatility_monitor
        from web.services import get_data_provider_service

        try:
            # 获取数据提供者
            data_service = get_data_provider_service()
            data_provider = data_service.get_provider()

            # 创建监控器
            monitor = get_volatility_monitor(data_provider)
            symbols = list(monitor.DEFAULT_SYMBOLS.keys())

            # 生成报告
            report = monitor.generate_risk_report(symbols)

            return JsonResponse({
                "success": True,
                "report": report
            })

        except Exception as e:
            logger.error(f"[ApiHandler] 生成期货报告失败: {e}")
            return JsonResponse(
                {"success": False, "error": str(e)},
                status=HTTPStatus.INTERNAL_SERVER_ERROR
            )


# ============================================================
# Bot Webhook 处理器
# ============================================================

class BotHandler:
    """
    机器人 Webhook 处理器
    
    处理各平台的机器人回调请求。
    """
    
    def handle_webhook(self, platform: str, form_data: Dict[str, list], headers: Dict[str, str], body: bytes) -> Response:
        """
        处理 Webhook 请求
        
        Args:
            platform: 平台名称 (feishu, dingtalk, wecom, telegram)
            form_data: POST 数据（已解析）
            headers: HTTP 请求头
            body: 原始请求体
            
        Returns:
            Response 对象
        """
        try:
            from bot.handler import handle_webhook
            from bot.models import WebhookResponse
            
            # 调用 bot 模块处理
            webhook_response = handle_webhook(platform, headers, body)
            
            # 转换为 web 响应
            return JsonResponse(
                webhook_response.body,
                status=HTTPStatus(webhook_response.status_code)
            )
            
        except ImportError as e:
            logger.error(f"[BotHandler] Bot 模块未正确安装: {e}")
            return JsonResponse(
                {"error": "Bot module not available"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"[BotHandler] 处理 {platform} Webhook 失败: {e}")
            return JsonResponse(
                {"error": str(e)},
                status=HTTPStatus.INTERNAL_SERVER_ERROR
            )


# ============================================================
# 处理器工厂
# ============================================================

_page_handler: PageHandler | None = None
_api_handler: ApiHandler | None = None
_bot_handler: BotHandler | None = None


def get_page_handler() -> PageHandler:
    """获取页面处理器实例"""
    global _page_handler
    if _page_handler is None:
        _page_handler = PageHandler()
    return _page_handler


def get_api_handler() -> ApiHandler:
    """获取 API 处理器实例"""
    global _api_handler
    if _api_handler is None:
        _api_handler = ApiHandler()
    return _api_handler


def get_bot_handler() -> BotHandler:
    """获取 Bot 处理器实例"""
    global _bot_handler
    if _bot_handler is None:
        _bot_handler = BotHandler()
    return _bot_handler
