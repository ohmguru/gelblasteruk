'use client'

import { useEffect, useRef, useState } from 'react'

declare global {
  interface Window {
    google: any
    initMap: () => void
  }
}

interface Venue {
  source: string
  category: string
  name: string
  brand?: string
  url?: string
  postcode?: string
  lat: number
  lon: number
  phone?: string
  rating?: string
  price_level?: string
  business_status?: string
  opening_hours?: string
}

const categoryColors: { [key: string]: string } = {
  arcade_bar: '#FF6B6B',
  climbing: '#4ECDC4',
  mini_golf: '#45B7D1',
  karting: '#96CEB4',
  bowling: '#FECA57',
  escape_rooms: '#FF9FF3',
  trampoline: '#54A0FF',
  ice_skating: '#5F27CD',
  amusement_arcade: '#00D2D3',
  roller_skating: '#FF6348',
  laser_tag: '#2ED573',
  vr_arcade: '#FFA502',
  soft_play: '#3742FA',
  paintball: '#2F3542',
  axe_throwing: '#A4B0BE',
  indoor_skydiving: '#F8B500'
}

const categoryNames: { [key: string]: string } = {
  arcade_bar: 'Arcade Bar',
  climbing: 'Climbing',
  mini_golf: 'Mini Golf',
  karting: 'Karting',
  bowling: 'Bowling',
  escape_rooms: 'Escape Rooms',
  trampoline: 'Trampoline',
  ice_skating: 'Ice Skating',
  amusement_arcade: 'Amusement Arcade',
  roller_skating: 'Roller Skating',
  laser_tag: 'Laser Tag',
  vr_arcade: 'VR Arcade',
  soft_play: 'Soft Play',
  paintball: 'Paintball',
  axe_throwing: 'Axe Throwing',
  indoor_skydiving: 'Indoor Skydiving'
}

