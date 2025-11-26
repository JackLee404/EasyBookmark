# EasyBookmark

<div align="center">
  <img src="assets/logo.svg" alt="EasyBookmark Logo" width="200" height="200">
</div>



一个强大而易用的PDF处理工具，提供目录提取、内容分析等功能，帮助您更高效地处理PDF文档。

## 功能特性

- **PDF目录提取**：自动或手动提取PDF文档的目录结构
- **智能内容分析**：使用LLM（大预言模型）技术分析PDF内容，提取关键信息
- **用户友好界面**：直观的图形界面
- **配置管理**：灵活的配置选项，适应不同用户需求

## 系统要求

### Windows
- Windows 10/11 64位
- Python 3.9+
- 至少2GB内存
- 200MB可用磁盘空间

## 安装方法

### 方法一：使用预编译的可执行文件

1. 从[发布页面](https://github.com/JackLee404/EasyBookmark/releases)下载适合您操作系统的安装包
2. Windows用户：运行`.exe`文件进行安装
3. Mac用户：将`.app`文件拖到应用程序文件夹

### 方法二：从源码安装

1. 克隆或下载本仓库
   ```bash
   git clone https://github.com/JackLee404/EasyBookmark.git
cd EasyBookmark
   ```

2. 创建虚拟环境（推荐）
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

4. 运行应用程序
   ```bash
   python src/main.py
   ```

## 使用说明

### 1. 启动应用程序

Windows用户：双击桌面上的EasyBookmark快捷方式或从开始菜单启动

Mac用户：从应用程序文件夹中启动EasyBookmark

### 2. 打开PDF文件

- 点击"文件" > "打开"，或使用快捷键`Ctrl+O`（Windows）/`Cmd+O`（Mac）
- 浏览并选择要处理的PDF文件
- 输入LLM的API参数

### 3. 提取目录

#### 方法一：使用AI自动提取目录
- 打开PDF文件后，点击"工具" > "提取目录" > "AI自动提取"
- 设置目录所在的页码范围
- 点击"开始提取"按钮，程序会使用AI提取PDF中的目录
- 提取完成后，可以在下方预览区域查看提取结果

#### 方法二：导入JSON格式目录

如果没有LLM的API，您也可以通过复制目录的文本（如果可以）将文本发送给LLM以及需要的JSON格式

```
PROMPT:
你是一个专业的PDF目录提取助手。请从提供的文本和PDF页面图片中提取目录信息，并按照指定格式输出。
                
                提取规则：
                1. 结合文本内容和页面图片，识别目录项的标题、页码和层级关系
                2. 忽略页眉、页脚、页码等无关信息
                3. 正确判断每个目录项的层级（通常通过缩进或数字格式判断）
                4. 对于没有明确页码的项，尝试推断或标记为-1
                
                输出格式必须是JSON数组，每项包含三个字段：
                - title: 目录项标题
                - page: 页码（整数）
                - level: 层级（从1开始）
                
                示例输出：
                [{"title": "第一章 介绍", "page": 1, "level": 1}, {"title": "1.1 背景", "page": 2, "level": 2}]
                
                重要：请确保输出是纯JSON格式，不要包含任何额外的文本解释或说明。
                
                {这里输入你复制的目录文本}
```



- 打开PDF文件后，点击"工具" > "提取目录" > "导入JSON目录"
- 准备好JSON格式的目录文件（格式参考docs/toc_example.json）
- 选择JSON文件，程序会验证并显示导入的目录内容

- 无论使用哪种方法提取目录，都可以：
  - 设置"页码偏置值"调整目录页码
  - 编辑目录条目
  - 保存处理后的PDF文件

### 4. 内容分析

- 选择要分析的页面范围
- 点击"工具" > "内容分析"
- 等待分析完成后查看结果

### 5. 配置设置

- 可以配置以下选项：
  - 默认保存位置
  - LLM设置（API密钥等）
  - 界面语言（如果支持）

### 注意事项

- 模型需要支持OpenAI接口规范，程序在处理时会优先使用多模态方法处理否则尝试文本提取
- 提取目录的准确性取决于PDF质量和目录格式的规范性
- 页码偏置值用于调整书签的实际页码，正数表示向后偏移，负数表示向前偏移
- JSON目录文件必须遵循指定格式，包含title、page和level三个字段
- 导入的目录页码会自动验证是否在PDF有效范围内

## 配置文件说明

应用程序使用JSON格式的配置文件，第一次运行时存储在程序根目录下的名为`config.json`的文件中

主要配置项：

- `default_save_path`: 默认保存路径
- `openai_api_key`: OpenAI API密钥（加密存储）
- `model_name`: 使用的LLM模型名称

## 常见问题

### 1. 无法提取PDF目录

- 确保PDF文件不是扫描件或加密文件
- 尝试使用"手动提取"功能
- 检查是否有足够的权限访问PDF文件

### 2. 内容分析失败

- 确保已正确配置OpenAI API密钥
- 检查网络连接是否正常
- 尝试减少分析的页面范围

### 3. 应用程序崩溃

- 确保您的系统满足要求
- 更新到最新版本的应用程序
- 如果问题持续，请联系邮箱或提交issues

## 命令行工具

EasyBookmark还提供命令行工具，方便批量处理或自动化操作：

```bash
# 提取PDF目录到JSON文件
python -m src.cli --input document.pdf --output toc.json --action extract_toc

# 分析PDF内容
python -m src.cli --input document.pdf --output analysis.txt --action analyze --pages 1-10
```

## 开发指南

如果您想参与开发或自定义功能：

1. 按照"从源码安装"部分的步骤设置开发环境
2. 代码结构：
   - `src/`: 主源代码目录
   - `tests/`: 测试文件
   - `assets/`: 图标和其他资源

3. 运行测试：
   ```bash
   python -m unittest discover -s tests
   ```

4. 运行应用：
   ```bash
   # 直接运行
   python main.py
   
   # 或通过src目录运行
   python src/main.py
   ```

5. 打包应用（如需）：
   ```bash
   python package_app.py
   ```

## 许可证

本项目采用MIT许可证。详见[LICENSE](LICENSE)文件。

## 联系方式

- 项目主页：[https://github.com/JackLee404/EasyBookmark](https://github.com/JackLee404/EasyBookmark)
- issues: [https://github.com/JackLee404/EasyBookmark/issues](https://github.com/JackLee404/EasyBookmark/issues)
	- 📫: deepsea404@hotmail.com



## 致谢

本项目使用了以下开源库：

- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI框架
- [pypdf](https://pypi.org/project/pypdf/) - PDF处理
- [LangChain](https://www.langchain.com/) - LLM应用框架
- [OpenAI Python](https://github.com/openai/openai-python) - OpenAI API客户端

## 更新日志

### v1.0.0
- 初始版本发布
- 支持PDF目录提取
- 支持内容分析功能
- 提供图形界面和命令行接口
