/* Experiment dashboard client */

const STAGES = [
  "clarifying",
  "planning",
  "retrieving",
  "searching",
  "writing",
  "evaluating",
  "awaiting_approval",
  "completed",
];

const STAGE_ALIASES = {
  started: null,
  clarifying: "clarifying",
  clarified: "clarifying",
  awaiting_clarification: "clarifying",
  planning: "planning",
  planned: "planning",
  retrieving: "retrieving",
  retrieved: "retrieving",
  searching: "searching",
  searched: "searching",
  writing: "writing",
  drafted: "writing",
  evaluating: "evaluating",
  evaluated: "evaluating",
  refining: "evaluating",
  awaiting_approval: "awaiting_approval",
  completed: "completed",
  rejected: "completed",
  crashed: null,
  error: null,
};

const state = {
  sessionId: null,
  source: null,
  sides: {
    without: { status: "idle", tokens: 0, maxStage: -1, crashed: false },
    with: { status: "idle", tokens: 0, maxStage: -1, crashed: false },
  },
};

const $ = (id) => document.getElementById(id);

function initPipelines() {
  for (const side of ["without", "with"]) {
    const ol = $(side === "without" ? "pipeWithout" : "pipeWith");
    ol.innerHTML = "";
    for (const stage of STAGES) {
      const li = document.createElement("li");
      li.dataset.stage = stage;
      li.innerHTML = `<span class="step-name">${stage.replaceAll("_", " ")}</span>`;
      ol.appendChild(li);
    }
  }
}

function setModeHint() {
  const mode = $("mode").value;
  const live = $("liveControls");
  const crashField = $("crashAtField");
  const crashAt = $("crashAt") ? $("crashAt").value : "writing";
  if (mode === "live") {
    live.classList.remove("hidden");
    if (crashField) crashField.classList.add("hidden");
    $("modeHint").textContent =
      "Live: real agents. Needs Temporal server + worker. Crash/Resume acts on the non-Temporal side.";
  } else {
    live.classList.add("hidden");
    if (crashField) crashField.classList.remove("hidden");
    $("modeHint").textContent =
      `Showcase: scripted crash mid-${crashAt}. No API keys or Temporal server.`;
  }
}

function resetSide(side) {
  state.sides[side] = { status: "idle", tokens: 0, maxStage: -1, crashed: false };
  const suffix = side === "without" ? "Without" : "With";
  $(`status${suffix}`).textContent = "idle";
  $(`status${suffix}`).className = "status-chip" + (side === "with" ? " good" : "");
  $(`tokens${suffix}`).textContent = "0";
  $(`run${suffix}`).textContent = "-";
  $(`events${suffix}`).innerHTML = "";
  $(`reportPanel${suffix}`).classList.add("hidden");
  $(`report${suffix}`).textContent = "";
  $(`eval${suffix}`).textContent = "";
  updatePipeline(side, "idle");
}

