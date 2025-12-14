const els = {
  url: document.getElementById("url"),
  run: document.getElementById("run"),
  forceRun: document.getElementById("forceRun"),

  langDropdown: document.getElementById("langDropdown"),
  langButton: document.getElementById("langButton"),
  langMenu: document.getElementById("langMenu"),
  langSearch: document.getElementById("langSearch"),
  langList: document.getElementById("langList"),
  langLabel: document.getElementById("langLabel"),

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
let lastSubmittedUrl = "";

function setHidden(el, hidden) {
  if (hidden) el.classList.add("hidden");
  else el.classList.remove("hidden");
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

function renderResult(job) {
  setHidden(els.resultCard, false);

  const score = Number(job.report?.overall_score ?? 0);
  els.scorePct.textContent = `${Math.max(0, Math.min(100, score))}%`;
  els.scoreCircle.style.setProperty("--pct", String(Math.max(0, Math.min(100, score))));
  let color = "#2ee59d";
  if (score < 50) color = "var(--danger)";
  else if (score < 80) color = "#ffd24a";
  els.scoreCircle.style.setProperty("--score-color", color);

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

  const dangers = (job.report?.danger || []).map((d) => {
    const sev = typeof d.severity === "number" ? ` (severity ${d.severity}/5)` : "";
    return `${d.category}${sev}: ${d.description}`;
  });
  setList(els.dangerList, dangers);

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

async function runAnalysis({ force }) {
  const url = els.url.value.trim();
  if (!url) return;
  lastSubmittedUrl = url;

  els.run.disabled = true;
  setHidden(els.statusCard, false);
  setHidden(els.resultCard, true);
  setHidden(els.errorBox, true);
  setHidden(els.infoBox, true);
  els.statusText.textContent = "queued";
  setProgress(0);

  try {
    const { job_id, cached } = await postJson("/api/analyze", {
      url,
      output_language: selectedLanguage.code,
      force: Boolean(force),
    });
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
