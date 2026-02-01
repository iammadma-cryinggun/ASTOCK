# -*- coding: utf-8 -*-
"""
===================================
Web 模板层 - HTML 页面生成 (重构版)
===================================

职责：
1. 生成 HTML 页面
2. 管理 CSS 样式
3. 提供可复用的页面组件

新架构设计：
- 三个主要板块：查询、订阅、期货
- 清晰展示报告类型差异
- 展示数据来源和分析逻辑
"""

from __future__ import annotations

import html
from typing import Optional


# ============================================================
# CSS 样式定义
# ============================================================

BASE_CSS = """
:root {
    --primary: #2563eb;
    --primary-hover: #1d4ed8;
    --bg: #f8fafc;
    --card: #ffffff;
    --text: #1e293b;
    --text-light: #64748b;
    --border: #e2e8f0;
    --success: #10b981;
    --error: #ef4444;
    --warning: #f59e0b;
}

* {
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background-color: var(--bg);
    color: var(--text);
    margin: 0;
    padding: 0;
}

/* 布局容器 */
.app-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

/* 导航栏 */
.navbar {
    background: var(--card);
    padding: 1rem 2rem;
    border-radius: 1rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    margin-bottom: 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.navbar-brand {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.navbar-nav {
    display: flex;
    gap: 0.5rem;
}

.nav-link {
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    text-decoration: none;
    color: var(--text-light);
    font-size: 0.875rem;
    transition: all 0.2s;
    background: transparent;
    border: 1px solid transparent;
}

.nav-link:hover {
    color: var(--primary);
    background: rgba(37, 99, 235, 0.05);
}

.nav-link.active {
    color: var(--primary);
    background: rgba(37, 99, 235, 0.1);
    border-color: var(--primary);
    font-weight: 500;
}

/* 卡片 */
.card {
    background: var(--card);
    border-radius: 1rem;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    margin-bottom: 1.5rem;
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.card-title {
    font-size: 1.25rem;
    font-weight: 600;
    margin: 0;
    color: var(--text);
}

.card-body {
    color: var(--text-light);
    line-height: 1.6;
}

/* 表单元素 */
.form-group {
    margin-bottom: 1.5rem;
}

label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: var(--text);
    font-size: 0.875rem;
}

input[type="text"], select, textarea {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid var(--border);
    border-radius: 0.5rem;
    font-size: 0.875rem;
    transition: all 0.2s;
}

input[type="text"]:focus, select:focus, textarea:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

button {
    background-color: var(--primary);
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 0.5rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 0.875rem;
}

button:hover {
    background-color: var(--primary-hover);
    transform: translateY(-1px);
}

button:active {
    transform: translateY(0);
}

button:disabled {
    background-color: var(--text-light);
    cursor: not-allowed;
    transform: none;
}

.btn-secondary {
    background-color: var(--text-light);
}

.btn-secondary:hover {
    background-color: var(--text);
}

.btn-success {
    background-color: var(--success);
}

.btn-success:hover {
    background-color: #059669;
}

.btn-sm {
    padding: 0.5rem 1rem;
    font-size: 0.8rem;
}

/* 输入组 */
.input-group {
    display: flex;
    gap: 0.5rem;
}

.input-group input {
    flex: 1;
}

/* 报告类型选择器 */
.report-type-selector {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
}

.report-type-radio {
    display: none;
}

.report-type-label {
    flex: 1;
    padding: 0.75rem;
    border: 2px solid var(--border);
    border-radius: 0.5rem;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
    position: relative;
}

.report-type-label:hover {
    border-color: var(--primary);
    background: rgba(37, 99, 235, 0.05);
}

.report-type-radio:checked + .report-type-label {
    border-color: var(--primary);
    background: rgba(37, 99, 235, 0.1);
    color: var(--primary);
    font-weight: 600;
}

.report-type-description {
    display: block;
    font-size: 0.75rem;
    color: var(--text-light);
    margin-top: 0.25rem;
}

/* 任务列表 */
.task-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.task-list:empty::after {
    content: '暂无任务';
    display: block;
    text-align: center;
    color: var(--text-light);
    font-size: 0.875rem;
    padding: 2rem;
}

.task-card {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    background: var(--bg);
    border-radius: 0.75rem;
    border: 1px solid var(--border);
    transition: all 0.2s;
}

.task-card:hover {
    border-color: var(--primary);
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.task-card.running {
    border-color: var(--primary);
    background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 100%);
}

.task-card.completed {
    border-color: var(--success);
    background: linear-gradient(135deg, #ecfdf5 0%, #f8fafc 100%);
}

.task-card.failed {
    border-color: var(--error);
    background: linear-gradient(135deg, #fef2f2 0%, #f8fafc 100%);
}

.task-status {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    flex-shrink: 0;
}

.task-card.running .task-status {
    background: var(--primary);
    color: white;
}

.task-card.completed .task-status {
    background: var(--success);
    color: white;
}

.task-card.failed .task-status {
    background: var(--error);
    color: white;
}

.task-main {
    flex: 1;
    min-width: 0;
}

.task-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.25rem;
}

.task-code {
    font-family: monospace;
    font-weight: 600;
    color: var(--primary);
    background: white;
    padding: 0.15rem 0.4rem;
    border-radius: 0.25rem;
}

.task-name {
    color: var(--text-light);
    font-size: 0.875rem;
}

.task-meta {
    display: flex;
    gap: 1rem;
    font-size: 0.75rem;
    color: var(--text-light);
}

.task-result {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 0.25rem;
}

.task-advice {
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    font-size: 0.75rem;
    font-weight: 600;
    background: var(--primary);
    color: white;
}

.task-advice.buy { background: #059669; }
.task-advice.sell { background: #dc2626; }
.task-advice.hold { background: #d97706; }
.task-advice.wait { background: #6b7280; }

.task-score {
    font-size: 0.75rem;
    color: var(--text-light);
}

.task-actions {
    display: flex;
    gap: 0.25rem;
}

.task-btn {
    width: 28px;
    height: 28px;
    padding: 0;
    border-radius: 0.375rem;
    background: transparent;
    color: var(--text-light);
    font-size: 0.875rem;
    display: flex;
    align-items: center;
    justify-content: center;
}

.task-btn:hover {
    background: rgba(0,0,0,0.05);
    color: var(--text);
    transform: none;
}

/* Spinner */
.spinner {
    display: inline-block;
    width: 14px;
    height: 14px;
    border: 2px solid currentColor;
    border-right-color: transparent;
    border-radius: 50%;
    animation: spin 0.75s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* 订阅列表 */
.subscription-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1rem;
}

.subscription-card {
    padding: 1rem;
    border: 1px solid var(--border);
    border-radius: 0.75rem;
    transition: all 0.2s;
}

.subscription-card:hover {
    border-color: var(--primary);
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.subscription-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
}

.subscription-code {
    font-family: monospace;
    font-weight: 600;
    color: var(--primary);
}

.subscription-status {
    font-size: 0.75rem;
    padding: 0.15rem 0.4rem;
    border-radius: 0.25rem;
    background: var(--border);
}

.subscription-status.active {
    background: #d1fae5;
    color: #065f46;
}

.subscription-status.inactive {
    background: #f3f4f6;
    color: #6b7280;
}

.subscription-body {
    font-size: 0.875rem;
    color: var(--text-light);
}

/* 期货监控 */
.futures-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1rem;
}

.futures-card {
    padding: 1rem;
    border: 1px solid var(--border);
    border-radius: 0.75rem;
    transition: all 0.2s;
}

.futures-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.futures-card.risk-low { background: #ecfdf5; border-color: #10b981; }
.futures-card.risk-medium { background: #fef3c7; border-color: #f59e0b; }
.futures-card.risk-high { background: #fed7aa; border-color: #f97316; }
.futures-card.risk-extreme { background: #fee2e2; border-color: #ef4444; }

.futures-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid rgba(0,0,0,0.1);
}

.futures-symbol {
    font-family: monospace;
    font-weight: 600;
    font-size: 1rem;
}

.futures-price {
    font-weight: 600;
}

.futures-metrics {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
}

.futures-metric {
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
}

.futures-label {
    font-size: 0.7rem;
    color: var(--text-light);
}

.futures-value {
    font-size: 0.875rem;
    font-weight: 600;
}

.futures-risk {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 0.5rem;
    border-top: 1px solid rgba(0,0,0,0.1);
}

.risk-badge {
    padding: 0.2rem 0.5rem;
    border-radius: 0.25rem;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
}

/* 底部信息 */
.footer {
    text-align: center;
    color: var(--text-light);
    font-size: 0.75rem;
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border);
}

/* 空状态 */
.empty-state {
    text-align: center;
    padding: 3rem 1rem;
    color: var(--text-light);
}

.empty-state-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.empty-state-text {
    font-size: 0.875rem;
}

/* Toast */
.toast {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%) translateY(100px);
    background: white;
    border-left: 4px solid var(--success);
    padding: 1rem 1.5rem;
    border-radius: 0.5rem;
    box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    display: flex;
    align-items: center;
    gap: 0.75rem;
    transition: all 0.3s;
    opacity: 0;
    z-index: 1000;
}

.toast.show {
    transform: translateX(-50%) translateY(0);
    opacity: 1;
}

.toast.error { border-left-color: var(--error); }
.toast.warning { border-left-color: var(--warning); }

/* 辅助类 */
.text-muted { color: var(--text-light); font-size: 0.875rem; }
.text-center { text-align: center; }
.mt-1 { margin-top: 0.25rem; }
.mt-2 { margin-top: 0.5rem; }
.mt-4 { margin-top: 1rem; }
.mb-2 { margin-bottom: 0.5rem; }
.mb-4 { margin-bottom: 1rem; }
"""