function updatePipeline(side, status) {
  const ol = $(side === "without" ? "pipeWithout" : "pipeWith");
  const mapped = STAGE_ALIASES[status] ?? null;
  const sideState = state.sides[side];

  if (status === "crashed") {
    sideState.crashed = true;
    for (const li of ol.querySelectorAll("li")) {
      li.classList.remove("current");
    }
    // Mark the stage after max completed as lost/in-flight
    const idx = Math.min(sideState.maxStage + 1, STAGES.length - 1);
    const target = ol.querySelectorAll("li")[idx];
    if (target) {
      target.classList.add("lost");
      target.classList.add("current");
    }
    return;
  }

  if (mapped) {
    const idx = STAGES.indexOf(mapped);
    if (idx > sideState.maxStage && status !== "crashed") {
      // advancing
    }
    // completed stages: any stage before current is done; current is current
    // if status is a terminal alias like drafted, treat that stage as done
    const terminal = [
      "clarified",
      "planned",
      "retrieved",
      "searched",
      "drafted",
      "evaluated",
      "completed",
    ].includes(status);

    if (terminal && idx >= sideState.maxStage) {
      sideState.maxStage = idx;
    } else if (!terminal && idx >= 0) {
      // in-progress — don't advance max yet beyond previous
    }

    for (const li of ol.querySelectorAll("li")) {
      const s = li.dataset.stage;
      const i = STAGES.indexOf(s);
      li.classList.remove("current", "done", "lost");
      if (sideState.crashed && i > sideState.maxStage) {
        // leave uncleared after crash until recovery
      }
      if (i < sideState.maxStage || (terminal && i === idx)) {
        li.classList.add("done");
      } else if (i === idx && !terminal) {
        li.classList.add("current");
      } else if (i === idx && terminal) {
        li.classList.add("done");
      }
      if (status === "completed" && i <= idx) {
        li.classList.add("done");
        li.classList.remove("current");
      }
    }

    if (!terminal && idx >= 0) {
      const li = ol.querySelector(`li[data-stage="${mapped}"]`);
      if (li) {
        li.classList.add("current");
        li.classList.remove("lost");
      }
    }

    if (status === "completed") {
      sideState.maxStage = STAGES.length - 1;
      for (const li of ol.querySelectorAll("li")) {
        li.classList.add("done");
        li.classList.remove("current", "lost");
      }
    }
  }
}

function chipClass(status) {
  if (status === "crashed" || status === "error" || status === "rejected") return "status-chip bad";
  if (status === "completed") return "status-chip good";
  if (status === "awaiting_approval" || status === "awaiting_clarification") return "status-chip warn";
  if (status && status !== "idle") return "status-chip active";
  return "status-chip";
}

function formatTokens(n) {
  return Number(n || 0).toLocaleString();
}

