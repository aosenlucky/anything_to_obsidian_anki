const state = {
  sourcePath: null,
  analysis: null,
  cards: [],
  notePaths: [],
};

const $ = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "请求失败");
  }
  return payload;
}

function toast(message) {
  const box = $("toast");
  box.textContent = message;
  box.classList.add("show");
  window.clearTimeout(box.dataset.timer);
  box.dataset.timer = window.setTimeout(() => box.classList.remove("show"), 4200);
}

function setBusy(button, busy) {
  if (!button) return;
  button.disabled = busy || button.dataset.locked === "true";
  button.dataset.label ??= button.textContent;
  button.textContent = busy ? "处理中..." : button.dataset.label;
}

function setCommandBusy(button, busy) {
  if (!button) return;
  button.disabled = busy;
  button.classList.toggle("is-busy", busy);
}

async function refreshStatus() {
  try {
    const result = await api("/api/status");
    $("deepseekStatus").textContent = result.deepseek;
    $("ankiStatus").textContent = result.anki;
    $("vaultStatus").textContent = result.obsidian;
  } catch (error) {
    toast(error.message);
  }
}

async function runCloudPull(button, options, successLabel) {
  setCommandBusy(button, true);
  $("lastRun").textContent = "云端同步中";
  try {
    const result = await api("/api/cloud/pull", {
      method: "POST",
      body: JSON.stringify(options),
    });
    renderCloudResult(result);
    toast(`${successLabel}：拉取 ${result.pulled} 条`);
    await refreshStatus();
  } catch (error) {
    $("lastRun").textContent = "操作失败";
    toast(error.message);
  } finally {
    setCommandBusy(button, false);
  }
}

function renderCloudResult(result) {
  const rows = result.results || [];
  $("lastRun").textContent = rows.length ? `最近处理 ${rows.length} 条` : "云端暂无新内容";
  $("notesCount").textContent = `${rows.reduce((total, row) => total + (row.note_paths || []).length, 0)} 篇`;
  $("cardsCount").textContent = `${rows.reduce((total, row) => total + (row.card_count || 0), 0)} 张`;

  $("notesPreview").classList.toggle("empty-state", rows.length === 0);
  $("notesPreview").innerHTML = rows.length
    ? rows.map(renderCloudRow).join("")
    : "云端队列里暂无待处理内容";

  $("cardsPreview").classList.add("empty-state");
  $("cardsPreview").innerHTML = rows.length
    ? "完整同步会直接把生成的卡片送往 Anki；本区只预览本地手动分析产生的卡片。"
    : "暂无卡片";
}

function renderCloudRow(row) {
  const notes = (row.note_paths || []).map((path) => `<li>${escapeHtml(path)}</li>`).join("");
  const statusClass = row.status === "processed" ? "ok" : "fail";
  return `
    <article class="run-item ${statusClass}">
      <div>
        <strong>${escapeHtml(row.source_path || row.id)}</strong>
        <p>${row.status === "processed" ? "已完成" : escapeHtml(row.error || "处理失败")}</p>
      </div>
      ${notes ? `<ul>${notes}</ul>` : ""}
    </article>
  `;
}

function formPayload(form) {
  const data = new FormData(form);
  return Object.fromEntries(data.entries());
}

function renderAnalysis(result) {
  const analysis = result.analysis || {};
  state.analysis = analysis;
  state.cards = result.cards || [];
  state.notePaths = result.note_paths || [];

  $("domainValue").textContent = analysis.domain || "-";
  $("typeValue").textContent = analysis.knowledge_type || "-";
  $("priorityValue").textContent = analysis.priority || "-";
  $("reviewValue").textContent = analysis.review_method || "-";
  $("summaryText").textContent = analysis.source_summary || "暂无摘要";
  $("reviewFlag").textContent = analysis.needs_user_review ? "需要人工复核" : "可写入";

  const notes = analysis.notes || [];
  $("notesCount").textContent = `${notes.length} 篇`;
  $("notesPreview").classList.toggle("empty-state", notes.length === 0);
  $("notesPreview").innerHTML = notes.length ? notes.map(renderNote).join("") : "暂无 Note";
  renderCards(state.cards);

  $("writeBtn").disabled = !state.analysis || state.notePaths.length > 0;
  $("syncBtn").disabled = state.cards.length === 0 || state.notePaths.length === 0;
}