# ============================================================
# 辅助函数
# ============================================================

def render_base(title: str, content: str, extra_css: str = "", extra_js: str = "") -> bytes:
    """渲染基础 HTML 模板"""
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)}</title>
  <style>{BASE_CSS}{extra_css}</style>
</head>
<body>
  {content}
  {extra_js}
</body>
</html>""".encode("utf-8")


def render_navbar(active: str = "query") -> str:
    """渲染导航栏"""
    nav_items = {
        "query": ("🔍 查询分析", "/"),
        "subscription": ("📋 订阅监控", "/subscription"),
        "futures": ("📊 期货监控", "/futures"),
        "history": ("📜 历史记录", "/history"),
    }

    nav_links = []
    for key, (text, href) in nav_items.items():
        active_class = "active" if key == active else ""
        nav_links.append(f'<a class="nav-link {active_class}" href="{href}">{text}</a>')

    return f"""
    <nav class="navbar">
      <div class="navbar-brand">📈 智能股票分析</div>
      <div class="navbar-nav">
        {''.join(nav_links)}
      </div>
    </nav>
    """


def render_toast(message: str, toast_type: str = "success") -> str:
    """渲染 Toast 通知"""
    icon_map = {"success": "✅", "error": "❌", "warning": "⚠️"}
    icon = icon_map.get(toast_type, "ℹ️")
    type_class = f" {toast_type}" if toast_type != "success" else ""

    return f"""
    <div id="toast" class="toast show{type_class}">
        <span class="icon">{icon}</span> {html.escape(message)}
    </div>
    <script>
        setTimeout(() => document.getElementById('toast').classList.remove('show'), 3000);
    </script>
    """


# ============================================================
# 页面模板
# ============================================================

def render_config_page(
    stock_list: str,
    env_filename: str,
    message: Optional[str] = None
) -> bytes:
    """
    渲染查询分析页面（重构版）

    三个板块：查询、订阅、期货
    """
    safe_value = html.escape(stock_list)
    toast_html = render_toast(message) if message else ""

    # 分析组件的 JavaScript
    analysis_js = """
