const PALETTE = [
  '#6D28D9', // violet
  '#7E22CE', // purple
  '#A21CAF', // fuchsia
  '#BE185D', // pink
  '#BE123C', // rose
  '#4338CA', // indigo
  '#475569', // slate
  '#52525B', // zinc
  '#57534E', // stone
]

function hashString(str) {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i)
    hash |= 0
  }
  return Math.abs(hash)
}

export function avatarColor(merchantId) {
  if (!merchantId) return PALETTE[0]
  return PALETTE[hashString(merchantId) % PALETTE.length]
}
