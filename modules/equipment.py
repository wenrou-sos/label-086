"""
设备效率模块
展示电铲装车效率、矿车运输效率，识别低效设备并提供检修建议
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from utils.data_loader import load_shovel_efficiency, load_truck_efficiency


def render_equipment_efficiency():
    """渲染设备效率分析模块"""
    st.markdown("## 🚜 设备效率分析")
    
    shovel_df = load_shovel_efficiency()
    truck_df = load_truck_efficiency()
    
    if shovel_df.empty or truck_df.empty:
        st.warning("设备效率数据加载失败，请检查数据文件")
        return
    
    # 筛选控件
    col1, col2, col3 = st.columns(3)
    with col1:
        date_min = shovel_df['date'].min().date()
        date_max = shovel_df['date'].max().date()
        default_start = date_max - pd.Timedelta(days=30)
        date_range = st.date_input(
            "选择统计周期",
            value=(default_start, date_max),
            min_value=date_min,
            max_value=date_max
        )
    with col2:
        equipment_type = st.selectbox(
            "设备类型",
            ["全部设备", "电铲", "矿车"],
            index=0
        )
    with col3:
        sort_order = st.selectbox(
            "排序方式",
            ["效率从低到高（优先关注）", "效率从高到低"],
            index=0
        )
    
    st.markdown("---")
    
    # 过滤数据
    start_date, end_date = date_range
    shovel_filtered = shovel_df[
        (shovel_df['date'] >= pd.to_datetime(start_date)) &
        (shovel_df['date'] <= pd.to_datetime(end_date))
    ].copy()
    truck_filtered = truck_df[
        (truck_df['date'] >= pd.to_datetime(start_date)) &
        (truck_df['date'] <= pd.to_datetime(end_date))
    ].copy()
    
    # 总体KPI
    _render_overall_kpi(shovel_filtered, truck_filtered)
    
    st.markdown("---")
    
    # 电铲效率分析
    if equipment_type in ["全部设备", "电铲"]:
        _render_shovel_analysis(shovel_filtered, sort_order)
        st.markdown("---")
    
    # 矿车效率分析
    if equipment_type in ["全部设备", "矿车"]:
        _render_truck_analysis(truck_filtered, sort_order)
        st.markdown("---")
    
    # 低效设备检修建议
    _render_maintenance_suggestions(shovel_filtered, truck_filtered)


def _render_overall_kpi(shovel_df, truck_df):
    """渲染总体KPI指标"""
    avg_shovel_efficiency = shovel_df['loading_efficiency'].mean()
    avg_truck_efficiency = truck_df['trips_per_shift'].mean()
    total_cars = shovel_df['cars_loaded'].sum()
    total_tons = truck_df['tons_transported'].sum()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="平均电铲装车效率",
            value=f"{avg_shovel_efficiency:.1f} 秒/车",
            delta="数值越低越好"
        )
    with col2:
        st.metric(
            label="平均矿车运输效率",
            value=f"{avg_truck_efficiency:.1f} 趟/班",
            delta="数值越高越好"
        )
    with col3:
        st.metric(
            label="累计装车数",
            value=f"{total_cars:,.0f} 车"
        )
    with col4:
        st.metric(
            label="累计运输量",
            value=f"{total_tons:,.0f} 吨"
        )


def _render_shovel_analysis(shovel_df, sort_order):
    """渲染电铲效率分析"""
    st.markdown("### ⛏️ 电铲装车效率分析")
    
    # 按设备汇总
    shovel_summary = shovel_df.groupby('equipment_id').agg({
        'loading_efficiency': 'mean',
        'cars_loaded': 'sum',
        'operating_hours': 'sum',
        'date': 'count'
    }).reset_index()
    shovel_summary.columns = ['设备编号', '平均装车效率(秒/车)', '累计装车数', '运行时长(小时)', '工作天数']
    
    # 排序
    ascending = True if "从低到高" in sort_order else False
    shovel_summary = shovel_summary.sort_values('平均装车效率(秒/车)', ascending=ascending)
    
    # 图表 - 柱状图
    fig_colors = ['#dc2626' if x >= shovel_summary['平均装车效率(秒/车)'].quantile(0.75) 
                  else '#f59e0b' if x >= shovel_summary['平均装车效率(秒/车)'].quantile(0.5)
                  else '#2563eb' 
                  for x in shovel_summary['平均装车效率(秒/车)']]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=shovel_summary['设备编号'],
        y=shovel_summary['平均装车效率(秒/车)'],
        marker_color=fig_colors,
        text=shovel_summary['平均装车效率(秒/车)'].round(1),
        textposition='outside'
    ))
    fig.add_hline(
        y=shovel_summary['平均装车效率(秒/车)'].mean(),
        line_dash="dash",
        line_color="#6b7280",
        annotation_text=f"平均值: {shovel_summary['平均装车效率(秒/车)'].mean():.1f}秒/车"
    )
    fig.update_layout(
        title='各电铲平均装车效率（秒/车，越低越好）',
        xaxis_title='电铲编号',
        yaxis_title='装车效率（秒/车）',
        template='plotly_white',
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # 效率趋势 - 选择设备查看
    col1, col2 = st.columns([1, 2])
    with col1:
        selected_shovel = st.selectbox(
            "选择电铲查看效率趋势",
            options=shovel_summary['设备编号'].tolist(),
            key='shovel_trend_select'
        )
    with col2:
        shovel_trend = shovel_df[shovel_df['equipment_id'] == selected_shovel].copy()
        shovel_trend = shovel_trend.sort_values('date')
        
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=shovel_trend['date'],
            y=shovel_trend['loading_efficiency'],
            mode='lines+markers',
            name='装车效率',
            line=dict(color='#2563eb', width=2),
            marker=dict(size=5)
        ))
        fig_trend.add_hline(
            y=shovel_trend['loading_efficiency'].mean(),
            line_dash="dash",
            line_color="#dc2626",
            annotation_text=f"平均: {shovel_trend['loading_efficiency'].mean():.1f}秒"
        )
        fig_trend.update_layout(
            title=f'{selected_shovel} 装车效率趋势',
            xaxis_title='日期',
            yaxis_title='装车效率（秒/车）',
            template='plotly_white',
            height=300
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    
    # 数据表格
    with st.expander("📋 电铲效率明细数据"):
        st.dataframe(
            shovel_summary.round(2),
            use_container_width=True,
            hide_index=True
        )


def _render_truck_analysis(truck_df, sort_order):
    """渲染矿车效率分析"""
    st.markdown("### 🚛 矿车运输效率分析")
    
    # 按设备汇总
    truck_summary = truck_df.groupby('equipment_id').agg({
        'trips_per_shift': 'mean',
        'tons_transported': 'sum',
        'operating_hours': 'sum',
        'date': 'count'
    }).reset_index()
    truck_summary.columns = ['设备编号', '平均运输效率(趟/班)', '累计运输量(吨)', '运行时长(小时)', '班次数']
    
    # 排序：矿车效率越高越好，所以排序逻辑与电铲相反
    ascending = False if "从低到高" in sort_order else True
    truck_summary = truck_summary.sort_values('平均运输效率(趟/班)', ascending=ascending)
    
    # 图表
    fig_colors = ['#dc2626' if x <= truck_summary['平均运输效率(趟/班)'].quantile(0.25)
                  else '#f59e0b' if x <= truck_summary['平均运输效率(趟/班)'].quantile(0.5)
                  else '#059669'
                  for x in truck_summary['平均运输效率(趟/班)']]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=truck_summary['设备编号'],
        y=truck_summary['平均运输效率(趟/班)'],
        marker_color=fig_colors,
        text=truck_summary['平均运输效率(趟/班)'].round(1),
        textposition='outside'
    ))
    fig.add_hline(
        y=truck_summary['平均运输效率(趟/班)'].mean(),
        line_dash="dash",
        line_color="#6b7280",
        annotation_text=f"平均值: {truck_summary['平均运输效率(趟/班)'].mean():.1f}趟/班"
    )
    fig.update_layout(
        title='各矿车平均运输效率（趟/班，越高越好）',
        xaxis_title='矿车编号',
        yaxis_title='运输效率（趟/班）',
        template='plotly_white',
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # 班次对比
    shift_summary = truck_df.groupby('shift')['trips_per_shift'].mean().reset_index()
    fig_shift = go.Figure()
    fig_shift.add_trace(go.Bar(
        x=shift_summary['shift'],
        y=shift_summary['trips_per_shift'],
        marker_color=['#2563eb', '#f59e0b', '#7c3aed'],
        text=shift_summary['trips_per_shift'].round(1),
        textposition='outside'
    ))
    fig_shift.update_layout(
        title='各班次平均运输效率对比',
        xaxis_title='班次',
        yaxis_title='平均运输效率（趟/班）',
        template='plotly_white',
        height=300
    )
    st.plotly_chart(fig_shift, use_container_width=True)
    
    # 数据表格
    with st.expander("📋 矿车效率明细数据"):
        st.dataframe(
            truck_summary.round(2),
            use_container_width=True,
            hide_index=True
        )


def _render_maintenance_suggestions(shovel_df, truck_df):
    """渲染低效设备检修建议"""
    st.markdown("### 🔧 低效设备检修建议")
    
    # 获取低效设备 - 电铲（效率最低的前5台，即秒数最高的）
    shovel_low = shovel_df.groupby('equipment_id').agg({
        'loading_efficiency': 'mean',
        'cars_loaded': 'sum',
        'operating_hours': 'sum'
    }).reset_index()
    shovel_low = shovel_low.sort_values('loading_efficiency', ascending=False).head(5)
    shovel_low['设备类型'] = '电铲'
    shovel_low['效率指标'] = shovel_low['loading_efficiency'].round(1).astype(str) + ' 秒/车'
    
    # 获取低效设备 - 矿车（效率最低的前5台，即趟数最少的）
    truck_low = truck_df.groupby('equipment_id').agg({
        'trips_per_shift': 'mean',
        'tons_transported': 'sum',
        'operating_hours': 'sum'
    }).reset_index()
    truck_low = truck_low.sort_values('trips_per_shift', ascending=True).head(5)
    truck_low['设备类型'] = '矿车'
    truck_low['效率指标'] = truck_low['trips_per_shift'].round(1).astype(str) + ' 趟/班'
    
    # 合并展示
    col_shovel, col_truck = st.columns(2)
    
    with col_shovel:
        st.markdown("#### ⚠️ 电铲装车效率最低 TOP 5")
        shovel_display = shovel_low[['equipment_id', '设备类型', '效率指标', 'cars_loaded', 'operating_hours']].copy()
        shovel_display.columns = ['设备编号', '设备类型', '效率指标', '累计装车数', '运行时长(小时)']
        shovel_display['运行时长(小时)'] = shovel_display['运行时长(小时)'].round(1)
        
        for _, row in shovel_display.iterrows():
            suggestion = _get_shovel_suggestion(row['运行时长(小时)'])
            with st.container(border=True):
                st.markdown(f"**{row['设备编号']}** - {row['效率指标']}")
                st.markdown(f"- 📦 累计装车: {row['累计装车数']:,} 车")
                st.markdown(f"- ⏱️ 运行时长: {row['运行时长(小时)']:.0f} 小时")
                st.markdown(f"- 💡 检修建议: {suggestion}")
    
    with col_truck:
        st.markdown("#### ⚠️ 矿车运输效率最低 TOP 5")
        truck_display = truck_low[['equipment_id', '设备类型', '效率指标', 'tons_transported', 'operating_hours']].copy()
        truck_display.columns = ['设备编号', '设备类型', '效率指标', '累计运输量(吨)', '运行时长(小时)']
        truck_display['运行时长(小时)'] = truck_display['运行时长(小时)'].round(1)
        
        for _, row in truck_display.iterrows():
            suggestion = _get_truck_suggestion(row['运行时长(小时)'])
            with st.container(border=True):
                st.markdown(f"**{row['设备编号']}** - {row['效率指标']}")
                st.markdown(f"- 🚚 累计运输: {row['累计运输量(吨)']:,.0f} 吨")
                st.markdown(f"- ⏱️ 运行时长: {row['运行时长(小时)']:.0f} 小时")
                st.markdown(f"- 💡 检修建议: {suggestion}")


def _get_shovel_suggestion(hours):
    """根据运行时长给出电铲检修建议"""
    if hours > 2000:
        return "设备运行时间较长，建议进行全面检修：检查铲斗磨损、液压系统、钢丝绳状态"
    elif hours > 1500:
        return "建议进行中期维护：检查润滑系统、电气连接、制动装置"
    else:
        return "建议检查装车操作流程，排查是否为驾驶员操作习惯问题，同时检查斗齿磨损情况"


def _get_truck_suggestion(hours):
    """根据运行时长给出矿车检修建议"""
    if hours > 2000:
        return "设备运行时间较长，建议进行全面检修：检查发动机、变速箱、制动系统、轮胎磨损"
    elif hours > 1500:
        return "建议进行中期维护：更换机油、检查液压系统、调整制动间隙"
    else:
        return "建议检查运输路线规划，排查是否存在调度不合理问题，同时检查车辆装载效率"