export default function VenueMap() {
  const mapRef = useRef<HTMLDivElement>(null)
  // Use a broad type here to avoid requiring Google Maps types at build time
  const [map, setMap] = useState<any | null>(null)
  const [venues, setVenues] = useState<Venue[]>([])
  const [loading, setLoading] = useState(true)
  const [mapType, setMapType] = useState<'roadmap' | 'satellite'>('roadmap')
  const [isClient, setIsClient] = useState(false)
  
  // Ensure we're on the client side
  useEffect(() => {
    console.log('Setting client-side flag')
    setIsClient(true)
  }, [])

  useEffect(() => {
    // Load venues data
    console.log('Loading venues...')
    fetch('/api/venues')
      .then(res => {
        console.log('Venues API response status:', res.status)
        return res.json()
      })
      .then(data => {
        console.log('Venues loaded:', data.length, 'venues')
        setVenues(data)
      })
      .catch(err => {
        console.error('Error loading venues:', err)
      })
  }, [])

  useEffect(() => {
    if (!isClient) {
      console.log('Not on client side yet, skipping map initialization')
      return
    }
    
    const loadGoogleMapsScript = () => {
      return new Promise<void>((resolve, reject) => {
        // Check if Google Maps is already loaded
        if (window.google && window.google.maps) {
          console.log('Google Maps already loaded')
          resolve()
          return
        }

        console.log('Loading Google Maps script...')
        const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || 'AIzaSyC6FR_yyhABA4mA7cC5Y6PNEVBtRKV9xLk'
        console.log('Using API key:', apiKey.substring(0, 10) + '...')
        
        const script = document.createElement('script')
        script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places&callback=initMap`
        script.async = true
        script.defer = true
        
        // Create global callback
        window.initMap = () => {
          console.log('Google Maps script loaded via callback')
          resolve()
        }
        
        script.onerror = (error) => {
          console.error('Error loading Google Maps script:', error)
          reject(error)
        }
        
        document.head.appendChild(script)
      })
    }

    let retryCount = 0
    const maxRetries = 50 // 5 seconds total wait time
    
    const initMap = async () => {
      // Wait for the ref to be available
      if (!mapRef.current) {
        if (retryCount < maxRetries) {
          console.log(`Map ref not ready, waiting... (attempt ${retryCount + 1}/${maxRetries})`)
          retryCount++
          setTimeout(initMap, 100)
          return
        } else {
          console.error('Map ref never became available after 5 seconds')
          setLoading(false)
          return
        }
      }

      try {
        console.log('Map ref is ready, loading Google Maps...')
        await loadGoogleMapsScript()
        
        if (mapRef.current && window.google && window.google.maps) {
          console.log('Creating map instance...')
          const mapInstance = new (window as any).google.maps.Map(mapRef.current, {
            zoom: 11,
            center: { lat: 51.5074, lng: -0.1278 }, // London center
            mapTypeId: mapType,
            styles: [
              {
                featureType: 'poi',
                stylers: [{ visibility: 'off' }]
              }
            ]
          })
          
          console.log('Map created successfully')
          setMap(mapInstance)
          setLoading(false)
        } else {
          console.error('Google Maps API not available or map ref is null')
          setLoading(false)
        }
      } catch (error) {
        console.error('Error initializing map:', error)
        setLoading(false)
      }
    }

    // Small delay to ensure DOM is ready
    const timer = setTimeout(initMap, 100)
    return () => clearTimeout(timer)
  }, [mapType, isClient])

  useEffect(() => {
    if (map && venues.length > 0) {
      venues.forEach(venue => {
        if (venue.lat && venue.lon) {
          const marker = new (window as any).google.maps.Marker({
            position: { lat: venue.lat, lng: venue.lon },
            map: map,
            title: venue.name || 'Unnamed Venue',
            icon: {
              path: (window as any).google.maps.SymbolPath.CIRCLE,
              fillColor: categoryColors[venue.category] || '#666',
              fillOpacity: 0.8,
              strokeColor: '#333',
              strokeWeight: 2,
              scale: 8
            }
          })

          const infoWindow = new (window as any).google.maps.InfoWindow({
            content: createInfoWindowContent(venue)
          })

          marker.addListener('click', () => {
            infoWindow.open(map, marker)
          })
        }
      })
    }
  }, [map, venues])

  const createInfoWindowContent = (venue: Venue) => {
    return `
      <div style="max-width: 300px;">
        <div style="font-weight: bold; font-size: 16px; color: #1a73e8; margin-bottom: 5px;">
          ${venue.name || 'Unnamed Venue'}
        </div>
        <div style="margin: 3px 0; font-size: 13px;">
          <strong>Category:</strong> ${categoryNames[venue.category] || venue.category}
        </div>
        ${venue.brand ? `<div style="margin: 3px 0; font-size: 13px;"><strong>Brand:</strong> ${venue.brand}</div>` : ''}
        ${venue.postcode ? `<div style="margin: 3px 0; font-size: 13px;"><strong>Postcode:</strong> ${venue.postcode}</div>` : ''}
        ${venue.phone ? `<div style="margin: 3px 0; font-size: 13px;"><strong>Phone:</strong> ${venue.phone}</div>` : ''}
        ${venue.rating ? `<div style="margin: 3px 0; font-size: 13px;"><strong>Rating:</strong> ${venue.rating}/5</div>` : ''}
        ${venue.url ? `<div style="margin: 3px 0; font-size: 13px;"><a href="${venue.url}" target="_blank" style="color: #1a73e8;">Visit Website</a></div>` : ''}
        <div style="margin: 3px 0; font-size: 13px;"><strong>Source:</strong> ${venue.source}</div>
      </div>
    `
  }

  const getCategoryCounts = () => {
    const counts: { [key: string]: number } = {}
    venues.forEach(venue => {
      counts[venue.category] = (counts[venue.category] || 0) + 1
    })
    return counts
  }

  // Don't render anything until we're on the client
  if (!isClient) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="text-lg font-bold mb-2">Loading London Venues Map...</div>
          <div className="text-sm text-gray-600">Initializing Client</div>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="text-lg font-bold mb-2">Loading London Venues Map...</div>
          <div className="text-sm text-gray-600">Initializing Google Maps</div>
        </div>
      </div>
    )
  }

  const categoryCounts = getCategoryCounts()

  return (
    <div className="relative h-screen w-full">
      {/* Map Controls */}
      <div className="absolute top-4 left-4 bg-white p-3 rounded-lg shadow-lg z-10">
        <button 
          onClick={() => {
            setMapType('roadmap')
            if (map) map.setMapTypeId('roadmap')
          }}
          className={`px-3 py-2 mr-2 rounded ${mapType === 'roadmap' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
        >
          Roadmap
        </button>
        <button 
          onClick={() => {
            setMapType('satellite')
            if (map) map.setMapTypeId('satellite')
          }}
          className={`px-3 py-2 rounded ${mapType === 'satellite' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
        >
          Satellite
        </button>
      </div>

      {/* Legend */}
      <div className="absolute top-4 right-4 bg-white p-4 rounded-lg shadow-lg z-10 max-h-96 overflow-y-auto w-64">
        <h3 className="text-lg font-bold mb-3">Venue Categories</h3>
        {Object.entries(categoryCounts)
          .sort(([,a], [,b]) => b - a)
          .map(([category, count]) => (
            <div key={category} className="flex items-center mb-2">
              <div 
                className="w-5 h-5 rounded-full border-2 border-gray-800 mr-3"
                style={{ backgroundColor: categoryColors[category] || '#666' }}
              />
              <span className="text-sm">
                {categoryNames[category] || category} ({count})
              </span>
            </div>
          ))}
        <div className="mt-4 text-sm text-gray-600">
          Total Venues: {venues.length}
        </div>
      </div>

      {/* Map Container */}
      <div 
        ref={mapRef} 
        className="w-full h-full" 
        style={{ minHeight: '400px', backgroundColor: '#e5e7eb' }}
        id="google-map"
      >
        <div className="flex items-center justify-center h-full text-gray-600">
          Map container ready
        </div>
      </div>
    </div>
  )
}
