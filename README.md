# Learning Asset Processor

本项目是一个本地知识流程工具，把原始材料保存到 Obsidian Vault，调用 DeepSeek API 生成结构化 Notes 和少量高质量 Anki 卡片，并通过 AnkiConnect 同步到 Anki。

## 安装

```powershell
cd D:\Project\Obsidian_Anki\learning-asset-processor
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## 配置

复制配置文件：

```powershell
copy config.yaml.example config.yaml
copy .env.example .env
```

在 `config.yaml` 中修改 Vault 路径：

```yaml
obsidian:
  vault_path: "D:/Obsidian/MyVault"
```

在 `.env` 中填写 DeepSeek API Key：

```env
DEEPSEEK_API_KEY=你的 API Key
```

DeepSeek 模型名不是硬编码。默认是：

```yaml
ai:
  provider: "deepseek"
  base_url: "https://api.deepseek.com"
  model: "deepseek-v4-pro"
```

可以改成 DeepSeek 当前实际可用的模型名，例如：

```yaml
ai:
  model: "deepseek-v4-pro"
```

不要把 `.env` 提交到版本库。

## 配置 AnkiConnect

1. 打开 Anki。
2. 安装 AnkiConnect 插件。
3. 保持 Anki 运行。
4. 默认服务地址为 `http://127.0.0.1:8765`。

## 初始化 Obsidian Vault

```powershell
python -m app.main init
```

该命令会创建：

- `10_Sources`
- `20_Notes`
- `50_Reviews`
- `90_System`
- Dataview Dashboard 文件

如果目录或 Dashboard 已存在，不会覆盖。

## 启动本地 Web 服务

```powershell
python -m app.main serve
```

访问：

```text
http://127.0.0.1:8000
```

也可以双击 `run.bat`。

## 手机树洞 Cloud Inbox

项目已包含一个可部署到 Vercel 的 Cloud Inbox：

```text
cloud-inbox/
```

它用于手机随时提交内容，电脑开机后再运行本地 Agent 拉取：

```powershell
python -m app.main pull-inbox
```

拉取后继续 AI 处理和 Anki 同步：

```powershell
python -m app.main pull-inbox --process-ai --sync-anki
```

完整部署步骤见：

[docs-cloud-inbox.md](docs-cloud-inbox.md)

如果 Vercel 在你的网络环境访问慢，可以迁移到 EdgeOne Pages / Makers：

[docs-edgeone-pages.md](docs-edgeone-pages.md)

## 本地自动同步

本地服务支持开机后自动定时拉取 Cloud Inbox。配置项在 `config.yaml`：

```yaml
automation:
  enabled: true
  interval_minutes: 10
  mode: "full"
  run_on_start: true
  notify_on_success: false
  notify_on_failure: true
```

`mode` 可选：

- `obsidian_only`：只拉取到 Obsidian Source
- `notes_only`：拉取并生成 Obsidian Note
- `full`：拉取、生成 Note，并同步 Anki

安装 Windows 登录自动启动：

```powershell
cd D:\Project\Obsidian_Anki\learning-asset-processor
.\scripts\install-autostart.ps1
```

脚本会优先注册 Windows 计划任务；如果当前权限不允许注册计划任务，会自动在当前用户的 Startup 文件夹创建兜底启动脚本。

卸载自动启动：

```powershell
.\scripts\uninstall-autostart.ps1
```

手动启动或停止后台服务：

```powershell
.\scripts\start-background-service.ps1
.\scripts\stop-background-service.ps1
```

状态和运行记录保存在：

```text
app/storage/automation_state.json
app/storage/automation_runs.json
app/storage/failed_items.json
```

如果状态面板显示 `HTTP 404`、`NOT_FOUND` 或 `The site does not exist`，通常是 `config.yaml` 里的 `cloud_inbox.api_url` 仍指向旧域名或 EdgeOne 项目地址不可用。把它改成当前可访问的 EdgeOne 生产域名后，下一轮自动同步会继续尝试。

