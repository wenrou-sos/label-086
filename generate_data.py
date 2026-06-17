"""
露天矿生产指标模拟数据生成脚本
生成所有分析模块所需的CSV数据文件
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def create_data_directory():
    """创建数据目录"""
    if not os.path.exists('data'):
        os.makedirs('data')


def generate_production_data():
    """生成产量数据（日、月、年维度）"""
    dates = pd.date_range(start='2024-01-01', end='2025-12-31', freq='D')
    
    np.random.seed(42)
    n = len(dates)
    
    # 基础产量，带季节性波动
    base_ore = 8000 + 2000 * np.sin(np.arange(n) * 2 * np.pi / 365)
    base_rock = 15000 + 3000 * np.sin(np.arange(n) * 2 * np.pi / 365 + 0.5)
    
    daily_data = pd.DataFrame({
        'date': dates,
        'ore_volume': np.maximum(5000, base_ore + np.random.normal(0, 800, n)),
        'rock_volume': np.maximum(10000, base_rock + np.random.normal(0, 1500, n)),
        'planned_ore': base_ore,
        'planned_rock': base_rock
    })
    
    daily_data['total_volume'] = daily_data['ore_volume'] + daily_data['rock_volume']
    daily_data['planned_total'] = daily_data['planned_ore'] + daily_data['planned_rock']
    daily_data['completion_rate'] = daily_data['total_volume'] / daily_data['planned_total'] * 100
    
    # 保存日数据
    daily_data.to_csv('data/daily_production.csv', index=False, encoding='utf-8-sig')
    
    # 生成月数据
    daily_data['year_month'] = daily_data['date'].dt.to_period('M')
    monthly_data = daily_data.groupby('year_month').agg({
        'ore_volume': 'sum',
        'rock_volume': 'sum',
        'total_volume': 'sum',
        'planned_ore': 'sum',
        'planned_rock': 'sum',
        'planned_total': 'sum'
    }).reset_index()
    monthly_data['completion_rate'] = monthly_data['total_volume'] / monthly_data['planned_total'] * 100
    monthly_data['year_month'] = monthly_data['year_month'].astype(str)
    monthly_data.to_csv('data/monthly_production.csv', index=False, encoding='utf-8-sig')
    
    # 生成年数据
    daily_data['year'] = daily_data['date'].dt.year
    yearly_data = daily_data.groupby('year').agg({
        'ore_volume': 'sum',
        'rock_volume': 'sum',
        'total_volume': 'sum',
        'planned_ore': 'sum',
        'planned_rock': 'sum',
        'planned_total': 'sum'
    }).reset_index()
    yearly_data['completion_rate'] = yearly_data['total_volume'] / yearly_data['planned_total'] * 100
    yearly_data.to_csv('data/yearly_production.csv', index=False, encoding='utf-8-sig')
    
    print("产量数据生成完成")


def generate_equipment_data():
    """生成设备效率数据"""
    np.random.seed(123)
    
    # 电铲数据
    shovel_ids = [f'电铲-{i:02d}' for i in range(1, 16)]
    shovel_dates = pd.date_range(start='2025-01-01', end='2025-12-31', freq='D')
    
    shovel_records = []
    for shovel in shovel_ids:
        base_efficiency = np.random.uniform(45, 90)  # 秒/车
        for date in shovel_dates:
            efficiency = base_efficiency + np.random.normal(0, 8)
            cars_loaded = int(np.random.uniform(30, 80))
            shovel_records.append({
                'date': date,
                'equipment_id': shovel,
                'equipment_type': '电铲',
                'loading_efficiency': max(25, efficiency),
                'cars_loaded': cars_loaded,
                'operating_hours': np.random.uniform(6, 12)
            })
    
    shovel_df = pd.DataFrame(shovel_records)
    shovel_df.to_csv('data/shovel_efficiency.csv', index=False, encoding='utf-8-sig')
    
    # 矿车数据
    truck_ids = [f'矿车-{i:03d}' for i in range(1, 31)]
    shifts = ['早班', '中班', '晚班']
    
    truck_records = []
    for truck in truck_ids:
        base_efficiency = np.random.uniform(6, 14)  # 趟/班
        for date in shovel_dates:
            for shift in shifts:
                efficiency = base_efficiency + np.random.normal(0, 1.5)
                truck_records.append({
                    'date': date,
                    'shift': shift,
                    'equipment_id': truck,
                    'equipment_type': '矿车',
                    'trips_per_shift': max(2, efficiency),
                    'tons_transported': np.random.uniform(50, 150) * max(2, efficiency),
                    'operating_hours': np.random.uniform(4, 8)
                })
    
    truck_df = pd.DataFrame(truck_records)
    truck_df.to_csv('data/truck_efficiency.csv', index=False, encoding='utf-8-sig')
    
    print("设备效率数据生成完成")


def generate_loss_dilution_data():
    """生成损失贫化数据"""
    np.random.seed(456)
    
    dates = pd.date_range(start='2024-01-01', end='2025-12-31', freq='W')
    n = len(dates)
    
    # 采矿区域
    zones = ['A区', 'B区', 'C区', 'D区']
    
    records = []
    for zone in zones:
        base_loss = np.random.uniform(3, 6)
        base_dilution = np.random.uniform(4, 8)
        base_grade = np.random.uniform(28, 35)
        
        for i, date in enumerate(dates):
            loss_rate = base_loss + np.random.normal(0, 0.8) + 0.5 * np.sin(i * np.pi / 26)
            dilution_rate = base_dilution + np.random.normal(0, 1) + 0.3 * np.cos(i * np.pi / 26)
            actual_grade = base_grade + np.random.normal(0, 1.5)
            predicted_grade = base_grade + np.random.normal(0, 0.8)
            
            is_anomaly = np.random.random() < 0.08
            anomaly_reason = ''
            if is_anomaly:
                reasons = ['地质条件变化', '爆破质量不佳', '设备故障', '操作失误', '测量误差']
                anomaly_reason = np.random.choice(reasons)
                loss_rate *= 1.5
                dilution_rate *= 1.4
            
            records.append({
                'date': date,
                'zone': zone,
                'loss_rate': max(0.5, loss_rate),
                'dilution_rate': max(0.5, dilution_rate),
                'actual_grade': actual_grade,
                'predicted_grade': predicted_grade,
                'is_anomaly': is_anomaly,
                'anomaly_reason': anomaly_reason,
                'ore_mined': np.random.uniform(50000, 150000)
            })
    
    df = pd.DataFrame(records)
    df.to_csv('data/loss_dilution.csv', index=False, encoding='utf-8-sig')
    
    print("损失贫化数据生成完成")


def generate_blasting_data():
    """生成爆破效果数据"""
    np.random.seed(789)
    
    records = []
    
    # 爆破参数：炸药单耗与块度合格率
    # 最佳炸药单耗区间约为 0.45-0.55 kg/t
    n = 500
    
    for i in range(n):
        date = pd.to_datetime('2024-01-01') + timedelta(days=np.random.randint(0, 730))
        
        # 炸药单耗
        powder_factor = np.random.uniform(0.25, 0.80)
        
        # 块度合格率：呈倒U形分布，在0.5左右最高
        optimal_pf = 0.50
        base_quality = 92 - 120 * (powder_factor - optimal_pf) ** 2
        fragmentation_quality = base_quality + np.random.normal(0, 3)
        fragmentation_quality = min(98, max(60, fragmentation_quality))
        
        # 其他参数
        blast_area = np.random.choice(['A区', 'B区', 'C区', 'D区'])
        hole_count = int(np.random.uniform(30, 100))
        total_explosive = powder_factor * np.random.uniform(5000, 20000)
        
        # 识别最佳区间
        is_optimal = 0.45 <= powder_factor <= 0.55 and fragmentation_quality >= 85
        
        records.append({
            'date': date,
            'blast_id': f'BLAST-{i+1:04d}',
            'blast_area': blast_area,
            'powder_factor': round(powder_factor, 3),
            'fragmentation_quality': round(fragmentation_quality, 1),
            'hole_count': hole_count,
            'total_explosive': round(total_explosive, 1),
            'is_optimal': is_optimal
        })
    
    df = pd.DataFrame(records)
    df = df.sort_values('date').reset_index(drop=True)
    df.to_csv('data/blasting_effect.csv', index=False, encoding='utf-8-sig')
    
    print("爆破效果数据生成完成")


def generate_cost_data():
    """生成成本数据"""
    np.random.seed(101)
    
    dates = pd.date_range(start='2024-01-01', end='2025-12-31', freq='ME')
    n = len(dates)
    
    records = []
    
    for i, date in enumerate(dates):
        # 各项成本构成（元/吨）
        base_drilling = 1.8
        base_blasting = 2.2
        base_loading = 1.5
        base_transport = 3.5
        
        # 季节性波动和趋势
        seasonal = 0.1 * np.sin(i * np.pi / 6)
        trend = i * 0.005
        
        drilling_cost = base_drilling + seasonal + np.random.normal(0, 0.1) + trend
        blasting_cost = base_blasting + seasonal * 0.8 + np.random.normal(0, 0.12) + trend * 1.2
        loading_cost = base_loading + seasonal * 0.5 + np.random.normal(0, 0.08) + trend * 0.8
        transport_cost = base_transport + seasonal * 1.2 + np.random.normal(0, 0.15) + trend * 1.5
        
        total_cost = drilling_cost + blasting_cost + loading_cost + transport_cost
        
        # 随机异常
        is_anomaly = np.random.random() < 0.1
        anomaly_type = ''
        suggestions = ''
        
        if is_anomaly:
            cost_types = ['drilling', 'blasting', 'loading', 'transport']
            anomaly_type = np.random.choice(cost_types)
            if anomaly_type == 'drilling':
                drilling_cost *= 1.3
                suggestions = '检查钻头磨损情况，优化钻孔参数'
            elif anomaly_type == 'blasting':
                blasting_cost *= 1.35
                suggestions = '优化爆破设计，控制炸药用量'
            elif anomaly_type == 'loading':
                loading_cost *= 1.4
                suggestions = '检查电铲设备状态，合理调度'
            else:
                transport_cost *= 1.25
                suggestions = '优化运输路线，减少空驶距离'
            
            total_cost = drilling_cost + blasting_cost + loading_cost + transport_cost
        
        records.append({
            'date': date.strftime('%Y-%m'),
            'year': date.year,
            'month': date.month,
            'drilling_cost': round(drilling_cost, 2),
            'blasting_cost': round(blasting_cost, 2),
            'loading_cost': round(loading_cost, 2),
            'transport_cost': round(transport_cost, 2),
            'total_cost': round(total_cost, 2),
            'is_anomaly': is_anomaly,
            'anomaly_type': anomaly_type,
            'optimization_suggestion': suggestions
        })
    
    df = pd.DataFrame(records)
    df.to_csv('data/mining_cost.csv', index=False, encoding='utf-8-sig')
    
    print("成本数据生成完成")


def main():
    """主函数：生成所有模拟数据"""
    print("开始生成露天矿生产指标模拟数据...")
    create_data_directory()
    
    generate_production_data()
    generate_equipment_data()
    generate_loss_dilution_data()
    generate_blasting_data()
    generate_cost_data()
    
    print("\n所有数据生成完成！文件保存在 data/ 目录下")
    print("生成的文件列表：")
    for f in os.listdir('data'):
        print(f"  - {f}")


if __name__ == '__main__':
    main()
