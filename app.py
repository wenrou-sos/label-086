"""
露天矿关键生产指标分析看板
主应用入口文件

功能模块：
1. 产量分析
2. 设备效率
3. 损失贫化
4. 爆破效果
5. 成本分析
"""

import os
import sys
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.data_loader import (
    check_data_files,
    load_monthly_production,
    load_shovel_efficiency,
    load_truck_efficiency,
    load_loss_dilution,
    load_blasting_effect,
    load_mining_cost
)
from modules.production import render_production_analysis
from modules.equipment import render_equipment_efficiency
from modules.loss_dilution import render_loss_dilution
from modules.blasting import render_blasting_effect
from modules.cost import render_cost_analysis


st.set_page_config(
    page_title="露天矿关键生产指标分析看板",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded"
)


def load_css():
    """加载自定义CSS样式"""
    st.markdown("""
    <style>
    .main {
        padding-top: 1rem;
    }
    .stMetric {
        background-color: #f8fafc;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e2e8f0;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.875rem;
        color: #64748b;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.75rem;
        font-weight: 600;
        color: #0f172a;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 100rem;
    }
    h1, h2, h3 {
        color: #0f172a;
    }
    </style>
    """, unsafe_allow_html=True)


def check_and_generate_data():
    """检查数据文件，如不存在则生成"""
    missing = check_data_files()
    if missing:
        with st.spinner(f"检测到缺失 {len(missing)} 个数据文件，正在生成模拟数据..."):
            try:
                os.system(f"{sys.executable} generate_data.py")
                st.success("模拟数据生成完成！")
            except Exception as e:
                st.error(f"数据生成失败: {e}")
                st.info("请手动运行: python generate_data.py")


def render_overview():
    """渲染首页概览"""
    st.markdown("# ⛏️ 露天矿关键生产指标分析看板")
    st.markdown("---")
    
    st.markdown("### 📊 系统概览")
    st.markdown("""
    本看板系统集成了露天矿生产的五大核心指标分析模块，通过直观的数据可视化，
    帮助管理人员快速掌握生产动态，发现问题并优化决策。
    """)
    
    st.markdown("---")
    
    # 加载核心数据用于展示概览KPI
    try:
        prod_df = load_monthly_production().tail(6)
        shovel_df = load_shovel_efficiency()
        truck_df = load_truck_efficiency()
        loss_df = load_loss_dilution()
        blast_df = load_blasting_efficiency()
        cost_df = load_mining_cost().tail(6)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if len(prod_df) > 0:
                total = prod_df['total_volume'].sum()
                st.metric(
                    label="近6月采剥总量",
                    value=f"{total/10000:.1f}万吨",
                    delta=f"月均 {total/6/10000:.1f}万"
                )
        
        with col2:
            if len(shovel_df) > 0:
                avg_eff = shovel_df['loading_efficiency'].mean()
                st.metric(
                    label="电铲平均装车效率",
                    value=f"{avg_eff:.1f} 秒/车",
                    delta="越低越好"
                )
        
        with col3:
            if len(loss_df) > 0:
                avg_loss = loss_df['loss_rate'].mean()
                avg_dil = loss_df['dilution_rate'].mean()
                st.metric(
                    label="平均损失率/贫化率",
                    value=f"{avg_loss:.1f}% / {avg_dil:.1f}%",
                    delta="参考: 5%/8%"
                )
        
        with col4:
            if len(blast_df) > 0:
                optimal_rate = blast_df['is_optimal'].sum() / len(blast_df) * 100
                st.metric(
                    label="爆破最佳区间占比",
                    value=f"{optimal_rate:.1f}%",
                    delta="目标: >60%"
                )
        
        with col5:
            if len(cost_df) > 0:
                avg_cost = cost_df['total_cost'].mean()
                st.metric(
                    label="近6月平均单位成本",
                    value=f"{avg_cost:.2f} 元/吨",
                    delta=f"最新 {cost_df.iloc[-1]['total_cost']:.2f}"
                )
        
    except Exception as e:
        st.warning(f"概览数据加载异常: {e}")
    
    st.markdown("---")
    
    # 模块介绍卡片
    st.markdown("### 📚 功能模块介绍")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.container(border=True)
        st.markdown("#### 🏭 产量分析")
        st.markdown("""
        - 日/月/年多维度产量趋势
        - 实际产量与计划对比
        - 计划完成率可视化
        - 支持数据下钻分析
        """)
        
        st.container(border=True)
        st.markdown("#### 🚜 设备效率")
        st.markdown("""
        - 电铲装车效率监控
        - 矿车运输效率统计
        - 低效设备自动识别
        - 检修建议智能推荐
        """)
    
    with col2:
        st.container(border=True)
        st.markdown("#### ⚠️ 损失贫化")
        st.markdown("""
        - 损失率与贫化率趋势
        - 实际品位与预测对比
        - 异常数据自动标记
        - 原因分析与建议
        """)
        
        st.container(border=True)
        st.markdown("#### 💥 爆破效果")
        st.markdown("""
        - 炸药单耗与块度关系
        - 最佳参数区间识别
        - 相关性分析
        - 趋势预测功能
        """)
    
    with col3:
        st.container(border=True)
        st.markdown("#### 💰 成本分析")
        st.markdown("""
        - 四项成本构成拆解
        - 同比环比对比分析
        - 成本异常预警
        - 优化建议方案
        """)


def main():
    """主函数"""
    load_css()
    
    # 数据检查
    check_and_generate_data()
    
    # 侧边栏导航
    with st.sidebar:
        st.markdown("# ⛏️ 导航菜单")
        st.markdown("---")
        
        page = st.radio(
            "选择分析模块",
            [
                "🏠 系统概览",
                "🏭 产量分析",
                "🚜 设备效率",
                "⚠️ 损失贫化",
                "💥 爆破效果",
                "💰 成本分析"
            ],
            index=0
        )
        
        st.markdown("---")
        st.markdown("### ℹ️ 使用说明")
        st.markdown("""
        1. 从左侧菜单选择功能模块
        2. 使用页面顶部的筛选器调整分析范围
        3. 点击图表可进行交互操作
        4. 展开折叠面板查看详细数据
        """)
        
        st.markdown("---")
        st.markdown("### 📅 数据说明")
        st.markdown("""
        - 数据周期: 2024-2025年
        - 数据类型: 模拟生产数据
        - 更新频率: 可配置
        """)
    
    # 页面路由
    if page == "🏠 系统概览":
        render_overview()
    elif page == "🏭 产量分析":
        render_production_analysis()
    elif page == "🚜 设备效率":
        render_equipment_efficiency()
    elif page == "⚠️ 损失贫化":
        render_loss_dilution()
    elif page == "💥 爆破效果":
        render_blasting_effect()
    elif page == "💰 成本分析":
        render_cost_analysis()
    
    # 页脚
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #94a3b8; padding: 1rem;'>"
        "露天矿关键生产指标分析看板 | 基于 Streamlit + Plotly 构建"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
