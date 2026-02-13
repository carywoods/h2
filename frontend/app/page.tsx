'use client'

import { useState } from 'react'

export default function IntakePage() {
  const [companyName, setCompanyName] = useState('')
  const [companyUrl, setCompanyUrl] = useState('')
  const [email, setEmail] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsSubmitting(true)

    try {
      const response = await fetch('/api/intake', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          company_name: companyName,
          company_url: companyUrl,
          email: email,
        }),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Failed to submit')
      }

      setSubmitted(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (submitted) {
    return (
      <main style={styles.main}>
        <div style={styles.window}>
          <div style={styles.titleBar}>
            <div style={styles.trafficLights}>
              <div style={{...styles.trafficLight, background: '#ff5f57'}} />
              <div style={{...styles.trafficLight, background: '#febc2e'}} />
              <div style={{...styles.trafficLight, background: '#28c840'}} />
            </div>
            <div style={styles.windowTitle}>HarnessAI</div>
          </div>
          <div style={styles.windowContent}>
            <div style={styles.successIcon}>✓</div>
            <p style={styles.successMessage}>
              Your operational profile is being generated.
            </p>
            <p style={styles.successSub}>
              You'll receive an email when it's ready.
            </p>
          </div>
        </div>
      </main>
    )
  }

  return (
    <main style={styles.main}>
      <div style={styles.window}>
        <div style={styles.titleBar}>
          <div style={styles.trafficLights}>
            <div style={{...styles.trafficLight, background: '#ff5f57'}} />
            <div style={{...styles.trafficLight, background: '#febc2e'}} />
            <div style={{...styles.trafficLight, background: '#28c840'}} />
          </div>
          <div style={styles.windowTitle}>HarnessAI</div>
        </div>
        <div style={styles.windowContent}>
          <p style={styles.tagline}>Request your operational profile.</p>

          <form onSubmit={handleSubmit} style={styles.form}>
            <div style={styles.field}>
              <label htmlFor="companyName" style={styles.label}>
                Company Name
              </label>
              <input
                id="companyName"
                type="text"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                required
                placeholder="Acme Inc."
              />
            </div>

            <div style={styles.field}>
              <label htmlFor="companyUrl" style={styles.label}>
                Company URL
              </label>
              <input
                id="companyUrl"
                type="text"
                value={companyUrl}
                onChange={(e) => setCompanyUrl(e.target.value)}
                required
                placeholder="acme.com"
              />
            </div>

            <div style={styles.field}>
              <label htmlFor="email" style={styles.label}>
                Business Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="you@acme.com"
              />
            </div>

            {error && <p style={styles.error}>{error}</p>}

            <button type="submit" disabled={isSubmitting} style={styles.button}>
              {isSubmitting ? 'Submitting...' : 'Submit'}
            </button>
          </form>
        </div>
      </div>
    </main>
  )
}

const styles: { [key: string]: React.CSSProperties } = {
  main: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '48px 24px',
  },
  window: {
    width: '100%',
    maxWidth: '480px',
    background: 'rgba(255, 255, 255, 0.85)',
    backdropFilter: 'blur(40px)',
    WebkitBackdropFilter: 'blur(40px)',
    borderRadius: '12px',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12), 0 2px 8px rgba(0, 0, 0, 0.08)',
    border: '1px solid rgba(255, 255, 255, 0.6)',
    overflow: 'hidden',
  },
  titleBar: {
    height: '52px',
    background: 'rgba(246, 246, 246, 0.8)',
    borderBottom: '1px solid rgba(0, 0, 0, 0.08)',
    display: 'flex',
    alignItems: 'center',
    padding: '0 16px',
    position: 'relative',
  },
  trafficLights: {
    display: 'flex',
    gap: '8px',
  },
  trafficLight: {
    width: '12px',
    height: '12px',
    borderRadius: '50%',
    boxShadow: 'inset 0 0.5px 1px rgba(0, 0, 0, 0.2)',
  },
  windowTitle: {
    position: 'absolute',
    left: '50%',
    transform: 'translateX(-50%)',
    fontSize: '13px',
    fontWeight: 500,
    color: '#1d1d1f',
    letterSpacing: '-0.01em',
  },
  windowContent: {
    padding: '32px',
  },
  tagline: {
    fontSize: '22px',
    fontWeight: 600,
    color: '#1d1d1f',
    marginBottom: '28px',
    letterSpacing: '-0.02em',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  field: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  label: {
    fontSize: '13px',
    fontWeight: 500,
    color: '#1d1d1f',
  },
  error: {
    fontSize: '13px',
    color: '#ff3b30',
    background: 'rgba(255, 59, 48, 0.08)',
    padding: '10px 12px',
    borderRadius: '8px',
  },
  button: {
    marginTop: '8px',
  },
  successIcon: {
    width: '64px',
    height: '64px',
    borderRadius: '50%',
    background: 'linear-gradient(135deg, #34c759, #30d158)',
    color: 'white',
    fontSize: '36px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    margin: '0 auto 24px',
    boxShadow: '0 4px 16px rgba(52, 199, 89, 0.3)',
  },
  successMessage: {
    fontSize: '20px',
    fontWeight: 600,
    marginBottom: '12px',
    textAlign: 'center',
    color: '#1d1d1f',
    letterSpacing: '-0.02em',
  },
  successSub: {
    fontSize: '14px',
    color: '#6e6e73',
    textAlign: 'center',
  },
}
