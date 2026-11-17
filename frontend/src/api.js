const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

export async function api(path, { method = 'GET', body, token } = {}) {
  const headers = {}
  if (body) headers['Content-Type'] = 'application/json'
  if (token) headers.Authorization = `Bearer ${token}`

  const response = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })

  if (response.status === 204) return null

  const data = await response.json().catch(() => null)

  if (!response.ok) {
    const detail = data && data.detail
    throw new Error(
      typeof detail === 'string' ? detail : 'Datos inválidos, revisa el formulario',
    )
  }

  return data
}

export function hora(texto) {
  return texto.slice(0, 5)
}

export const DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
