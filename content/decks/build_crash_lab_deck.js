/**
 * Build Durable agents crash lab deck (B&W, matches lab UI / diagram style).
 * Run: node content/decks/build_crash_lab_deck.js
 */
const path = require("path");
const pptxgen = require("/tmp/pptx-build/node_modules/pptxgenjs");

const ROOT = path.resolve(__dirname, "../..");
const ASSETS = path.join(ROOT, "content/assets");
const OUT = path.join(__dirname, "2026-07-31-durable-agents-crash-lab.pptx");

const C = {
  bg: "FFFFFF",
  ink: "1A1A1A",
  muted: "555555",
  faint: "888888",
  fill: "F0F0F0",
  line: "CCCCCC",
  white: "FFFFFF",
};

const font = "Arial";
const mono = "Courier New";

function footer(slide, n, total = 12) {
  slide.addText(`Durable agents crash lab  ·  ${n}/${total}`, {
    x: 0.5,
    y: 5.25,
    w: 7.5,
    h: 0.25,
    fontSize: 10,
    fontFace: font,
    color: C.faint,
    margin: 0,
  });
  slide.addText("github.com/ryanlingo/durable-research-agent", {
    x: 5.5,
    y: 5.25,
    w: 4,
    h: 0.25,
    fontSize: 9,
    fontFace: mono,
    color: C.faint,
    align: "right",
    margin: 0,
  });
}

function titleBar(slide, title) {
  slide.addText(title, {
    x: 0.5,
    y: 0.35,
    w: 9,
    h: 0.55,
    fontSize: 28,
    fontFace: font,
    bold: true,
    color: C.ink,
    margin: 0,
  });
}

