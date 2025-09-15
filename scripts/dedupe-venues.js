#!/usr/bin/env node
/*
  Deduplicate venues in venue-map-app/venue_data.json
  - Merges items within ~60m regardless of name; up to 200m if names similar
  - Prefers Google/Places sources over OSM when merging
  - Writes the deduped result back to the same file and creates a backup
*/

const fs = require('fs')
const path = require('path')

const FILE = path.join(process.cwd(), 'venue-map-app', 'venue_data.json')
const BACKUP = path.join(process.cwd(), 'venue-map-app', `venue_data.backup.${Date.now()}.json`)

function normalizeName(name) {
  if (!name) return ''
  return String(name)
    .toLowerCase()
    .replace(/&/g, 'and')
    .replace(/[^a-z0-9]+/g, ' ')
    .replace(/\b(the|london|city|camden|market)\b/g, '')
    .replace(/\s+/g, ' ')
    .trim()
}

function nameSimilar(a, b) {
  const na = normalizeName(a)
  const nb = normalizeName(b)
  if (!na || !nb) return false
  if (na === nb) return true
  return na.includes(nb) || nb.includes(na)
}

function haversineMeters(lat1, lon1, lat2, lon2) {
  const toRad = (v) => (v * Math.PI) / 180
  const R = 6371e3
  const dLat = toRad(lat2 - lat1)
  const dLon = toRad(lon2 - lon1)
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) * Math.sin(dLon / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return R * c
}

function sourceWeight(s) {
  if (!s) return 0
  const v = String(s).toLowerCase()
  if (v.includes('google') || v.includes('places') || v.includes('gmaps')) return 3
  if (v.includes('osm') || v.includes('openstreetmap')) return 2
  return 1
}

function richnessScore(v) {
  let score = 0
  if (v.url) score += 1
  if (v.postcode) score += 1
  if (v.phone) score += 1
  if (v.rating) score += 1
  if (v.price_level) score += 1
  score += sourceWeight(v.source)
  return score
}

function choosePreferred(a, b) {
  // Prefer Google over OSM if present
  const aw = sourceWeight(a.source)
  const bw = sourceWeight(b.source)
  if (aw !== bw) return aw > bw ? a : b
  const ar = richnessScore(a)
  const br = richnessScore(b)
  return br > ar ? b : a
}

function merge(a, b) {
  const chosen = choosePreferred(a, b)
  const other = chosen === a ? b : a
  return {
    source: chosen.source || other.source,
    category: chosen.category || other.category,
    name: chosen.name || other.name,
    brand: chosen.brand || other.brand,
    url: chosen.url || other.url,
    postcode: chosen.postcode || other.postcode,
    lat: chosen.lat ?? other.lat,
    lon: chosen.lon ?? other.lon,
    phone: chosen.phone || other.phone,
    rating: chosen.rating || other.rating,
    price_level: chosen.price_level || other.price_level,
    business_status: chosen.business_status || other.business_status,
    opening_hours: chosen.opening_hours || other.opening_hours,
  }
}

function dedupe(list) {
  const out = []
  for (const v of list) {
    if (typeof v.lat !== 'number' || typeof v.lon !== 'number') {
      out.push(v)
      continue
    }
    const idx = out.findIndex((o) => {
      if (typeof o.lat !== 'number' || typeof o.lon !== 'number') return false
      const d = haversineMeters(v.lat, v.lon, o.lat, o.lon)
      if (d <= 60) return true
      if (d <= 200 && nameSimilar(v.name, o.name)) return true
      return false
    })
    if (idx >= 0) out[idx] = merge(out[idx], v)
    else out.push(v)
  }
  return out
}

function main() {
  const raw = fs.readFileSync(FILE, 'utf8')
  const data = JSON.parse(raw)
  console.log(`Loaded ${data.length} venues from ${FILE}`)
  fs.writeFileSync(BACKUP, JSON.stringify(data, null, 2))
  console.log(`Backup written to ${BACKUP}`)
  const deduped = dedupe(data)
  console.log(`Deduped to ${deduped.length} venues`)
  fs.writeFileSync(FILE, JSON.stringify(deduped, null, 2))
  console.log(`Updated deduped file written to ${FILE}`)
}

main()

