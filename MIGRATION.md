# SingleFile Archiver - 隐私保护迁移指南

## 概述

为了保护个人隐私和提高项目的可移植性，我们已经移除了代码中硬编码的个人路径。现在项目使用环境变量进行配置。

## 迁移步骤

### 1. 创建环境配置文件

```bash
# 复制示例配置文件
cp .env.example .env
```

### 2. 编辑 .env 文件

根据你的需求修改以下路径：

```bash
# 编辑配置文件
nano .env
```

示例配置：
```env
SINGLEFILE_DATA_DIR=/Users/yourusername/Documents/singlefile
SINGLEFILE_ARCHIVE_DIR=/Users/yourusername/Documents/Archives/Web
SINGLEFILE_INCOMING_DIR=/Users/yourusername/Downloads
```

### 3. 更新 Docker Compose（如果使用）

如果你使用 Docker Compose，现在可以：

```bash
# 使用默认配置（推荐）
docker-compose up

# 或者复制示例文件进行自定义
cp docker-compose.example.yml docker-compose.override.yml
# 然后编辑 docker-compose.override.yml
```

## 默认行为

如果没有设置环境变量，系统会使用以下默认路径：

- **数据目录**: `~/.local/share/singlefile`
- **归档目录**: `~/.local/share/singlefile/archive`
- **输入目录**: `~/.local/share/singlefile/incoming`

## 向后兼容性

- 现有的 `data/config.json` 文件中的路径设置仍然有效
- 环境变量优先级高于代码默认值
- 配置文件设置优先级最高

## 验证迁移

运行以下命令验证配置：

```bash
# 查看当前配置
singlefile-archiver info

# 测试基本功能
singlefile-archiver test
```

## 注意事项

1. **个人配置文件** (`data/config.json`) 已被添加到 `.gitignore`，不会被提交到版本控制
2. **环境文件** (`.env`) 也被保护，不会暴露个人路径
3. **日志文件** 包含个人URL历史，已被保护
4. **所有数据目录** 现在都被忽略，确保个人数据安全

## 故障排除

如果遇到路径相关问题：

1. 检查 `.env` 文件是否存在并配置正确
2. 确保所有目录都有适当的读写权限
3. 运行 `singlefile-archiver info` 查看当前使用的路径