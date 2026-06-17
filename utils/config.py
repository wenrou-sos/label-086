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
    """加载预警配置，如不存在则使用默认配置，加载后自动验证纠正"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            merged = _merge_config(DEFAULT_CONFIG, config)
            fixed, _ = auto_fix_config(merged)
            return fixed
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()


def save_config(config, auto_fix=True):
    """
    保存配置到本地JSON文件
    
    参数:
        config: 要保存的配置字典
        auto_fix: 是否自动纠正不合法配置
    
    返回: (success, fixes, errors)
        success: bool, 是否保存成功
        fixes: list, 自动纠正的说明
        errors: list, 验证错误
    """
    try:
        if auto_fix:
            config, fixes = auto_fix_config(config)
        else:
            fixes = []
        
        is_valid, errors, _ = validate_config(config)
        if not is_valid:
            return False, fixes, errors
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True, fixes, []
    except Exception as e:
        return False, [], [f"配置保存失败: {e}"]


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


def validate_config(config):
    """
    验证配置是否合法
    
    返回: (is_valid, errors, warnings)
        is_valid: bool, 是否完全合法
        errors: list, 错误信息（必须修复）
        warnings: list, 警告信息（建议修复）
    """
    errors = []
    warnings = []
    
    blast = config.get('blasting', {})
    opt_min = blast.get('optimal_powder_min', 0.45)
    opt_max = blast.get('optimal_powder_max', 0.55)
    
    if opt_min >= opt_max:
        errors.append(f"爆破最佳单耗区间不合法：下限({opt_min}) >= 上限({opt_max})")
    
    ld = config.get('loss_dilution', {})
    loss_warn = ld.get('loss_rate_warning', 5.0)
    loss_danger = ld.get('loss_rate_danger', 7.0)
    if loss_warn >= loss_danger:
        errors.append(f"损失率阈值不合法：预警({loss_warn}) >= 危险({loss_danger})")
    
    dil_warn = ld.get('dilution_rate_warning', 8.0)
    dil_danger = ld.get('dilution_rate_danger', 10.0)
    if dil_warn >= dil_danger:
        errors.append(f"贫化率阈值不合法：预警({dil_warn}) >= 危险({dil_danger})")
    
    grade_warn = ld.get('grade_deviation_warning', 2.0)
    grade_danger = ld.get('grade_deviation_danger', 4.0)
    if grade_warn >= grade_danger:
        errors.append(f"品位偏差阈值不合法：预警({grade_warn}) >= 危险({grade_danger})")
    
    prod = config.get('production', {})
    comp_warn = prod.get('completion_rate_warning', 90)
    comp_danger = prod.get('completion_rate_danger', 80)
    if comp_warn <= comp_danger:
        errors.append(f"完成率阈值不合法：预警({comp_warn}) <= 危险({comp_danger})")
    
    equip = config.get('equipment', {})
    shovel_warn = equip.get('shovel_efficiency_warning', 80)
    shovel_danger = equip.get('shovel_efficiency_danger', 90)
    if shovel_warn >= shovel_danger:
        errors.append(f"电铲效率阈值不合法：预警({shovel_warn}) >= 危险({shovel_danger})")
    
    truck_warn = equip.get('truck_efficiency_warning', 8)
    truck_danger = equip.get('truck_efficiency_danger', 6)
    if truck_warn <= truck_danger:
        errors.append(f"矿车效率阈值不合法：预警({truck_warn}) <= 危险({truck_danger})")
    
    cost = config.get('cost', {})
    tc_warn = cost.get('total_cost_warning', 9.5)
    tc_danger = cost.get('total_cost_danger', 10.5)
    if tc_warn >= tc_danger:
        errors.append(f"单位成本阈值不合法：预警({tc_warn}) >= 危险({tc_danger})")
    
    fluc_warn = cost.get('cost_fluctuation_warning', 5.0)
    fluc_danger = cost.get('cost_fluctuation_danger', 10.0)
    if fluc_warn >= fluc_danger:
        errors.append(f"成本波动阈值不合法：预警({fluc_warn}) >= 危险({fluc_danger})")
    
    blast_qual_warn = blast.get('quality_warning', 80.0)
    blast_qual_danger = blast.get('quality_danger', 70.0)
    if blast_qual_warn <= blast_qual_danger:
        errors.append(f"块度合格率阈值不合法：预警({blast_qual_warn}) <= 危险({blast_qual_danger})")
    
    is_valid = len(errors) == 0
    return is_valid, errors, warnings


def auto_fix_config(config):
    """
    自动纠正配置中的不合法值
    
    返回: (fixed_config, fixes)
        fixed_config: 纠正后的配置
        fixes: list, 纠正说明
    """
    fixed = _merge_config(DEFAULT_CONFIG, config)
    fixes = []
    
    blast = fixed['blasting']
    if blast['optimal_powder_min'] >= blast['optimal_powder_max']:
        old_min, old_max = blast['optimal_powder_min'], blast['optimal_powder_max']
        blast['optimal_powder_min'] = min(old_min, old_max)
        blast['optimal_powder_max'] = max(old_min, old_max)
        fixes.append(f"爆破最佳单耗区间已自动修正：{old_min}-{old_max} → {blast['optimal_powder_min']}-{blast['optimal_powder_max']}")
    
    ld = fixed['loss_dilution']
    if ld['loss_rate_warning'] >= ld['loss_rate_danger']:
        old_w, old_d = ld['loss_rate_warning'], ld['loss_rate_danger']
        ld['loss_rate_warning'] = min(old_w, old_d)
        ld['loss_rate_danger'] = max(old_w, old_d)
        fixes.append(f"损失率阈值已自动修正：预警{old_w} → {ld['loss_rate_warning']}, 危险{old_d} → {ld['loss_rate_danger']}")
    
    if ld['dilution_rate_warning'] >= ld['dilution_rate_danger']:
        old_w, old_d = ld['dilution_rate_warning'], ld['dilution_rate_danger']
        ld['dilution_rate_warning'] = min(old_w, old_d)
        ld['dilution_rate_danger'] = max(old_w, old_d)
        fixes.append(f"贫化率阈值已自动修正：预警{old_w} → {ld['dilution_rate_warning']}, 危险{old_d} → {ld['dilution_rate_danger']}")
    
    if ld['grade_deviation_warning'] >= ld['grade_deviation_danger']:
        old_w, old_d = ld['grade_deviation_warning'], ld['grade_deviation_danger']
        ld['grade_deviation_warning'] = min(old_w, old_d)
        ld['grade_deviation_danger'] = max(old_w, old_d)
        fixes.append(f"品位偏差阈值已自动修正：预警{old_w} → {ld['grade_deviation_warning']}, 危险{old_d} → {ld['grade_deviation_danger']}")
    
    prod = fixed['production']
    if prod['completion_rate_warning'] <= prod['completion_rate_danger']:
        old_w, old_d = prod['completion_rate_warning'], prod['completion_rate_danger']
        prod['completion_rate_warning'] = max(old_w, old_d)
        prod['completion_rate_danger'] = min(old_w, old_d)
        fixes.append(f"完成率阈值已自动修正：预警{old_w} → {prod['completion_rate_warning']}, 危险{old_d} → {prod['completion_rate_danger']}")
    
    equip = fixed['equipment']
    if equip['shovel_efficiency_warning'] >= equip['shovel_efficiency_danger']:
        old_w, old_d = equip['shovel_efficiency_warning'], equip['shovel_efficiency_danger']
        equip['shovel_efficiency_warning'] = min(old_w, old_d)
        equip['shovel_efficiency_danger'] = max(old_w, old_d)
        fixes.append(f"电铲效率阈值已自动修正：预警{old_w} → {equip['shovel_efficiency_warning']}, 危险{old_d} → {equip['shovel_efficiency_danger']}")
    
    if equip['truck_efficiency_warning'] <= equip['truck_efficiency_danger']:
        old_w, old_d = equip['truck_efficiency_warning'], equip['truck_efficiency_danger']
        equip['truck_efficiency_warning'] = max(old_w, old_d)
        equip['truck_efficiency_danger'] = min(old_w, old_d)
        fixes.append(f"矿车效率阈值已自动修正：预警{old_w} → {equip['truck_efficiency_warning']}, 危险{old_d} → {equip['truck_efficiency_danger']}")
    
    cost = fixed['cost']
    if cost['total_cost_warning'] >= cost['total_cost_danger']:
        old_w, old_d = cost['total_cost_warning'], cost['total_cost_danger']
        cost['total_cost_warning'] = min(old_w, old_d)
        cost['total_cost_danger'] = max(old_w, old_d)
        fixes.append(f"单位成本阈值已自动修正：预警{old_w} → {cost['total_cost_warning']}, 危险{old_d} → {cost['total_cost_danger']}")
    
    if cost['cost_fluctuation_warning'] >= cost['cost_fluctuation_danger']:
        old_w, old_d = cost['cost_fluctuation_warning'], cost['cost_fluctuation_danger']
        cost['cost_fluctuation_warning'] = min(old_w, old_d)
        cost['cost_fluctuation_danger'] = max(old_w, old_d)
        fixes.append(f"成本波动阈值已自动修正：预警{old_w} → {cost['cost_fluctuation_warning']}, 危险{old_d} → {cost['cost_fluctuation_danger']}")
    
    if blast['quality_warning'] <= blast['quality_danger']:
        old_w, old_d = blast['quality_warning'], blast['quality_danger']
        blast['quality_warning'] = max(old_w, old_d)
        blast['quality_danger'] = min(old_w, old_d)
        fixes.append(f"块度合格率阈值已自动修正：预警{old_w} → {blast['quality_warning']}, 危险{old_d} → {blast['quality_danger']}")
    
    return fixed, fixes


def safe_get_optimal_range(blast_cfg):
    """
    安全获取爆破最佳单耗区间，确保下限 < 上限
    
    返回: (opt_min, opt_max)
    """
    opt_min = blast_cfg.get('optimal_powder_min', 0.45)
    opt_max = blast_cfg.get('optimal_powder_max', 0.55)
    if opt_min >= opt_max:
        opt_min, opt_max = min(opt_min, opt_max), max(opt_min, opt_max)
    return opt_min, opt_max
