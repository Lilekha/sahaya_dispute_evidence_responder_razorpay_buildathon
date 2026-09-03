# SaHaYa — React Dashboard Build Spec

> **How to use this file.** Save it as `BUILD_SPEC.md` in your `Buildathon/` folder. Then open Claude Code in that folder and run the prompts in §12 in order. Do not paste this whole file as one prompt — it is a reference document the agent reads, and §12 gives the sequence of small prompts that build against it.

---

## 1. What we are building

**SaHaYa** — *Saboot Hai Yahan*, "the evidence is here."

A dispute-response console for Indian merchants on card payments. When a bank claws money back, SaHaYa works out whether the dispute is worth contesting, assembles the evidence packet the card network requires, flags what is missing, and drafts the rebuttal.

**The product's distinctive belief:** it will tell you *not* to fight. Every commercial competitor is paid a share of recoveries, so none of them can afford to say "accept this one." SaHaYa has no such incentive, so the ACCEPT recommendation is a first-class result, styled as confidently as CONTEST — never as a failure state.

**Positioning:** an independent fintech tool that works with Razorpay. It is not a Razorpay product and must not imply that it is. No Razorpay logo. No "a Razorpay company." A single line in the footer: *Built on Razorpay's dispute schema.*

---

## 2. Existing repo structure

```
Buildathon/
├── data/                      # source CSVs — DO NOT MODIFY
├── notebooks/
│   ├── 01_EDA_Chargeback_Evidence_Responder.ipynb
│   ├── 02_ML_Decision_Engine.ipynb
│   ├── 03_Evidence_Responder_Export.ipynb
│   └── outputs/
│       └── dashboard/dashboard_data.json    # <-- THE ONLY DATA THE APP NEEDS
├── prompts/
├── src/                       # python generation scripts — leave alone
└── app/                       # <-- CREATE THIS. The React app lives here.
```

Copy `notebooks/outputs/dashboard/dashboard_data.json` into `app/public/dashboard_data.json`.

**Fetch it at runtime — do not `import` it.** It is ~1.4 MB; importing bloats the bundle.

---

## 3. Stack

- **Vite + React 18** (JavaScript, not TypeScript — speed matters more than types here)
- **Tailwind CSS**
- **Recharts** for charts
- **lucide-react** for icons
- **react-router-dom** for routing
- No state library. `useState` + a single `DataContext` is enough.

---

## 4. Design language

Razorpay's design system is called **Blade** and describes itself as a "Developer-First Financial Canvas": data-dense, precise, transparent, built for people who read numbers for a living. SaHaYa borrows that *posture* without borrowing the brand.

### 4.1 Colour tokens

```js
// tailwind.config.js -> theme.extend.colors
prussian:  '#012652',   // sidebar, deep headers
dodger:    '#0D94FB',   // primary action, links, focus rings
ink:       '#1A1F36',   // primary text
slate:     '#5A6478',   // secondary text
line:      '#E3E8EF',   // borders, dividers
canvas:    '#F7F9FC',   // page background
surface:   '#FFFFFF',   // cards, panels
contest:   '#0F7B4F',   // CONTEST recommendation
accept:    '#B45309',   // ACCEPT recommendation  (amber, NOT red)
gap:       '#C0392B',   // missing evidence
```

**Critical:** ACCEPT is **amber, never red.** Red reads as error. Accepting a dispute is a correct, profitable decision — the palette must say "considered choice," not "something went wrong." This is the single most important colour decision in the app.

### 4.2 Type

One family: **Inter** (`@fontsource/inter`, weights 400/500/600/700).

- Page title — 24px / 600
- Section heading — 16px / 600
- Body — 14px / 400
- Metric value — 28px / 600, `font-variant-numeric: tabular-nums`
- Table + data — 13px / 400, tabular-nums

**All currency and probability figures must use tabular numerals** so columns align. This is a financial console; misaligned digits look broken.

Sentence case everywhere. No ALL-CAPS labels.

### 4.3 Shape and depth

- Radius **4px** on everything. Blade's "razor edge." No `rounded-xl`, no pills except status badges (which are `rounded-full`, 2px vertical padding).
- **Borders, not shadows.** `1px solid #E3E8EF`. The only shadow in the app is on the sidebar's right edge.
- 8px spacing grid.

