import { NextApiRequest, NextApiResponse } from 'next'
import fs from 'fs'
import path from 'path'

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' })
  }

  try {
    const dataPath = path.join(process.cwd(), 'venue_data.json')
    console.log('Looking for venue data at:', dataPath)
    const jsonData = fs.readFileSync(dataPath, 'utf8')
    const venues = JSON.parse(jsonData)
    console.log('Successfully loaded', venues.length, 'venues')
    
    res.status(200).json(venues)
  } catch (error: unknown) {
    console.error('Error reading venue data:', error)
    const message = error instanceof Error ? error.message : String(error)
    res.status(500).json({ message: 'Error loading venue data', error: message })
  }
}
