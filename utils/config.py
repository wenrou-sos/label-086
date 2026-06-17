"""
预警配置管理模块
支持各指标阈值的自定义配置和本地持久化
"""

import json
import os
import streamlit as st

CONFIG_FILE = 'alert_config.json'

DEFAULT_CONFIG = {
    "production": {
        "completion_rate_warning": 90,
        "completion_rate_danger": 80,
        "target_ore_volume": 8000,
        "target_total_volume": 23000
    },
    "equipment": {
        "shovel_efficiency_warning": 80,
        "shovel_efficiency_danger": 90,
        "truck_efficiency_warning": 8,
        "truck_efficiency_danger": 6,
        "bottom_n_count": 5
    },
    "loss_dilution": {
        "loss_rate_warning": 5.0,
        "loss_rate_danger": 7.0,
        "dilution_rate_warning": 8.0,
        "dilution_rate_danger": 10.0,
        "grade_deviation_warning": 2.0,
        "grade_deviation_danger": 4.0
    },
    "blasting": {
        "optimal_powder_min": 0.45,
        "optimal_powder_max": 0.55,
        "quality_target": 85.0,
        "quality_warning": 80.0,
        "quality_danger": 70.0
    },
    "cost": {
        "total_cost_warning": 9.5,
        "total_cost_danger": 10.5,
        "cost_fluctuation_warning": 5.0,
        "cost_fluctuation_danger": 10.0
    }
}


@st.cache_data(ttl=60)
def load_config():
    """加载预警配置，如不存在则使用默认配置"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return _merge_config(DEFAULT_CONFIG, config)
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()


def save_config(config):
    """保存配置到本地JSON文件"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"配置保存失败: {e}")
        return False


def reset_config():
    """重置为默认配置"""
    if os.path.exists(CONFIG_FILE):
        try:
            os.remove(CONFIG_FILE)
            return True
        except Exception:
            return False
    return True


def _merge_config(default, user):
    """合并用户配置到默认配置，确保所有键都存在"""
    result = default.copy()
    for section in result:
        if section in user and isinstance(user[section], dict):
            for key in result[section]:
                if key in user[section]:
                    result[section][key] = user[section][key]
    return result


def get_config_section(section_name):
    """获取指定模块的配置"""
    config = load_config()
    return config.get(section_name, {})


def is_value_ok(value, warning_threshold, danger_threshold, higher_is_better=True):
    """
    判断值的状态
    
    参数:
        value: 当前值
        warning_threshold: 警告阈值
        danger_threshold: 危险阈值
        higher_is_better: 是否值越高越好
    
    返回: 'ok', 'warning', 'danger'
    """
    if higher_is_better:
        if value >= warning_threshold:
            return 'ok'
        elif value >= danger_threshold:
            return 'warning'
        else:
            return 'danger'
    else:
        if value <= warning_threshold:
            return 'ok'
        elif value <= danger_threshold:
            return 'warning'
        else:
            return 'danger'


def get_status_color(status):
    """获取状态对应的颜色"""
    colors = {
        'ok': '#059669',
        'warning': '#f59e0b',
        'danger': '#dc2626'
    }
    return colors.get(status, '#6b7280')


def get_status_label(status):
    """获取状态对应的文字标签"""
    labels = {
        'ok': '✅ 正常',
        'warning': '⚠️ 预警',
        'danger': '🚨 异常'
    }
    return labels.get(status, '❓ 未知')