### 4.4 What to avoid

Do not produce the generic AI dashboard: four identical gradient stat cards across the top, a soft grey drop-shadow under every card, an emoji in every heading, or a `→` appended to button text. Structure should encode meaning — a border exists because two things are genuinely separate, not for decoration.

---

## 5. Data contract

`dashboard_data.json` has four top-level keys: `meta`, `model_metrics`, `merchants`, `disputes`.

### 5.1 `merchants[]` — 9 records

```
merchant_id, name, archetype, description, fulfillment_type,
documentation_maturity   (0–1, evidence availability)
demo_priority            (1 = best demo; sort by this)
n_disputes, n_contest, n_accept
total_disputed, at_risk_value, projected_recovery
avg_p_win, mean_packet_completeness
```

### 5.2 `disputes[]` — 361 records

```
dispute_id, merchant_id, transaction_id
reason_code, reason_description, network
dispute_amount, contest_fee
dispute_created_at, respond_by, days_to_deadline
p_win            (0–1, calibrated win probability)
breakeven        (0–1, contest_fee / dispute_amount)
expected_value   (INR; p_win * amount - fee)
recommendation   ('CONTEST' | 'ACCEPT')
evidence_slots[] (6 per dispute — see below)
evidence_required, evidence_submitted, evidence_gaps, packet_completeness
top_drivers[]    ({feature, impact, direction})
rebuttal_draft   (string for CONTEST, null for ACCEPT)
actual_outcome   ('won' | 'lost' | 'accepted_refunded')
historical_action
```

`evidence_slots[]` items:
```
evidence_type, label, status ('SUBMIT' | 'GAP' | 'SKIP'),
required, available, quality, source_system, evidence_timestamp
```

### 5.3 `model_metrics`

```
win_prediction:     { test_roc_auc, test_pr_auc, test_brier,
                      precision, recall, n_train, n_test }
evidence_selection: { precision, recall, f1, exact_match_rate,
                      n_slots_evaluated, method }
economics:          { always_accept, always_contest, model, perfect_foresight }
uplift_vs_always_contest, false_positive_cost, false_negative_cost
```

---

## 6. Layout shell

```
┌────────────┬──────────────────────────────────────────────┐
│            │  merchant switcher            ₹ at risk      │
│  SaHaYa    ├──────────────────────────────────────────────┤
│  saboot    │                                              │
│  hai yahan │                                              │
│            │              route content                   │
│  Overview  │                                              │
│  Disputes  │                                              │
│  Evidence  │                                              │
│  How it    │                                              │
│   works    │                                              │
│            │                                              │
│  ──────    │                                              │
│  merchant  │                                              │
│  card      │                                              │
└────────────┴──────────────────────────────────────────────┘
```

- Sidebar 240px, `bg-prussian`, fixed. Wordmark at top: "SaHaYa" 20px/600 white, with "saboot hai yahan" 11px/400 at 60% opacity beneath.
- Active nav item: white text, 2px `dodger` left border, subtle lighter background.
- Topbar 56px, white, bottom border. Merchant switcher on the left, portfolio value-at-risk on the right.
- Content max-width 1280px, 24px padding.

**Merchant switcher** is the signature interaction. A button showing the current merchant's avatar (2-letter monogram on a colour derived from `merchant_id`), name, and archetype. Clicking opens a dropdown listing all 9 sorted by `demo_priority`, each row showing name, archetype, dispute count, and a small documentation-maturity bar. Switching re-filters everything instantly. Keyboard navigable, closes on Escape and outside click.

---

## 7. Screens

### 7.1 Overview — `/`

The hero is **one sentence, not a row of stat cards**:

> **SaHaYa recommends contesting 59 of TripWell's 78 disputes, and accepting the other 19.**
> Contesting everything would waste ₹X in fees on cases the evidence cannot win.

Set at 20px/400 with the numbers in 600. Computed from the selected merchant.

Below it, four figures in a bordered row (not four separate shadowed cards — one container, three vertical dividers):

