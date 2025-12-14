const els = {
  apiKey: document.getElementById("apiKey"),
  apiKeyLabel: document.getElementById("apiKeyLabel"),
  apiKeyHelp: document.getElementById("apiKeyHelp"),
  
  providerDropdown: document.getElementById("providerDropdown"),
  providerButton: document.getElementById("providerButton"),
  providerMenu: document.getElementById("providerMenu"),
  providerLabel: document.getElementById("providerLabel"),

  url: document.getElementById("url"),
  run: document.getElementById("run"),
  forceRun: document.getElementById("forceRun"),

  langDropdown: document.getElementById("langDropdown"),
  langButton: document.getElementById("langButton"),
  langMenu: document.getElementById("langMenu"),
  langSearch: document.getElementById("langSearch"),
  langList: document.getElementById("langList"),
  langLabel: document.getElementById("langLabel"),

  historyToggle: document.getElementById("historyToggle"),
  historyCard: document.getElementById("historyCard"),
  historyRefresh: document.getElementById("historyRefresh"),
  historyList: document.getElementById("historyList"),

  statusCard: document.getElementById("statusCard"),
  statusText: document.getElementById("statusText"),
  progressPill: document.getElementById("progressPill"),
  progressBar: document.getElementById("progressBar"),
  infoBox: document.getElementById("infoBox"),
  errorBox: document.getElementById("errorBox"),
  resultCard: document.getElementById("resultCard"),
  scoreCircle: document.getElementById("scoreCircle"),
  scorePct: document.getElementById("scorePct"),
  verdictText: document.getElementById("verdictText"),
  generatedAt: document.getElementById("generatedAt"),
  rerunBtn: document.getElementById("rerunBtn"),
  reportSummary: document.getElementById("reportSummary"),
  whatsRight: document.getElementById("whatsRight"),
  whatsWrong: document.getElementById("whatsWrong"),
  dangerList: document.getElementById("dangerList"),
  sourcesList: document.getElementById("sourcesList"),
  claimsJson: document.getElementById("claimsJson"),
  transcript: document.getElementById("transcript"),
};

const LANGUAGES_PINNED = [
  { code: "ar", name: "Arabic" },
  { code: "en", name: "English" },
  { code: "fr", name: "French" },
];

const LANGUAGES_OTHERS = [
  { code: "bn", name: "Bengali" },
  { code: "zh", name: "Chinese" },
  { code: "cs", name: "Czech" },
  { code: "da", name: "Danish" },
  { code: "nl", name: "Dutch" },
  { code: "fi", name: "Finnish" },
  { code: "de", name: "German" },
  { code: "el", name: "Greek" },
  { code: "he", name: "Hebrew" },
  { code: "hi", name: "Hindi" },
  { code: "hu", name: "Hungarian" },
  { code: "id", name: "Indonesian" },
  { code: "it", name: "Italian" },
  { code: "ja", name: "Japanese" },
  { code: "ko", name: "Korean" },
  { code: "ms", name: "Malay" },
  { code: "no", name: "Norwegian" },
  { code: "fa", name: "Persian" },
  { code: "pl", name: "Polish" },
  { code: "pt", name: "Portuguese" },
  { code: "ro", name: "Romanian" },
  { code: "ru", name: "Russian" },
  { code: "es", name: "Spanish" },
  { code: "sw", name: "Swahili" },
  { code: "sv", name: "Swedish" },
  { code: "tl", name: "Filipino (Tagalog)" },
  { code: "th", name: "Thai" },
  { code: "tr", name: "Turkish" },
  { code: "uk", name: "Ukrainian" },
  { code: "ur", name: "Urdu" },
  { code: "vi", name: "Vietnamese" },
].sort((a, b) => a.name.localeCompare(b.name));

const LANGUAGES = [...LANGUAGES_PINNED, ...LANGUAGES_OTHERS];

let selectedLanguage = LANGUAGES[0];
let selectedProvider = "gemini";
let lastSubmittedUrl = "";
let currentReportLanguage = null;

