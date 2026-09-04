// Vite's dev server fails to resolve a %26-encoded '&' in public/ (falls back to index.html),
// so '&' is left raw here and only spaces are percent-encoded — matches what encodeURI() does.
export const MERCHANT_ICONS = {
  M000001: '/icons/Loops%20&%20Knots%20by%20Ananya.png',
  M000002: '/icons/SoleCraft.png',
  M000003: '/icons/Gyan%20IAS%20Study%20Circle.png',
  M000004: '/icons/CodePilot.png',
  M000005: '/icons/FitForge.png',
  M000006: '/icons/TripWell.png',
  M000007: '/icons/SwitchCart.png',
}
