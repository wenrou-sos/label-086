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
from utils.config import (
    load_config,
    save_config,
    reset_config,
    DEFAULT_CONFIG
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


def render_overview(config):
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
        blast_df = load_blasting_effect()
        cost_df = load_mining_cost().tail(6)
        
        blast_cfg = config['blasting']
        eq_cfg = config['equipment']
        ld_cfg = config['loss_dilution']
        cost_cfg = config['cost']
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if len(prod_df) > 0:
                total = prod_df['total_volume'].sum()
                avg_monthly = total / 6
                target = config['production']['target_total_volume'] * 30
                status = 'ok' if avg_monthly >= target * 0.9 else 'warning'
                status_color = '#059669' if status == 'ok' else '#f59e0b'
                st.metric(
                    label="近6月采剥总量",
                    value=f"{total/10000:.1f}万吨",
                    delta=f"月均 {total/6/10000:.1f}万"
                )
                st.caption(f"<span style='color:{status_color}'>月目标: {target/10000:.1f}万吨</span>", unsafe_allow_html=True)
        
        with col2:
            if len(shovel_df) > 0:
                avg_eff = shovel_df['loading_efficiency'].mean()
                warn = eq_cfg['shovel_efficiency_warning']
                danger = eq_cfg['shovel_efficiency_danger']
                status = 'ok' if avg_eff <= warn else ('warning' if avg_eff <= danger else 'danger')
                status_color = '#059669' if status == 'ok' else ('#f59e0b' if status == 'warning' else '#dc2626')
                status_text = '✅ 正常' if status == 'ok' else ('⚠️ 预警' if status == 'warning' else '🚨 异常')
                st.metric(
                    label="电铲平均装车效率",
                    value=f"{avg_eff:.1f} 秒/车",
                    delta=status_text,
                    delta_color='normal'
                )
                st.caption(f"<span style='color:{status_color}'>预警线: {warn} 秒/车</span>", unsafe_allow_html=True)
        
        with col3:
            if len(loss_df) > 0:
                avg_loss = loss_df['loss_rate'].mean()
                avg_dil = loss_df['dilution_rate'].mean()
                loss_warn = ld_cfg['loss_rate_warning']
                dil_warn = ld_cfg['dilution_rate_warning']
                loss_ok = avg_loss <= loss_warn
                dil_ok = avg_dil <= dil_warn
                status = 'ok' if (loss_ok and dil_ok) else 'warning'
                status_color = '#059669' if status == 'ok' else '#f59e0b'
                status_text = '✅ 正常' if status == 'ok' else '⚠️ 预警'
                st.metric(
                    label="平均损失率/贫化率",
                    value=f"{avg_loss:.1f}% / {avg_dil:.1f}%",
                    delta=status_text,
                    delta_color='normal'
                )
                st.caption(f"<span style='color:{status_color}'>参考线: {loss_warn}% / {dil_warn}%</span>", unsafe_allow_html=True)
        
        with col4:
            if len(blast_df) > 0:
                opt_min = blast_cfg['optimal_powder_min']
                opt_max = blast_cfg['optimal_powder_max']
                is_optimal = (blast_df['powder_factor'] >= opt_min) & (blast_df['powder_factor'] <= opt_max)
                optimal_rate = is_optimal.sum() / len(blast_df) * 100
                target_rate = 60
                status = 'ok' if optimal_rate >= target_rate else 'warning'
                status_color = '#059669' if status == 'ok' else '#f59e0b'
                status_text = '✅ 达标' if status == 'ok' else '⚠️ 偏低'
                st.metric(
                    label="爆破最佳区间占比",
                    value=f"{optimal_rate:.1f}%",
                    delta=status_text,
                    delta_color='normal'
                )
                st.caption(f"<span style='color:{status_color}'>最佳区间: {opt_min}-{opt_max} kg/t</span>", unsafe_allow_html=True)
        
        with col5:
            if len(cost_df) > 0:
                avg_cost = cost_df['total_cost'].mean()
                latest_cost = cost_df.iloc[-1]['total_cost']
                warn = cost_cfg['total_cost_warning']
                danger = cost_cfg['total_cost_danger']
                status = 'ok' if latest_cost <= warn else ('warning' if latest_cost <= danger else 'danger')
                status_color = '#059669' if status == 'ok' else ('#f59e0b' if status == 'warning' else '#dc2626')
                status_text = '✅ 正常' if status == 'ok' else ('⚠️ 预警' if status == 'warning' else '🚨 异常')
                st.metric(
                    label="近6月平均单位成本",
                    value=f"{avg_cost:.2f} 元/吨",
                    delta=status_text,
                    delta_color='normal'
                )
                st.caption(f"<span style='color:{status_color}'>预警线: {warn} 元/吨</span>", unsafe_allow_html=True)
        
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


def render_alert_settings():
    """渲染预警设置面板"""
    st.markdown("### ⚙️ 预警设置")
    st.markdown("自定义各指标的预警阈值，修改后保存生效")
    
    config = load_config()
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 产量", "🚜 设备", "⚠️ 损失贫化", "💥 爆破", "💰 成本"
    ])
    
    with tab1:
        st.markdown("**产量指标阈值**")
        prod_cfg = config['production'].copy()
        prod_cfg['completion_rate_warning'] = st.slider(
            "计划完成率预警线 (%)", 50, 120,
            int(prod_cfg['completion_rate_warning']), 1,
            key="prod_warn"
        )
        prod_cfg['completion_rate_danger'] = st.slider(
            "计划完成率危险线 (%)", 30, 100,
            int(prod_cfg['completion_rate_danger']), 1,
            key="prod_danger"
        )
        prod_cfg['target_total_volume'] = st.number_input(
            "目标日采剥总量 (吨/日)", 5000, 50000,
            int(prod_cfg['target_total_volume']), 500,
            key="prod_target"
        )
        config['production'] = prod_cfg
    
    with tab2:
        st.markdown("**设备效率阈值**")
        eq_cfg = config['equipment'].copy()
        eq_cfg['shovel_efficiency_warning'] = st.slider(
            "电铲效率预警线 (秒/车，越小越好)", 40, 120,
            int(eq_cfg['shovel_efficiency_warning']), 1,
            key="shovel_warn"
        )
        eq_cfg['shovel_efficiency_danger'] = st.slider(
            "电铲效率危险线 (秒/车)", 50, 150,
            int(eq_cfg['shovel_efficiency_danger']), 1,
            key="shovel_danger"
        )
        eq_cfg['truck_efficiency_warning'] = st.slider(
            "矿车效率预警线 (趟/班，越大越好)", 3, 20,
            int(eq_cfg['truck_efficiency_warning']), 1,
            key="truck_warn"
        )
        eq_cfg['truck_efficiency_danger'] = st.slider(
            "矿车效率危险线 (趟/班)", 1, 15,
            int(eq_cfg['truck_efficiency_danger']), 1,
            key="truck_danger"
        )
        eq_cfg['bottom_n_count'] = st.slider(
            "低效设备展示数量 (台)", 3, 10,
            int(eq_cfg['bottom_n_count']), 1,
            key="bottom_n"
        )
        config['equipment'] = eq_cfg
    
    with tab3:
        st.markdown("**损失贫化阈值**")
        ld_cfg = config['loss_dilution'].copy()
        ld_cfg['loss_rate_warning'] = st.slider(
            "损失率预警线 (%)", 1.0, 15.0,
            float(ld_cfg['loss_rate_warning']), 0.5,
            key="loss_warn"
        )
        ld_cfg['loss_rate_danger'] = st.slider(
            "损失率危险线 (%)", 2.0, 20.0,
            float(ld_cfg['loss_rate_danger']), 0.5,
            key="loss_danger"
        )
        ld_cfg['dilution_rate_warning'] = st.slider(
            "贫化率预警线 (%)", 2.0, 20.0,
            float(ld_cfg['dilution_rate_warning']), 0.5,
            key="dil_warn"
        )
        ld_cfg['dilution_rate_danger'] = st.slider(
            "贫化率危险线 (%)", 3.0, 25.0,
            float(ld_cfg['dilution_rate_danger']), 0.5,
            key="dil_danger"
        )
        ld_cfg['grade_deviation_warning'] = st.slider(
            "品位偏差预警线 (±%)", 0.5, 10.0,
            float(ld_cfg['grade_deviation_warning']), 0.5,
            key="grade_warn"
        )
        ld_cfg['grade_deviation_danger'] = st.slider(
            "品位偏差危险线 (±%)", 1.0, 15.0,
            float(ld_cfg['grade_deviation_danger']), 0.5,
            key="grade_danger"
        )
        config['loss_dilution'] = ld_cfg
    
    with tab4:
        st.markdown("**爆破效果阈值**")
        bl_cfg = config['blasting'].copy()
        col_a, col_b = st.columns(2)
        with col_a:
            bl_cfg['optimal_powder_min'] = st.number_input(
                "最佳单耗下限 (kg/t)", 0.20, 0.60,
                float(bl_cfg['optimal_powder_min']), 0.05,
                key="blast_min"
            )
        with col_b:
            bl_cfg['optimal_powder_max'] = st.number_input(
                "最佳单耗上限 (kg/t)", 0.40, 0.80,
                float(bl_cfg['optimal_powder_max']), 0.05,
                key="blast_max"
            )
        bl_cfg['quality_target'] = st.slider(
            "块度合格率目标 (%)", 70, 99,
            int(bl_cfg['quality_target']), 1,
            key="blast_target"
        )
        bl_cfg['quality_warning'] = st.slider(
            "块度合格率预警线 (%)", 50, 95,
            int(bl_cfg['quality_warning']), 1,
            key="blast_warn"
        )
        bl_cfg['quality_danger'] = st.slider(
            "块度合格率危险线 (%)", 40, 85,
            int(bl_cfg['quality_danger']), 1,
            key="blast_danger"
        )
        config['blasting'] = bl_cfg
    
    with tab5:
        st.markdown("**成本指标阈值**")
        cost_cfg = config['cost'].copy()
        cost_cfg['total_cost_warning'] = st.slider(
            "单位成本预警线 (元/吨)", 6.0, 15.0,
            float(cost_cfg['total_cost_warning']), 0.5,
            key="cost_warn"
        )
        cost_cfg['total_cost_danger'] = st.slider(
            "单位成本危险线 (元/吨)", 7.0, 20.0,
            float(cost_cfg['total_cost_danger']), 0.5,
            key="cost_danger"
        )
        cost_cfg['cost_fluctuation_warning'] = st.slider(
            "成本波动预警线 (±%)", 1.0, 20.0,
            float(cost_cfg['cost_fluctuation_warning']), 0.5,
            key="cost_fluc_warn"
        )
        cost_cfg['cost_fluctuation_danger'] = st.slider(
            "成本波动危险线 (±%)", 2.0, 30.0,
            float(cost_cfg['cost_fluctuation_danger']), 0.5,
            key="cost_fluc_danger"
        )
        config['cost'] = cost_cfg
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 保存配置", use_container_width=True, type="primary"):
            if save_config(config):
                st.success("配置保存成功！页面将自动刷新")
                from utils import config as cfg_mod
                cfg_mod.load_config.clear()
                st.rerun()
    with col2:
        if st.button("🔄 恢复默认", use_container_width=True):
            if reset_config():
                from utils import config as cfg_mod
                cfg_mod.load_config.clear()
                st.success("已恢复默认配置")
                st.rerun()
    
    st.caption("💡 配置保存在 alert_config.json 文件中")


def main():
    """主函数"""
    load_css()
    
    # 数据检查
    check_and_generate_data()
    
    # 加载配置
    alert_config = load_config()
    
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
        
        with st.expander("⚙️ 预警设置", expanded=False):
            render_alert_settings()
        
        st.markdown("---")
        st.markdown("### ℹ️ 使用说明")
        st.markdown("""
        1. 从左侧菜单选择功能模块
        2. 使用页面顶部的筛选器调整分析范围
        3. 点击图表可进行交互操作
        4. 展开折叠面板查看详细数据
        5. 打开「预警设置」可自定义阈值
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
        render_overview(alert_config)
    elif page == "🏭 产量分析":
        render_production_analysis(alert_config)
    elif page == "🚜 设备效率":
        render_equipment_efficiency(alert_config)
    elif page == "⚠️ 损失贫化":
        render_loss_dilution(alert_config)
    elif page == "💥 爆破效果":
        render_blasting_effect(alert_config)
    elif page == "💰 成本分析":
        render_cost_analysis(alert_config)
    
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
