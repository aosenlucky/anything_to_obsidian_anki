# Anything to Obsidian Anki - 必须手动执行的部署步骤

本地已完成：

- Vercel 项目已链接到 `anything_to_obsidian_anki`。
- Cloud Inbox 构建已通过。
- 本地 Agent `pull-inbox` 已实现。
- 随机 `INBOX_TOKEN` / `AGENT_TOKEN` 已生成到：
  - `secrets.generated.env`
  - `cloud-inbox/secrets.generated.env`

不要把这两个文件提交或发给别人。

## 1. 手动创建 Supabase 表

进入 Supabase Project -> SQL Editor，执行：

```text
cloud-inbox/supabase/schema.sql
```

执行后，在 Supabase Project Settings -> API 找到：

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

## 2. 读取本地生成的 Token

在项目根目录执行：

```powershell
cd D:\Project\Obsidian_Anki\learning-asset-processor
Get-Content .\secrets.generated.env
```

里面会有：

```env
INBOX_TOKEN=...
AGENT_TOKEN=...
CLOUD_INBOX_AGENT_TOKEN=...
```

`AGENT_TOKEN` 和 `CLOUD_INBOX_AGENT_TOKEN` 是同一个值。

## 3. 写入 Vercel 环境变量

如果你的 Vercel CLI 没有持久登录，请带上 `-VercelToken`。

```powershell
cd D:\Project\Obsidian_Anki\learning-asset-processor\cloud-inbox

.\scripts\set-vercel-env.ps1 `
  -SupabaseUrl "你的 SUPABASE_URL" `
  -SupabaseServiceRoleKey "你的 SUPABASE_SERVICE_ROLE_KEY" `
  -InboxToken "你的 INBOX_TOKEN" `
  -AgentToken "你的 AGENT_TOKEN" `
  -VercelToken "你的 VERCEL_TOKEN"
```

如果已经 `npx vercel login` 成功，可以省略 `-VercelToken`。

## 4. 部署生产环境

```powershell
cd D:\Project\Obsidian_Anki\learning-asset-processor\cloud-inbox
.\scripts\deploy-prod.ps1 -VercelToken "你的 VERCEL_TOKEN"
```

如果已经登录：

```powershell
.\scripts\deploy-prod.ps1
```

记下部署完成后的 Production URL，例如：

```text
https://anything-to-obsidian-anki.vercel.app
```

实际 URL 以 Vercel 输出为准。

## 5. 配置本地 Agent

把上一步的 Production URL、`AGENT_TOKEN` 和你的 Obsidian Vault 路径填进去：

```powershell
cd D:\Project\Obsidian_Anki\learning-asset-processor

.\scripts\configure-local-inbox.ps1 `
  -CloudInboxUrl "你的 Vercel Production URL" `
  -AgentToken "你的 AGENT_TOKEN" `
  -VaultPath "D:\你的\Obsidian\Vault"
```

然后确认 `.env` 里有新的 DeepSeek Key：

```env
DEEPSEEK_API_KEY=你的新 DeepSeek Key
```

## 6. 测试手机树洞

浏览器打开：

```text
你的 Vercel Production URL
```

输入 `INBOX_TOKEN`，提交一条测试内容。

## 7. 本地拉取测试

只拉取到 Obsidian Source：

```powershell
python -m app.main pull-inbox
```

拉取并继续 AI 处理、同步 Anki：

```powershell
python -m app.main pull-inbox --process-ai --sync-anki
```

## 8. 开机自动拉取

任务计划程序里设置登录时运行：

```text
D:\Project\Obsidian_Anki\learning-asset-processor\run-pull-inbox.bat
```
