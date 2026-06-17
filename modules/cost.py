"""
成本分析模块
将采矿单位成本拆解为四项成本构成，支持同比环比分析，异常预警等
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from utils.data_loader import load_mining_cost


def render_cost_analysis(config=None):
    """渲染成本分析模块"""
    st.markdown("## 💰 成本分析")
    
    if config is None:
        from utils.config import load_config
        config = load_config()
    
    cost_cfg = config['cost']
    
    df = load_mining_cost()
    if df.empty:
        st.warning("成本数据加载失败，请检查数据文件")
        return
    
    # 根据配置动态标记异常
    df = _add_dynamic_anomaly(df, cost_cfg)
    
    # 筛选控件
    col1, col2, col3 = st.columns(3)
    with col1:
        years = ['全部年份'] + sorted(df['year'].unique().tolist())
        selected_year = st.selectbox("选择年份", years)
    with col2:
        analysis_type = st.selectbox(
            "分析类型",
            ["成本构成分析", "同比环比分析", "成本趋势分析"],
            index=0
        )
    with col3:
        show_anomaly = st.checkbox("高亮显示异常数据", value=True)
    
    st.markdown("---")
    
    # 过滤数据
    filtered_df = df.copy()
    if selected_year != '全部年份':
        filtered_df = filtered_df[filtered_df['year'] == selected_year]
    
    # 总体KPI
    _render_kpi_cards(filtered_df, df, cost_cfg)
    
    st.markdown("---")
    
    # 根据分析类型显示内容
    if analysis_type == "成本构成分析":
        _render_cost_composition(filtered_df, show_anomaly, cost_cfg)
    elif analysis_type == "同比环比分析":
        _render_yoy_mom_analysis(df, filtered_df, cost_cfg)
    else:
        _render_cost_trend(df, filtered_df, cost_cfg)
    
    st.markdown("---")
    
    # 成本异常预警
    _render_cost_warnings(df, filtered_df, cost_cfg)
    
    # 详细数据
    with st.expander("📋 查看完整成本数据"):
        display_df = filtered_df.copy()
        display_cols = {
            'date': '月份',
            'drilling_cost': '穿孔成本(元/吨)',
            'blasting_cost': '爆破成本(元/吨)',
            'loading_cost': '铲装成本(元/吨)',
            'transport_cost': '运输成本(元/吨)',
            'total_cost': '总成本(元/吨)',
            'is_anomaly': '是否异常',
            'optimization_suggestion': '优化建议'
        }
        display_df = display_df[list(display_cols.keys())]
        display_df.columns = list(display_cols.values())
        st.dataframe(display_df, use_container_width=True, hide_index=True, height=500)


def _add_dynamic_anomaly(df, cost_cfg):
    """根据配置动态添加成本异常标记"""
    df = df.copy()
    warn = cost_cfg['total_cost_warning']
    fluc_warn = cost_cfg['cost_fluctuation_warning']
    
    # 基于单位成本阈值的异常
    df['is_anomaly_dyn_cost'] = df['total_cost'] > warn
    
    # 基于波动的异常（环比变化超过阈值）
    df['mom_pct'] = df['total_cost'].pct_change() * 100
    df['is_anomaly_dyn_fluc'] = df['mom_pct'].abs() > fluc_warn
    
    # 综合异常标记
    df['is_anomaly_dyn'] = df['is_anomaly_dyn_cost'] | df['is_anomaly_dyn_fluc']
    
    # 异常类型
    def _get_anomaly_type(row):
        if row['is_anomaly_dyn_cost']:
            return 'total'
        elif row['is_anomaly_dyn_fluc']:
            return 'fluctuation'
        return None
    
    df['anomaly_type_dyn'] = df.apply(_get_anomaly_type, axis=1)
    
    return df


def _render_kpi_cards(current_df, full_df, cost_cfg):
    """渲染KPI指标卡片"""
    avg_total = current_df['total_cost'].mean()
    
    warn = cost_cfg['total_cost_warning']
    danger = cost_cfg['total_cost_danger']
    
    # 单位成本状态
    if avg_total <= warn:
        status = 'ok'
        status_color = '#059669'
        status_label = '✅ 正常'
    elif avg_total <= danger:
        status = 'warning'
        status_color = '#f59e0b'
        status_label = '⚠️ 预警'
    else:
        status = 'danger'
        status_color = '#dc2626'
        status_label = '🚨 异常'
    
    # 计算环比（与上一个周期比较）
    if len(current_df) >= 2:
        last_period = current_df.iloc[-1]
        prev_period = current_df.iloc[-2]
        mom_change = (last_period['total_cost'] - prev_period['total_cost']) / prev_period['total_cost'] * 100
    else:
        mom_change = 0
    
    # 计算同比
    if len(full_df) >= 12 and len(current_df) > 0:
        last = current_df.iloc[-1]
        last_year_month = full_df[
            (full_df['year'] == last['year'] - 1) & 
            (full_df['month'] == last['month'])
        ]
        if len(last_year_month) > 0:
            yoy_change = (last['total_cost'] - last_year_month.iloc[0]['total_cost']) / last_year_month.iloc[0]['total_cost'] * 100
        else:
            yoy_change = 0
    else:
        yoy_change = 0
    
    # 各成本占比
    avg_drilling = current_df['drilling_cost'].mean()
    avg_blasting = current_df['blasting_cost'].mean()
    avg_loading = current_df['loading_cost'].mean()
    avg_transport = current_df['transport_cost'].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="平均单位成本",
            value=f"{avg_total:.2f} 元/吨",
            delta=status_label,
            delta_color='normal'
        )
        st.caption(f"<span style='color:{status_color}'>预警: {warn}元 | 危险: {danger}元</span>", unsafe_allow_html=True)
    with col2:
        delta_color = "inverse" if yoy_change > 0 else "normal"
        st.metric(
            label="同比变化",
            value=f"{yoy_change:+.2f}%",
            delta="vs去年同期",
            delta_color=delta_color
        )
    with col3:
        # 最高成本项
        cost_items = [('穿孔', avg_drilling), ('爆破', avg_blasting), ('铲装', avg_loading), ('运输', avg_transport)]
        max_item = max(cost_items, key=lambda x: x[1])
        st.metric(
            label="最高成本项",
            value=max_item[0],
            delta=f"{max_item[1]:.2f} 元/吨"
        )
    with col4:
        anomaly_count = int(current_df['is_anomaly_dyn'].sum())
        total_count = len(current_df)
        st.metric(
            label="成本异常次数",
            value=f"{anomaly_count} 次",
            delta=f"占比 {anomaly_count/total_count*100:.1f}%" if total_count > 0 else ""
        )


def _render_cost_composition(df, show_anomaly, cost_cfg):
    """渲染成本构成分析"""
    st.markdown("### 🧩 成本构成分析")
    
    warn = cost_cfg['total_cost_warning']
    danger = cost_cfg['total_cost_danger']
    
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        # 堆叠柱状图
        fig = go.Figure()
        
        colors = {
            'drilling_cost': '#3b82f6',
            'blasting_cost': '#ef4444',
            'loading_cost': '#10b981',
            'transport_cost': '#8b5cf6'
        }
        labels = {
            'drilling_cost': '穿孔成本',
            'blasting_cost': '爆破成本',
            'loading_cost': '铲装成本',
            'transport_cost': '运输成本'
        }
        
        for cost_col, color in colors.items():
            fig.add_trace(go.Bar(
                x=df['date'],
                y=df[cost_col],
                name=labels[cost_col],
                marker_color=color
            ))
        
        # 标记异常（使用动态异常标记）
        if show_anomaly:
            anomaly_df = df[df['is_anomaly_dyn'] == True]
            for _, row in anomaly_df.iterrows():
                fig.add_vline(
                    x=row['date'],
                    line_dash="dash",
                    line_color="#dc2626",
                    line_width=2,
                    opacity=0.6
                )
        
        # 预警线
        fig.add_hline(
            y=warn,
            line_dash="dash",
            line_color="#f59e0b",
            line_width=1.5,
            annotation_text=f"预警线 ({warn}元/吨)",
            annotation_position="top right"
        )
        
        # 危险线
        fig.add_hline(
            y=danger,
            line_dash="dot",
            line_color="#dc2626",
            line_width=1.5,
            annotation_text=f"危险线 ({danger}元/吨)",
            annotation_position="bottom right"
        )
        
        fig.update_layout(
            barmode='stack',
            title='各月成本构成堆叠图',
            xaxis_title='月份',
            yaxis_title='单位成本（元/吨）',
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
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 饼图 - 平均成本构成
        avg_costs = {
            '穿孔': df['drilling_cost'].mean(),
            '爆破': df['blasting_cost'].mean(),
            '铲装': df['loading_cost'].mean(),
            '运输': df['transport_cost'].mean()
        }
        
        fig_pie = px.pie(
            values=list(avg_costs.values()),
            names=list(avg_costs.keys()),
            title='平均成本构成占比',
            color_discrete_sequence=['#3b82f6', '#ef4444', '#10b981', '#8b5cf6'],
            hole=0.4
        )
        fig_pie.update_traces(
            textposition='inside',
            textinfo='percent+label'
        )
        fig_pie.update_layout(height=450)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # 各成本项趋势对比
    st.markdown("#### 📈 各成本项趋势对比")
    fig_line = go.Figure()
    
    for cost_col, color in colors.items():
        fig_line.add_trace(go.Scatter(
            x=df['date'],
            y=df[cost_col],
            mode='lines+markers',
            name=labels[cost_col],
            line=dict(color=color, width=2),
            marker=dict(size=5)
        ))
    
    fig_line.add_trace(go.Scatter(
        x=df['date'],
        y=df['total_cost'],
        mode='lines',
        name='总成本',
        line=dict(color='#111827', width=3, dash='dash')
    ))
    
    fig_line.update_layout(
        title='各成本项及总成本趋势',
        xaxis_title='月份',
        yaxis_title='单位成本（元/吨）',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        template='plotly_white',
        height=380
    )
    st.plotly_chart(fig_line, use_container_width=True)


def _render_yoy_mom_analysis(full_df, current_df, cost_cfg):
    """渲染同比环比分析"""
    st.markdown("### 📊 同比环比分析")
    
    fluc_warn = cost_cfg['cost_fluctuation_warning']
    fluc_danger = cost_cfg['cost_fluctuation_danger']
    
    # 计算同比和环比数据
    analysis_df = current_df.copy()
    analysis_df = analysis_df.sort_values('date')
    
    # 环比
    analysis_df['mom_total'] = analysis_df['total_cost'].pct_change() * 100
    analysis_df['mom_drilling'] = analysis_df['drilling_cost'].pct_change() * 100
    analysis_df['mom_blasting'] = analysis_df['blasting_cost'].pct_change() * 100
    analysis_df['mom_loading'] = analysis_df['loading_cost'].pct_change() * 100
    analysis_df['mom_transport'] = analysis_df['transport_cost'].pct_change() * 100
    
    # 同比
    for i, row in analysis_df.iterrows():
        last_year = full_df[
            (full_df['year'] == row['year'] - 1) & 
            (full_df['month'] == row['month'])
        ]
        if len(last_year) > 0:
            ly = last_year.iloc[0]
            analysis_df.loc[i, 'yoy_total'] = (row['total_cost'] - ly['total_cost']) / ly['total_cost'] * 100
            analysis_df.loc[i, 'yoy_drilling'] = (row['drilling_cost'] - ly['drilling_cost']) / ly['drilling_cost'] * 100
            analysis_df.loc[i, 'yoy_blasting'] = (row['blasting_cost'] - ly['blasting_cost']) / ly['blasting_cost'] * 100
            analysis_df.loc[i, 'yoy_loading'] = (row['loading_cost'] - ly['loading_cost']) / ly['loading_cost'] * 100
            analysis_df.loc[i, 'yoy_transport'] = (row['transport_cost'] - ly['transport_cost']) / ly['transport_cost'] * 100
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔄 环比变化（%）")
        fig_mom = go.Figure()
        
        mom_cols = {
            'mom_total': ('总成本', '#111827'),
            'mom_drilling': ('穿孔', '#3b82f6'),
            'mom_blasting': ('爆破', '#ef4444'),
            'mom_loading': ('铲装', '#10b981'),
            'mom_transport': ('运输', '#8b5cf6')
        }
        
        for col, (label, color) in mom_cols.items():
            fig_mom.add_trace(go.Bar(
                x=analysis_df['date'],
                y=analysis_df[col],
                name=label,
                marker_color=color,
                opacity=0.7 if label != '总成本' else 1
            ))
        
        fig_mom.add_hline(y=0, line_color="gray", line_dash="dash")
        # 波动预警线（正负）
        fig_mom.add_hline(y=fluc_warn, line_dash="dash", line_color="#f59e0b", line_width=1, annotation_text=f"+{fluc_warn}%")
        fig_mom.add_hline(y=-fluc_warn, line_dash="dash", line_color="#f59e0b", line_width=1, annotation_text=f"-{fluc_warn}%")
        fig_mom.add_hline(y=fluc_danger, line_dash="dot", line_color="#dc2626", line_width=1, annotation_text=f"+{fluc_danger}%")
        fig_mom.add_hline(y=-fluc_danger, line_dash="dot", line_color="#dc2626", line_width=1, annotation_text=f"-{fluc_danger}%")
        
        fig_mom.update_layout(
            title='各成本项环比变化率',
            xaxis_title='月份',
            yaxis_title='环比变化率（%）',
            barmode='group',
            template='plotly_white',
            height=380
        )
        st.plotly_chart(fig_mom, use_container_width=True)
    
    with col2:
        st.markdown("#### 📅 同比变化（%）")
        fig_yoy = go.Figure()
        
        yoy_cols = {
            'yoy_total': ('总成本', '#111827'),
            'yoy_drilling': ('穿孔', '#3b82f6'),
            'yoy_blasting': ('爆破', '#ef4444'),
            'yoy_loading': ('铲装', '#10b981'),
            'yoy_transport': ('运输', '#8b5cf6')
        }
        
        for col, (label, color) in yoy_cols.items():
            if col in analysis_df.columns:
                fig_yoy.add_trace(go.Bar(
                    x=analysis_df['date'],
                    y=analysis_df[col],
                    name=label,
                    marker_color=color,
                    opacity=0.7 if label != '总成本' else 1
                ))
        
        fig_yoy.add_hline(y=0, line_color="gray", line_dash="dash")
        # 波动预警线
        fig_yoy.add_hline(y=fluc_warn, line_dash="dash", line_color="#f59e0b", line_width=1)
        fig_yoy.add_hline(y=-fluc_warn, line_dash="dash", line_color="#f59e0b", line_width=1)
        
        fig_yoy.update_layout(
            title='各成本项同比变化率',
            xaxis_title='月份',
            yaxis_title='同比变化率（%）',
            barmode='group',
            template='plotly_white',
            height=380
        )
        st.plotly_chart(fig_yoy, use_container_width=True)
    
    # 详细同比环比数据
    with st.expander("📋 查看同比环比详细数据"):
        display_cols = ['date', 'total_cost', 'mom_total', 'yoy_total',
                       'drilling_cost', 'mom_drilling', 'yoy_drilling',
                       'blasting_cost', 'mom_blasting', 'yoy_blasting',
                       'loading_cost', 'mom_loading', 'yoy_loading',
                       'transport_cost', 'mom_transport', 'yoy_transport']
        display_df = analysis_df.copy()
        for col in display_cols:
            if 'mom_' in col or 'yoy_' in col:
                display_df[col] = display_df[col].round(2).astype(str) + '%'
            elif 'cost' in col:
                display_df[col] = display_df[col].round(2)
        
        display_df.columns = [
            '月份', '总成本', '总成本环比', '总成本同比',
            '穿孔成本', '穿孔环比', '穿孔同比',
            '爆破成本', '爆破环比', '爆破同比',
            '铲装成本', '铲装环比', '铲装同比',
            '运输成本', '运输环比', '运输同比'
        ]
        st.dataframe(display_df, use_container_width=True, hide_index=True)


def _render_cost_trend(full_df, current_df, cost_cfg):
    """渲染成本趋势分析"""
    st.markdown("### 📈 成本趋势分析")
    
    warn = cost_cfg['total_cost_warning']
    danger = cost_cfg['total_cost_danger']
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 总成本趋势 + 移动平均
        df = current_df.copy().sort_values('date')
        
        window = min(3, len(df))
        df['ma_total'] = df['total_cost'].rolling(window=window).mean()
        
        fig = go.Figure()
        
        # 各区域柱（显示异常，使用动态异常标记）
        colors = ['#dc2626' if a else '#2563eb' for a in df['is_anomaly_dyn']]
        
        fig.add_trace(go.Bar(
            x=df['date'],
            y=df['total_cost'],
            name='单位成本',
            marker_color=colors,
            opacity=0.7
        ))
        
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['ma_total'],
            mode='lines',
            name=f'{window}月移动平均',
            line=dict(color='#f59e0b', width=2.5, dash='dash')
        ))
        
        # 预警线
        fig.add_hline(
            y=warn,
            line_dash="dash",
            line_color="#f59e0b",
            line_width=1.5,
            annotation_text=f"预警线 ({warn}元/吨)",
            annotation_position="top right"
        )
        
        # 危险线
        fig.add_hline(
            y=danger,
            line_dash="dot",
            line_color="#dc2626",
            line_width=1.5,
            annotation_text=f"危险线 ({danger}元/吨)",
            annotation_position="bottom right"
        )
        
        fig.update_layout(
            title='单位成本趋势（红色为异常月份）',
            xaxis_title='月份',
            yaxis_title='单位成本（元/吨）',
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1
            ),
            template='plotly_white',
            height=420
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 📊 成本分布统计")
        
        # 箱线图
        cost_data = []
        cost_labels = ['穿孔', '爆破', '铲装', '运输']
        cost_cols = ['drilling_cost', 'blasting_cost', 'loading_cost', 'transport_cost']
        
        for label, col in zip(cost_labels, cost_cols):
            cost_data.extend([(label, v) for v in current_df[col].values])
        
        box_df = pd.DataFrame(cost_data, columns=['成本项', '金额(元/吨)'])
        
        fig_box = px.box(
            box_df,
            x='成本项',
            y='金额(元/吨)',
            title='各成本项分布',
            color='成本项',
            color_discrete_sequence=['#3b82f6', '#ef4444', '#10b981', '#8b5cf6'],
            template='plotly_white'
        )
        fig_box.update_layout(height=420, showlegend=False)
        st.plotly_chart(fig_box, use_container_width=True)
    
    # 成本热力图（按月对比）
    st.markdown("#### 🗓️ 月度成本热力图")
    pivot_df = current_df.pivot_table(
        index='year',
        columns='month',
        values='total_cost',
        aggfunc='mean'
    )
    
    fig_heatmap = go.Figure(data=go.Heatmap(
        z=pivot_df.values,
        x=pivot_df.columns.astype(str) + '月',
        y=pivot_df.index.astype(str) + '年',
        colorscale='RdYlGn_r',
        text=pivot_df.round(2).values,
        texttemplate="%{text}",
        textfont={"size": 11},
        hoverongaps=False
    ))
    fig_heatmap.update_layout(
        title='各年月单位成本热力图（元/吨）',
        xaxis_title='月份',
        yaxis_title='年份',
        height=300
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)


def _render_cost_warnings(full_df, current_df, cost_cfg):
    """渲染成本异常预警和优化建议"""
    st.markdown("### ⚠️ 成本异常预警与优化建议")
    
    anomaly_df = current_df[current_df['is_anomaly_dyn'] == True].copy()
    
    if anomaly_df.empty:
        st.success("🎉 当前筛选条件下没有成本异常记录！")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🚨 异常记录详情")
        
        anomaly_type_map = {
            'total': '单位成本超标',
            'fluctuation': '成本波动过大'
        }
        
        for _, row in anomaly_df.head(10).iterrows():
            anomaly_type = anomaly_type_map.get(row['anomaly_type_dyn'], '未知')
            
            with st.container(border=True):
                st.markdown(f"**📅 {row['date']}** - {anomaly_type}")
                st.markdown(f"- 当月总成本: {row['total_cost']:.2f} 元/吨")
                
                if 'mom_pct' in row and pd.notna(row['mom_pct']):
                    st.markdown(f"- 环比变化: {row['mom_pct']:+.2f}%")
                
                if row['anomaly_type_dyn'] == 'total':
                    st.markdown(f"- 💡 **优化建议**: 关注成本构成，重点控制{_get_max_cost_item(row)}项支出")
                else:
                    st.markdown(f"- 💡 **优化建议**: 分析波动原因，加强成本预算管控")
    
    with col2:
        st.markdown("#### 📊 异常类型分布")
        
        type_counts = anomaly_df['anomaly_type_dyn'].map(anomaly_type_map).value_counts().reset_index()
        type_counts.columns = ['异常类型', '次数']
        
        fig = px.pie(
            type_counts,
            names='异常类型',
            values='次数',
            title='各成本异常类型分布',
            color_discrete_sequence=['#ef4444', '#f59e0b', '#8b5cf6', '#3b82f6'],
            hole=0.4
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
        
        # 通用优化建议
        st.markdown("#### 💡 成本优化建议汇总")
        opt_min = cost_cfg.get('optimal_powder_min', 0.45)
        opt_max = cost_cfg.get('optimal_powder_max', 0.55)
        suggestions = [
            "穿孔成本: 优化钻孔参数，减少废孔率；定期检查钻头磨损情况",
            f"爆破成本: 采用最佳炸药单耗区间（{opt_min}-{opt_max}kg/t），优化爆破设计",
            "铲装成本: 合理调度电铲设备，减少等待时间；加强设备维护",
            "运输成本: 优化运输路线，减少空驶距离；合理配置矿车数量"
        ]
        for s in suggestions:
            st.markdown(f"- {s}")


def _get_max_cost_item(row):
    """获取单条记录中最高的成本项"""
    cost_items = [
        ('穿孔', row['drilling_cost']),
        ('爆破', row['blasting_cost']),
        ('铲装', row['loading_cost']),
        ('运输', row['transport_cost'])
    ]
    max_item = max(cost_items, key=lambda x: x[1])
    return max_item[0]