| Value at risk | Projected recovery | Disputes to review | Evidence completeness |
|---|---|---|---|
| `at_risk_value` | `projected_recovery` | `n_disputes` | `mean_packet_completeness` |

Then two panels side by side:

**Left — Recommendation split.** A horizontal stacked bar, contest green vs accept amber, with counts. Below it: "N disputes fall below their break-even threshold. Contesting them costs more than the amount at stake."

**Right — Where the money sits.** Recharts horizontal bar of `dispute_amount` summed by `reason_code`, sorted descending.

Full width below: **Deadline pressure.** Disputes bucketed by `days_to_deadline` (≤3, 4–7, 8–14, 15+), bar chart, earliest bucket in `gap` red. Every dispute has a hard bank deadline; this is the screen's one urgency signal.

### 7.2 Disputes — `/disputes`

A dense table. 13px, tabular-nums, row height 44px, hover highlight, whole row clickable.

Columns: Dispute ID · Reason (humanised) · Amount · Win probability · Break-even · Recommendation · Deadline

- **Win probability** — number plus a 40px inline bar
- **Break-even** — number, `slate`. When `p_win` is close to `breakeven` (within 0.05), show both in `ink` to signal a marginal call.
- **Recommendation** — pill badge, contest green / accept amber
- **Deadline** — "4 days"; red when ≤3

Filters above the table: recommendation (All / Contest / Accept), reason code, and a sort control (deadline / amount / win probability). Filter state in URL query params so the demo is linkable.

Empty state: "No disputes match these filters. Clear them to see all N."

### 7.3 Dispute detail — `/disputes/:id`

The most important screen. Two columns, 60/40.

**Left column:**

*Header* — dispute ID, reason code humanised, amount 28px/600, network, days to deadline.

*The decision panel* — the centrepiece. Show the arithmetic openly:

```
Win probability          62.4%   ▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░
Break-even threshold     14.2%   ▓▓▓░░░░░░░░░░░░░░░░

  0.624 × ₹5,280  −  ₹750   =   ₹2,545 expected value

RECOMMENDATION: CONTEST
```

Both bars on the same scale so the comparison is visual. Then one plain sentence: *"Worth contesting — the expected recovery exceeds the ₹750 cost of filing."* Or for accept: *"Not worth contesting — the ₹750 filing cost exceeds what we expect to recover."*

*Evidence checklist* — the six slots, each a row:

- `SUBMIT` — green check, label, source system, date, quality bar
- `GAP` — red alert icon, label, and the text "Required but not on file"
- `SKIP` — grey dash, label, muted, "Not required for this claim type"

Header line: "4 of 5 required documents available." Sort SUBMIT first, then GAP, then SKIP.

*Rebuttal draft* — for CONTEST only. Monospace, 13px, on `canvas` background inside a bordered panel, preserving line breaks. Copy button. Below it a bordered notice: *"Drafted from records on file. No evidence is generated. Review before submitting."*

Two actions at the bottom: **Approve and submit** (primary, dodger) and **Override to accept** (secondary). Clicking either sets local state and shows a confirmation strip — "Submitted for review by you on <date>." Nothing persists; this is a prototype and the sign-off step is the point.

**Right column:**

*Why this recommendation* — `top_drivers[]`, each as a row: an up or down arrow (green/red), the humanised feature name, and a small horizontal bar sized by `|impact|`. Heading: "What moved this prediction."

*Case facts* — transaction ID, network, dispute raised date, respond-by date, historical action.

*Model note* — small, `slate`: "Win probability from a calibrated random forest (test ROC-AUC 0.73). Evidence requirements from the card network's published rules for this reason code."

### 7.4 Evidence — `/evidence`

Portfolio view of record-keeping quality — this is the screen that makes the merchant-switcher meaningful.

- **Which documents are missing most often.** Horizontal bar: for each of the 6 evidence types, share of disputes where status is `GAP`.
- **Requirement matrix.** A 6×6 grid, reason code × evidence type, filled cell where required. This is a published network rule, and showing it demonstrates the system implements a real standard rather than a guess.
- **Packet completeness distribution.** Histogram of `packet_completeness` across the merchant's disputes.
- One line beneath: "Missing required evidence is the strongest single predictor of losing a dispute."

### 7.5 How it works — `/methodology`