<script>
(function() {
    const codeInput = document.getElementById('analysis_code');
    const submitBtn = document.getElementById('analysis_btn');
    const taskList = document.getElementById('task_list');

    const tasks = new Map();
    let pollInterval = null;
    const MAX_POLL_COUNT = 120;
    const POLL_INTERVAL_MS = 3000;
    const MAX_TASKS_DISPLAY = 15;

    // 获取报告类型
    function getReportType() {
        return document.querySelector('input[name="report_type"]:checked').value;
    }

    // 输入验证
    codeInput.addEventListener('input', function(e) {
        this.value = this.value.toUpperCase().replace(/[^A-Z0-9.]/g, '');
        if (this.value.length > 8) {
            this.value = this.value.slice(0, 8);
        }
        updateButtonState();
    });

    codeInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !submitBtn.disabled) {
            submitAnalysis();
        }
    });

    function updateButtonState() {
        const code = codeInput.value.trim();
        const isAStock = /^\\d{6}$/.test(code);
        const isHKStock = /^HK\\d{5}$/.test(code);
        const isUSStock = /^[A-Z]{1,5}(\\.[A-Z]{1,2})?$/.test(code);
        submitBtn.disabled = !(isAStock || isHKStock || isUSStock);
    }

    function formatTime(isoString) {
        if (!isoString) return '-';
        const date = new Date(isoString);
        return date.toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit'});
    }

    function calcDuration(start, end) {
        if (!start) return '-';
        const startTime = new Date(start).getTime();
        const endTime = end ? new Date(end).getTime() : Date.now();
        const seconds = Math.floor((endTime - startTime) / 1000);
        if (seconds < 60) return seconds + 's';
        const minutes = Math.floor(seconds / 60);
        const remainSec = seconds % 60;
        return minutes + 'm' + remainSec + 's';
    }

    function getAdviceClass(advice) {
        if (!advice) return '';
        if (advice.includes('买') || advice.includes('加仓')) return 'buy';
        if (advice.includes('卖') || advice.includes('减仓')) return 'sell';
        if (advice.includes('持有')) return 'hold';
        return 'wait';
    }

    function renderTaskCard(taskId, taskData) {
        const task = taskData.task || {};
        const status = task.status || 'pending';
        const code = task.code || taskId.split('_')[0];
        const result = task.result || {};
        const isExpanded = taskData.expanded || false;

        let statusIcon = '⏳';
        if (status === 'running') { statusIcon = '<span class="spinner"></span>'; }
        else if (status === 'completed') { statusIcon = '✓'; }
        else if (status === 'failed') { statusIcon = '✗'; }

        let resultHtml = '';
        if (status === 'completed' && result.operation_advice) {
            const adviceClass = getAdviceClass(result.operation_advice);
            resultHtml = '<div class="task-result">' +
                '<span class="task-advice ' + adviceClass + '">' + result.operation_advice + '</span>' +
                '<span class="task-score">评分: ' + (result.sentiment_score || '-') + '</span>' +
                '</div>';
        } else if (status === 'failed') {
            resultHtml = '<div class="task-result"><span class="task-advice sell">失败</span></div>';
        }

        // 展开的详细内容
        let detailHtml = '';
        if (isExpanded && status === 'completed') {
            const reportType = task.report_type || 'simple';

            if (reportType === 'full') {
                // 完整报告格式
                detailHtml = '<div class="task-detail" style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border);">';

                // 核心结论
                if (result.analysis_summary) {
                    detailHtml += '<div style="margin-bottom: 0.75rem;"><strong>📌 核心结论:</strong><p style="margin: 0.25rem 0; color: var(--text-light);">' + escapeHtml(result.analysis_summary) + '</p></div>';
                }

                // 技术面分析
                if (result.technical_analysis) {
                    detailHtml += '<div style="margin-bottom: 0.75rem;"><strong>📈 技术面:</strong><p style="margin: 0.25rem 0; color: var(--text-light); font-size: 0.875rem;">' + escapeHtml(result.technical_analysis) + '</p></div>';
                }

                // 基本面分析
                if (result.fundamental_analysis) {
                    detailHtml += '<div style="margin-bottom: 0.75rem;"><strong>💼 基本面:</strong><p style="margin: 0.25rem 0; color: var(--text-light); font-size: 0.875rem;">' + escapeHtml(result.fundamental_analysis) + '</p></div>';
                }

                // 消息面分析
                if (result.news_summary) {
                    detailHtml += '<div style="margin-bottom: 0.75rem;"><strong>📰 消息面:</strong><p style="margin: 0.25rem 0; color: var(--text-light); font-size: 0.875rem;">' + escapeHtml(result.news_summary) + '</p></div>';
                }

                // 新闻列表（带情绪评分）
                if (result.news_list && result.news_list.length > 0) {
                    detailHtml += '<div style="margin-bottom: 0.75rem;"><strong>📰 新闻详情:</strong><div style="max-height: 400px; overflow-y: auto;">';
                    for (const news of result.news_list) {
                        const sentimentLabel = news.sentiment_label || '⚪中性';
                        const sentimentScore = news.sentiment_score || '';
                        const category = news.category || '';
                        const source = news.source || '';
                        const date = news.published_date || '';
                        detailHtml += '<div style="padding: 0.5rem; margin-bottom: 0.5rem; border-left: 3px solid var(--border); background: var(--bg-secondary);">';
                        detailHtml += '<div style="display: flex; justify-content: space-between; align-items: start;">';
                        detailHtml += '<div style="flex: 1; padding-right: 0.5rem;">';
                        if (category) {
                            detailHtml += '<span style="font-size: 0.75rem; color: var(--text-muted); margin-right: 0.5rem;">' + escapeHtml(category) + '</span>';
                        }
                        detailHtml += '<a href="' + escapeHtml(news.url || '#') + '" target="_blank" style="color: var(--primary); text-decoration: none; font-weight: 500;">' + escapeHtml(news.title) + '</a>';
                        detailHtml += '</div>';
                        detailHtml += '<div style="text-align: right;">';
                        detailHtml += '<span style="font-size: 0.875rem;">' + sentimentLabel + '</span>';
                        if (sentimentScore && sentimentScore !== 'N/A') {
                            detailHtml += '<div style="font-size: 0.75rem; color: var(--text-muted);">评分: ' + sentimentScore + '</div>';
                        }
                        detailHtml += '</div>';
                        detailHtml += '</div>';
                        if (news.snippet) {
                            detailHtml += '<p style="margin: 0.25rem 0 0 0; font-size: 0.875rem; color: var(--text-light);">' + escapeHtml(news.snippet) + '</p>';
                        }
                        detailHtml += '<div style="margin-top: 0.25rem; font-size: 0.75rem; color: var(--text-muted);">';
                        if (source) {
                            detailHtml += escapeHtml(source);
                        }
                        if (date) {
                            detailHtml += ' | ' + escapeHtml(date);
                        }
                        detailHtml += '</div>';
                        detailHtml += '</div>';
                    }
                    detailHtml += '</div></div>';
                }

                // 操作建议
                if (result.operation_advice) {
                    detailHtml += '<div style="margin-bottom: 0.75rem;"><strong>🎯 操作建议:</strong> <span style="color: var(--primary); font-weight: 600;">' + escapeHtml(result.operation_advice) + '</span></div>';
                }

                // 风险提示
                if (result.risk_warning) {
                    detailHtml += '<div style="margin-bottom: 0.75rem;"><strong>⚠️ 风险提示:</strong><p style="margin: 0.25rem 0; color: #dc2626; font-size: 0.875rem;">' + escapeHtml(result.risk_warning) + '</p></div>';
                }

                detailHtml += '</div>';
            } else {
                // 精简报告格式
                detailHtml = '<div class="task-detail" style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border);">';

                // 核心结论
                if (result.analysis_summary) {
                    detailHtml += '<div style="margin-bottom: 0.5rem;"><strong>📌 ' + escapeHtml(result.analysis_summary) + '</strong></div>';
                }

                // 趋势预测
                if (result.trend_prediction) {
                    detailHtml += '<div style="font-size: 0.875rem; margin-bottom: 0.25rem;"><strong>📊 趋势:</strong> ' + escapeHtml(result.trend_prediction) + '</div>';
                }

                // 操作建议
                if (result.operation_advice) {
                    detailHtml += '<div style="font-size: 0.875rem; margin-bottom: 0.25rem;"><strong>🎯 建议:</strong> ' + escapeHtml(result.operation_advice) + '</div>';
                }

                // 置信度
                if (result.confidence_level) {
                    detailHtml += '<div style="font-size: 0.875rem; margin-bottom: 0.25rem;"><strong>📈 置信度:</strong> ' + escapeHtml(result.confidence_level) + '</div>';
                }

                // 关键看点
                if (result.key_points) {
                    detailHtml += '<div style="font-size: 0.875rem; margin-top: 0.5rem;"><strong>💡 关键看点:</strong><p style="margin: 0.25rem 0; color: var(--text-light);">' + escapeHtml(result.key_points) + '</p></div>';
                }

                detailHtml += '</div>';
            }
        }

        return '<div class="task-card ' + status + '" id="task_' + taskId + '" style="' + (isExpanded ? 'cursor: default;' : 'cursor: pointer;') + '" onclick="toggleTaskDetail(\\''+taskId+'\\')">' +
            '<div class="task-status">' + statusIcon + '</div>' +
            '<div class="task-main">' +
                '<div class="task-header">' +
                    '<span class="task-code">' + code + '</span>' +
                    '<span class="task-name">' + (result.name || code) + '</span>' +
                '</div>' +
                '<div class="task-meta">' +
                    '<span>⏱ ' + formatTime(task.start_time) + '</span>' +
                    '<span>⏳ ' + calcDuration(task.start_time, task.end_time) + '</span>' +
                    '<span>' + (task.report_type === 'full' ? '📊完整' : '📝精简') + '</span>' +
                '</div>' +
                detailHtml +
            '</div>' +
            resultHtml +
            '<div class="task-actions">' +
                '<button class="task-btn" onclick="event.stopPropagation(); removeTask(\\''+taskId+'\\')">×</button>' +
            '</div>' +
        '</div>';
    }

    // HTML 转义函数
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // 切换任务详情展开/收起
    window.toggleTaskDetail = function(taskId) {
        const taskData = tasks.get(taskId);
        if (taskData && taskData.task && taskData.task.status === 'completed') {
            taskData.expanded = !taskData.expanded;
            renderAllTasks();
        }
    };

    function renderAllTasks() {
        if (tasks.size === 0) {
            taskList.innerHTML = '<div class="empty-state"><div class="empty-state-icon">🔍</div><div class="empty-state-text">输入股票代码开始分析</div></div>';
            return;
        }

        let html = '';
        const sortedTasks = Array.from(tasks.entries())
            .sort((a, b) => (b[1].task?.start_time || '').localeCompare(a[1].task?.start_time || ''));

        sortedTasks.slice(0, MAX_TASKS_DISPLAY).forEach(([taskId, taskData]) => {
            html += renderTaskCard(taskId, taskData);
        });

        if (sortedTasks.length > MAX_TASKS_DISPLAY) {
            html += '<div class="text-center text-muted mt-2">... 还有 ' + (sortedTasks.length - MAX_TASKS_DISPLAY) + ' 个任务</div>';
        }

        taskList.innerHTML = html;
    }

    window.removeTask = function(taskId) {
        tasks.delete(taskId);
        renderAllTasks();
        checkStopPolling();
    };

    function pollAllTasks() {
        let hasRunning = false;

        tasks.forEach((taskData, taskId) => {
            const status = taskData.task?.status;
            if (status === 'running' || status === 'pending' || !status) {
                hasRunning = true;
                taskData.pollCount = (taskData.pollCount || 0) + 1;

                if (taskData.pollCount > MAX_POLL_COUNT) {
                    taskData.task = taskData.task || {};
                    taskData.task.status = 'failed';
                    taskData.task.error = '轮询超时';
                    return;
                }

                fetch('/task?id=' + encodeURIComponent(taskId))
                    .then(r => r.json())
                    .then(data => {
                        if (data.success && data.task) {
                            taskData.task = data.task;
                            renderAllTasks();
                        }
                    })
                    .catch(() => {});
            }
        });

        if (!hasRunning) {
            checkStopPolling();
        }
    }

    function checkStopPolling() {
        let hasRunning = false;
        tasks.forEach((taskData) => {
            const status = taskData.task?.status;
            if (status === 'running' || status === 'pending' || !status) {
                hasRunning = true;
            }
        });

        if (!hasRunning && pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
        }
    }

    function startPolling() {
        if (!pollInterval) {
            pollInterval = setInterval(pollAllTasks, POLL_INTERVAL_MS);
        }
    }

    window.submitAnalysis = function() {
        const code = codeInput.value.trim();
        const isAStock = /^\\d{6}$/.test(code);
        const isHKStock = /^HK\\d{5}$/.test(code);
        const isUSStock = /^[A-Z]{1,5}(\\.[A-Z]{1,2})?$/.test(code);

        if (!(isAStock || isHKStock || isUSStock)) {
            return;
        }

        submitBtn.disabled = true;
        submitBtn.textContent = '提交中...';

        const reportType = getReportType();
        fetch('/analysis?code=' + encodeURIComponent(code) + '&report_type=' + encodeURIComponent(reportType))
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const taskId = data.task_id;
                    tasks.set(taskId, {
                        task: {
                            code: code,
                            status: 'running',
                            start_time: new Date().toISOString(),
                            report_type: reportType
                        },
                        pollCount: 0
                    });

                    renderAllTasks();
                    startPolling();
                    codeInput.value = '';

                    setTimeout(() => {
                        fetch('/task?id=' + encodeURIComponent(taskId))
                            .then(r => r.json())
                            .then(d => {
                                if (d.success && d.task) {
                                    tasks.get(taskId).task = d.task;
                                    renderAllTasks();
                                }
                            });
                    }, 500);
                } else {
                    alert('提交失败: ' + (data.error || '未知错误'));
                }
            })
            .catch(error => {
                alert('请求失败: ' + error.message);
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = '🚀 开始分析';
                updateButtonState();
            });
    };

    updateButtonState();
    renderAllTasks();
})();
</script>
"""

    content = f"""
  <div class="app-container">
    {render_navbar("query")}

    <!-- 主内容区域：两列布局 -->
    <div style="display: grid; grid-template-columns: 1fr 350px; gap: 1.5rem; align-items: start;">
      <!-- 左侧：快速分析 -->
      <div>
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">🔍 快速分析</h2>
          </div>
          <div class="card-body">
            <!-- 报告类型选择 -->
            <div class="form-group">
              <label>选择报告类型</label>
              <div class="report-type-selector">
                <input type="radio" name="report_type" id="report_simple" value="simple" class="report-type-radio" checked>
                <label for="report_simple" class="report-type-label">
                  📝 精简报告
                  <span class="report-type-description">核心结论 + 关键数据 + 操作建议</span>
                </label>

                <input type="radio" name="report_type" id="report_full" value="full" class="report-type-radio">
                <label for="report_full" class="report-type-label">
                  📊 完整报告
                  <span class="report-type-description">决策仪表盘 + 数据透视 + 情报分析</span>
                </label>
              </div>
            </div>

            <!-- 代码输入 -->
            <div class="form-group" style="margin-bottom: 1rem;">
              <label for="analysis_code">股票代码</label>
              <div class="input-group">
                <input
                    type="text"
                    id="analysis_code"
                    placeholder="A股 600519 / 港股 HK00700 / 美股 AAPL"
                    maxlength="8"
                    autocomplete="off"
                />
                <button type="button" id="analysis_btn" class="btn-success" onclick="submitAnalysis()" disabled>
                  🚀 开始分析
                </button>
              </div>
              <p class="text-muted mt-1">支持 A股(6位数字)、港股(HK+5位)、美股(1-5个字母)</p>
            </div>

            <!-- 任务列表 -->
            <div id="task_list" class="task-list"></div>
          </div>
        </div>

        <!-- 数据来源说明 -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title" style="font-size: 1rem;">📊 数据来源与分析逻辑</h3>
          </div>
          <div class="card-body">
            <div style="font-size: 0.875rem; line-height: 1.8;">
              <p><strong>📈 技术面数据：</strong>AkShare/Tushare/Yahoo Finance (实时行情+历史数据)</p>
              <p><strong>📰 新闻数据：</strong>Tavily/SerpAPI/Bocha (多维度实时搜索)</p>
              <p><strong>🤖 AI 分析：</strong>Google Gemini / OpenAI 兼容 API (temperature=0.0 确保一致性)</p>
              <p><strong>📊 分析维度：</strong>技术面(MA/量能) + 基本面 + 消息面 + 趋势分析</p>
              <hr style="border: none; border-top: 1px solid var(--border); margin: 1rem 0;">
              <p><strong>报告类型说明：</strong></p>
              <ul style="margin: 0.5rem 0; padding-left: 1.25rem;">
                <li><strong>精简报告</strong>：快速查看核心结论、买卖点位、操作建议</li>
                <li><strong>完整报告</strong>：深度分析技术面/基本面/消息面，包含决策仪表盘、数据透视、情报分析、作战计划</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：订阅管理 -->
      <div>
        <div class="card">
          <div class="card-header">
            <h3 class="card-title" style="font-size: 1rem;">📋 订阅管理</h3>
          </div>
          <div class="card-body">
            <form method="post" action="/update">
              <div class="form-group">
                <label for="stock_list">自选股列表</label>
                <p class="text-muted mb-2">用于定时分析，一行一个或逗号分隔</p>
                <textarea
                    id="stock_list"
                    name="stock_list"
                    rows="8"
                    placeholder="例如：600519, 000001"
                >{safe_value}</textarea>
              </div>
              <button type="submit" class="btn-secondary" style="width: 100%;">💾 保存配置</button>
              <p class="text-muted mt-2 text-center">配置文件: {html.escape(env_filename)}</p>
            </form>
          </div>
        </div>

        <!-- API 说明 -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title" style="font-size: 1rem;">🔌 API 接口</h3>
          </div>
          <div class="card-body">
            <div style="font-size: 0.75rem; font-family: monospace; line-height: 1.6;">
              GET /health<br>
              GET /analysis?code=xxx<br>
              GET /tasks<br>
              GET /task?id=xxx<br>
              GET /detail?id=xxx
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="footer">
      <p>📊 智能股票分析系统 | AI驱动决策 | 数据仅供参考</p>
    </div>
  </div>

  {toast_html}
  {analysis_js}
