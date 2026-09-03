# SaHaYa — Chargeback Evidence Responder

## What this project is
A dispute-response console for Indian merchants on card payments.
Razorpay AI Buildathon submission, Track 02 (AI Risk Manager).
SaHaYa = "Saboot Hai Yahan" — the evidence is here.

## Repo layout
- data/           source CSVs — DO NOT MODIFY
- notebooks/      3 Jupyter notebooks (EDA, ML, export) — DO NOT MODIFY
- notebooks/outputs/dashboard/dashboard_data.json   the app's only data source
- src/            python generation scripts — DO NOT MODIFY
- app/            the React dashboard — all frontend work happens here
- BUILD_SPEC.md   the full design and build specification

## Rules
- Read BUILD_SPEC.md before any frontend work. It is the source of truth.
- Never modify anything outside app/ unless I explicitly ask.
- The app fetches /dashboard_data.json at runtime. Never import it — it is 1.4 MB.
- ACCEPT recommendations are AMBER (#B45309), never red. Accepting a dispute
  is a correct decision, not an error state.
- Border radius is 4px everywhere. Borders, not shadows.
- All currency and percentage figures use tabular numerals.
- Sentence case in all UI copy. No ALL-CAPS labels.

## Stack
Vite + React 18 (JavaScript, not TypeScript), Tailwind, Recharts,
lucide-react, react-router-dom.

## Commands
cd app && npm run dev      # dev server
cd app && npm run build    # production build