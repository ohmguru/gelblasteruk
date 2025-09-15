import { NextApiRequest, NextApiResponse } from 'next'
import fs from 'fs'
import path from 'path'

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' })
  }

  try {
    // Read pre-processed (deduped) data file. The build step ensures it’s up to date.
    const candidates = [
      path.join(process.cwd(), 'venue-map-app', 'venue_data.json'),
      path.join(process.cwd(), 'venue_data.json'),
      path.join(__dirname, '../../../venue-map-app/venue_data.json'),
    ]
    const dataPath = candidates.find((p) => {
      try { return fs.existsSync(p) } catch { return false }
    }) || candidates[0]

    const jsonData = fs.readFileSync(dataPath, 'utf8')
    const venues = JSON.parse(jsonData)
    res.status(200).json(venues)
  } catch (error: unknown) {
    console.error('Error reading venue data:', error)
    const message = error instanceof Error ? error.message : String(error)
    res.status(500).json({ message: 'Error loading venue data', error: message })
  }
}
