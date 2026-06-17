"""
产量分析模块
实现按日、月、年多维度展示采剥总量趋势图表、计划完成率计算等功能
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from utils.data_loader import (
    load_daily_production,
    load_monthly_production,
    load_yearly_production
)


def render_production_analysis(config=None):
    """渲染产量分析模块"""
    st.markdown("## 🏭 产量分析")
    
    if config is None:
        from utils.config import load_config
        config = load_config()
    
    prod_cfg = config['production']
    
    # 数据加载
    daily_df = load_daily_production()
    monthly_df = load_monthly_production()
    yearly_df = load_yearly_production()
    
    if daily_df.empty or monthly_df.empty or yearly_df.empty:
        st.warning("产量数据加载失败，请检查数据文件")
        return
    
    # 顶部筛选栏
    col1, col2, col3 = st.columns(3)
    with col1:
        time_dimension = st.selectbox(
            "时间维度",
            ["按日", "按月", "按年"],
            index=1
        )
    with col2:
        metric_type = st.selectbox(
            "指标类型",
            ["采剥总量", "矿石量", "岩石量"],
            index=0
        )
    with col3:
        date_range = _get_date_range(time_dimension, daily_df, monthly_df, yearly_df)
    
    st.markdown("---")
    
    # 根据维度选择数据
    if time_dimension == "按日":
        df = daily_df.copy()
        df = df[(df['date'] >= pd.to_datetime(date_range[0])) & 
                (df['date'] <= pd.to_datetime(date_range[1]))]
        x_col = 'date'
        x_label = '日期'
    elif time_dimension == "按月":
        df = monthly_df.copy()
        df = df[(df['year_month'] >= date_range[0]) & 
                (df['year_month'] <= date_range[1])]
        x_col = 'year_month'
        x_label = '月份'
    else:
        df = yearly_df.copy()
        df = df[(df['year'] >= date_range[0]) & 
                (df['year'] <= date_range[1])]
        x_col = 'year'
        x_label = '年份'
    
    # 选择指标列
    metric_map = {
        "采剥总量": ('total_volume', 'planned_total'),
        "矿石量": ('ore_volume', 'planned_ore'),
        "岩石量": ('rock_volume', 'planned_rock')
    }
    actual_col, planned_col = metric_map[metric_type]
    
    # KPI指标卡片
    _render_kpi_cards(df, actual_col, planned_col, metric_type, time_dimension, prod_cfg)
    
    st.markdown("---")
    
    # 主图表：产量趋势与计划对比
    fig_trend = _create_trend_chart(df, x_col, actual_col, planned_col, x_label, metric_type)
    st.plotly_chart(fig_trend, use_container_width=True)
    
    st.markdown("---")
    
    # 计划完成率趋势
    col_chart, col_table = st.columns([2, 1])
    
    with col_chart:
        fig_completion = _create_completion_rate_chart(df, x_col, x_label, prod_cfg)
        st.plotly_chart(fig_completion, use_container_width=True)
    
    with col_table:
        st.markdown("### 📊 数据明细")
        display_cols = [x_col, actual_col, planned_col, 'completion_rate']
        display_df = df[display_cols].copy()
        display_df.columns = [x_label, f'实际{metric_type}(吨)', f'计划{metric_type}(吨)', '完成率(%)']
        display_df['完成率(%)'] = display_df['完成率(%)'].round(2)
        st.dataframe(
            display_df,
            use_container_width=True,
            height=400,
            hide_index=True
        )
    
    # 下钻功能
    if time_dimension in ["按年", "按月"]:
        st.markdown("---")
        _render_drill_down(time_dimension, df, x_col, daily_df, monthly_df, metric_type)


def _get_date_range(time_dimension, daily_df, monthly_df, yearly_df):
    """获取日期范围选择"""
    if time_dimension == "按日":
        min_date = daily_df['date'].min().date()
        max_date = daily_df['date'].max().date()
        default_start = max_date - pd.Timedelta(days=90)
        default_start = max(default_start, min_date)
        return st.date_input(
            "选择日期范围",
            value=(default_start, max_date),
            min_value=min_date,
            max_value=max_date
        )
    elif time_dimension == "按月":
        months = sorted(monthly_df['year_month'].unique())
        return st.select_slider(
            "选择月份范围",
            options=months,
            value=(months[0], months[-1])
        )
    else:
        years = sorted(yearly_df['year'].unique())
        return st.select_slider(
            "选择年份范围",
            options=years,
            value=(years[0], years[-1])
        )


def _render_kpi_cards(df, actual_col, planned_col, metric_type, time_dimension, prod_cfg):
    """渲染KPI指标卡片"""
    total_actual = df[actual_col].sum()
    total_planned = df[planned_col].sum()
    avg_completion = df['completion_rate'].mean()
    
    warn = prod_cfg['completion_rate_warning']
    danger = prod_cfg['completion_rate_danger']
    
    if avg_completion >= warn:
        status = 'ok'
        status_color = '#059669'
        status_label = '✅ 达标'
    elif avg_completion >= danger:
        status = 'warning'
        status_color = '#f59e0b'
        status_label = '⚠️ 预警'
    else:
        status = 'danger'
        status_color = '#dc2626'
        status_label = '🚨 异常'
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label=f"实际{metric_type}",
            value=f"{total_actual:,.0f} 吨",
            delta=None
        )
    with col2:
        st.metric(
            label=f"计划{metric_type}",
            value=f"{total_planned:,.0f} 吨",
            delta=None
        )
    with col3:
        diff = total_actual - total_planned
        delta_pct = (diff / total_planned * 100) if total_planned > 0 else 0
        st.metric(
            label="完成率",
            value=f"{avg_completion:.1f}%",
            delta=status_label,
            delta_color="normal"
        )
        st.caption(f"<span style='color:{status_color}'>预警线: {warn}% | 危险线: {danger}%</span>", unsafe_allow_html=True)
    with col4:
        period = len(df)
        period_label = "天" if time_dimension == "按日" else ("个月" if time_dimension == "按月" else "年")
        avg_daily = total_actual / period if period > 0 else 0
        st.metric(
            label=f"平均{time_dimension.replace('按', '每')}产量",
            value=f"{avg_daily:,.0f} 吨",
            delta=None
        )


def _create_trend_chart(df, x_col, actual_col, planned_col, x_label, metric_type):
    """创建产量趋势与计划对比图"""
    fig = go.Figure()
    
    # 实际产量柱状图
    fig.add_trace(go.Bar(
        x=df[x_col],
        y=df[actual_col],
        name=f'实际{metric_type}',
        marker_color='#2563eb',
        opacity=0.85
    ))
    
    # 计划产量折线图
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[planned_col],
        name=f'计划{metric_type}',
        mode='lines+markers',
        line=dict(color='#dc2626', width=2.5),
        marker=dict(size=6)
    ))
    
    fig.update_layout(
        title=dict(
            text=f'{metric_type}趋势与计划对比',
            font=dict(size=18)
        ),
        xaxis_title=x_label,
        yaxis_title='产量（吨）',
        barmode='group',
        hovermode='x unified',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        template='plotly_white',
        height=450
    )
    
    return fig


def _create_completion_rate_chart(df, x_col, x_label, prod_cfg):
    """创建计划完成率趋势图"""
    fig = go.Figure()
    
    warn = prod_cfg['completion_rate_warning']
    danger = prod_cfg['completion_rate_danger']
    
    # 完成率折线
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df['completion_rate'],
        mode='lines+markers',
        name='完成率',
        line=dict(color='#059669', width=2.5),
        marker=dict(size=7),
        fill='tozeroy',
        fillcolor='rgba(5, 150, 105, 0.1)'
    ))
    
    # 100%目标线
    fig.add_hline(
        y=100,
        line_dash="dash",
        line_color="#dc2626",
        line_width=2,
        annotation_text="目标线 (100%)",
        annotation_position="bottom right"
    )
    
    # 预警线
    fig.add_hline(
        y=warn,
        line_dash="dash",
        line_color="#f59e0b",
        line_width=1.5,
        annotation_text=f"预警线 ({warn}%)",
        annotation_position="top left"
    )
    
    # 危险线
    fig.add_hline(
        y=danger,
        line_dash="dot",
        line_color="#dc2626",
        line_width=1.5,
        annotation_text=f"危险线 ({danger}%)",
        annotation_position="bottom left"
    )
    
    y_min = min(danger - 5, df['completion_rate'].min() - 5)
    y_max = max(105, df['completion_rate'].max() + 5)
    
    fig.update_layout(
        title=dict(
            text='计划完成率趋势',
            font=dict(size=16)
        ),
        xaxis_title=x_label,
        yaxis_title='完成率（%）',
        yaxis=dict(range=[y_min, y_max]),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        template='plotly_white',
        height=400
    )
    
    return fig


def _render_drill_down(time_dimension, df, x_col, daily_df, monthly_df, metric_type):
    """渲染数据下钻功能"""
    st.markdown("### 🔍 数据下钻")
    
    selected = st.selectbox(
        f"选择要下钻查看的{'年份' if time_dimension == '按年' else '月份'}",
        options=df[x_col].tolist(),
        index=len(df) - 1
    )
    
    if time_dimension == "按年":
        # 年 -> 月下钻
        drill_df = monthly_df.copy()
        drill_df['year'] = drill_df['year_month'].str[:4].astype(int)
        drill_df = drill_df[drill_df['year'] == selected]
        
        metric_map = {
            "采剥总量": ('total_volume', 'planned_total'),
            "矿石量": ('ore_volume', 'planned_ore'),
            "岩石量": ('rock_volume', 'planned_rock')
        }
        actual_col, planned_col = metric_map[metric_type]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=drill_df['year_month'],
            y=drill_df[actual_col],
            name=f'实际{metric_type}',
            marker_color='#2563eb'
        ))
        fig.add_trace(go.Scatter(
            x=drill_df['year_month'],
            y=drill_df[planned_col],
            name=f'计划{metric_type}',
            mode='lines+markers',
            line=dict(color='#dc2626', width=2)
        ))
        fig.update_layout(
            title=f'{selected}年 各月{metric_type}详情',
            xaxis_title='月份',
            yaxis_title='产量（吨）',
            template='plotly_white',
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        # 月 -> 日下钻
        drill_df = daily_df.copy()
        drill_df['year_month'] = drill_df['date'].dt.to_period('M').astype(str)
        drill_df = drill_df[drill_df['year_month'] == selected]
        
        metric_map = {
            "采剥总量": ('total_volume', 'planned_total'),
            "矿石量": ('ore_volume', 'planned_ore'),
            "岩石量": ('rock_volume', 'planned_rock')
        }
        actual_col, planned_col = metric_map[metric_type]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=drill_df['date'],
            y=drill_df[actual_col],
            name=f'实际{metric_type}',
            marker_color='#2563eb'
        ))
        fig.add_trace(go.Scatter(
            x=drill_df['date'],
            y=drill_df[planned_col],
            name=f'计划{metric_type}',
            mode='lines+markers',
            line=dict(color='#dc2626', width=2)
        ))
        fig.update_layout(
            title=f'{selected} 各日{metric_type}详情',
            xaxis_title='日期',
            yaxis_title='产量（吨）',
            template='plotly_white',
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)
