import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
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
