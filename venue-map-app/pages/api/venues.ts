import { NextApiRequest, NextApiResponse } from 'next'
import fs from 'fs'
import path from 'path'

type Venue = {
  source?: string
  category?: string
  name?: string
  brand?: string
  url?: string
  postcode?: string
  lat?: number
  lon?: number
  phone?: string
  rating?: string
  price_level?: string
  business_status?: string
  opening_hours?: string
}

function normalizeName(name?: string): string {
  if (!name) return ''
  return name
    .toLowerCase()
    .replace(/&/g, 'and')
    .replace(/[^a-z0-9]+/g, ' ') // collapse punctuation
    .replace(/\b(the|london|city|camden|market)\b/g, '') // trim common locality noise
    .replace(/\s+/g, ' ')
    .trim()
}

function nameSimilar(a?: string, b?: string): boolean {
  const na = normalizeName(a)
  const nb = normalizeName(b)
  if (!na || !nb) return false
  if (na === nb) return true
  // allow partial containment for small deltas (e.g. "babylon park" vs "babylon park camden")
  return na.includes(nb) || nb.includes(na)
}

function haversineMeters(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const toRad = (v: number) => (v * Math.PI) / 180
  const R = 6371e3
  const dLat = toRad(lat2 - lat1)
  const dLon = toRad(lon2 - lon1)
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return R * c
}

function chooseRicher(a: Venue, b: Venue): Venue {
  const sourcePriority = (s?: string) => {
    const map: Record<string, number> = { google: 3, gmaps: 3, places: 3, osm: 2, manual: 1 }
    return s ? map[s.toLowerCase()] ?? 0 : 0
  }
  const richness = (v: Venue) => {
    let score = 0
    if (v.url) score += 1
    if (v.postcode) score += 1
    if (v.phone) score += 1
    if (v.rating) score += 1
    if (v.price_level) score += 1
    score += sourcePriority(v.source)
    return score
  }
  const ar = richness(a)
  const br = richness(b)
  return br > ar ? b : a
}

function mergeVenues(target: Venue, incoming: Venue): Venue {
  const chosen = chooseRicher(target, incoming)
  const other = chosen === target ? incoming : target
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

function dedupeVenues(input: Venue[]): Venue[] {
  const out: Venue[] = []
  for (const v of input) {
    if (typeof v.lat !== 'number' || typeof v.lon !== 'number') {
      out.push(v)
      continue
    }
    const idx = out.findIndex((o) => {
      if (typeof o.lat !== 'number' || typeof o.lon !== 'number') return false
      const distance = haversineMeters(v.lat!, v.lon!, o.lat!, o.lon!)
      // Only dedupe when names are similar AND within ~200m to avoid false merges in dense areas
      if (distance <= 200 && nameSimilar(v.name, o.name)) return true
      return false
    })
    if (idx >= 0) {
      out[idx] = mergeVenues(out[idx], v)
    } else {
      out.push(v)
    }
  }
  return out
}

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' })
  }

  try {
    // Try common locations for the data file both locally and in serverless
    const candidates = [
      path.join(process.cwd(), 'venue_data.json'),
      path.join(process.cwd(), 'venue-map-app', 'venue_data.json'),
      path.join(__dirname, '../../../venue_data.json'),
    ]
    const dataPath = candidates.find((p) => {
      try { return fs.existsSync(p) } catch { return false }
    }) || candidates[0]

    console.log('Loading venue data from:', dataPath)
    const jsonData = fs.readFileSync(dataPath, 'utf8')
    const venues: Venue[] = JSON.parse(jsonData)
    const deduped = dedupeVenues(venues)
    console.log('Loaded', venues.length, 'venues; deduped to', deduped.length)

    res.status(200).json(deduped)
  } catch (error: unknown) {
    console.error('Error reading venue data:', error)
    const message = error instanceof Error ? error.message : String(error)
    res.status(500).json({ message: 'Error loading venue data', error: message })
  }
}
