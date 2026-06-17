# 露天矿关键生产指标分析看板 - 部署说明文档

## 一、项目概述

本项目是一个基于 Streamlit 和 Plotly 构建的露天矿生产数据可视化分析看板，
包含产量分析、设备效率、损失贫化、爆破效果、成本分析五大核心模块。

## 二、环境要求

### 2.1 软件环境
- Python 版本：3.9 ~ 3.13
- 操作系统：Windows / macOS / Linux

### 2.2 Python 依赖库
```
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.17.0
```

## 三、部署步骤

### 3.1 本地开发环境部署

#### 步骤1：克隆或复制项目文件
将项目文件复制到目标目录，确保目录结构如下：
```
label-086/
├── app.py                    # 主应用入口
├── generate_data.py          # 模拟数据生成脚本
├── requirements.txt          # 依赖库列表
├── DEPLOYMENT.md             # 部署说明文档（本文件）
├── USAGE.md                  # 功能使用说明文档
├── utils/                    # 工具模块
│   ├── __init__.py
│   └── data_loader.py        # 数据加载模块
├── modules/                  # 功能模块
│   ├── __init__.py
│   ├── production.py         # 产量分析模块
│   ├── equipment.py          # 设备效率模块
│   ├── loss_dilution.py      # 损失贫化模块
│   ├── blasting.py           # 爆破效果模块
│   └── cost.py               # 成本分析模块
└── data/                     # 数据目录（自动生成）
    ├── daily_production.csv
    ├── monthly_production.csv
    ├── yearly_production.csv
    ├── shovel_efficiency.csv
    ├── truck_efficiency.csv
    ├── loss_dilution.csv
    ├── blasting_effect.csv
    └── mining_cost.csv
```

#### 步骤2：创建虚拟环境（推荐）
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 步骤3：安装依赖库
```bash
pip install -r requirements.txt
```

#### 步骤4：生成模拟数据
```bash
python generate_data.py
```

> **注意**：如果不手动执行此步骤，首次启动应用时会自动检测并生成数据。

#### 步骤5：启动应用
```bash
streamlit run app.py
```

启动成功后，终端会显示本地访问地址，默认是：
- 本地访问：http://localhost:8501
- 网络访问：http://<本机IP>:8501

### 3.2 生产环境部署

#### 方案一：使用 Streamlit Community Cloud（推荐用于演示）

1. 将代码推送到 GitHub 仓库
2. 访问 https://streamlit.io/cloud 并登录
3. 点击 "New app"，选择对应的 GitHub 仓库、分支和主文件（app.py）
4. 点击 "Deploy" 完成部署

#### 方案二：Docker 容器化部署

创建 `Dockerfile`：
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 生成数据
RUN python generate_data.py

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

构建并运行：
```bash
# 构建镜像
docker build -t open-pit-dashboard .

# 运行容器
docker run -p 8501:8501 open-pit-dashboard
```

#### 方案三：Linux 服务器部署（使用 systemd）

1. 将项目文件复制到服务器，例如 `/opt/open-pit-dashboard/`
2. 创建虚拟环境并安装依赖
3. 创建 systemd 服务文件 `/etc/systemd/system/open-pit-dashboard.service`：

```ini
[Unit]
Description=Open Pit Production Dashboard
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/open-pit-dashboard
Environment=PATH=/opt/open-pit-dashboard/venv/bin
ExecStart=/opt/open-pit-dashboard/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

4. 启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl start open-pit-dashboard
sudo systemctl enable open-pit-dashboard
```

## 四、配置说明

### 4.1 Streamlit 配置文件

可在项目目录创建 `.streamlit/config.toml` 进行高级配置：

```toml
[server]
port = 8501
address = "0.0.0.0"
maxUploadSize = 200

[theme]
base = "light"
primaryColor = "#2563eb"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f8fafc"
textColor = "#0f172a"
font = "sans serif"

[browser]
gatherUsageStats = false
```

### 4.2 数据配置

- 数据文件格式：CSV（UTF-8 with BOM 编码，确保中文正常显示）
- 数据目录：默认 `data/` 目录
- 如需更换数据源，请保持 CSV 文件字段结构不变

## 五、常见问题排查

### Q1：启动时提示缺少数据文件
- **原因**：首次运行未生成模拟数据
- **解决**：执行 `python generate_data.py` 手动生成，或重启应用自动生成

### Q2：页面显示中文乱码
- **原因**：CSV 文件编码问题
- **解决**：确保 CSV 文件使用 UTF-8 with BOM 编码保存

### Q3：图表不显示或显示异常
- **原因**：Plotly 或浏览器兼容性问题
- **解决**：
  1. 升级 Plotly：`pip install --upgrade plotly`
  2. 使用现代浏览器（Chrome、Firefox、Edge）
  3. 清除浏览器缓存

### Q4：应用启动后访问慢
- **原因**：首次加载数据缓存
- **解决**：等待数据加载完成后，后续访问会使用缓存，速度会明显提升

### Q5：端口被占用
- **原因**：8501 端口已被其他程序占用
- **解决**：
  ```bash
  streamlit run app.py --server.port=8502
  ```

## 六、性能优化建议

1. **数据缓存**：项目已使用 `@st.cache_data` 装饰器缓存数据加载，无需额外配置
2. **数据量控制**：生产数据建议按月/年归档，避免单表数据过大
3. **服务器配置**：建议至少 2核4G 配置，并发用户较多时可适当提升
4. **部署区域**：尽量将应用部署在离用户较近的区域

## 七、安全建议

1. 生产环境建议配置 HTTPS
2. 如需外部访问，建议配置反向代理（Nginx）并设置访问认证
3. 定期备份数据目录
4. 敏感生产数据请做好脱敏处理

## 八、技术支持

如遇部署问题，可参考以下资源：
- Streamlit 官方文档：https://docs.streamlit.io/
- Plotly 官方文档：https://plotly.com/python/
- Pandas 官方文档：https://pandas.pydata.org/docs/
