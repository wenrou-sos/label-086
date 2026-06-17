"""
爆破效果模块
分析炸药单耗与块度合格率关系、识别最佳参数区间、提供相关性分析等
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from utils.data_loader import load_blasting_effect


def render_blasting_effect(config=None):
    """渲染爆破效果分析模块"""
    st.markdown("## 💥 爆破效果分析")
    
    if config is None:
        from utils.config import load_config
        config = load_config()
    
    blast_cfg = config['blasting']
    
    df = load_blasting_effect()
    if df.empty:
        st.warning("爆破效果数据加载失败，请检查数据文件")
        return
    
    df = _add_optimal_flags(df, blast_cfg)
    
    # 筛选控件
    col1, col2, col3 = st.columns(3)
    with col1:
        areas = ['全部区域'] + sorted(df['blast_area'].unique().tolist())
        selected_area = st.selectbox("选择爆破区域", areas)
    with col2:
        date_min = df['date'].min().date()
        date_max = df['date'].max().date()
        default_start = date_max - pd.Timedelta(days=365)
        date_range = st.date_input(
            "选择时间范围",
            value=(default_start, date_max),
            min_value=date_min,
            max_value=date_max
        )
    with col3:
        show_optimal_only = st.checkbox("仅显示最佳区间数据", value=False)
    
    st.markdown("---")
    
    # 过滤数据
    start_date, end_date = date_range
    filtered_df = df[
        (df['date'] >= pd.to_datetime(start_date)) &
        (df['date'] <= pd.to_datetime(end_date))
    ].copy()
    
    if selected_area != '全部区域':
        filtered_df = filtered_df[filtered_df['blast_area'] == selected_area]
    
    if show_optimal_only:
        filtered_df = filtered_df[filtered_df['is_optimal_dyn'] == True]
    
    # 总体KPI
    _render_kpi_cards(filtered_df, blast_cfg)
    
    st.markdown("---")
    
    # 核心散点图
    _render_scatter_analysis(filtered_df, blast_cfg)
    
    st.markdown("---")
    
    # 相关性分析和趋势预测
    col1, col2 = st.columns(2)
    with col1:
        _render_correlation_analysis(filtered_df)
    with col2:
        _render_trend_prediction(filtered_df, blast_cfg)
    
    st.markdown("---")
    
    # 最佳区间分析
    _render_optimal_zone_analysis(filtered_df, blast_cfg)
    
    st.markdown("---")
    
    # 区域对比
    _render_area_comparison(filtered_df, selected_area, blast_cfg)
    
    # 详细数据表
    with st.expander("📋 查看爆破记录明细"):
        display_df = filtered_df.copy()
        display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
        display_df = display_df.sort_values('date', ascending=False)
        display_cols = {
            'date': '日期',
            'blast_id': '爆破编号',
            'blast_area': '爆破区域',
            'powder_factor': '炸药单耗(kg/t)',
            'fragmentation_quality': '块度合格率(%)',
            'hole_count': '炮孔数',
            'total_explosive': '炸药总量(kg)',
            'is_optimal_dyn': '是否最佳区间'
        }
        display_df = display_df[list(display_cols.keys())]
        display_df.columns = list(display_cols.values())
        st.dataframe(display_df, use_container_width=True, hide_index=True, height=500)


def _add_optimal_flags(df, blast_cfg):
    """根据配置动态添加最佳区间标记"""
    df = df.copy()
    opt_min = blast_cfg['optimal_powder_min']
    opt_max = blast_cfg['optimal_powder_max']
    quality_target = blast_cfg['quality_target']
    
    df['is_optimal_dyn'] = (
        (df['powder_factor'] >= opt_min) & 
        (df['powder_factor'] <= opt_max) &
        (df['fragmentation_quality'] >= quality_target)
    )
    return df


def _render_kpi_cards(df, blast_cfg):
    """渲染KPI指标卡片"""
    avg_powder = df['powder_factor'].mean()
    avg_quality = df['fragmentation_quality'].mean()
    optimal_count = df['is_optimal_dyn'].sum()
    optimal_rate = optimal_count / len(df) * 100 if len(df) > 0 else 0
    total_blasts = len(df)
    
    opt_min = blast_cfg['optimal_powder_min']
    opt_max = blast_cfg['optimal_powder_max']
    quality_target = blast_cfg['quality_target']
    quality_warn = blast_cfg['quality_warning']
    quality_danger = blast_cfg['quality_danger']
    
    # 块度合格率状态
    if avg_quality >= quality_target:
        q_status = 'ok'
        q_color = '#059669'
        q_label = '✅ 达标'
    elif avg_quality >= quality_warn:
        q_status = 'warning'
        q_color = '#f59e0b'
        q_label = '⚠️ 预警'
    else:
        q_status = 'danger'
        q_color = '#dc2626'
        q_label = '🚨 异常'
    
    # 平均单耗状态
    if opt_min <= avg_powder <= opt_max:
        p_status = 'ok'
        p_color = '#059669'
        p_label = '✅ 最佳区间'
    else:
        p_status = 'warning'
        p_color = '#f59e0b'
        p_label = '⚠️ 偏离最佳'
    
    # 最佳区间平均质量
    optimal_df = df[df['is_optimal_dyn'] == True]
    optimal_avg_quality = optimal_df['fragmentation_quality'].mean() if len(optimal_df) > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="平均炸药单耗",
            value=f"{avg_powder:.3f} kg/t",
            delta=p_label,
            delta_color='normal'
        )
        st.caption(f"<span style='color:{p_color}'>最佳: {opt_min}-{opt_max} kg/t</span>", unsafe_allow_html=True)
    with col2:
        st.metric(
            label="平均块度合格率",
            value=f"{avg_quality:.1f}%",
            delta=q_label,
            delta_color='normal'
        )
        st.caption(f"<span style='color:{q_color}'>目标: {quality_target}%</span>", unsafe_allow_html=True)
    with col3:
        st.metric(
            label="最佳区间占比",
            value=f"{optimal_rate:.1f}%",
            delta=f"{optimal_count}/{total_blasts} 次"
        )
    with col4:
        st.metric(
            label="总爆破次数",
            value=f"{total_blasts} 次"
        )


def _render_scatter_analysis(df, blast_cfg):
    """渲染炸药单耗与块度合格率散点图"""
    st.markdown("### 📊 炸药单耗 vs 块度合格率")
    
    opt_min = blast_cfg['optimal_powder_min']
    opt_max = blast_cfg['optimal_powder_max']
    
    fig = go.Figure()
    
    # 非最佳数据
    non_optimal = df[df['is_optimal_dyn'] == False]
    fig.add_trace(go.Scatter(
        x=non_optimal['powder_factor'],
        y=non_optimal['fragmentation_quality'],
        mode='markers',
        name='普通数据',
        marker=dict(
            color='#6b7280',
            size=8,
            opacity=0.6,
            line=dict(width=1, color='white')
        ),
        hovertemplate=(
            '炸药单耗: %{x:.3f} kg/t<br>'
            '块度合格率: %{y:.1f}%<br>'
            '<extra></extra>'
        )
    ))
    
    # 最佳区间数据
    optimal = df[df['is_optimal_dyn'] == True]
    if not optimal.empty:
        fig.add_trace(go.Scatter(
            x=optimal['powder_factor'],
            y=optimal['fragmentation_quality'],
            mode='markers',
            name='最佳区间',
            marker=dict(
                color='#059669',
                size=10,
                symbol='circle',
                line=dict(width=2, color='white')
            ),
            hovertemplate=(
                '炸药单耗: %{x:.3f} kg/t<br>'
                '块度合格率: %{y:.1f}%<br>'
                '✅ 最佳参数区间<br>'
                '<extra></extra>'
            )
        ))
    
    # 添加最佳区间背景
    fig.add_vrect(
        x0=opt_min, x1=opt_max,
        fillcolor="#059669", opacity=0.1,
        layer="below", line_width=0,
        annotation_text=f"最佳区间<br>{opt_min}-{opt_max} kg/t",
        annotation_position="top right"
    )
    
    # 添加质量目标线
    quality_target = blast_cfg['quality_target']
    fig.add_hline(
        y=quality_target,
        line_dash="dash",
        line_color="#059669",
        line_width=1.5,
        annotation_text=f"目标合格率 ({quality_target}%)",
        annotation_position="top left"
    )
    
    # 添加趋势线
    if len(df) > 10:
        z = np.polyfit(df['powder_factor'], df['fragmentation_quality'], 2)
        p = np.poly1d(z)
        x_trend = np.linspace(df['powder_factor'].min(), df['powder_factor'].max(), 100)
        y_trend = p(x_trend)
        
        fig.add_trace(go.Scatter(
            x=x_trend,
            y=y_trend,
            mode='lines',
            name='二次趋势线',
            line=dict(color='#dc2626', width=2.5, dash='dash')
        ))
    
    fig.update_layout(
        title='炸药单耗与块度合格率关系散点图',
        xaxis_title='炸药单耗 (kg/t)',
        yaxis_title='块度合格率 (%)',
        yaxis=dict(range=[55, 100]),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        template='plotly_white',
        height=450,
        hovermode='closest'
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_correlation_analysis(df):
    """渲染相关性分析"""
    st.markdown("### 🔗 相关性分析")
    
    if len(df) < 5:
        st.info("数据量不足，无法进行相关性分析")
        return
    
    corr = df['powder_factor'].corr(df['fragmentation_quality'])
    abs_corr = abs(corr)
    
    if abs_corr >= 0.8:
        strength = "强相关"
        color = "#059669"
    elif abs_corr >= 0.5:
        strength = "中等相关"
        color = "#f59e0b"
    elif abs_corr >= 0.3:
        strength = "弱相关"
        color = "#2563eb"
    else:
        strength = "极弱或无相关"
        color = "#6b7280"
    
    direction = "正相关" if corr > 0 else "负相关"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=corr,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f'相关系数 (Pearson)<br><span style="color:{color}; font-size:0.8em">{strength} · {direction}</span>'},
        gauge={
            'axis': {'range': [-1, 1], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#e5e7eb",
            'steps': [
                {'range': [-1, -0.8], 'color': '#fecaca'},
                {'range': [-0.8, -0.5], 'color': '#fed7aa'},
                {'range': [-0.5, 0.5], 'color': '#f3f4f6'},
                {'range': [0.5, 0.8], 'color': '#fed7aa'},
                {'range': [0.8, 1], 'color': '#fecaca'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': corr
            }
        },
        number={'valueformat': '.3f'}
    ))
    
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("#### 📈 统计摘要")
    stats = {
        '爆破次数': len(df),
        '炸药单耗范围': f"{df['powder_factor'].min():.3f} ~ {df['powder_factor'].max():.3f}",
        '块度合格率范围': f"{df['fragmentation_quality'].min():.1f}% ~ {df['fragmentation_quality'].max():.1f}%",
        '炸药单耗标准差': f"{df['powder_factor'].std():.4f}",
        '块度合格率标准差': f"{df['fragmentation_quality'].std():.2f}%"
    }
    for k, v in stats.items():
        st.markdown(f"- **{k}**: {v}")


def _render_trend_prediction(df, blast_cfg):
    """渲染趋势预测"""
    st.markdown("### 🔮 块度合格率趋势预测")
    
    quality_target = blast_cfg['quality_target']
    
    if len(df) < 10:
        st.info("数据量不足，无法进行趋势预测")
        return
    
    df_daily = df.groupby(df['date'].dt.to_period('W').dt.start_time).agg({
        'powder_factor': 'mean',
        'fragmentation_quality': 'mean'
    }).reset_index()
    df_daily = df_daily.sort_values('date')
    
    window = min(4, len(df_daily))
    df_daily['ma_quality'] = df_daily['fragmentation_quality'].rolling(window=window).mean()
    
    x = np.arange(len(df_daily))
    y = df_daily['fragmentation_quality'].values
    
    if len(x) >= 5:
        z = np.polyfit(x, y, 1)
        slope, intercept = z
        
        future_x = np.arange(len(df_daily), len(df_daily) + 4)
        future_y = slope * future_x + intercept
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df_daily['date'],
            y=df_daily['fragmentation_quality'],
            mode='lines+markers',
            name='实际块度合格率',
            line=dict(color='#2563eb', width=2),
            marker=dict(size=6)
        ))
        
        fig.add_trace(go.Scatter(
            x=df_daily['date'],
            y=df_daily['ma_quality'],
            mode='lines',
            name=f'{window}周移动平均',
            line=dict(color='#f59e0b', width=2, dash='dash')
        ))
        
        last_date = df_daily['date'].iloc[-1]
        future_dates = [last_date + pd.Timedelta(weeks=i) for i in range(1, 5)]
        fig.add_trace(go.Scatter(
            x=future_dates,
            y=future_y,
            mode='lines+markers',
            name='趋势预测',
            line=dict(color='#059669', width=2, dash='dot'),
            marker=dict(size=8, symbol='diamond')
        ))
        
        # 添加目标线
        fig.add_hline(
            y=quality_target,
            line_dash="dash",
            line_color="#059669",
            line_width=1.5,
            annotation_text=f"目标 ({quality_target}%)",
            annotation_position="top left"
        )
        
        fig.update_layout(
            title='块度合格率周趋势及预测',
            xaxis_title='日期',
            yaxis_title='块度合格率 (%)',
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1
            ),
            template='plotly_white',
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)
        
        trend_dir = "上升" if slope > 0 else "下降"
        st.markdown(f"""
        **趋势分析**: 
        - 当前趋势: **{trend_dir}** (斜率: {slope:+.4f}/周)
        - 预测未来4周平均合格率: **{np.mean(future_y):.1f}%**
        """)


def _render_optimal_zone_analysis(filtered_df, blast_cfg):
    """渲染最佳区间分析"""
    st.markdown("### 🎯 最佳炸药单耗区间分析")
    
    opt_min = blast_cfg['optimal_powder_min']
    opt_max = blast_cfg['optimal_powder_max']
    
    # 动态分段
    pf_min = filtered_df['powder_factor'].min()
    pf_max = filtered_df['powder_factor'].max()
    
    # 构造分段
    bins = [pf_min - 0.01]
    if opt_min > pf_min:
        bins.append(opt_min)
    bins.append(opt_max)
    if pf_max > opt_max:
        bins.append(pf_max + 0.01)
    
    # 生成标签
    labels = []
    for i in range(len(bins) - 1):
        labels.append(f"{bins[i]:.2f}-{bins[i+1]:.2f}")
    
    df = filtered_df.copy()
    df['pf_range'] = pd.cut(df['powder_factor'], bins=bins, labels=labels)
    
    zone_stats_list = []
    for label, group in df.groupby('pf_range'):
        if len(group) > 0:
            zone_stats_list.append({
                '单耗区间(kg/t)': str(label),
                '爆破次数': len(group),
                '平均合格率(%)': group['fragmentation_quality'].mean(),
                '合格率标准差': group['fragmentation_quality'].std(),
                '平均单耗': group['powder_factor'].mean(),
                'is_optimal': opt_min <= group['powder_factor'].mean() <= opt_max
            })
    
    zone_stats = pd.DataFrame(zone_stats_list)
    if zone_stats.empty:
        st.info("数据不足，无法进行区间分析")
        return
    
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        fig = go.Figure()
        
        colors = ['#059669' if r['is_optimal'] else '#dc2626' 
                  for _, r in zone_stats.iterrows()]
        
        fig.add_trace(go.Bar(
            x=zone_stats['单耗区间(kg/t)'],
            y=zone_stats['平均合格率(%)'],
            marker_color=colors,
            text=zone_stats['平均合格率(%)'].round(1).astype(str) + '%',
            textposition='outside',
            error_y=dict(
                type='data',
                array=zone_stats['合格率标准差'].fillna(0),
                visible=True,
                color='#6b7280'
            )
        ))
        
        # 添加目标线
        quality_target = blast_cfg['quality_target']
        fig.add_hline(
            y=quality_target,
            line_dash="dash",
            line_color="#059669",
            line_width=1.5,
            annotation_text=f"目标 ({quality_target}%)"
        )
        
        fig.update_layout(
            title='各炸药单耗区间块度合格率对比',
            xaxis_title='炸药单耗区间 (kg/t)',
            yaxis_title='平均块度合格率 (%)',
            yaxis=dict(range=[65, 100]),
            template='plotly_white',
            height=380
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 📊 最佳区间表现")
        optimal = df[df['is_optimal_dyn'] == True]
        non_optimal = df[df['is_optimal_dyn'] == False]
        
        metrics = {
            '指标': ['平均块度合格率', '平均炸药单耗', '爆破次数占比'],
            '最佳区间': [
                f"{optimal['fragmentation_quality'].mean():.1f}%" if len(optimal) > 0 else "-",
                f"{optimal['powder_factor'].mean():.3f} kg/t" if len(optimal) > 0 else "-",
                f"{len(optimal)/len(df)*100:.1f}%" if len(df) > 0 else "-"
            ],
            '其他区间': [
                f"{non_optimal['fragmentation_quality'].mean():.1f}%" if len(non_optimal) > 0 else "-",
                f"{non_optimal['powder_factor'].mean():.3f} kg/t" if len(non_optimal) > 0 else "-",
                f"{len(non_optimal)/len(df)*100:.1f}%" if len(df) > 0 else "-"
            ]
        }
        
        st.dataframe(pd.DataFrame(metrics), use_container_width=True, hide_index=True)
        
        if len(optimal) > 0 and len(non_optimal) > 0:
            diff = optimal['fragmentation_quality'].mean() - non_optimal['fragmentation_quality'].mean()
            st.success(f"""
            💡 **优化建议**:
            将炸药单耗控制在 **{opt_min}-{opt_max} kg/t** 区间，
            可使块度合格率提升约 **{diff:.1f}%**
            """)


def _render_area_comparison(filtered_df, selected_area, blast_cfg):
    """渲染区域对比分析"""
    st.markdown("### 🗺️ 各爆破区域对比")
    
    if filtered_df.empty or 'blast_area' not in filtered_df.columns:
        st.info("暂无区域对比数据")
        return
    
    area_groups = filtered_df.groupby('blast_area')
    
    area_stats_list = []
    for area, group in area_groups:
        area_stats_list.append({
            '区域': area,
            '平均单耗': group['powder_factor'].mean(),
            '单耗标准差': group['powder_factor'].std(),
            '平均合格率(%)': group['fragmentation_quality'].mean(),
            '合格率标准差': group['fragmentation_quality'].std(),
            '爆破次数': len(group),
            '最佳次数': int(group['is_optimal_dyn'].sum())
        })
    
    area_stats = pd.DataFrame(area_stats_list)
    
    if area_stats.empty:
        st.info("暂无区域对比数据")
        return
    
    area_stats['最佳占比(%)'] = (area_stats['最佳次数'] / area_stats['爆破次数'] * 100).round(1)
    area_stats = area_stats.sort_values('区域').reset_index(drop=True)
    
    color_palette = ['#2563eb', '#059669', '#f59e0b', '#7c3aed', '#dc2626', '#0891b2']
    area_colors = [color_palette[i % len(color_palette)] for i in range(len(area_stats))]
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            x=area_stats['区域'],
            y=area_stats['平均合格率(%)'],
            marker_color=area_colors,
            text=area_stats['平均合格率(%)'].round(1).astype(str) + '%',
            textposition='outside',
            error_y=dict(
                type='data',
                array=area_stats['合格率标准差'].fillna(0),
                visible=True
            )
        ))
        
        quality_target = blast_cfg['quality_target']
        fig1.add_hline(
            y=quality_target,
            line_dash="dash",
            line_color="#059669",
            line_width=1.5,
            annotation_text=f"目标 ({quality_target}%)"
        )
        
        y_min = max(60, area_stats['平均合格率(%)'].min() - 10)
        fig1.update_layout(
            title='各区域平均块度合格率',
            xaxis_title='爆破区域',
            yaxis_title='合格率 (%)',
            yaxis=dict(range=[y_min, 100]),
            template='plotly_white',
            height=320
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=area_stats['区域'],
            y=area_stats['最佳占比(%)'],
            marker_color=area_colors,
            text=area_stats['最佳占比(%)'].astype(str) + '%',
            textposition='outside'
        ))
        fig2.update_layout(
            title='各区域最佳参数区间占比',
            xaxis_title='爆破区域',
            yaxis_title='最佳占比 (%)',
            template='plotly_white',
            height=320
        )
        st.plotly_chart(fig2, use_container_width=True)
