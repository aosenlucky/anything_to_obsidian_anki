"use client";

import {
  BookOpen,
  Cloud,
  Feather,
  Inbox,
  KeyRound,
  Layers3,
  LockKeyhole,
  Send,
  Sparkles,
  Sprout,
} from "lucide-react";
import { FormEvent, useEffect, useState } from "react";

type SubmitState = "idle" | "saving" | "saved" | "error";

const sourceTypes = [
  { value: "manual", label: "手动" },
  { value: "article", label: "文章" },
  { value: "book", label: "书籍" },
  { value: "video", label: "视频" },
  { value: "course", label: "课程" },
  { value: "conversation", label: "对话" },
];

const domains = ["Cloud", "AI", "English", "History", "General", "Parenting", "Travel", "Wealth"];

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

    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const payload = Object.fromEntries(form.entries());
    delete payload.token;
    window.localStorage.setItem("lap_inbox_token", token);

    try {
      const response = await fetch("/api/inbox", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "保存失败");
      }
      setState("saved");
      setMessage(data.duplicate ? "这条内容已经在队列里。" : "已收下，等待本地 Agent 拉取。");
      formElement.reset();
    } catch (error) {
      setState("error");
      setMessage(error instanceof Error ? error.message : "保存失败");
    }
  }

  return (
    <main className="page">
      <section className="experience" aria-labelledby="page-title">
        <aside className="story-panel">
          <div className="brand-row">
            <span className="brand-mark" aria-hidden="true">
              <Sprout size={18} strokeWidth={2} />
            </span>
            <span>Learning Asset Inbox</span>
          </div>

          <div className="tree-scene" aria-hidden="true">
            <div className="canopy canopy-a" />
            <div className="canopy canopy-b" />
            <div className="trunk">
              <div className="hollow">
                <Inbox size={34} strokeWidth={1.7} />
              </div>
            </div>
            <div className="root root-left" />
            <div className="root root-right" />
          </div>

          <div className="hero-copy">
            <p className="eyebrow">Cloud Queue</p>
            <h1 id="page-title">把碎片先放进树洞。</h1>
            <p>
              手机上的文章、摘录、灵感和对话先进入云端队列，等电脑开机后再回到 Obsidian 与 Anki。
            </p>
          </div>

          <div className="signal-grid">
            <div>
              <Cloud size={18} strokeWidth={1.8} />
              <span>云端暂存</span>
            </div>
            <div>
              <Layers3 size={18} strokeWidth={1.8} />
              <span>本地归档</span>
            </div>
            <div>
              <Sparkles size={18} strokeWidth={1.8} />
              <span>稍后加工</span>
            </div>
          </div>
        </aside>

        <form className="capture-card" onSubmit={submit}>
          <div className="form-head">
            <div>
              <p className="eyebrow">Quick Capture</p>
              <h2>投递一条材料</h2>
            </div>
            <span className="secure-chip">
              <LockKeyhole size={15} strokeWidth={1.8} />
              私有
            </span>
          </div>

          <label className="field">
            <span>
              <KeyRound size={16} strokeWidth={1.9} />
              投递口令
            </span>
            <input
              name="token"
              type="password"
              value={token}
              onChange={(event) => setToken(event.target.value)}
              placeholder="输入 INBOX_TOKEN"
              autoComplete="current-password"
              required
            />
            <small>等同于 EdgeOne 环境变量 INBOX_TOKEN，仅保存在当前浏览器。</small>
          </label>

          <div className="grid">
            <label className="field">
              <span>
                <BookOpen size={16} strokeWidth={1.9} />
                来源类型
              </span>
              <select name="source_type" defaultValue="manual">
                {sourceTypes.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>
                <Feather size={16} strokeWidth={1.9} />
                领域提示
              </span>
              <select name="domain_hint" defaultValue="">
                <option value="">自动判断</option>
                {domains.map((domain) => (
                  <option key={domain}>{domain}</option>
                ))}
              </select>
            </label>
          </div>

          <label className="field">
            <span>标题</span>
            <input name="title" placeholder="可选" />
          </label>

          <label className="field">
            <span>加工意图</span>
            <textarea
              name="my_intent"
              rows={3}
              placeholder="例如：加工成客户话术、Anki 卡、周复盘素材"
            />
          </label>

          <label className="field">
            <span>内容</span>
            <textarea
              name="raw_input"
              rows={9}
              placeholder="粘贴 URL、文章片段、读书摘录、灵感或对话记录"
              required
            />
          </label>

          <button className="submit-button" disabled={state === "saving"}>
            <Send size={17} strokeWidth={2} />
            {state === "saving" ? "投递中..." : "放进树洞"}
          </button>

          {message ? <p className={`message ${state}`}>{message}</p> : null}
        </form>
      </section>
    </main>
  );
}
