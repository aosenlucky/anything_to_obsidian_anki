# 从 Vercel 迁移到 EdgeOne Pages / Makers

目标：把手机树洞 `cloud-inbox` 从 Vercel 换到 EdgeOne Pages / Makers，解决 Vercel 默认域名在国内访问慢或不可访问的问题。

当前项目是 Next.js App Router，并包含服务端 API：

- `POST /api/inbox`
- `GET /api/agent/items`
- `PATCH /api/agent/items/[id]`
- `GET /api/health`

EdgeOne Makers 支持 Next.js 和动态接口部署，因此可以继续使用同一套 `cloud-inbox` 代码。

## 你需要准备

1. EdgeOne Makers / Pages 账号。
2. 一个 EdgeOne API Token。
3. Supabase 仍然沿用现在这套，不需要重建表。
4. 已有四个环境变量：
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `INBOX_TOKEN`
   - `AGENT_TOKEN`

本地生成的 Token 在：

```powershell
Get-Content D:\Project\Obsidian_Anki\learning-asset-processor\secrets.generated.env
```

## 第一步：在 EdgeOne 控制台创建项目

如果你使用 CLI 部署，项目不存在时通常会自动创建。项目名建议沿用：

```text
anything_to_obsidian_anki
```

## 第二步：在 EdgeOne 控制台添加环境变量

进入 EdgeOne Makers / Pages 控制台，找到项目：

```text
anything_to_obsidian_anki
```

进入项目设置，找到类似这些名字的入口：

```text
Environment Variables
环境变量
Variables
```

添加 4 个生产环境变量：

```text
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
INBOX_TOKEN
AGENT_TOKEN
```

值和 Vercel 当前使用的一样。

注意：

- `SUPABASE_SERVICE_ROLE_KEY` 是 Supabase 的 Secret Key，不是 Published Key。
- `INBOX_TOKEN` 是手机网页提交时用。
- `AGENT_TOKEN` 是本地电脑拉取时用。
- 不要把这些值发给别人或提交到仓库。

## 第三步：部署到 EdgeOne

进入 cloud-inbox 目录：

```powershell
cd D:\Project\Obsidian_Anki\learning-asset-processor\cloud-inbox
```

执行：

```powershell
.\scripts\deploy-edgeone-prod.ps1 -EdgeOneApiToken "你的_EDGEONE_API_TOKEN"
```

也可以手动执行底层命令：

```powershell
npm install
npm run build
npx edgeone@latest makers deploy -n anything_to_obsidian_anki -t "你的_EDGEONE_API_TOKEN" -e production
```

部署成功后，EdgeOne 会返回访问 URL。把这个 URL 记下来。

## 第四步：绑定自有域名

在 EdgeOne 项目里找到：

```text
Custom Domain
自定义域名
Domain
```

添加你的域名，例如：

```text
inbox.yourdomain.com
```

然后按 EdgeOne 控制台提示去 DNS 服务商添加 CNAME。

生效后，访问：

```text
https://inbox.yourdomain.com/api/health
```

应该看到：

```json
{"ok":true,"service":"learning-asset-cloud-inbox"}
```

## 第五步：切换本地 Agent 到 EdgeOne 域名

确认 EdgeOne 域名能访问后，执行：

```powershell
cd D:\Project\Obsidian_Anki\learning-asset-processor

.\scripts\switch-cloud-inbox-url.ps1 `
  -CloudInboxUrl "https://你的 EdgeOne 域名"
```

然后测试：

```powershell
python -m app.main pull-inbox
```

## 回滚到 Vercel

如果 EdgeOne 还没完全配置好，可以随时切回 Vercel：

```powershell
.\scripts\switch-cloud-inbox-url.ps1 `
  -CloudInboxUrl "https://anythingtoobsidiananki.vercel.app"
```

## 测试功能

1. 打开 EdgeOne 域名。
2. 输入 `INBOX_TOKEN`。
3. 提交一条测试内容。
4. 本地执行：

```powershell
python -m app.main pull-inbox
```

成功后应该在 Obsidian 看到：

```text
10_Sources/Manual/YYYY-MM-DD｜标题｜手动.md
```

完整流程：

```powershell
python -m app.main pull-inbox --process-ai --sync-anki
```

完整流程需要：

- 本地 `.env` 有可用 `DEEPSEEK_API_KEY`
- Anki 已打开
- AnkiConnect 已安装并监听 `http://127.0.0.1:8765`
