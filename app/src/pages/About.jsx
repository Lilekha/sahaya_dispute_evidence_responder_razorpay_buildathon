import { Link } from 'react-router-dom'

const STATS = [
  { value: '₹34,802', caption: 'average loss per card-fraud case (RBI)' },
  { value: '75%+', caption: "of India's card fraud value is card-not-present" },
  { value: '44–55%', caption: 'typical merchant win rate when a dispute is contested' },
  {
    value: '1.5%',
    caption: "Visa's VAMP threshold — the dispute rate that triggers network monitoring",
  },
]

const STEPS = [
  { title: 'Predict', body: 'Estimate the odds of winning, calibrated against real outcomes' },
  {
    title: 'Assemble',
    body: "Match the dispute's reason code to the evidence the card network actually requires",
  },
  { title: 'Decide', body: 'Compare the odds against the filing cost — not a fixed 50/50 guess' },
  {
    title: 'Explain',
    body: 'Show the reasoning and a draft response a human reviews before submitting',
  },
]

function StatBlock({ value, caption, index }) {
  const rightCol = index % 2 === 1
  const bottomRow = index >= 2
  return (
    <div
      className={`p-3 sm:p-4 ${rightCol ? 'border-l border-line' : ''} ${
        bottomRow ? 'border-t border-line' : ''
      }`}
    >
      <div className="num text-[20px] font-semibold text-ink sm:text-[28px]">{value}</div>
      <div className="mt-1 text-[11px] text-slate">{caption}</div>
    </div>
  )
}

export default function About() {
  return (
    <div className="flex flex-col gap-6">
      <div className="border border-line bg-surface p-4">
        <h2 className="text-base font-semibold text-ink">
          A merchant&rsquo;s worst moment: the money is already gone
        </h2>
        <p className="mt-3 max-w-[640px] text-sm text-ink">
          When a customer disputes a card payment, the bank debits the merchant immediately —
          before anyone has reviewed anything. The merchant then has one narrow window to submit
          evidence and argue for the money back. Most small merchants don&rsquo;t know which
          documents matter for which kind of claim, or whether fighting is even worth the filing
          fee. SaHaYa answers both questions automatically.
        </p>
      </div>

      <div className="border border-line bg-surface p-4">
        <h2 className="text-base font-semibold text-ink">
          The scale of the problem, in public numbers
        </h2>
        <div className="mt-4 grid grid-cols-2 border border-line">
          {STATS.map((s, i) => (
            <StatBlock key={s.caption} index={i} value={s.value} caption={s.caption} />
          ))}
        </div>
        <p className="mt-3 text-[12px] text-slate">
          Figures are industry and RBI-published benchmarks. No India-specific chargeback dataset
          is publicly available — see &ldquo;How it works&rdquo; for how this project&rsquo;s data
          was built.
        </p>
      </div>

      <div className="border border-line bg-surface p-4">
        <h2 className="text-base font-semibold text-ink">
          India runs on UPI. This tool is built for cards. Here&rsquo;s why.
        </h2>
        <p className="mt-3 max-w-[640px] text-sm text-ink">
          Since February 2025, NPCI auto-resolves UPI chargebacks through settlement
          reconciliation between banks. The merchant submits no evidence and makes no decision —
          the outcome is decided algorithmically before they&rsquo;re even involved. Card disputes
          work differently: the outcome depends on what evidence the merchant submits, against a
          specific reason code, before a deadline. That&rsquo;s a judgement problem, and it&rsquo;s
          where a tool like SaHaYa creates value. Building for UPI would mean automating a
          decision nobody gets to make.
        </p>
      </div>

      <div className="border border-line bg-surface p-4">
        <h2 className="text-base font-semibold text-ink">
          Nobody else can afford to tell you not to fight
        </h2>
        <p className="mt-3 max-w-[640px] text-sm text-ink">
          Commercial chargeback tools charge a percentage of what they recover for you. That means
          they earn nothing by advising you to accept a dispute — even when fighting it would lose
          you money. SaHaYa has no such incentive. It&rsquo;s designed to tell you the truth about
          a dispute&rsquo;s economics, including when the honest answer is &ldquo;don&rsquo;t
          bother.&rdquo;
        </p>
      </div>

      <div className="border border-line bg-surface p-4">
        <h2 className="text-base font-semibold text-ink">Four steps, every dispute</h2>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((step, i) => (
            <div key={step.title} className="border border-line p-4">
              <div className="num flex h-6 w-6 items-center justify-center border border-line text-[12px] font-semibold text-ink">
                {i + 1}
              </div>
              <div className="mt-2 text-sm font-semibold text-ink">{step.title}</div>
              <p className="mt-1 text-[13px] text-slate">{step.body}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="border border-line bg-surface p-4">
        <h2 className="text-base font-semibold text-ink">What this is, plainly</h2>
        <ul className="mt-4 flex list-disc flex-col gap-2 pl-5 text-sm text-ink marker:text-slate">
          <li>
            Built for card disputes (Visa, Mastercard, RuPay) — UPI is out of scope, and the
            section above explains why.
          </li>
          <li>
            Built on a synthetic dataset calibrated to published industry benchmarks, since no
            public India-specific chargeback dataset exists.
          </li>
          <li>Built for the Razorpay AI Buildathon, Track 02 (AI Risk Manager).</li>
          <li>
            Full methodology, metrics, and limitations are on the{' '}
            <Link
              to="/methodology"
              className="text-dodger underline-offset-2 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-dodger"
            >
              How it works
            </Link>{' '}
            page.
          </li>
        </ul>
      </div>
    </div>
  )
}
