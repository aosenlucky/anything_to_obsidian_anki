"use client";

import { FormEvent, useEffect, useState } from "react";

type SubmitState = "idle" | "saving" | "saved" | "error";

export default function Page() {
  const [token, setToken] = useState("");
  const [state, setState] = useState<SubmitState>("idle");
  const [message, setMessage] = useState("");

  useEffect(() => {
    setToken(window.localStorage.getItem("lap_inbox_token") || "");
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setState("saving");
    setMessage("");
    const form = new FormData(event.currentTarget);
    const payload = Object.fromEntries(form.entries());
    window.localStorage.setItem("lap_inbox_token", token);

    try {
      const response = await fetch("/api/inbox", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "保存失败");
      }
      setState("saved");
      setMessage(data.duplicate ? "这条内容已经在队列里了。" : "已丢进 Inbox，等电脑开机后会自动拉取。");
      event.currentTarget.reset();
    } catch (error) {
      setState("error");
      setMessage(error instanceof Error ? error.message : "保存失败");
    }
  }

  return (
    <main className="page">
      <section className="hero">
        <div className="mark" aria-hidden="true" />
        <p className="eyebrow">Learning Asset Inbox</p>
        <h1>把新知识先丢进树洞。</h1>
        <p className="lead">手机上看到的文章、摘录、想法和对话，先保存到云端队列。电脑开机后，本地 Agent 会拉回 Obsidian 和 Anki。</p>
      </section>

      <form className="capture-card" onSubmit={submit}>
        <label>
          私有 Token
          <input
            name="token"
            type="password"
            value={token}
            onChange={(event) => setToken(event.target.value)}
            placeholder="INBOX_TOKEN"
            required
          />
        </label>

        <div className="grid">
          <label>
            来源类型
            <select name="source_type" defaultValue="manual">
              <option value="manual">手动</option>
              <option value="article">文章</option>
              <option value="book">书籍</option>
              <option value="video">视频</option>
              <option value="course">课程</option>
              <option value="conversation">对话</option>
            </select>
          </label>
          <label>
            领域提示
            <select name="domain_hint" defaultValue="">
              <option value="">自动判断</option>
              <option>Cloud</option>
              <option>AI</option>
              <option>English</option>
              <option>History</option>
              <option>General</option>
              <option>Parenting</option>
              <option>Travel</option>
              <option>Wealth</option>
            </select>
          </label>
        </div>

        <label>
          标题
          <input name="title" placeholder="可选" />
        </label>

        <label>
          加工意图
          <textarea name="my_intent" rows={3} placeholder="例如：加工成客户话术、Anki 卡、周复盘素材" />
        </label>

        <label>
          内容
          <textarea name="raw_input" rows={10} placeholder="粘贴 URL、文章片段、读书摘录、灵感或对话记录" required />
        </label>

        <button disabled={state === "saving"}>{state === "saving" ? "保存中..." : "丢进 Inbox"}</button>
        {message ? <p className={`message ${state}`}>{message}</p> : null}
      </form>
    </main>
  );
}