"""

    return render_base(
        title="查询分析 | 智能股票分析",
        content=content
    )


def render_subscription_page(subscription_list: list = None) -> bytes:
    """
    渲染订阅监控页面
    """
    if subscription_list is None:
        subscription_list = []

    # 生成订阅卡片
    subscription_cards = ""
    for item in subscription_list:
        subscription_cards += f"""
        <div class="subscription-card">
          <div class="subscription-header">
            <span class="subscription-code">{html.escape(item.get('code', ''))}</span>
            <span class="subscription-status {'active' if item.get('active') else 'inactive'}">
              {'监控中' if item.get('active') else '已暂停'}
            </span>
          </div>
          <div class="subscription-body">
            <div><strong>{html.escape(item.get('name', ''))}</strong></div>
            <div class="text-muted mt-1">最后更新: {item.get('last_update', '-')}</div>
            <div class="mt-2">
              <span class="task-advice {item.get('advice_class', '')}">{item.get('advice', '-')}</span>
              <span class="task-score">评分: {item.get('score', '-')}</span>
            </div>
          </div>
        </div>
        """

    if not subscription_cards:
        subscription_cards = '<div class="empty-state"><div class="empty-state-icon">📋</div><div class="empty-state-text">暂无订阅标的</div></div>'

    content = f"""
  <div class="app-container">
    {render_navbar("subscription")}

    <div class="card">
      <div class="card-header">
        <h2 class="card-title">📋 订阅监控</h2>
        <button class="btn-sm">🔄 刷新全部</button>
      </div>
      <div class="card-body">
        <p class="text-muted">订阅标的将自动定期分析，并在关键信号变化时推送通知。</p>
      </div>
    </div>

    <div class="subscription-grid">
      {subscription_cards}
    </div>

    <div class="footer">
      <p>📊 订阅监控 | 自动分析 | 实时推送</p>
    </div>
  </div>