const PROVIDERS = {
  gemini: { name: "Gemini", label: "Gemini API Key *", help: '🔑 <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color: var(--accent);">Get free Gemini API key</a>' },
  openai: { name: "OpenAI", label: "OpenAI API Key *", help: '🔑 <a href="https://platform.openai.com/api-keys" target="_blank" style="color: var(--accent);">Get OpenAI API key</a>' },
  deepseek: { name: "DeepSeek", label: "DeepSeek API Key *", help: '🔑 <a href="https://platform.deepseek.com/api_keys" target="_blank" style="color: var(--accent);">Get DeepSeek API key</a>' },
};

const RTL_LANGS = new Set(["ar", "fa", "he", "ur"]);

function setHidden(el, hidden) {
  if (hidden) el.classList.add("hidden");
  else el.classList.remove("hidden");
}

function setText(el, text) {
  if (!el) return;
  el.textContent = text ?? "";
}

function isRtlLanguage(code) {
  return RTL_LANGS.has(String(code || "").toLowerCase());
}

// --- Provider Dropdown ---
if (els.providerButton && els.providerMenu) {
  els.providerButton.addEventListener("click", (e) => {
    e.stopPropagation();
    els.providerMenu.classList.toggle("hidden");
  });

  els.providerMenu.addEventListener("click", (e) => {
    const item = e.target.closest(".dropdownItem");
    if (!item) return;
    const val = item.dataset.value;
    if (val && PROVIDERS[val]) {
      selectedProvider = val;
      els.providerLabel.textContent = PROVIDERS[val].name;
      els.apiKeyLabel.textContent = PROVIDERS[val].label;
      els.apiKeyHelp.innerHTML = PROVIDERS[val].help;
      els.providerMenu.classList.add("hidden");
    }
  });

  document.addEventListener("click", (e) => {
    if (!els.providerDropdown.contains(e.target)) {
      els.providerMenu.classList.add("hidden");
    }
  });
}
// -------------------------

function applyOutputDirection() {
  const lang = String(currentReportLanguage || selectedLanguage?.code || "en").toLowerCase();
  const dir = isRtlLanguage(lang) ? "rtl" : "ltr";

  // AI-generated (human-readable) fields: set explicit direction by chosen output language.
  const outputEls = [els.reportSummary, els.whatsRight, els.whatsWrong, els.dangerList];
  for (const el of outputEls) {
    if (!el) continue;
    el.setAttribute("dir", dir);
    el.setAttribute("lang", lang);
  }

  // Mixed/structured blocks: keep readable in any locale.
  if (els.sourcesList) els.sourcesList.setAttribute("dir", "auto");
  if (els.transcript) els.transcript.setAttribute("dir", "auto");
  if (els.claimsJson) els.claimsJson.setAttribute("dir", "ltr");
}

function setProgress(pct) {
  els.progressPill.textContent = `${pct}%`;
  els.progressBar.style.width = `${pct}%`;
}

function setList(ul, items) {
  ul.innerHTML = "";
  for (const item of items || []) {
    const li = document.createElement("li");
    li.textContent = item;
    ul.appendChild(li);
  }
}

function setDangerList(ul, items) {
  ul.innerHTML = "";
  for (const d of items || []) {
    const li = document.createElement("li");

    const head = document.createElement("bdi");
    head.setAttribute("dir", "ltr");
    const sev =
      typeof d.severity === "number" && Number.isFinite(d.severity) ? ` (severity ${d.severity}/5)` : "";
    head.textContent = `${d.category || "other"}${sev}`;

    const sep = document.createElement("span");
    sep.textContent = ": ";

    const body = document.createElement("span");
    body.textContent = d.description || "";

    li.appendChild(head);
    li.appendChild(sep);
    li.appendChild(body);
    ul.appendChild(li);
  }
}

function setSources(ul, sources) {
  ul.innerHTML = "";
  for (const s of sources || []) {
    const li = document.createElement("li");
    const a = document.createElement("a");
    const pub = s.publisher ? `${s.publisher} — ` : "";
    a.href = s.url;
    a.target = "_blank";
    a.rel = "noreferrer";
    a.textContent = `${pub}${s.title}`;
    li.appendChild(a);
    ul.appendChild(li);
  }
}

async function postJson(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || `Request failed (${res.status})`);
  }
  return data;
}

async function getJson(url) {
  const res = await fetch(url);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || `Request failed (${res.status})`);
  }
  return data;
}