function appendEvent(side, event) {
  const box = $(side === "without" ? "eventsWithout" : "eventsWith");
  const div = document.createElement("div");
  const type = event.type || "event";
  div.className = `event ${type}`;
  const msg = event.message || JSON.stringify(event);
  div.innerHTML = `<span class="etype">[${type}]</span>${escapeHtml(msg)}`;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function applySideEvent(side, event) {
  const suffix = side === "without" ? "Without" : "With";
  const sideState = state.sides[side];

  if (event.run_id) {
    $(`run${suffix}`).textContent = String(event.run_id).slice(0, 18);
  }

  if (event.tokens && typeof event.tokens.total_tokens === "number") {
    sideState.tokens = event.tokens.total_tokens;
    $(`tokens${suffix}`).textContent = formatTokens(sideState.tokens);
  }

  if (event.status) {
    sideState.status = event.status;
    const chip = $(`status${suffix}`);
    chip.textContent = event.status;
    chip.className = chipClass(event.status);
    if (event.type === "recovered") {
      sideState.crashed = false;
    }
    updatePipeline(side, event.status);
  } else if (event.type === "crashed") {
    sideState.status = "crashed";
    sideState.crashed = true;
    const chip = $(`status${suffix}`);
    chip.textContent = "crashed";
    chip.className = chipClass("crashed");
    updatePipeline(side, "crashed");
  }

  if (event.type && event.type !== "ping" && event.type !== "snapshot") {
    appendEvent(side, event);
  }

  if (event.type === "completed" || event.report || event.evaluation) {
    if (event.report || event.evaluation) {
      $(`reportPanel${suffix}`).classList.remove("hidden");
    }
    if (event.evaluation) {
      const e = event.evaluation;
      $(`eval${suffix}`).textContent =
        `faithfulness=${num(e.faithfulness)}  relevance=${num(e.relevance)}  overall=${num(e.overall)}`;
    }
    if (event.report) {
      $(`report${suffix}`).textContent = event.report;
    }
  }

  // Live token bar preview even before comparison
  updateLiveBars();
}

function num(v) {
  if (v == null || Number.isNaN(Number(v))) return "-";
  return Number(v).toFixed(2);
}

function updateLiveBars() {
  const a = state.sides.without.tokens || 0;
  const b = state.sides.with.tokens || 0;
  const max = Math.max(a, b, 1);
  $("barWithout").style.width = `${(a / max) * 100}%`;
  $("barWith").style.width = `${(b / max) * 100}%`;
  $("barWithoutLabel").textContent = formatTokens(a);
  $("barWithLabel").textContent = formatTokens(b);
}

function showComparison(comparison) {
  if (!comparison) return;
  $("comparison").classList.remove("hidden");
  $("comparisonHeadline").textContent = comparison.headline || "";
  const ul = $("comparisonBullets");
  ul.innerHTML = "";
  for (const b of comparison.bullets || []) {
    const li = document.createElement("li");
    li.textContent = b;
    ul.appendChild(li);
  }
  const a = comparison.without_tokens || state.sides.without.tokens || 0;
  const b = comparison.with_tokens || state.sides.with.tokens || 0;
  const waste = comparison.wasted_tokens ?? Math.max(0, a - b);
  let pct = comparison.savings_percent;
  if (pct == null || Number.isNaN(Number(pct))) {
    pct = a > 0 ? Math.round((1000 * waste) / a) / 10 : 0;
  }
  const pctLabel = Number(pct).toLocaleString(undefined, {
    maximumFractionDigits: 1,
  });
  $("wastePill").textContent =
    `Temporal saved ~${formatTokens(waste)} tokens · ${pctLabel}%`;
  const max = Math.max(a, b, 1);
  $("barWithout").style.width = `${(a / max) * 100}%`;
  $("barWith").style.width = `${(b / max) * 100}%`;
  $("barWithoutLabel").textContent = formatTokens(a);
  $("barWithLabel").textContent = formatTokens(b);

  const reRan = comparison.re_executed || [];
  const reBlock = $("reRanBlock");
  const reList = $("reRanList");
  const reTotal = $("reRanTotal");
  if (reRan.length) {
    reBlock.classList.remove("hidden");
    reList.innerHTML = "";
    for (const item of reRan) {
      const li = document.createElement("li");
      const step = item.step || "?";
      const tok = Number(item.tokens || 0);
      const reason = item.reason ? ` — ${item.reason}` : "";
      li.textContent = `${step}: +${formatTokens(tok)} tokens${reason}`;
      reList.appendChild(li);
    }
    const reTok =
      comparison.re_executed_tokens ??
      reRan.reduce((s, x) => s + Number(x.tokens || 0), 0);
    reTotal.textContent = `Re-paid after resume: ${formatTokens(reTok)} tokens`;
  } else {
    reBlock.classList.add("hidden");
    reList.innerHTML = "";
    reTotal.textContent = "";
  }
}

function handleEvent(event) {
  if (!event || event.type === "ping") return;

  if (event.type === "snapshot" && event.snapshot) {
    const snap = event.snapshot;
    applySnapshot(snap);
    return;
  }

  if (event.type === "comparison" || event.comparison) {
    showComparison(event.comparison || event);
  }

  if (event.side === "without") {
    applySideEvent("without", event);
  } else if (event.side === "with" || event.side === "with_temporal" || event.side === "temporal") {
    applySideEvent("with", event);
  } else if (event.side === "system") {
    // show system messages on both lightly? keep session meta
    if (event.message) {
      $("sessionMeta").textContent = event.message;
    }
  }
}

function applySnapshot(snap) {
  $("sessionMeta").textContent = `session ${snap.session_id} · ${snap.mode}`;
  for (const side of ["without", "with"]) {
    const data = side === "without" ? snap.without : snap.with;
    if (!data) continue;
    const suffix = side === "without" ? "Without" : "With";
    state.sides[side].tokens = (data.tokens && data.tokens.total_tokens) || 0;
    state.sides[side].status = data.status || "idle";
    state.sides[side].crashed = !!data.crashed;
    $(`tokens${suffix}`).textContent = formatTokens(state.sides[side].tokens);
    $(`status${suffix}`).textContent = data.status || "idle";
    $(`status${suffix}`).className = chipClass(data.status || "idle");
    if (data.run_id) $(`run${suffix}`).textContent = String(data.run_id).slice(0, 18);
    updatePipeline(side, data.status || "idle");
    const box = $(`events${suffix}`);
    box.innerHTML = "";
    for (const ev of data.events || []) {
      appendEvent(side, ev);
      if (ev.status) {
        // rebuild max stage from history
        const mapped = STAGE_ALIASES[ev.status];
        if (mapped) {
          const idx = STAGES.indexOf(mapped);
          const terminal = [
            "clarified", "planned", "retrieved", "searched",
            "drafted", "evaluated", "completed",
          ].includes(ev.status);
          if (terminal && idx > state.sides[side].maxStage) {
            state.sides[side].maxStage = idx;
          }
        }
      }
    }
    updatePipeline(side, data.status || "idle");
    if (data.report || data.evaluation) {
      $(`reportPanel${suffix}`).classList.remove("hidden");
      if (data.evaluation) {
        const e = data.evaluation;
        $(`eval${suffix}`).textContent =
          `faithfulness=${num(e.faithfulness)}  relevance=${num(e.relevance)}  overall=${num(e.overall)}`;
      }
      if (data.report) $(`report${suffix}`).textContent = data.report;
    }
  }
  if (snap.comparison && Object.keys(snap.comparison).length) {
    showComparison(snap.comparison);
  }
  updateLiveBars();
}

async function startSession() {
  await stopSession(false);
  resetSide("without");
  resetSide("with");
  $("comparison").classList.add("hidden");

  const body = {
    query: $("query").value.trim(),
    mode: $("mode").value,
    auto_approve: $("autoApprove").checked,
    pace: Number($("pace").value),
    crash_at: $("crashAt") ? $("crashAt").value : "writing",
    sides: "both",
  };

  $("btnStart").disabled = true;
  $("btnStop").disabled = false;
  $("sessionMeta").textContent = "starting…";

  const res = await fetch("/api/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    $("sessionMeta").textContent = `failed to start (${res.status})`;
    $("btnStart").disabled = false;
    $("btnStop").disabled = true;
    return;
  }
  const snap = await res.json();
  state.sessionId = snap.session_id;
  applySnapshot(snap);
  openEventStream(snap.session_id);
  $("btnStart").disabled = false;
}

function openEventStream(sessionId) {
  if (state.source) {
    state.source.close();
    state.source = null;
  }
  const es = new EventSource(`/api/sessions/${sessionId}/events`);
  state.source = es;
  es.onmessage = (msg) => {
    try {
      const data = JSON.parse(msg.data);
      handleEvent(data);
    } catch (err) {
      console.warn("bad event", err);
    }
  };
  es.onerror = () => {
    // browser will retry; leave meta alone
  };
}

async function stopSession(resetButtons = true) {
  if (state.source) {
    state.source.close();
    state.source = null;
  }
  if (state.sessionId) {
    try {
      await fetch(`/api/sessions/${state.sessionId}`, { method: "DELETE" });
    } catch (_) {
      /* ignore */
    }
    state.sessionId = null;
  }
  if (resetButtons) {
    $("btnStop").disabled = true;
    $("sessionMeta").textContent = "No active session";
  }
}

async function postAction(path) {
  if (!state.sessionId) return;
  const res = await fetch(`/api/sessions/${state.sessionId}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision: "approved" }),
  });
  if (!res.ok) {
    const text = await res.text();
    $("sessionMeta").textContent = `action failed: ${text}`;
  }
}

function wire() {
  initPipelines();
  setModeHint();
  $("mode").addEventListener("change", setModeHint);
  if ($("crashAt")) {
    $("crashAt").addEventListener("change", setModeHint);
  }
  $("btnStart").addEventListener("click", () => startSession());
  $("btnStop").addEventListener("click", () => stopSession(true));
  $("btnCrash").addEventListener("click", () => postAction("/crash/without"));
  $("btnResume").addEventListener("click", () => postAction("/resume/without"));
  $("btnApproveWithout").addEventListener("click", () => postAction("/approve/without"));
  $("btnApproveWith").addEventListener("click", () => postAction("/approve/with"));
}

wire();
