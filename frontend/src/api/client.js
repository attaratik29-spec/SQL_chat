import axios from 'axios'

// Determine the API base URL:
// - In production (e.g., deployed on Render), VITE_API_BASE_URL points to the backend URL
//   (e.g., "https://sql-chat-backend.onrender.com" or "https://sql-chat-backend.onrender.com/api").
// - In local development (when VITE_API_BASE_URL is not set), it defaults to '/api',
//   which Vite's local dev server automatically proxies to http://localhost:8000.
let cleanBaseUrl = (import.meta.env.VITE_API_BASE_URL || '').trim().replace(/\/+$/, '')

if (cleanBaseUrl && !cleanBaseUrl.startsWith('/') && !cleanBaseUrl.startsWith('http://') && !cleanBaseUrl.startsWith('https://')) {
  cleanBaseUrl = `https://${cleanBaseUrl}`
}

const resolvedBaseUrl = cleanBaseUrl
  ? cleanBaseUrl.endsWith('/api')
    ? cleanBaseUrl
    : `${cleanBaseUrl}/api`
  : '/api'

const api = axios.create({
  baseURL: resolvedBaseUrl,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

export const getSchema = () => api.get('/schema')

export const submitQuery = (query, contextHistory = []) =>
  api.post('/query', { query, context_history: contextHistory })

export const submitClarified = (originalQuery, answers, partialIntent) =>
  api.post('/query/clarified', {
    original_query:  originalQuery,
    answers,
    partial_intent:  partialIntent,
  })

export const submitDirectSql = (sql) =>
  api.post('/query/direct-sql', { sql })

export default api