async function pollJob(jobId) {
  while (true) {
    const job = await getJson(`/api/jobs/${jobId}`);
    els.statusText.textContent = job.status;
    setProgress(job.progress);

    if (job.status === "failed") {
      setHidden(els.errorBox, false);
      els.errorBox.textContent = job.error || "Unknown error.";
      setHidden(els.resultCard, true);
      return;
    }

    if (job.status === "completed") {
      setHidden(els.errorBox, true);
      renderResult(job);
      return;
    }

    await new Promise((r) => setTimeout(r, 2000));
  }
}

function humanizeEnum(value) {
  if (!value) return "";
  return String(value)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function scoreColor(score) {
  const s = Number(score ?? 0);
  if (s < 50) return "var(--danger)";
  if (s < 80) return "#ffd24a";
  return "#2ee59d";
}

function renderResult(job) {
  setHidden(els.resultCard, false);
  currentReportLanguage = job.output_language || currentReportLanguage || selectedLanguage.code;
  applyOutputDirection();

  const score = Number(job.report?.overall_score ?? 0);
  els.scorePct.textContent = `${Math.max(0, Math.min(100, score))}%`;
  els.scoreCircle.style.setProperty("--pct", String(Math.max(0, Math.min(100, score))));
  els.scoreCircle.style.setProperty("--score-color", scoreColor(score));

  const verdict = humanizeEnum(job.report?.overall_verdict);
  els.verdictText.textContent = verdict ? `Overall: ${verdict}` : "";

  const generated = job.report?.generated_at;
  if (generated) {
    const d = new Date(generated);
    els.generatedAt.textContent = Number.isNaN(d.getTime()) ? String(generated) : d.toLocaleString();
  } else {
    els.generatedAt.textContent = "";
  }

  els.reportSummary.textContent = job.report?.summary || "";
  setList(els.whatsRight, job.report?.whats_right || []);
  setList(els.whatsWrong, job.report?.whats_wrong || []);

  setDangerList(els.dangerList, job.report?.danger || []);

  setSources(els.sourcesList, job.report?.sources_used || []);

  els.claimsJson.textContent = JSON.stringify(job.report?.claims || [], null, 2);
  els.transcript.textContent = job.transcript || "";
}

function openLangMenu() {
  setHidden(els.langMenu, false);
  els.langSearch.value = "";
  renderLangList("");
  els.langSearch.focus();
}

function closeLangMenu() {
  setHidden(els.langMenu, true);
}

function renderLangList(filter) {
  const q = (filter || "").trim().toLowerCase();
  const items = LANGUAGES.filter((l) => {
    if (!q) return true;
    return l.name.toLowerCase().includes(q) || l.code.toLowerCase().includes(q);
  });

  els.langList.innerHTML = "";
  for (const l of items) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "dropdownItem";
    btn.innerHTML = `${l.name} <span class="code">(${l.code})</span>`;
    btn.addEventListener("click", () => {
      selectedLanguage = l;
      els.langLabel.textContent = l.name;
      closeLangMenu();
    });
    els.langList.appendChild(btn);
  }
}

els.langButton.addEventListener("click", () => {
  const isOpen = !els.langMenu.classList.contains("hidden");
  if (isOpen) closeLangMenu();
  else openLangMenu();
});

els.langSearch.addEventListener("input", (e) => renderLangList(e.target.value));

document.addEventListener("click", (e) => {
  if (!els.langDropdown.contains(e.target)) closeLangMenu();
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeLangMenu();
});

function setSelectedLanguageByCode(code) {
  const c = String(code || "").toLowerCase();
  const match = LANGUAGES.find((l) => l.code === c);
  if (match) {
    selectedLanguage = match;
    setText(els.langLabel, match.name);
  }
}

function formatWhen(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? String(iso) : d.toLocaleString();
}

