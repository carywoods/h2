'use client'

import { useState } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

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
      const response = await fetch(`${API_URL}/intake`, {
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
        <div style={styles.container}>
          <p style={styles.successMessage}>
            Your operational profile is being generated.
          </p>
          <p style={styles.successSub}>
            You'll receive an email when it's ready.
          </p>
        </div>
      </main>
    )
  }

  return (
    <main style={styles.main}>
      <div style={styles.container}>
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
  container: {
    width: '100%',
    maxWidth: '400px',
  },
  tagline: {
    fontSize: '14px',
    color: '#4a5568',
    marginBottom: '32px',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '24px',
  },
  field: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  label: {
    fontSize: '12px',
    fontWeight: 500,
    color: '#1a2b4a',
  },
  error: {
    fontSize: '14px',
    color: '#c53030',
  },
  button: {
    marginTop: '8px',
  },
  successMessage: {
    fontSize: '18px',
    fontWeight: 500,
    marginBottom: '12px',
  },
  successSub: {
    fontSize: '14px',
    color: '#4a5568',
  },
}
