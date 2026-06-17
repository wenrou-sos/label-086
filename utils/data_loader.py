"""
数据加载工具模块
提供各模块CSV数据的统一加载接口
"""

import os
import pandas as pd
import streamlit as st


@st.cache_data
def load_daily_production():
    """加载日产量数据"""
    try:
        df = pd.read_csv('data/daily_production.csv')
        df['date'] = pd.to_datetime(df['date'])
        return df
    except FileNotFoundError:
        st.error("日产量数据文件不存在")
        return pd.DataFrame()


@st.cache_data
def load_monthly_production():
    """加载月产量数据"""
    try:
        df = pd.read_csv('data/monthly_production.csv')
        return df
    except FileNotFoundError:
        st.error("月产量数据文件不存在")
        return pd.DataFrame()


@st.cache_data
def load_yearly_production():
    """加载年产量数据"""
    try:
        df = pd.read_csv('data/yearly_production.csv')
        return df
    except FileNotFoundError:
        st.error("年产量数据文件不存在")
        return pd.DataFrame()


@st.cache_data
def load_shovel_efficiency():
    """加载电铲效率数据"""
    try:
        df = pd.read_csv('data/shovel_efficiency.csv')
        df['date'] = pd.to_datetime(df['date'])
        return df
    except FileNotFoundError:
        st.error("电铲效率数据文件不存在")
        return pd.DataFrame()


@st.cache_data
def load_truck_efficiency():
    """加载矿车效率数据"""
    try:
        df = pd.read_csv('data/truck_efficiency.csv')
        df['date'] = pd.to_datetime(df['date'])
        return df
    except FileNotFoundError:
        st.error("矿车效率数据文件不存在")
        return pd.DataFrame()


@st.cache_data
def load_loss_dilution():
    """加载损失贫化数据"""
    try:
        df = pd.read_csv('data/loss_dilution.csv')
        df['date'] = pd.to_datetime(df['date'])
        return df
    except FileNotFoundError:
        st.error("损失贫化数据文件不存在")
        return pd.DataFrame()


@st.cache_data
def load_blasting_effect():
    """加载爆破效果数据"""
    try:
        df = pd.read_csv('data/blasting_effect.csv')
        df['date'] = pd.to_datetime(df['date'])
        return df
    except FileNotFoundError:
        st.error("爆破效果数据文件不存在")
        return pd.DataFrame()


@st.cache_data
def load_mining_cost():
    """加载采矿成本数据"""
    try:
        df = pd.read_csv('data/mining_cost.csv')
        return df
    except FileNotFoundError:
        st.error("采矿成本数据文件不存在")
        return pd.DataFrame()


def check_data_files():
    """检查所有数据文件是否存在"""
    required_files = [
        'data/daily_production.csv',
        'data/monthly_production.csv',
        'data/yearly_production.csv',
        'data/shovel_efficiency.csv',
        'data/truck_efficiency.csv',
        'data/loss_dilution.csv',
        'data/blasting_effect.csv',
        'data/mining_cost.csv'
    ]
    
    missing = [f for f in required_files if not os.path.exists(f)]
    return missing
