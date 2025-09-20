# SingleFile Archiver

一个现代化的自动化URL归档系统，使用Python CLI框架构建。可以批量处理CSV文件中的URL，并使用SingleFile Docker容器进行网页归档，同时提供智能文件监控功能。

## ✨ 功能特性

- 🚀 **现代CLI界面**: 基于Typer框架的丰富命令行界面
- 📦 **批量处理**: 可配置批次大小的URL处理
- 🔄 **自动重试**: 失败的URL自动重试，可配置重试次数
- 📝 **失败记录**: 自动导出失败URL到文件并支持重试
- 🔍 **智能去重**: 自动检查URL是否已存在，避免重复归档
- 🏷️ **网页标题命名**: 基于网页标题和时间戳生成文件名
- 👁️ **实时文件监控**: 监控incoming文件夹，自动归档带时间戳的HTML文件
- 🎯 **特殊模式**: 支持"X 上的"文件特殊处理规则
- 📊 **详细日志**: 完整的处理日志记录
- 🐳 **容器化**: Docker容器运行，支持自动启动
- ⚙️ **配置管理**: JSON配置文件，类型安全的配置验证

## 🏗️ 项目结构

```
singlefile/
├── src/singlefile_archiver/    # 核心代码包
│   ├── cli.py                  # CLI主入口
│   ├── core/                   # 核心功能模块
│   │   ├── archive.py          # URL归档功能
│   │   ├── monitor.py          # 文件监控功能  
│   │   ├── retry.py            # 重试功能
│   │   └── docker.py           # Docker管理
│   ├── services/               # 业务逻辑服务
│   │   ├── csv_processor.py    # CSV文件处理
│   │   ├── file_monitor.py     # 文件系统监控
│   │   └── docker_service.py   # Docker API包装
│   └── utils/                  # 工具模块
│       ├── config.py           # 配置管理
│       ├── logging.py          # 日志设置
│       └── paths.py            # 路径工具
├── scripts/                    # 安装和管理脚本
├── legacy/                     # 旧版本文件归档
├── Git_Hub.csv                 # GitHub URL数据
├── Twitter.csv                 # Twitter URL数据
└── docker-compose.yml          # Docker服务配置
```

## 🚀 快速开始

### 1. 安装系统

```bash
bash scripts/install.sh
```

### 2. 测试安装

```bash
singlefile-archiver info
```

### 3. 启动Docker服务

```bash
./docker_management_cli.sh start
```

## 📖 使用指南

### URL归档

```bash
# 归档GitHub URLs (干运行)
singlefile-archiver archive urls Git_Hub.csv --dry-run

# 实际归档，自定义批次大小
singlefile-archiver archive urls Git_Hub.csv --batch-size 5

# 归档Twitter URLs
singlefile-archiver archive urls Twitter.csv
```

### 文件监控

```bash
# 查看监控状态
singlefile-archiver monitor status

# 扫描现有文件
singlefile-archiver monitor scan

# 扫描并移动匹配的文件
singlefile-archiver monitor scan --move

# 启动实时监控
singlefile-archiver monitor start
```

### 重试失败的URLs

```bash
# 重试失败的URLs
singlefile-archiver retry failed_urls_20250824_*.txt
```

### Docker管理

```bash
# 查看Docker状态
singlefile-archiver docker status

# 使用便捷管理脚本
./docker_management_cli.sh status
./docker_management_cli.sh logs
./docker_management_cli.sh monitor
```

## ⚙️ 配置

系统使用JSON配置文件，位于项目数据目录。主要配置项：

- **archive_batch_size**: 批次处理大小 (默认: 10)
- **max_retries**: 最大重试次数 (默认: 10) 
- **retry_delay**: 重试延迟 (默认: 2秒)
- **monitor_watch_dir**: 监控目录
- **monitor_archive_dir**: 归档目录
- **docker_container**: Docker容器名

## 🎯 文件监控规则

系统会自动处理以下类型的HTML文件：

### 1. 包含"X 上的"的文件
- 任何文件名包含"X 上的"的HTML文件都会被移动
- 无需时间戳格式

### 2. 带时间戳格式的文件
支持多种时间戳格式：
- `(8_20_2025 1:18:55 PM).html`
- `(2025-08-20 13:18:55).html` 
- `(20250820_131855).html`
- `(2025-08-20).html`
- `(8_20_2025).html`

支持中文冒号（：）和英文冒号（:）。

## 🐳 Docker集成

系统包含两个Docker服务：

1. **singlefile-cli**: SingleFile命令行工具容器
2. **singlefile-monitor-cli**: CLI文件监控服务容器

```bash
# 启动所有服务
./docker_management_cli.sh start

# 查看监控日志
./docker_management_cli.sh monitor

# 重启服务
./docker_management_cli.sh restart
```

## 📊 数据统计

当前数据：
- **Git_Hub.csv**: ~617个URL
- **Twitter.csv**: ~3,257个URL  
- **总计**: ~3,874个URL

## 🔄 从旧版本迁移

如果您使用的是旧版本脚本，系统已自动将旧文件移动到 `legacy/` 目录：

- `legacy/scripts/` - 原始Python脚本
- `legacy/docker/` - 原始Docker配置
- `legacy/tests/` - 测试文件
- `legacy/data/` - 历史数据文件
- `legacy/logs/` - 历史日志

旧文件被保留用于参考，但建议使用新的CLI系统。

## 🛠️ 开发

### 项目开发设置

```bash
# 安装开发依赖
pip install -e .

# 运行测试
singlefile-archiver test all

# 开发模式运行
python -m singlefile_archiver.cli --help
```

### 扩展功能

系统支持插件扩展，可在 `src/singlefile_archiver/plugins/` 中添加自定义功能。

## 📝 许可证

项目遵循开源许可证。详见项目代码。

## 🚨 故障排除

### 常见问题

1. **CLI命令找不到**
   ```bash
   # 检查安装
   which singlefile-archiver
   # 重新安装
   bash scripts/install.sh
   ```

2. **Docker容器无法启动**
   ```bash
   # 检查Docker状态
   ./docker_management_cli.sh status
   # 重建容器
   ./docker_management_cli.sh build
   ```

3. **文件监控不工作**
   ```bash
   # 检查监控状态
   singlefile-archiver monitor status
   # 扫描测试
   singlefile-archiver monitor scan
   ```

更多帮助请查看：
```bash
singlefile-archiver --help
singlefile-archiver COMMAND --help
```