"""

    return render_base(
        title="订阅监控 | 智能股票分析",
        content=content
    )


def render_futures_page(metrics_list: list = None, extreme_symbols: list = None, data_unavailable: bool = False) -> bytes:
    """
    渲染期货监控页面
    """
    if metrics_list is None:
        metrics_list = []
    if extreme_symbols is None:
        extreme_symbols = []

    # 数据不可用提示
    unavailable_alert = ""
    if data_unavailable:
        unavailable_alert = f"""
        <div class="card" style="background: #fef3c7; border-color: #f59e0b;">
          <div class="card-body" style="text-align: center; color: #92400e;">
            <div style="font-size: 1.25rem; font-weight: 600; margin-bottom: 0.5rem;">⚠️ 数据源暂时不可用</div>
            <div style="font-size: 0.875rem;">无法从 Yahoo Finance 获取 CBOE 波动率指数数据（可能是网络问题或API限制）</div>
            <div style="font-size: 0.75rem; margin-top: 0.5rem;">请稍后刷新页面重试，或配置代理/VPN</div>
          </div>
        </div>
        """

    # 生成极端风险预警
    extreme_alert = ""
    if extreme_symbols:
        extreme_alert = f"""
        <div class="card" style="background: #fee2e2; border-color: #ef4444;">
          <div class="card-body" style="text-align: center; color: #991b1b;">
            <div style="font-size: 1.25rem; font-weight: 600; margin-bottom: 0.5rem;">🚨 极端风险预警</div>
            <div>检测到 {len(extreme_symbols)} 个标的出现 IV-HV 极端背离</div>
          </div>
        </div>
        """

    # 生成期货卡片
    futures_cards = ""
    for m in metrics_list:
        risk_class = f"risk-{m.get('risk_level', 'low')}"
        iv_pct = m.get('iv_percentile', 0)

        # IV 分位数颜色
        if iv_pct >= 95:
            iv_color = '#ef4444'
        elif iv_pct >= 90:
            iv_color = '#f97316'
        elif iv_pct >= 80:
            iv_color = '#f59e0b'
        else:
            iv_color = '#10b981'

        futures_cards += f"""
        <div class="futures-card {risk_class}">
          <div class="futures-header">
            <span class="futures-symbol">{html.escape(m.get('symbol', ''))}</span>
            <span style="font-size: 0.875rem; color: var(--text-light);">{html.escape(m.get('name', ''))}</span>
            <span class="futures-price">${m.get('current_price', 0):.2f}</span>
          </div>
          <div class="futures-metrics">
            <div class="futures-metric">
              <span class="futures-label">IV (隐含波动率)</span>
              <span class="futures-value">{m.get('iv_current', 0):.2f}%</span>
            </div>
            <div class="futures-metric">
              <span class="futures-label">IV 分位数</span>
              <span class="futures-value" style="color: {iv_color};">{iv_pct:.1f}%</span>
            </div>
            <div class="futures-metric">
              <span class="futures-label">HV (历史波动率)</span>
              <span class="futures-value">{m.get('hv_20d', 0):.2f}%</span>
            </div>
            <div class="futures-metric">
              <span class="futures-label">IV-HV 背离度</span>
              <span class="futures-value">{m.get('iv_hv_divergence', 0):+.2f}%</span>
            </div>
          </div>
          <div class="futures-risk">
            <span class="risk-badge">{m.get('risk_level', 'low').upper()}</span>
            <span class="text-muted" style="font-size: 0.7rem;">{m.get('timestamp', '')[:16]}</span>
          </div>
        </div>
        """

    if not futures_cards:
        futures_cards = '<div class="empty-state"><div class="empty-state-icon">📊</div><div class="empty-state-text">暂无监控数据</div></div>'

    # 图例
    legend = """
    <div class="card">
      <div class="card-body" style="display: flex; gap: 1.5rem; justify-content: center; flex-wrap: wrap;">
        <div style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.875rem;">
          <span style="width: 12px; height: 12px; border-radius: 50%; background: #10b981;"></span>
          <span>安全 (低)</span>
        </div>
        <div style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.875rem;">
          <span style="width: 12px; height: 12px; border-radius: 50%; background: #f59e0b;"></span>
          <span>警告 (中)</span>
        </div>
        <div style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.875rem;">
          <span style="width: 12px; height: 12px; border-radius: 50%; background: #f97316;"></span>
          <span>高危 (高)</span>
        </div>
        <div style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.875rem;">
          <span style="width: 12px; height: 12px; border-radius: 50%; background: #ef4444;"></span>
          <span>极端 (极高)</span>
        </div>
      </div>
    </div>
    """

    content = f"""
  <div class="app-container">
    {render_navbar("futures")}

    {extreme_alert}

    <div class="card">
      <div class="card-header">
        <h2 class="card-title">📊 期货/期权波动率监控</h2>
        <button class="btn-sm" onclick="location.reload()">🔄 刷新</button>
      </div>
      <div class="card-body">
        <p class="text-muted">
          监控贵金属、商品、加密货币的 IV-HV 背离信号。当 IV 处于历史高位且显著高于 HV 时，表明期权杠杆极其昂贵，多头面临时间损耗反噬。
        </p>
      </div>
    </div>

    {legend}

    <div class="futures-grid">
      {futures_cards}
    </div>

    <div class="footer">
      <p>💡 数据来源: CBOE 官方波动率指数 (VIX, GVZ, OVX 等) | 消除波动率微笑偏差</p>
      <p class="mt-1">数据每5分钟自动刷新 | IV-HV 背离策略预警</p>
    </div>
  </div>
