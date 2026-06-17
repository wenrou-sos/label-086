"""
损失贫化模块
可视化展示矿石损失率和贫化率变化趋势、品位对比、异常数据标记等
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from utils.data_loader import load_loss_dilution


def render_loss_dilution():
    """渲染损失贫化分析模块"""
    st.markdown("## ⚠️ 损失贫化分析")
    
    df = load_loss_dilution()
    if df.empty:
        st.warning("损失贫化数据加载失败，请检查数据文件")
        return
    
    # 筛选控件
    col1, col2, col3 = st.columns(3)
    with col1:
        zones = ['全部区域'] + sorted(df['zone'].unique().tolist())
        selected_zone = st.selectbox("选择采矿区域", zones)
    with col2:
        date_min = df['date'].min().date()
        date_max = df['date'].max().date()
        default_start = date_max - pd.Timedelta(days=180)
        date_range = st.date_input(
            "选择时间范围",
            value=(default_start, date_max),
            min_value=date_min,
            max_value=date_max
        )
    with col3:
        show_anomaly_only = st.checkbox("仅显示异常数据", value=False)
    
    st.markdown("---")
    
    # 过滤数据
    start_date, end_date = date_range
    filtered_df = df[
        (df['date'] >= pd.to_datetime(start_date)) &
        (df['date'] <= pd.to_datetime(end_date))
    ].copy()
    
    if selected_zone != '全部区域':
        filtered_df = filtered_df[filtered_df['zone'] == selected_zone]
    
    if show_anomaly_only:
        filtered_df = filtered_df[filtered_df['is_anomaly'] == True]
    
    # 总体KPI
    _render_kpi_cards(filtered_df)
    
    st.markdown("---")
    
    # 损失率与贫化率趋势
    _render_trend_charts(filtered_df, selected_zone)
    
    st.markdown("---")
    
    # 品位对比
    _render_grade_comparison(filtered_df, selected_zone)
    
    st.markdown("---")
    
    # 异常数据分析
    _render_anomaly_analysis(df, filtered_df)
    
    # 详细数据表
    with st.expander("📋 查看完整数据明细"):
        display_df = filtered_df.copy()
        display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
        display_df = display_df.sort_values('date', ascending=False)
        display_cols = {
            'date': '日期',
            'zone': '采矿区域',
            'loss_rate': '损失率(%)',
            'dilution_rate': '贫化率(%)',
            'actual_grade': '实际品位(%)',
            'predicted_grade': '预测品位(%)',
            'is_anomaly': '是否异常',
            'anomaly_reason': '异常原因',
            'ore_mined': '采矿量(吨)'
        }
        display_df = display_df[list(display_cols.keys())]
        display_df.columns = list(display_cols.values())
        display_df['损失率(%)'] = display_df['损失率(%)'].round(2)
        display_df['贫化率(%)'] = display_df['贫化率(%)'].round(2)
        display_df['实际品位(%)'] = display_df['实际品位(%)'].round(2)
        display_df['预测品位(%)'] = display_df['预测品位(%)'].round(2)
        display_df['采矿量(吨)'] = display_df['采矿量(吨)'].round(0).astype(int)
        st.dataframe(display_df, use_container_width=True, hide_index=True, height=500)


def _render_kpi_cards(df):
    """渲染KPI指标卡片"""
    avg_loss = df['loss_rate'].mean()
    avg_dilution = df['dilution_rate'].mean()
    avg_grade_diff = (df['actual_grade'] - df['predicted_grade']).mean()
    anomaly_count = df['is_anomaly'].sum()
    anomaly_rate = anomaly_count / len(df) * 100 if len(df) > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="平均损失率",
            value=f"{avg_loss:.2f}%",
            delta="行业参考: <5%"
        )
    with col2:
        st.metric(
            label="平均贫化率",
            value=f"{avg_dilution:.2f}%",
            delta="行业参考: <8%"
        )
    with col3:
        delta_color = "normal" if avg_grade_diff < 0 else "inverse"
        st.metric(
            label="平均品位偏差",
            value=f"{avg_grade_diff:+.2f}%",
            delta="实际vs预测",
            delta_color=delta_color
        )
    with col4:
        st.metric(
            label="异常数据占比",
            value=f"{anomaly_rate:.1f}%",
            delta=f"共{anomaly_count}次异常"
        )


def _render_trend_charts(df, selected_zone):
    """渲染损失率与贫化率趋势图"""
    st.markdown("### 📈 损失率与贫化率变化趋势")
    
    # 按区域分组展示
    if selected_zone == '全部区域':
        zones = sorted(df['zone'].unique())
    else:
        zones = [selected_zone]
    
    # 创建多图表
    tab1, tab2 = st.tabs(["趋势折线图", "区域对比箱线图"])
    
    with tab1:
        fig = go.Figure()
        
        colors = ['#2563eb', '#dc2626', '#059669', '#7c3aed']
        
        for i, zone in enumerate(zones):
            zone_df = df[df['zone'] == zone].sort_values('date')
            color = colors[i % len(colors)]
            
            # 损失率
            fig.add_trace(go.Scatter(
                x=zone_df['date'],
                y=zone_df['loss_rate'],
                mode='lines+markers',
                name=f'{zone} - 损失率',
                line=dict(color=color, width=2),
                marker=dict(size=5),
                legendgroup=zone
            ))
            
            # 贫化率（虚线）
            fig.add_trace(go.Scatter(
                x=zone_df['date'],
                y=zone_df['dilution_rate'],
                mode='lines',
                name=f'{zone} - 贫化率',
                line=dict(color=color, width=2, dash='dash'),
                marker=dict(size=4),
                legendgroup=zone,
                opacity=0.7
            ))
            
            # 标记异常点
            anomaly_df = zone_df[zone_df['is_anomaly'] == True]
            if not anomaly_df.empty:
                fig.add_trace(go.Scatter(
                    x=anomaly_df['date'],
                    y=anomaly_df['loss_rate'],
                    mode='markers',
                    name=f'{zone} - 异常点',
                    marker=dict(
                        color='red',
                        size=12,
                        symbol='star',
                        line=dict(width=2, color='DarkSlateGrey')
                    ),
                    showlegend=(i == 0)
                ))
        
        # 添加参考线
        fig.add_hline(
            y=5,
            line_dash="dot",
            line_color="gray",
            annotation_text="损失率警戒线 (5%)",
            annotation_position="top right"
        )
        fig.add_hline(
            y=8,
            line_dash="dot",
            line_color="gray",
            annotation_text="贫化率警戒线 (8%)",
            annotation_position="bottom right"
        )
        
        fig.update_layout(
            title='损失率与贫化率趋势（虚线为贫化率，实线为损失率）',
            xaxis_title='日期',
            yaxis_title='比率（%）',
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
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # 箱线图对比
        melted = df.melt(
            id_vars=['zone'],
            value_vars=['loss_rate', 'dilution_rate'],
            var_name='指标类型',
            value_name='数值'
        )
        melted['指标类型'] = melted['指标类型'].map({
            'loss_rate': '损失率(%)',
            'dilution_rate': '贫化率(%)'
        })
        
        fig_box = px.box(
            melted,
            x='zone',
            y='数值',
            color='指标类型',
            title='各区域损失率与贫化率分布对比',
            template='plotly_white',
            color_discrete_map={
                '损失率(%)': '#2563eb',
                '贫化率(%)': '#dc2626'
            }
        )
        fig_box.update_layout(
            xaxis_title='采矿区域',
            yaxis_title='比率（%）',
            height=400
        )
        st.plotly_chart(fig_box, use_container_width=True)


def _render_grade_comparison(df, selected_zone):
    """渲染实际品位与预测品位对比"""
    st.markdown("### 🔬 品位对比分析")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 散点图：实际vs预测
        fig_scatter = go.Figure()
        
        if selected_zone == '全部区域':
            zones = sorted(df['zone'].unique())
        else:
            zones = [selected_zone]
        
        colors = ['#2563eb', '#dc2626', '#059669', '#7c3aed']
        
        for i, zone in enumerate(zones):
            zone_df = df[df['zone'] == zone]
            color = colors[i % len(colors)]
            
            # 正常数据
            normal = zone_df[zone_df['is_anomaly'] == False]
            fig_scatter.add_trace(go.Scatter(
                x=normal['predicted_grade'],
                y=normal['actual_grade'],
                mode='markers',
                name=f'{zone} - 正常',
                marker=dict(color=color, size=8, opacity=0.7),
                legendgroup=zone
            ))
            
            # 异常数据
            anomaly = zone_df[zone_df['is_anomaly'] == True]
            if not anomaly.empty:
                fig_scatter.add_trace(go.Scatter(
                    x=anomaly['predicted_grade'],
                    y=anomaly['actual_grade'],
                    mode='markers',
                    name=f'{zone} - 异常',
                    marker=dict(
                        color=color,
                        size=12,
                        symbol='x',
                        line=dict(width=2, color='red')
                    ),
                    legendgroup=zone,
                    showlegend=(i == 0)
                ))
        
        # 添加对角线（理想线）
        min_val = min(df['predicted_grade'].min(), df['actual_grade'].min()) - 2
        max_val = max(df['predicted_grade'].max(), df['actual_grade'].max()) + 2
        fig_scatter.add_trace(go.Scatter(
            x=[min_val, max_val],
            y=[min_val, max_val],
            mode='lines',
            name='理想线(实际=预测)',
            line=dict(color='gray', width=2, dash='dash')
        ))
        
        fig_scatter.update_layout(
            title='实际品位 vs 地质预测品位',
            xaxis_title='地质预测品位 (%)',
            yaxis_title='实际品位 (%)',
            hovermode='closest',
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
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    with col2:
        # 统计信息
        st.markdown("#### 📊 品位偏差统计")
        df['grade_deviation'] = df['actual_grade'] - df['predicted_grade']
        
        stats = {
            '平均偏差': f"{df['grade_deviation'].mean():+.2f}%",
            '最大正偏差': f"{df['grade_deviation'].max():+.2f}%",
            '最大负偏差': f"{df['grade_deviation'].min():+.2f}%",
            '标准偏差': f"{df['grade_deviation'].std():.2f}%",
            '偏差在±2%内占比': f"{(abs(df['grade_deviation']) <= 2).sum() / len(df) * 100:.1f}%"
        }
        
        for key, value in stats.items():
            st.metric(label=key, value=value)


def _render_anomaly_analysis(full_df, filtered_df):
    """渲染异常数据分析"""
    st.markdown("### 🚨 异常数据分析")
    
    anomaly_df = filtered_df[filtered_df['is_anomaly'] == True].copy()
    
    if anomaly_df.empty:
        st.info("当前筛选条件下没有异常数据")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 异常原因分布
        reason_counts = anomaly_df['anomaly_reason'].value_counts().reset_index()
        reason_counts.columns = ['异常原因', '次数']
        
        fig_reason = px.pie(
            reason_counts,
            names='异常原因',
            values='次数',
            title='异常原因分布',
            color_discrete_sequence=px.colors.qualitative.Set2,
            hole=0.4
        )
        fig_reason.update_layout(height=350)
        st.plotly_chart(fig_reason, use_container_width=True)
    
    with col2:
        # 各区域异常次数
        zone_anomaly = anomaly_df.groupby('zone').size().reset_index(name='异常次数')
        zone_total = filtered_df.groupby('zone').size().reset_index(name='总次数')
        zone_stats = pd.merge(zone_anomaly, zone_total, on='zone')
        zone_stats['异常率(%)'] = (zone_stats['异常次数'] / zone_stats['总次数'] * 100).round(1)
        zone_stats = zone_stats.sort_values('异常率(%)', ascending=False)
        
        fig_zone = go.Figure()
        fig_zone.add_trace(go.Bar(
            x=zone_stats['zone'],
            y=zone_stats['异常率(%)'],
            marker_color='#dc2626',
            text=zone_stats['异常率(%)'].astype(str) + '%',
            textposition='outside'
        ))
        fig_zone.update_layout(
            title='各区域异常率对比',
            xaxis_title='采矿区域',
            yaxis_title='异常率（%）',
            template='plotly_white',
            height=350
        )
        st.plotly_chart(fig_zone, use_container_width=True)
    
    # 异常记录详情
    with st.expander("🔍 查看异常记录详情"):
        anomaly_display = anomaly_df.copy()
        anomaly_display['date'] = anomaly_display['date'].dt.strftime('%Y-%m-%d')
        anomaly_display = anomaly_display.sort_values('date', ascending=False)
        
        display_cols = ['date', 'zone', 'loss_rate', 'dilution_rate', 
                       'actual_grade', 'predicted_grade', 'anomaly_reason', 'ore_mined']
        anomaly_display = anomaly_display[display_cols]
        anomaly_display.columns = ['日期', '区域', '损失率(%)', '贫化率(%)', 
                                   '实际品位(%)', '预测品位(%)', '异常原因', '采矿量(吨)']
        anomaly_display['损失率(%)'] = anomaly_display['损失率(%)'].round(2)
        anomaly_display['贫化率(%)'] = anomaly_display['贫化率(%)'].round(2)
        anomaly_display['实际品位(%)'] = anomaly_display['实际品位(%)'].round(2)
        anomaly_display['预测品位(%)'] = anomaly_display['预测品位(%)'].round(2)
        anomaly_display['采矿量(吨)'] = anomaly_display['采矿量(吨)'].round(0).astype(int)
        
        st.dataframe(anomaly_display, use_container_width=True, hide_index=True)
