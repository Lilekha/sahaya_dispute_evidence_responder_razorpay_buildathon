import { useState } from 'react'
import { avatarColor } from '../lib/colors'
import { MERCHANT_ICONS } from '../lib/merchantIcons'

const STOPWORDS = new Set(['by', 'of', 'the', 'and', 'for'])

function getMonogram(name) {
  const words = (name ?? '')
    .split(/\s+/)
    .filter((w) => /[a-zA-Z]/.test(w))
    .filter((w) => !STOPWORDS.has(w.toLowerCase()))

  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase()
  }

  const word = words[0] ?? ''
  if (!word) return '—'

  const first = word[0]
  const internalCap = word.slice(1).match(/[A-Z]/)
  const second = internalCap ? internalCap[0] : (word[1] ?? first)
  return (first + second).toUpperCase()
}

export default function MerchantAvatar({ merchant, size = 32 }) {
  const [imgFailed, setImgFailed] = useState(false)
  const iconSrc = MERCHANT_ICONS[merchant.merchant_id]

  if (iconSrc && !imgFailed) {
    return (
      <span
        className="flex shrink-0 items-center justify-center overflow-hidden rounded-full border border-line bg-white"
        style={{ width: size, height: size }}
      >
        <img
          src={iconSrc}
          alt=""
          className="h-full w-full object-contain"
          onError={() => setImgFailed(true)}
        />
      </span>
    )
  }

  return (
    <span
      aria-hidden="true"
      className="flex shrink-0 items-center justify-center rounded-full font-semibold text-white"
      style={{
        width: size,
        height: size,
        backgroundColor: avatarColor(merchant.merchant_id),
        fontSize: size >= 32 ? 12 : 11,
      }}
    >
      {getMonogram(merchant.name)}
    </span>
  )
}