"""

    return render_base(
        title="期货监控 | 智能股票分析",
        content=content
    )


def render_history_page(history: list = None, stock_list: list = None) -> bytes:
    """
    渲染历史记录页面
    """
    if history is None:
        history = []
    if stock_list is None:
        stock_list = []

    # 生成历史记录卡片
    history_cards = ""
    for item in history:
        advice_class = "buy" if "买" in item.get("operation_advice", "") else "sell" if "卖" in item.get("operation_advice", "") else "wait"
        time_str = item.get("analysis_time", "")[:16] if item.get("analysis_time") else ""

        history_cards += f"""
        <div class="subscription-card" onclick="showDetail({item.get('id')})" style="cursor: pointer;">
          <div class="subscription-header">
            <div>
              <span class="subscription-code">{html.escape(item.get('code', ''))}</span>
              <span style="color: var(--text-light); font-size: 0.875rem; margin-left: 0.5rem;">{html.escape(item.get('name', ''))}</span>
            </div>
            <span class="task-advice {advice_class}">{html.escape(item.get('operation_advice', '未知'))}</span>
          </div>
          <div class="subscription-body">
            <div class="text-muted" style="font-size: 0.75rem;">{time_str}</div>
            <div class="mt-1" style="font-size: 0.875rem;">
              <span class="task-score">评分: {item.get('sentiment_score', 0)}</span>
              <span style="margin-left: 0.5rem;">{html.escape(item.get('trend_prediction', ''))}</span>
            </div>
            <div class="text-muted mt-1" style="font-size: 0.875rem;">
              {html.escape((item.get('analysis_summary') or '')[:100])}...
            </div>
          </div>
        </div>
        """

    if not history_cards:
        history_cards = '<div class="empty-state"><div class="empty-state-icon">📜</div><div class="empty-state-text">暂无分析记录</div></div>'

    content = f"""
  <div class="app-container">
    {render_navbar("history")}

    <div class="card">
      <div class="card-header">
        <h2 class="card-title">📜 分析历史</h2>
        <span class="text-muted" style="font-size: 0.875rem;">共 {len(history)} 条记录</span>
      </div>
    </div>

    <div class="subscription-grid" style="grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));">
      {history_cards}
    </div>

    <div class="footer">
      <p>📜 历史记录 | 点击查看详情</p>
    </div>
  </div>
"""

    return render_base(
        title="历史记录 | 智能股票分析",
        content=content
    )


def render_error_page(status_code: int, message: str, details: Optional[str] = None) -> bytes:
    """渲染错误页面"""
    details_html = f"<p class='text-muted'>{html.escape(details)}</p>" if details else ""

    content = f"""
  <div class="app-container">
    <div class="card" style="text-align: center; max-width: 500px; margin: 3rem auto;">
      <div style="font-size: 3rem; margin-bottom: 1rem;">😵</div>
      <h2>{status_code}</h2>
      <p class="text-muted">{html.escape(message)}</p>
      {details_html}
      <a href="/" style="color: var(--primary); text-decoration: none; display: inline-block; margin-top: 1rem;">← 返回首页</a>
    </div>
  </div>
"""

    return render_base(
        title=f"错误 {status_code}",
        content=content
    )
