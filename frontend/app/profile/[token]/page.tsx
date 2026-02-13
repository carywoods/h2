'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Profile {
  company_name: string
  industry_classification: string
  location: string
  estimated_size: string
  operational_snapshot: {
    technology_posture: string
    digital_maturity: string
    detected_technologies: string[]
    infrastructure_signals: string
  }
  market_position: {
    business_category: string
    public_reputation: string
    competitive_signals: string
    growth_indicators: string
  }
  strategic_observations: string[]
  identified_gaps: string[]
  data_confidence: {
    overall_score: string
    sources_used: string[]
    sources_unavailable: string[]
    freshness: string
  }
}

interface ProfileData {
  profile: Profile
  company_name: string
  created_at: string
}

export default function ProfilePage() {
  const params = useParams()
  const token = params.token as string

  const [data, setData] = useState<ProfileData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [visiblePanels, setVisiblePanels] = useState<number[]>([])
  const [isAnimationComplete, setIsAnimationComplete] = useState(false)

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await fetch(`${API_URL}/profile/${token}`)

        if (response.status === 202) {
          setError('Your profile is being prepared. Please check back shortly.')
          return
        }

        if (response.status === 410) {
          setError('This profile link has expired.')
          return
        }

        if (!response.ok) {
          throw new Error('Failed to load profile')
        }

        const profileData = await response.json()
        setData(profileData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Something went wrong')
      } finally {
        setLoading(false)
      }
    }

    fetchProfile()
  }, [token])

  // Staged panel animation
  useEffect(() => {
    if (!data) return

    const totalPanels = 8 // Number of panels to animate
    let currentPanel = 0

    const interval = setInterval(() => {
      if (currentPanel < totalPanels) {
        setVisiblePanels((prev) => [...prev, currentPanel])
        currentPanel++
      } else {
        clearInterval(interval)
        setIsAnimationComplete(true)
      }
    }, 300) // 300ms stagger

    return () => clearInterval(interval)
  }, [data])

  if (loading) {
    return (
      <main style={styles.main}>
        <div style={styles.loadingContainer}>
          <p style={styles.loadingText}>Loading your profile...</p>
          <div style={styles.progressContainer}>
            <div style={styles.progressLine} />
          </div>
        </div>
      </main>
    )
  }

  if (error) {
    return (
      <main style={styles.main}>
        <div style={styles.errorContainer}>
          <p style={styles.errorText}>{error}</p>
        </div>
      </main>
    )
  }

  if (!data) return null

  const { profile } = data

  return (
    <main style={styles.main}>
      <div style={styles.container}>
        {/* Header Panel */}
        <div
          style={{
            ...styles.panel,
            ...(visiblePanels.includes(0) ? styles.panelVisible : styles.panelHidden),
            animationDelay: '0ms',
          }}
        >
          <h1 style={styles.companyName}>{profile.company_name}</h1>
          <div style={styles.headerMeta}>
            <span style={styles.metaItem}>{profile.industry_classification}</span>
            <span style={styles.metaDivider}>|</span>
            <span style={styles.metaItem}>{profile.location}</span>
            <span style={styles.metaDivider}>|</span>
            <span style={styles.metaItem}>{profile.estimated_size}</span>
          </div>
        </div>

        <div className="profile-grid">
          {/* Left Column - Primary Data (65%) */}
          <div style={styles.leftColumn}>
            {/* Operational Snapshot */}
            <div
              style={{
                ...styles.panel,
                ...(visiblePanels.includes(1) ? styles.panelVisible : styles.panelHidden),
              }}
            >
              <h2 style={styles.sectionHeader}>Operational Snapshot</h2>

              <div style={styles.dataBlock}>
                <span style={styles.dataLabel}>Technology Posture</span>
                <p style={styles.dataValue}>{profile.operational_snapshot.technology_posture}</p>
              </div>

              <div style={styles.dataBlock}>
                <span style={styles.dataLabel}>Digital Maturity</span>
                <p style={styles.dataValue}>{profile.operational_snapshot.digital_maturity}</p>
              </div>

              <div style={styles.dataBlock}>
                <span style={styles.dataLabel}>Detected Technologies</span>
                <div style={styles.techList}>
                  {profile.operational_snapshot.detected_technologies.map((tech, i) => (
                    <span key={i} style={styles.techTag}>
                      {tech}
                    </span>
                  ))}
                </div>
              </div>

              <div style={styles.dataBlock}>
                <span style={styles.dataLabel}>Infrastructure Signals</span>
                <p style={styles.dataValue}>{profile.operational_snapshot.infrastructure_signals}</p>
              </div>
            </div>

            {/* Market Position */}
            <div
              style={{
                ...styles.panel,
                ...(visiblePanels.includes(2) ? styles.panelVisible : styles.panelHidden),
              }}
            >
              <h2 style={styles.sectionHeader}>Market Position</h2>

              <div style={styles.dataBlock}>
                <span style={styles.dataLabel}>Business Category</span>
                <p style={styles.dataValue}>{profile.market_position.business_category}</p>
              </div>

              <div style={styles.dataBlock}>
                <span style={styles.dataLabel}>Public Reputation</span>
                <p style={styles.dataValue}>{profile.market_position.public_reputation}</p>
              </div>

              <div style={styles.dataBlock}>
                <span style={styles.dataLabel}>Competitive Signals</span>
                <p style={styles.dataValue}>{profile.market_position.competitive_signals}</p>
              </div>

              <div style={styles.dataBlock}>
                <span style={styles.dataLabel}>Growth Indicators</span>
                <p style={styles.dataValue}>{profile.market_position.growth_indicators}</p>
              </div>
            </div>

            {/* Strategic Observations */}
            <div
              style={{
                ...styles.panel,
                ...(visiblePanels.includes(3) ? styles.panelVisible : styles.panelHidden),
              }}
            >
              <h2 style={styles.sectionHeader}>Strategic Observations</h2>
              <ul style={styles.observationList}>
                {profile.strategic_observations.map((obs, i) => (
                  <li key={i} style={styles.observationItem}>
                    {obs}
                  </li>
                ))}
              </ul>
            </div>

            {/* Identified Gaps */}
            <div
              style={{
                ...styles.panel,
                ...(visiblePanels.includes(4) ? styles.panelVisible : styles.panelHidden),
              }}
            >
              <h2 style={styles.sectionHeader}>Opportunities for Deeper Analysis</h2>
              <ul style={styles.observationList}>
                {profile.identified_gaps.map((gap, i) => (
                  <li key={i} style={styles.observationItem}>
                    {gap}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Right Column - Context (35%) */}
          <div style={styles.rightColumn}>
            {/* Data Confidence */}
            <div
              style={{
                ...styles.panel,
                ...(visiblePanels.includes(5) ? styles.panelVisible : styles.panelHidden),
              }}
            >
              <h2 style={styles.sectionHeader}>Data Confidence</h2>

              <div style={styles.confidenceScore}>
                <span style={styles.scoreValue}>{profile.data_confidence.overall_score}</span>
                <span style={styles.scoreLabel}>Confidence</span>
              </div>

              <div style={styles.dataBlock}>
                <span style={styles.dataLabel}>Sources Used</span>
                <ul style={styles.sourceList}>
                  {profile.data_confidence.sources_used.map((source, i) => (
                    <li key={i} style={styles.sourceItem}>
                      {source}
                    </li>
                  ))}
                </ul>
              </div>

              {profile.data_confidence.sources_unavailable.length > 0 && (
                <div style={styles.dataBlock}>
                  <span style={styles.dataLabel}>Sources Unavailable</span>
                  <ul style={styles.sourceList}>
                    {profile.data_confidence.sources_unavailable.map((source, i) => (
                      <li key={i} style={{ ...styles.sourceItem, color: '#718096' }}>
                        {source}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div style={styles.freshness}>{profile.data_confidence.freshness}</div>
            </div>

            {/* CTA - Only shows after animation complete */}
            {isAnimationComplete && (
              <div
                style={{
                  ...styles.panel,
                  ...styles.ctaPanel,
                  ...(visiblePanels.includes(6) ? styles.panelVisible : styles.panelHidden),
                }}
              >
                <p style={styles.ctaText}>
                  This took seconds with public data. Imagine what we build with full access.
                </p>
                <a
                  href="https://calendly.com/harnessai"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={styles.ctaButton}
                >
                  Schedule a deep analysis
                </a>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  )
}

const styles: { [key: string]: React.CSSProperties } = {
  main: {
    minHeight: '100vh',
    padding: '48px 24px',
    background: '#f5f5f7',
  },
  container: {
    maxWidth: '1200px',
    margin: '0 auto',
  },
  loadingContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '60vh',
    gap: '24px',
  },
  loadingText: {
    fontSize: '14px',
    color: '#6e6e73',
  },
  progressContainer: {
    width: '200px',
    height: '2px',
    background: 'rgba(0, 0, 0, 0.08)',
    overflow: 'hidden',
    borderRadius: '2px',
  },
  progressLine: {
    height: '100%',
    background: '#007aff',
    animation: 'progress-extend 3s ease-out forwards',
    borderRadius: '2px',
  },
  errorContainer: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '60vh',
  },
  errorText: {
    fontSize: '14px',
    color: '#6e6e73',
    background: 'rgba(255, 255, 255, 0.85)',
    backdropFilter: 'blur(40px)',
    WebkitBackdropFilter: 'blur(40px)',
    padding: '24px 32px',
    borderRadius: '12px',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
  },
  panel: {
    background: 'rgba(255, 255, 255, 0.85)',
    backdropFilter: 'blur(40px)',
    WebkitBackdropFilter: 'blur(40px)',
    borderRadius: '12px',
    padding: '24px',
    marginBottom: '16px',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
    border: '1px solid rgba(255, 255, 255, 0.6)',
    transition: 'opacity 0.2s ease-out, transform 0.2s ease-out',
  },
  panelHidden: {
    opacity: 0,
    transform: 'translateY(20px)',
  },
  panelVisible: {
    opacity: 1,
    transform: 'translateY(0)',
  },
  companyName: {
    fontSize: '32px',
    fontWeight: 600,
    color: '#1d1d1f',
    marginBottom: '12px',
    letterSpacing: '-0.02em',
  },
  headerMeta: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    flexWrap: 'wrap',
  },
  metaItem: {
    fontSize: '14px',
    color: '#6e6e73',
  },
  metaDivider: {
    color: 'rgba(0, 0, 0, 0.2)',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: '65% 35%',
    gap: '16px',
    marginTop: '16px',
  },
  leftColumn: {},
  rightColumn: {
    position: 'sticky' as const,
    top: '64px',
    alignSelf: 'start',
  },
  sectionHeader: {
    fontSize: '20px',
    fontWeight: 600,
    color: '#1d1d1f',
    marginBottom: '20px',
    paddingBottom: '12px',
    borderBottom: '1px solid rgba(0, 0, 0, 0.08)',
    letterSpacing: '-0.02em',
  },
  dataBlock: {
    marginBottom: '20px',
  },
  dataLabel: {
    display: 'block',
    fontSize: '11px',
    fontWeight: 600,
    color: '#86868b',
    marginBottom: '6px',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.8px',
  },
  dataValue: {
    fontSize: '14px',
    color: '#1d1d1f',
    lineHeight: 1.6,
  },
  techList: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '8px',
  },
  techTag: {
    display: 'inline-block',
    fontSize: '12px',
    color: '#1d1d1f',
    padding: '6px 12px',
    background: 'rgba(0, 122, 255, 0.08)',
    borderRadius: '6px',
    fontVariantNumeric: 'tabular-nums',
    fontWeight: 500,
  },
  observationList: {
    listStyle: 'none',
    padding: 0,
  },
  observationItem: {
    fontSize: '14px',
    color: '#1d1d1f',
    lineHeight: 1.6,
    marginBottom: '16px',
    paddingLeft: '16px',
    borderLeft: '3px solid #007aff',
  },
  confidenceScore: {
    display: 'flex',
    alignItems: 'baseline',
    gap: '8px',
    marginBottom: '24px',
  },
  scoreValue: {
    fontSize: '28px',
    fontWeight: 600,
    color: '#007aff',
    letterSpacing: '-0.02em',
  },
  scoreLabel: {
    fontSize: '13px',
    color: '#6e6e73',
  },
  sourceList: {
    listStyle: 'none',
    padding: 0,
    margin: 0,
  },
  sourceItem: {
    fontSize: '13px',
    color: '#1d1d1f',
    marginBottom: '6px',
    paddingLeft: '12px',
    position: 'relative' as const,
  },
  freshness: {
    fontSize: '12px',
    color: '#86868b',
    marginTop: '20px',
    paddingTop: '16px',
    borderTop: '1px solid rgba(0, 0, 0, 0.08)',
  },
  ctaPanel: {
    background: 'linear-gradient(135deg, rgba(0, 122, 255, 0.08), rgba(88, 86, 214, 0.08))',
    padding: '28px',
    marginTop: '16px',
  },
  ctaText: {
    fontSize: '15px',
    color: '#1d1d1f',
    marginBottom: '20px',
    lineHeight: 1.6,
    fontWeight: 500,
  },
  ctaButton: {
    display: 'inline-block',
    background: '#007aff',
    color: '#ffffff',
    padding: '12px 24px',
    fontSize: '14px',
    fontWeight: 500,
    textDecoration: 'none',
    borderRadius: '8px',
    boxShadow: '0 2px 8px rgba(0, 122, 255, 0.3)',
    transition: 'all 0.15s ease',
  },
}