## Web 使用流程

1. 粘贴文章、视频字幕、课程内容、读书摘录、会议纪要或 URL。
2. 点击“保存原始材料”。
3. 点击“开始 AI 分析”。
4. 预览 Notes 和 Anki 卡片。
5. 点击“写入 Obsidian”。
6. 勾选要同步的卡片。
7. 点击“同步到 Anki”。
8. 按需生成周复盘或月复盘。

## CLI 命令

采集 Source：

```powershell
python -m app.main capture --type article --input-file tests/sample_article.txt --intent "加工成 RAG 方案框架和客户话术" --domain AI
```

处理 Source 并写入 Notes：

```powershell
python -m app.main process --source "10_Sources/Articles/xxx.md"
```

同步已生成的待同步卡片：

```powershell
python -m app.main sync-anki --all
```

生成 Review：

```powershell
python -m app.main review --weekly
python -m app.main review --monthly
```

拉取 Cloud Inbox：

```powershell
python -m app.main pull-inbox
python -m app.main pull-inbox --process-ai --sync-anki
```

一键流程：

```powershell
python -m app.main run --type article --input-file tests/sample_article.txt --intent "加工成 RAG 方案框架和 Anki 卡" --domain AI --sync-anki
```

## 测试方式

检查导入：

```powershell
python -m compileall app
```

使用临时 Vault 测试初始化：

```powershell
mkdir D:\Temp\LapVault
copy config.yaml.example config.yaml
# 修改 config.yaml 的 obsidian.vault_path 为 D:/Temp/LapVault
python -m app.main init
```

在未配置 DeepSeek API Key 时，AI 处理会返回清晰错误，不会记录 API Key。

## 已完成能力

- FastAPI 本地服务。
- 中文本地 Web UI。
- 配置读取和 `.env` 加载。
- Obsidian Vault 目录初始化。
- Dataview Dashboards 生成。
- Source Capture 写入 Markdown。
- DeepSeek OpenAI-compatible API Client。
- AI 严格 JSON Prompt。
- JSON 解析、提取和一次自动修复。
- Note Markdown 生成。
- Anki 卡候选生成。
- `card_hash` 本地去重。
- `pending_cards.json` 待同步缓存。
- AnkiConnect 连接检测、Deck 创建、Basic 卡添加。
- Anki 同步后回写 Note YAML。
- Weekly / Monthly Review 脚手架生成。
- CLI 批处理入口。
- Vercel Cloud Inbox 手机树洞入口。
- 本地 `pull-inbox` Agent。
- 本地自动同步 Scheduler。
- Windows 登录自动启动脚本。
- 自动化状态和运行历史记录。

## 暂未完成能力和 TODO

- `sync-anki --all` 当前同步 `pending_cards.json`，后续可扩展为扫描全部 pending Notes。
- MVP 只支持 Anki `Basic` 卡型。
- AI 处理需要真实 DeepSeek API Key；离线 mock 模式尚未内置。
- URL 只做标题抓取，不抓取全文正文。
- Review 目前主要基于本地 Frontmatter 汇总，后续可加入 DeepSeek 聚类和主题输出草稿。
- 暂未实现 CSV 备用导出。
- Cloud Inbox 当前使用 Token 鉴权，后续可升级为正式登录系统。

## 常见问题

### DeepSeek API：未配置

确认 `.env` 中有：

```env
DEEPSEEK_API_KEY=你的 API Key
```

然后重新启动服务。

### Obsidian Vault：路径无效

确认 `config.yaml` 中的 `obsidian.vault_path` 是真实存在的本地路径。

### AnkiConnect：未连接

确认 Anki 正在运行，并且已安装 AnkiConnect 插件。默认地址为：

```text
http://127.0.0.1:8765
```

### 同名 Markdown 文件

工具不会覆盖旧文件，会自动追加 `-2`、`-3` 等序号。
