// Load presets for the input. ILLUSTRATIVE round numbers for a demo, not measurements:
// real appliances vary a lot. Edit them here; nothing else in the app hard-codes kWh.
export const PRESETS = [
  { label: "EV top-up", kwh: 7 },
  { label: "Laundry (wash + dry)", kwh: 3 },
  { label: "Dishwasher", kwh: 1.5 },
] as const

// Same bounds as the API (api/main.py validates load_kwh in 0..200).
export const MIN_KWH = 0
export const MAX_KWH = 200
