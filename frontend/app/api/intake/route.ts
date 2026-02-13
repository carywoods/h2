import { NextRequest, NextResponse } from 'next/server'

const ORCHESTRATOR_URL = process.env.ORCHESTRATOR_INTERNAL_URL || 'http://orchestrator:8000'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    const response = await fetch(`${ORCHESTRATOR_URL}/intake`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status })
    }

    return NextResponse.json(data)
  } catch (error) {
    console.error('Proxy error:', error)
    return NextResponse.json(
      { detail: 'Failed to connect to orchestrator' },
      { status: 502 }
    )
  }
}
