# Cloud Inbox 部署说明

Cloud Inbox 是手机端“树洞入口”。它可以部署在 EdgeOne Pages / Makers 或 Vercel，数据保存在 Supabase。电脑不需要一直开机；电脑开机后本地后台服务会自动把云端队列拉回 Obsidian，并可继续调用 DeepSeek 和 AnkiConnect。

## 架构

```text
手机 / 浏览器
  -> EdgeOne / Vercel cloud-inbox
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

## 4. 部署到 EdgeOne 或 Vercel

推荐通过 GitHub 导入 EdgeOne Pages / Makers。构建设置：

```text
框架预设：Next.js
根目录：cloud-inbox
输出目录：.next
构建命令：npm run build
安装命令：npm install
```

环境变量：

```text
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
INBOX_TOKEN
AGENT_TOKEN
```

如果继续使用 Vercel，进入 cloud-inbox 目录：

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

## 5. 手机免输入 Token

第一次在手机打开时，可以使用：

```text
https://你的-EdgeOne-域名/#token=你的-INBOX_TOKEN
```

页面会把 token 保存到当前浏览器，并清理地址栏。之后把页面加入浏览器收藏夹或添加到主屏幕即可，不需要每次查找、复制、粘贴 token。

如果更换手机、浏览器或清理了网站数据，再打开一次带 `#token=` 的链接即可。

## 6. 配置本地 Agent

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
  api_url: "https://你的-EdgeOne-域名"
  agent_token_env: "CLOUD_INBOX_AGENT_TOKEN"
  poll_limit: 10
```

在 `.env` 中配置：

```env
CLOUD_INBOX_AGENT_TOKEN=你的 AGENT_TOKEN
DEEPSEEK_API_KEY=你的新 DeepSeek Key
```

## 7. 手动拉取

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

## 8. Windows 开机自动同步

推荐使用项目内置脚本：

```powershell
cd D:\Project\Obsidian_Anki\learning-asset-processor
.\scripts\install-autostart.ps1
```

默认每 60 分钟同步一次。可以在 `config.yaml` 中调整：

```yaml
automation:
  enabled: true
  interval_minutes: 60
  mode: "full"
```

## 安全提醒

- 不要把 DeepSeek Key 写入代码。
- 不要把 `SUPABASE_SERVICE_ROLE_KEY` 放到浏览器端。
- `INBOX_TOKEN` 和 `AGENT_TOKEN` 请使用不同值。
- 之前在聊天里发过的 DeepSeek Key 建议立刻轮换。
- AnkiConnect 仍然只在本地使用，不需要暴露到公网。