function renderNote(note, index) {
  const tags = (note.tags || []).map((tag) => `<span>${escapeHtml(tag)}</span>`).join("");
  return `
    <details class="note-item" ${index === 0 ? "open" : ""}>
      <summary>${escapeHtml(note.title || "未命名知识资产")}</summary>
      <div class="note-body">
        <div class="note-meta">
          <span>${escapeHtml(note.domain || "General")}</span>
          <span>${escapeHtml(note.knowledge_type || "概念型")}</span>
          <span>${escapeHtml(note.priority || "medium")}</span>
          ${tags}
        </div>
        <div class="markdown-preview">${escapeHtml(note.one_sentence_summary || "")}

${escapeHtml(note.core_content || "")}</div>
      </div>
    </details>
  `;
}

function renderCards(cards) {
  $("cardsCount").textContent = `${cards.length} 张`;
  $("cardsPreview").classList.toggle("empty-state", cards.length === 0);
  $("cardsPreview").innerHTML = cards.length ? cards.map(renderCard).join("") : "暂无卡片";
  document.querySelectorAll("[data-card-index]").forEach((input) => {
    input.addEventListener("change", (event) => {
      const index = Number(event.target.dataset.cardIndex);
      state.cards[index].selected = event.target.checked;
    });
  });
}

function renderCard(card, index) {
  return `
    <label class="card-item">
      <input type="checkbox" data-card-index="${index}" ${card.selected === false ? "" : "checked"} />
      <div>
        <p class="card-face"><strong>Front：</strong>${escapeHtml(card.front)}</p>
        <p class="card-face"><strong>Back：</strong>${escapeHtml(card.back)}</p>
        <p class="muted-text">${escapeHtml(card.deck || "")}</p>
      </div>
    </label>
  `;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

$("captureForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = $("captureBtn");
  setBusy(button, true);
  try {
    const payload = formPayload(event.currentTarget);
    const result = await api("/api/capture", { method: "POST", body: JSON.stringify(payload) });
    state.sourcePath = result.source_path;
    $("sourcePath").textContent = result.source_path;
    $("processBtn").disabled = false;
    toast("原始材料已保存");
  } catch (error) {
    toast(error.message);
  } finally {
    setBusy(button, false);
  }
});

$("processBtn").addEventListener("click", async () => {
  if (!state.sourcePath) return;
  const button = $("processBtn");
  setBusy(button, true);
  try {
    const result = await api("/api/process", {
      method: "POST",
      body: JSON.stringify({ source_path: state.sourcePath, write_notes: false }),
    });
    renderAnalysis(result);
    toast("AI 分析已完成");
  } catch (error) {
    toast(error.message);
  } finally {
    setBusy(button, false);
  }
});

$("writeBtn").addEventListener("click", async () => {
  if (!state.sourcePath || !state.analysis) return;
  const button = $("writeBtn");
  setBusy(button, true);
  try {
    const result = await api("/api/process/write", {
      method: "POST",
      body: JSON.stringify({ source_path: state.sourcePath, analysis: state.analysis }),
    });
    renderAnalysis(result);
    $("writeBtn").disabled = true;
    toast(`已写入 ${result.note_paths.length} 篇 Note`);
  } catch (error) {
    toast(error.message);
  } finally {
    setBusy(button, false);
  }
});

$("syncBtn").addEventListener("click", async () => {
  const button = $("syncBtn");
  setBusy(button, true);
  try {
    const result = await api("/api/anki/sync", {
      method: "POST",
      body: JSON.stringify({ cards: state.cards }),
    });
    toast(`同步 ${result.synced} 张，跳过重复 ${result.skipped_duplicates} 张`);
    await refreshStatus();
  } catch (error) {
    toast(error.message);
  } finally {
    setBusy(button, false);
  }
});

$("weeklyBtn").addEventListener("click", () => createReview("weekly"));
$("monthlyBtn").addEventListener("click", () => createReview("monthly"));
$("statusBtn").addEventListener("click", refreshStatus);
$("cloudObsidianBtn").addEventListener("click", () =>
  runCloudPull($("cloudObsidianBtn"), { process_ai: false, sync_anki: false }, "已拉取到 Obsidian")
);
$("cloudAiBtn").addEventListener("click", () =>
  runCloudPull($("cloudAiBtn"), { process_ai: true, sync_anki: false }, "已拉取并写入笔记")
);
$("cloudFullBtn").addEventListener("click", () =>
  runCloudPull($("cloudFullBtn"), { process_ai: true, sync_anki: true }, "已完整同步")
);

async function createReview(kind) {
  const button = kind === "weekly" ? $("weeklyBtn") : $("monthlyBtn");
  setBusy(button, true);
  try {
    const result = await api(`/api/review/${kind}`, { method: "POST", body: "{}" });
    $("reviewPath").textContent = result.path;
    toast(kind === "weekly" ? "周复盘已生成" : "月复盘已生成");
  } catch (error) {
    toast(error.message);
  } finally {
    setBusy(button, false);
  }
}

refreshStatus();
