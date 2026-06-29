"use client";

import {
  BookOpen,
  CheckCircle2,
  ClipboardPaste,
  Feather,
  KeyRound,
  LockKeyhole,
  RefreshCw,
  Send,
  Sparkles,
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

function tokenFromLocation() {
  const search = new URLSearchParams(window.location.search);
  const hash = new URLSearchParams(window.location.hash.replace(/^#/, ""));
  return (
    hash.get("token") ||
    hash.get("inbox_token") ||
    search.get("token") ||
    search.get("inbox_token") ||
    search.get("t") ||
    ""
  ).trim();
}

function prefillFromLocation() {
  const search = new URLSearchParams(window.location.search);
  const title = (search.get("title") || "").trim();
  const text = (search.get("text") || search.get("raw_input") || "").trim();
  const url = (search.get("url") || search.get("source_url") || "").trim();
  const rawInput = [text, url && !text.includes(url) ? url : ""].filter(Boolean).join("\n\n");
  return { title, rawInput, sourceUrl: url };
}

function firstUrl(value: string) {
  return value.match(/https?:\/\/[^\s]+/)?.[0] || "";
}

export default function Page() {
  const [token, setToken] = useState("");
  const [tokenDraft, setTokenDraft] = useState("");
  const [showTokenSetup, setShowTokenSetup] = useState(false);
  const [title, setTitle] = useState("");
  const [rawInput, setRawInput] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [state, setState] = useState<SubmitState>("idle");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const linkToken = tokenFromLocation();
    const prefill = prefillFromLocation();
    const storedToken = window.localStorage.getItem("lap_inbox_token") || "";
    const nextToken = linkToken || storedToken;
    if (linkToken) {
      window.localStorage.setItem("lap_inbox_token", linkToken);
    }
    if (linkToken || prefill.title || prefill.rawInput) {
      window.history.replaceState(null, "", window.location.pathname);
    }
    setTitle(prefill.title);
    setRawInput(prefill.rawInput);
    setSourceUrl(prefill.sourceUrl);
    setToken(nextToken);
    setTokenDraft(nextToken);
    setShowTokenSetup(!nextToken);
  }, []);

  function saveToken() {
    const nextToken = tokenDraft.trim();
    if (!nextToken) {
      setMessage("请先填入投递口令。");
      setState("error");
      setShowTokenSetup(true);
      return;
    }
    window.localStorage.setItem("lap_inbox_token", nextToken);
    setToken(nextToken);
    setShowTokenSetup(false);
    setState("saved");
    setMessage("投递口令已保存。");
  }

  function clearToken() {
    window.localStorage.removeItem("lap_inbox_token");
    setToken("");
    setTokenDraft("");
    setShowTokenSetup(true);
    setState("idle");
    setMessage("已清除本机保存的投递口令。");
  }

  async function pasteFromClipboard() {
    if (!navigator.clipboard?.readText) {
      setState("error");
      setMessage("当前浏览器不支持直接读取剪贴板，请手动粘贴。");
      return;
    }

    try {
      const text = (await navigator.clipboard.readText()).trim();
      if (!text) {
        setState("error");
        setMessage("剪贴板里没有可投递的文本。");
        return;
      }
      setRawInput((current) => (current ? `${current}\n\n${text}` : text));
      setSourceUrl((current) => current || firstUrl(text));
      setState("idle");
      setMessage("已从剪贴板填入内容。");
    } catch {
      setState("error");
      setMessage("读取剪贴板失败，请使用系统粘贴。");
    }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const activeToken = token.trim();
    if (!activeToken) {
      setState("error");
      setMessage("请先保存投递口令。");
      setShowTokenSetup(true);
      return;
    }

    setState("saving");
    setMessage("");

    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const payload = Object.fromEntries(form.entries());

    try {
      const response = await fetch("/api/inbox", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${activeToken}`,
        },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "保存失败");
      }
      setState("saved");
      setMessage(data.duplicate ? "这条内容已经在队列里。" : "已收下，等待本地电脑自动同步。");
      setTitle("");
      setRawInput("");
      setSourceUrl("");
      formElement.reset();
    } catch (error) {
      setState("error");
      setMessage(error instanceof Error ? error.message : "保存失败");
    }
  }

  return (
    <main className="page">
      <section className="hero" aria-labelledby="page-title">
        <div className="brand-row">
          <span className="brand-mark" aria-hidden="true">
            <Sparkles size={17} strokeWidth={2} />
          </span>
          <span>Learning Asset Inbox</span>
        </div>

        <div className="hero-copy">
          <p className="eyebrow">Private Cloud Queue</p>
          <h1 id="page-title">把碎片先放进树洞。</h1>
          <p>手机上看到的文章、摘录、灵感和对话先进入云端队列；电脑开机后，后台会自动带回 Obsidian 和 Anki。</p>
        </div>

        <div className="status-row" aria-live="polite">
          <span className={token ? "status-chip ok" : "status-chip"}>
            {token ? <CheckCircle2 size={15} strokeWidth={2} /> : <LockKeyhole size={15} strokeWidth={2} />}
            {token ? "口令已保存" : "等待口令"}
          </span>
          <button type="button" className="quiet-button" onClick={() => setShowTokenSetup((value) => !value)}>
            <KeyRound size={15} strokeWidth={2} />
            {showTokenSetup ? "收起口令" : "更换口令"}
          </button>
        </div>
      </section>

      {showTokenSetup ? (
        <section className="token-panel" aria-label="投递口令">
          <label className="field">
            <span>
              <KeyRound size={16} strokeWidth={1.9} />
              投递口令
            </span>
            <input
              type="password"
              value={tokenDraft}
              onChange={(event) => setTokenDraft(event.target.value)}
              placeholder="首次粘贴一次 INBOX_TOKEN"
              autoComplete="current-password"
            />
          </label>
          <div className="token-actions">
            <button type="button" className="secondary-button" onClick={saveToken}>
              保存口令
            </button>
            <button type="button" className="quiet-button" onClick={clearToken}>
              清除
            </button>
          </div>
        </section>
      ) : null}

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
            <input name="domain_hint" list="domain-options" placeholder="自动判断或输入新领域" />
            <datalist id="domain-options">
              {domains.map((domain) => (
                <option key={domain} value={domain} />
              ))}
            </datalist>
          </label>
        </div>

        <label className="field">
          <span>标题</span>
          <input name="title" placeholder="可选" value={title} onChange={(event) => setTitle(event.target.value)} />
        </label>

        <label className="field">
          <span>加工意图</span>
          <textarea name="my_intent" rows={3} placeholder="例如：提炼成行动清单、Anki 卡、周复盘素材" />
        </label>

        <label className="field main-content-field">
          <span className="field-title">
            内容
            <button type="button" className="paste-button" onClick={pasteFromClipboard}>
              <ClipboardPaste size={15} strokeWidth={2} />
              从剪贴板粘贴
            </button>
          </span>
          <textarea
            name="raw_input"
            rows={10}
            placeholder="粘贴 URL、文章片段、读书摘录、灵感或对话记录"
            value={rawInput}
            onChange={(event) => setRawInput(event.target.value)}
            required
          />
        </label>
        <input type="hidden" name="source_url" value={sourceUrl} readOnly />

        <button className="submit-button" disabled={state === "saving"}>
          {state === "saving" ? <RefreshCw size={17} strokeWidth={2} /> : <Send size={17} strokeWidth={2} />}
          {state === "saving" ? "投递中..." : "放进树洞"}
        </button>

        {message ? <p className={`message ${state}`}>{message}</p> : null}
      </form>
    </main>
  );
}