The honesty screen. Judges will read this.

**Two measured components, side by side:**

| Evidence selection | Win prediction |
|---|---|
| Precision 0.994 | ROC-AUC 0.725 |
| Recall 0.986 | Precision 0.543 |
| Exact match 0.969 | Recall 0.618 |
| *Implements the card networks' published requirement rules — a deterministic standard, so near-perfect accuracy is the expected result.* | *Predicts a bank's judgement, which is genuinely uncertain. Reported as measured.* |

**The money view.** Recharts horizontal bar of `economics`: always accept ₹0, always contest, SaHaYa, perfect foresight. Annotate the uplift. Then plainly: "Contest fees are small relative to most dispute amounts, so contesting everything is a strong baseline. SaHaYa's advantage concentrates in small-value disputes, where the filing fee approaches the amount at stake and contesting destroys money."

**What each mistake costs.** Two figures from `false_positive_cost` and `false_negative_cost`, with one line each explaining the asymmetry.

**Scope and limits.** Four short blocks, plain prose, no hedging:

1. *Card disputes only.* NPCI auto-resolves UPI chargebacks through settlement reconciliation — no evidence is submitted and the merchant makes no decision, so an evidence responder has nothing to do there.
2. *Synthetic data.* Calibrated to published industry benchmarks; no India-specific chargeback statistics are public. Outcomes are modelled, not observed.
3. *Defense only.* Evidence is never generated. Gaps are disclosed. Every recommendation requires human sign-off.
4. *Merchant-scoped.* A customer disputing across several merchants appears as unrelated identities, matching a real single-merchant integration.

---

## 8. Component tree

```
src/
├── main.jsx
├── App.jsx                       # router + DataProvider
├── index.css                     # tailwind + Inter + tabular-nums
├── context/DataContext.jsx       # fetch json, selected merchant, derived selectors
├── lib/
│   ├── format.js                 # inr(), pct(), humanReason(), daysLeft()
│   └── colors.js                 # avatarColor(merchantId)
├── components/
│   ├── Sidebar.jsx
│   ├── Topbar.jsx
│   ├── MerchantSwitcher.jsx
│   ├── StatRow.jsx               # the 4-figure bordered row
│   ├── RecommendationBadge.jsx
│   ├── ProbabilityBar.jsx
│   ├── EvidenceChecklist.jsx
│   ├── DecisionPanel.jsx
│   ├── DriverList.jsx
│   ├── RebuttalPanel.jsx
│   └── charts/
│       ├── ReasonValueChart.jsx
│       ├── DeadlineChart.jsx
│       ├── EconomicsChart.jsx
│       └── EvidenceGapChart.jsx
└── pages/
    ├── Overview.jsx
    ├── Disputes.jsx
    ├── DisputeDetail.jsx
    ├── Evidence.jsx
    └── Methodology.jsx
```

---

## 9. Formatting rules

```js
inr(v)      // ₹5,280 — Indian grouping (1,23,456), no decimals above ₹100
pct(v, d=1) // 62.4%
humanReason(code)
// MERCHANDISE_NOT_RECEIVED     -> "Goods not received"
// UNAUTHORIZED_TRANSACTION     -> "Unauthorised transaction"
// MERCHANDISE_NOT_AS_DESCRIBED -> "Not as described"
// CREDIT_NOT_PROCESSED         -> "Refund not processed"
// RECURRING_BILLING_DISPUTE    -> "Subscription charge disputed"
// DUPLICATE_TRANSACTION        -> "Charged twice"
```

Use `Intl.NumberFormat('en-IN')`.

---

## 10. Quality floor

- Responsive to 768px: sidebar collapses to icons, detail page stacks to one column.
- Visible keyboard focus (`ring-2 ring-dodger`) on every interactive element.
- `prefers-reduced-motion` respected.
- Loading state while the JSON fetches; error state if it fails, naming the file.
- No console errors or React key warnings.
- Motion: only on state change — the switcher dropdown, the sign-off confirmation. No entrance animations on cards.

---

## 11. Copy rules