function renderHistory(items) {
  els.historyList.innerHTML = "";
  if (!items || items.length === 0) {
    const empty = document.createElement("div");
    empty.className = "muted small";
    empty.textContent = "No analyses yet.";
    els.historyList.appendChild(empty);
    return;
  }

  for (const item of items) {
    const row = document.createElement("div");
    row.className = "historyItem";

    const score = typeof item.overall_score === "number" ? item.overall_score : null;
    const scoreEl = document.createElement("div");
    scoreEl.className = "historyScore";
    if (score !== null) {
      scoreEl.style.color = scoreColor(score);
      scoreEl.textContent = `${score}%`;
    } else {
      scoreEl.style.color = "var(--muted)";
      scoreEl.textContent = "—";
    }

    const meta = document.createElement("div");
    meta.className = "historyMeta";
    const url = document.createElement("div");
    url.className = "historyUrl";
    url.textContent = item.url || "";
    const sub = document.createElement("div");
    sub.className = "historySub";
    const b1 = document.createElement("span");
    b1.className = "badge";
    b1.textContent = (item.output_language || "ar").toUpperCase();
    const b2 = document.createElement("span");
    b2.className = "badge";
    b2.textContent = item.status || "";
    const b3 = document.createElement("span");
    b3.className = "badge";
    b3.textContent = formatWhen(item.updated_at);
    sub.appendChild(b1);
    sub.appendChild(b2);
    sub.appendChild(b3);
    meta.appendChild(url);
    meta.appendChild(sub);

    const actions = document.createElement("div");
    const openBtn = document.createElement("button");
    openBtn.type = "button";
    openBtn.className = "btn btnSecondary";
    openBtn.textContent = "Open";
    openBtn.addEventListener("click", async () => {
      const job = await getJson(`/api/jobs/${item.id}`);
      setHidden(els.errorBox, true);
      setHidden(els.statusCard, true);
      els.url.value = job.url || "";
      lastSubmittedUrl = job.url || "";
      setSelectedLanguageByCode(job.output_language || "ar");
      els.forceRun.checked = false;
      setHidden(els.infoBox, false);
      els.infoBox.textContent = "Loaded from history.";
      renderResult(job);
      setHidden(els.historyCard, true);
    });
    actions.appendChild(openBtn);

    row.appendChild(scoreEl);
    row.appendChild(meta);
    row.appendChild(actions);
    els.historyList.appendChild(row);
  }
}

async function loadHistory() {
  const items = await getJson("/api/history?limit=50");
  renderHistory(items);
}

async function runAnalysis({ force }) {
  const url = els.url.value.trim();
  if (!url) return;
  
  const apiKey = els.apiKey.value.trim();
  if (!apiKey) {
    setHidden(els.statusCard, false);
    setHidden(els.resultCard, true);
    setHidden(els.infoBox, true);
    setHidden(els.errorBox, false);
    const providerInfo = PROVIDERS[selectedProvider] || PROVIDERS.gemini;
    els.errorBox.innerHTML = `Please enter your ${providerInfo.name} API key. ${providerInfo.help}`;
    return;
  }
  
  lastSubmittedUrl = url;

  els.run.disabled = true;
  setHidden(els.statusCard, false);
  setHidden(els.resultCard, true);
  setHidden(els.errorBox, true);
  setHidden(els.infoBox, true);
  els.statusText.textContent = "queued";
  setProgress(0);

  try {
    const payload = {
      url,
      output_language: selectedLanguage.code,
      provider: selectedProvider,
      force: Boolean(force),
      api_key: apiKey
    };
    
    const { job_id, cached } = await postJson("/api/analyze", payload);
    if (cached) {
      setHidden(els.infoBox, false);
      els.infoBox.textContent = "Loaded saved analysis. Enable re-run to refresh.";
    }
    await pollJob(job_id);
  } catch (e) {
    setHidden(els.errorBox, false);
    els.errorBox.textContent = e?.message || String(e);
  } finally {
    els.run.disabled = false;
  }
}

els.run.addEventListener("click", async () => {
  await runAnalysis({ force: els.forceRun.checked });
});

els.rerunBtn.addEventListener("click", async () => {
  if (lastSubmittedUrl) els.url.value = lastSubmittedUrl;
  els.forceRun.checked = true;
  await runAnalysis({ force: true });
});

if (els.historyToggle && els.historyCard) {
  els.historyToggle.addEventListener("click", async () => {
    const isHidden = els.historyCard.classList.contains("hidden");
    setHidden(els.historyCard, !isHidden);
    if (isHidden) {
      await loadHistory();
    }
  });
}

if (els.historyRefresh) {
  els.historyRefresh.addEventListener("click", async () => {
    await loadHistory();
  });
}