function imgFit(slide, rel, x, y, maxW, maxH) {
  const full = path.join(ASSETS, rel);
  // contain-ish: use max box; pptxgen keeps aspect with sizing contain
  slide.addImage({
    path: full,
    x,
    y,
    w: maxW,
    h: maxH,
    sizing: { type: "contain", w: maxW, h: maxH },
  });
}

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "Durable Research Agent";
  pres.title = "Durable agents crash lab";
  pres.subject = "Same research agent twice; crash mid-write; compare tokens";

  // ── 1. Title ──────────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0,
      y: 0,
      w: 0.12,
      h: 5.625,
      fill: { color: C.ink },
      line: { color: C.ink, width: 0 },
    });
    s.addText("DURABLE AGENTS", {
      x: 0.6,
      y: 1.5,
      w: 8.5,
      h: 0.35,
      fontSize: 12,
      fontFace: mono,
      color: C.muted,
      charSpacing: 4,
      margin: 0,
    });
    s.addText("Crash lab", {
      x: 0.6,
      y: 1.95,
      w: 8.5,
      h: 0.8,
      fontSize: 44,
      fontFace: font,
      bold: true,
      color: C.ink,
      margin: 0,
    });
    s.addText("Same research agent. Two control planes. One kill -9.", {
      x: 0.6,
      y: 2.85,
      w: 8.5,
      h: 0.4,
      fontSize: 18,
      fontFace: font,
      color: C.muted,
      margin: 0,
    });
    s.addText("github.com/ryanlingo/durable-research-agent", {
      x: 0.6,
      y: 4.6,
      w: 8.5,
      h: 0.3,
      fontSize: 12,
      fontFace: mono,
      color: C.faint,
      margin: 0,
    });
    s.addNotes(
      "Multi-step agents die when the process dies. Today we measure that with tokens, not slogans."
    );
  }

  // ── 2. Failure ────────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    titleBar(s, "The failure we care about");
    s.addText("Process dies mid-write: deploy, OOM, laptop sleep.", {
      x: 0.5,
      y: 1.05,
      w: 9,
      h: 0.35,
      fontSize: 16,
      fontFace: font,
      color: C.muted,
      margin: 0,
    });

    const cards = [
      { t: "What is lost?", d: "In-flight LLM result" },
      { t: "What is re-paid?", d: "Plan, write, judge…" },
      { t: "What is reused?", d: "Completed work, or not" },
    ];
    cards.forEach((c, i) => {
      const x = 0.5 + i * 3.1;
      s.addShape(pres.shapes.RECTANGLE, {
        x,
        y: 1.7,
        w: 2.9,
        h: 2.2,
        fill: { color: C.fill },
        line: { color: C.ink, width: 1 },
      });
      s.addText(c.t, {
        x: x + 0.2,
        y: 2.0,
        w: 2.5,
        h: 0.5,
        fontSize: 16,
        fontFace: font,
        bold: true,
        color: C.ink,
        margin: 0,
      });
      s.addText(c.d, {
        x: x + 0.2,
        y: 2.7,
        w: 2.5,
        h: 0.8,
        fontSize: 15,
        fontFace: font,
        color: C.muted,
        margin: 0,
      });
    });
    s.addText(
      "Retries fix bad HTTP. They do not fix process death.",
      {
        x: 0.5,
        y: 4.2,
        w: 9,
        h: 0.35,
        fontSize: 14,
        fontFace: font,
        italic: true,
        color: C.ink,
        margin: 0,
      }
    );
    footer(s, 2);
    s.addNotes(
      "Checkpoints help only as far as the recovery code you maintain."
    );
  }

  // ── 3. Two stacks ─────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    titleBar(s, "Same agent, two stacks");
    s.addTable(
      [
        [
          { text: "", options: { fill: { color: C.fill } } },
          {
            text: "Typical stack",
            options: { fill: { color: C.fill }, bold: true, color: C.ink },
          },
          {
            text: "Temporal",
            options: { fill: { color: C.fill }, bold: true, color: C.ink },
          },
        ],
        ["Control flow", "asyncio", "Workflow Execution"],
        ["Retries", "tenacity", "Activity Retry Policy"],
        ["State after crash", "SQLite you maintain", "Event History"],
        ["Human approval", "poll a DB row", "Signal"],
      ],
      {
        x: 0.5,
        y: 1.15,
        w: 9,
        colW: [2.2, 3.4, 3.4],
        border: { pt: 0.75, color: C.line },
        fontFace: font,
        fontSize: 13,
        color: C.ink,
        align: "left",
        valign: "middle",
      }
    );
    s.addText(
      "Shared: tools, prompts, RAG corpus, judge, token counters. Only orchestration changes.",
      {
        x: 0.5,
        y: 4.35,
        w: 9,
        h: 0.4,
        fontSize: 14,
        fontFace: font,
        color: C.muted,
        margin: 0,
      }
    );
    footer(s, 3);
    s.addNotes(
      "If tokens diverge after a crash, that is the control plane, not a different model."
    );
  }

  // ── 4. Pipeline ───────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    titleBar(s, "Pipeline (shared brain)");
    s.addText(
      "clarify → plan → retrieve → search (parallel) → write → evaluate → approve",
      {
        x: 0.5,
        y: 1.05,
        w: 9,
        h: 0.4,
        fontSize: 14,
        fontFace: mono,
        color: C.ink,
        margin: 0,
      }
    );
    imgFit(s, "diagrams/06-pipeline-linear.png", 0.5, 1.6, 9, 2.8);
    s.addText(
      "Search is parallel on both sides on purpose (fair comparison).",
      {
        x: 0.5,
        y: 4.55,
        w: 9,
        h: 0.3,
        fontSize: 13,
        fontFace: font,
        color: C.muted,
        margin: 0,
      }
    );
    footer(s, 4);
    s.addNotes(
      "Ordinary agent work. If durability is messy here, it is messier in a larger system."
    );
  }

  // ── 5. Architecture ───────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    titleBar(s, "Architecture");
    imgFit(s, "diagrams/02-shared-brain-two-runtimes.png", 0.4, 1.0, 9.2, 3.6);
    s.addText(
      "Everything above the split is the experimental control. Below it is the product decision.",
      {
        x: 0.5,
        y: 4.7,
        w: 9,
        h: 0.3,
        fontSize: 13,
        fontFace: font,
        color: C.muted,
        margin: 0,
      }
    );
    footer(s, 5);
    s.addNotes(
      "Shared agent logic above. without_temporal left. with_temporal right."
    );
  }

  // ── 6. Demo ───────────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    titleBar(s, "Demo: Showcase");
    s.addText(
      [
        { text: "Mode: Showcase  ·  Crash at: writing  ·  No API keys", options: { breakLine: true } },
        { text: "Live: python -m ui.app   or play the mp4", options: { breakLine: false } },
      ],
      {
        x: 0.5,
        y: 1.0,
        w: 9,
        h: 0.55,
        fontSize: 14,
        fontFace: mono,
        color: C.muted,
        margin: 0,
      }
    );
    imgFit(s, "media/2026-07-31-showcase-mid-run.png", 0.8, 1.65, 8.4, 3.2);
    footer(s, 6);
    s.addNotes(
      "Left: process + checkpoints. Right: Workflow Execution + Activities. Same crash point. Stop talking while pipelines move."
    );
  }

  // ── 7. Tokens ─────────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    titleBar(s, "After the crash: tokens");
    s.addText("Scripted Showcase (mid-write)", {
      x: 0.5,
      y: 1.0,
      w: 4.5,
      h: 0.3,
      fontSize: 14,
      fontFace: font,
      color: C.muted,
      margin: 0,
    });

    const stats = [
      { n: "~6,520", l: "Without Temporal" },
      { n: "~4,590", l: "With Temporal" },
      { n: "~29.6%", l: "Temporal savings" },
    ];
    stats.forEach((st, i) => {
      const x = 0.5 + i * 3.1;
      s.addShape(pres.shapes.RECTANGLE, {
        x,
        y: 1.45,
        w: 2.9,
        h: 1.7,
        fill: { color: i === 2 ? C.ink : C.fill },
        line: { color: C.ink, width: 1 },
      });
      s.addText(st.n, {
        x: x + 0.1,
        y: 1.7,
        w: 2.7,
        h: 0.7,
        fontSize: 28,
        fontFace: font,
        bold: true,
        color: i === 2 ? C.white : C.ink,
        align: "center",
        margin: 0,
      });
      s.addText(st.l, {
        x: x + 0.1,
        y: 2.5,
        w: 2.7,
        h: 0.4,
        fontSize: 13,
        fontFace: font,
        color: i === 2 ? "CCCCCC" : C.muted,
        align: "center",
        margin: 0,
      });
    });
    imgFit(
      s,
      "media/2026-07-31-showcase-comparison-panel.png",
      1.5,
      3.35,
      7,
      1.55
    );
    footer(s, 7);
    s.addNotes(
      "Reliability shows up as money. The bill tracks how complete your resume path is. Savings ~1,930 tokens."
    );
  }

  // ── 8. Without ────────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    titleBar(s, "Without Temporal: what re-ran");
    s.addText(
      [
        {
          text: "In-flight draft not checkpointed → rewrite",
          options: { bullet: true, breakLine: true },
        },
        {
          text: "Incomplete recovery can re-touch earlier steps",
          options: { bullet: true, breakLine: true },
        },
        {
          text: "UI lists What re-ran + token deltas",
          options: { bullet: true, breakLine: true },
        },
        {
          text: "Fair path: retries, checkpoints, approval; still re-pays",
          options: { bullet: true },
        },
      ],
      {
        x: 0.5,
        y: 1.1,
        w: 4.3,
        h: 3.2,
        fontSize: 15,
        fontFace: font,
        color: C.ink,
        paraSpaceAfter: 10,
        margin: 0,
      }
    );
    imgFit(s, "diagrams/03-crash-without-temporal.png", 5.0, 1.1, 4.5, 3.5);
    footer(s, 8);
    s.addNotes(
      "Gaps are intentional: mid-gather, re-eval, coarse status. See content/concepts/recovery-gaps.md"
    );
  }

  // ── 9. With Temporal ──────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    titleBar(s, "With Temporal: Worker vs Execution");
    s.addText(
      [
        {
          text: "Kill the Worker Process ≠ kill the Workflow Execution",
          options: { bullet: true, breakLine: true },
        },
        {
          text: "Event History records completed Activities",
          options: { bullet: true, breakLine: true },
        },
        {
          text: "On resume: replay history; completed Activities not re-run",
          options: { bullet: true },
        },
      ],
      {
        x: 0.5,
        y: 1.1,
        w: 4.3,
        h: 2.4,
        fontSize: 15,
        fontFace: font,
        color: C.ink,
        paraSpaceAfter: 10,
        margin: 0,
      }
    );
    imgFit(s, "diagrams/04-crash-with-temporal.png", 5.0, 1.0, 4.5, 3.6);
    footer(s, 9);
    s.addNotes(
      "Durable Execution means the run keeps progress through failures. You design the agent; stop re-implementing a half workflow engine."
    );
  }

  // ── 10. HITL ──────────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    titleBar(s, "HITL: poll vs Signal");
    imgFit(s, "diagrams/05-hitl-polling-vs-signal.png", 0.5, 1.0, 9, 3.5);
    s.addText(
      "Human time is long. Polling processes charge you for waiting. Signals do not.",
      {
        x: 0.5,
        y: 4.65,
        w: 9,
        h: 0.3,
        fontSize: 13,
        fontFace: font,
        color: C.muted,
        margin: 0,
      }
    );
    footer(s, 10);
    s.addNotes("Signal into Workflow Execution; Worker need not stay warm for the wait.");
  }

  // ── 11. Fairness ──────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    titleBar(s, "Fairness + intentional gaps");

    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.5,
      y: 1.15,
      w: 4.35,
      h: 3.5,
      fill: { color: C.fill },
      line: { color: C.ink, width: 1 },
    });
    s.addText("Fair", {
      x: 0.75,
      y: 1.35,
      w: 3.9,
      h: 0.4,
      fontSize: 18,
      fontFace: font,
      bold: true,
      color: C.ink,
      margin: 0,
    });
    s.addText(
      [
        {
          text: "Same tools, parallel search, judge, tokens",
          options: { bullet: true, breakLine: true },
        },
        {
          text: "Real checkpoints and approval on the left",
          options: { bullet: true, breakLine: true },
        },
        {
          text: "Crash both at a named stage when measuring",
          options: { bullet: true },
        },
      ],
      {
        x: 0.75,
        y: 1.9,
        w: 3.9,
        h: 2.4,
        fontSize: 14,
        fontFace: font,
        color: C.ink,
        paraSpaceAfter: 8,
        margin: 0,
      }
    );

    s.addShape(pres.shapes.RECTANGLE, {
      x: 5.15,
      y: 1.15,
      w: 4.35,
      h: 3.5,
      fill: { color: C.white },
      line: { color: C.ink, width: 1, dashType: "dash" },
    });
    s.addText("Intentional gaps", {
      x: 5.4,
      y: 1.35,
      w: 3.9,
      h: 0.4,
      fontSize: 18,
      fontFace: font,
      bold: true,
      color: C.ink,
      margin: 0,
    });
    s.addText(
      [
        {
          text: "Mid-write draft boundary",
          options: { bullet: true, breakLine: true },
        },
        {
          text: "Mid-gather search batch",
          options: { bullet: true, breakLine: true },
        },
        {
          text: "Coarse status resume",
          options: { bullet: true, breakLine: true },
        },
        {
          text: "Re-eval after some resumes",
          options: { bullet: true },
        },
      ],
      {
        x: 5.4,
        y: 1.9,
        w: 3.9,
        h: 2.4,
        fontSize: 14,
        fontFace: font,
        color: C.ink,
        paraSpaceAfter: 8,
        margin: 0,
      }
    );
    footer(s, 11);
    s.addNotes(
      "Closing every gap in-app is how teams invent a private Temporal with worse observability."
    );
  }

  // ── 12. Close ─────────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0,
      y: 0,
      w: 0.12,
      h: 5.625,
      fill: { color: C.ink },
      line: { color: C.ink, width: 0 },
    });
    s.addText("Try it", {
      x: 0.6,
      y: 1.2,
      w: 8.5,
      h: 0.6,
      fontSize: 36,
      fontFace: font,
      bold: true,
      color: C.ink,
      margin: 0,
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.6,
      y: 2.0,
      w: 8.5,
      h: 1.5,
      fill: { color: C.fill },
      line: { color: C.ink, width: 1 },
    });
    s.addText(
      [
        { text: "pip install -r requirements.txt", options: { breakLine: true } },
        { text: "python -m ui.app          # Showcase first", options: { breakLine: true } },
        { text: "content/tutorials/        # step-by-step", options: { breakLine: false } },
      ],
      {
        x: 0.85,
        y: 2.25,
        w: 8,
        h: 1.1,
        fontSize: 16,
        fontFace: mono,
        color: C.ink,
        margin: 0,
      }
    );
    s.addText(
      "If a crash doubles spend, the control plane is incomplete.",
      {
        x: 0.6,
        y: 3.8,
        w: 8.5,
        h: 0.4,
        fontSize: 16,
        fontFace: font,
        italic: true,
        color: C.muted,
        margin: 0,
      }
    );
    s.addText("github.com/ryanlingo/durable-research-agent", {
      x: 0.6,
      y: 4.5,
      w: 8.5,
      h: 0.3,
      fontSize: 13,
      fontFace: mono,
      color: C.faint,
      margin: 0,
    });
    s.addNotes(
      "Start with Showcase. If the token gap is obvious without a lecture, the control plane was the product."
    );
  }

  await pres.writeFile({ fileName: OUT });
  console.log("Wrote", OUT);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