- Sentence case. Active voice. No exclamation marks.
- Buttons say what happens: "Approve and submit", not "Submit".
- Never call an ACCEPT recommendation a failure, a loss, or a warning. It is a decision.
- Empty states direct: "No disputes match these filters."
- Footer, once: *SaHaYa — Saboot Hai Yahan · Built on Razorpay's dispute schema · Prototype, not affiliated with Razorpay*

---

## 12. Claude Code prompt sequence

Run these one at a time in `Buildathon/`, checking the result before moving on.

**Prompt 1 — scaffold**
```
Read BUILD_SPEC.md.

Create app/ as a Vite + React + Tailwind project.
Install: react-router-dom, recharts, lucide-react, @fontsource/inter
Configure tailwind.config.js with the exact colour tokens in §4.1 and
set 4px as the default border radius.
Copy notebooks/outputs/dashboard/dashboard_data.json to app/public/.
Set up index.css with Inter and tabular numerals for a .num class.
Build the app shell only: Sidebar, Topbar, router with 5 empty routes.
Verify `npm run dev` starts with no errors. Do not build pages yet.
```

**Prompt 2 — data layer**
```
Read BUILD_SPEC.md §5 and §9.

Build context/DataContext.jsx: fetch /dashboard_data.json, expose
{ data, loading, error, selectedMerchant, setSelectedMerchant,
  merchantDisputes, metrics }.
Default selected merchant = the one with demo_priority 1.
Build lib/format.js and lib/colors.js per §9.
Add loading and error states to App.jsx per §10.
Log the loaded counts to the console once to confirm the shape.
```

**Prompt 3 — merchant switcher**
```
Read BUILD_SPEC.md §6.

Build MerchantSwitcher.jsx: current merchant button with monogram avatar,
dropdown of all 9 sorted by demo_priority, each row showing name, archetype,
dispute count, documentation-maturity bar.
Keyboard navigable, Escape and outside-click close, visible focus rings.
Wire it into Topbar. Switching must re-filter the whole app.
```

**Prompt 4 — overview**
```
Read BUILD_SPEC.md §7.1.

Build pages/Overview.jsx with the sentence hero (not stat cards), the
4-figure bordered StatRow, the recommendation split bar, the
reason-code value chart, and the deadline pressure chart.
All figures come from the selected merchant.
```

**Prompt 5 — disputes table**
```
Read BUILD_SPEC.md §7.2.

Build pages/Disputes.jsx: dense sortable table with the specified columns,
inline probability bars, recommendation badges, deadline urgency colouring.
Filters for recommendation and reason code, sort control, state in URL params.
Rows link to /disputes/:id.
```

**Prompt 6 — dispute detail**
```
Read BUILD_SPEC.md §7.3.

Build pages/DisputeDetail.jsx with DecisionPanel (showing the arithmetic
openly), EvidenceChecklist, RebuttalPanel with copy button, DriverList,
case facts, and the two sign-off actions with local confirmation state.
This is the most important screen — give it the most care.
```

**Prompt 7 — evidence and methodology**
```
Read BUILD_SPEC.md §7.4 and §7.5.

Build pages/Evidence.jsx (gap frequency chart, 6x6 requirement matrix,
completeness histogram) and pages/Methodology.jsx (two-component metric
comparison, economics chart, error costs, scope and limits).
Use the exact copy given in the spec for the limits section.
```

**Prompt 8 — polish**
```
Read BUILD_SPEC.md §4.4, §10, §11.

Review every screen against the design rules. Fix: responsive behaviour
at 768px, keyboard focus rings, reduced-motion, tabular numerals on all
figures, sentence case, footer.
Check the ACCEPT badge is amber and never reads as an error.
Remove any decoration that does not encode information.
Report anything you changed and why.
```

**Prompt 9 — deploy**
```
Add a .gitignore for node_modules and dist.
Verify `npm run build` succeeds and `npm run preview` serves correctly.
Write app/README.md with local setup steps.
Confirm dashboard_data.json is in public/ and committed.
```

---

## 13. Order of work

Build in prompt order. If time runs short, screens 7.1, 7.2 and 7.3 are the demo; 7.4 and 7.5 can be thinner. Deploy to Vercel as soon as Prompt 1 succeeds — push a placeholder and get the URL working early, so the last night is not the first time you discover a build failure.
