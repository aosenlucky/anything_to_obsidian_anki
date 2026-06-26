# Cloud Inbox 部署说明

Cloud Inbox 是手机端“树洞入口”。它部署在 Vercel，数据保存在 Supabase。电脑不需要一直开机；电脑开机后运行本地 Agent，把云端队列拉回 Obsidian，并可继续调用 DeepSeek 和 AnkiConnect。

## 架构

```text
手机 / 浏览器
  -> Vercel cloud-inbox
  -> Supabase inbox_items
  -> Windows 本地 Agent pull-inbox
  -> Obsidian 10_Sources
  -> 可选：DeepSeek 处理、写 Notes、同步 Anki
```

## 1. 创建 Supabase 表

1. 新建 Supabase Project。
2. 打开 SQL Editor。
3. 执行：

```sql
-- 文件位置：
-- cloud-inbox/supabase/schema.sql
```

也就是复制 [schema.sql](cloud-inbox/supabase/schema.sql) 的内容执行。

需要保存这两个值：

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

`SUPABASE_SERVICE_ROLE_KEY` 只能放在 Vercel 服务端环境变量里，不要放到浏览器代码、README 截图或公开仓库。

## 2. 生成两个 Token

建议用 PowerShell 生成随机 Token：

```powershell
[System.Web.Security.Membership]::GeneratePassword(40, 8)
[System.Web.Security.Membership]::GeneratePassword(40, 8)
```

分别作为：

- `INBOX_TOKEN`：手机网页提交内容时使用。
- `AGENT_TOKEN`：本地电脑拉取队列时使用。

## 3. 本地测试 cloud-inbox

```powershell
cd D:\Project\Obsidian_Anki\learning-asset-processor\cloud-inbox
copy .env.example .env.local
```

填写：

```env
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
INBOX_TOKEN=
AGENT_TOKEN=
```

安装并启动：

```powershell
npm install
npm run dev
```

访问：

```text
http://127.0.0.1:3000
```

## 4. 部署到 Vercel

进入 cloud-inbox 目录：

```powershell
cd D:\Project\Obsidian_Anki\learning-asset-processor\cloud-inbox
```

登录并部署：

```powershell
npx vercel login
npx vercel
```

首次部署后，在 Vercel Project Settings -> Environment Variables 中添加：

```text
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
INBOX_TOKEN
AGENT_TOKEN
```

然后重新部署生产环境：

```powershell
npx vercel --prod
```

也可以使用 Vercel CLI 添加环境变量：

```powershell
npx vercel env add SUPABASE_URL production
npx vercel env add SUPABASE_SERVICE_ROLE_KEY production
npx vercel env add INBOX_TOKEN production
npx vercel env add AGENT_TOKEN production
```

## 5. 配置本地 Agent

复制本地配置：

```powershell
cd D:\Project\Obsidian_Anki\learning-asset-processor
copy config.yaml.example config.yaml
copy .env.example .env
```

在 `config.yaml` 中配置：

```yaml
cloud_inbox:
  enabled: true
  api_url: "https://你的-vercel-域名.vercel.app"
  agent_token_env: "CLOUD_INBOX_AGENT_TOKEN"
  poll_limit: 10
```

在 `.env` 中配置：

```env
CLOUD_INBOX_AGENT_TOKEN=你的 AGENT_TOKEN
DEEPSEEK_API_KEY=你的新 DeepSeek Key
```

## 6. 手动拉取

只拉回 Obsidian Source，不调用 AI：

```powershell
python -m app.main pull-inbox
```

拉回 Source，并继续 AI 处理、写 Notes、同步 Anki：

```powershell
python -m app.main pull-inbox --process-ai --sync-anki
```

先演练，不写文件、不回写云端：

```powershell
python -m app.main pull-inbox --dry-run
```

## 7. Windows 开机自动拉取

可以使用 Windows Task Scheduler：

1. 打开“任务计划程序”。
2. 创建基本任务。
3. 触发器选择“登录时”。
4. 操作选择“启动程序”。
5. 程序填：

```text
D:\Project\Obsidian_Anki\learning-asset-processor\run-pull-inbox.bat
```

如果不想每次都调用 AI，把 `run-pull-inbox.bat` 中的命令改成：

```bat
python -m app.main pull-inbox
```

## 安全提醒

- 不要把 DeepSeek Key 写入代码。
- 不要把 `SUPABASE_SERVICE_ROLE_KEY` 放到浏览器端。
- `INBOX_TOKEN` 和 `AGENT_TOKEN` 请使用不同值。
- 之前在聊天里发过的 DeepSeek Key 建议立刻轮换。
- AnkiConnect 仍然只在本地使用，不需要暴露到公网。
