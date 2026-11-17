import { useCallback, useEffect, useState } from 'react'
import { api, hora } from '../api.js'

function MyBookings({ token }) {
  const [citas, setCitas] = useState([])
  const [error, setError] = useState('')

  const cargar = useCallback(() => {
    api('/reservas/mis-reservas', { token })
      .then(setCitas)
      .catch((e) => setError(e.message))
  }, [token])

  useEffect(() => {
    cargar()
  }, [cargar])

  async function cancelar(id) {
    setError('')
    try {
      await api(`/reservas/${id}/cancelar`, { method: 'PATCH', token })
      cargar()
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div className="card">
      <h2>Mis reservas</h2>
      {citas.length === 0 && <p>Aún no tienes reservas.</p>}
      <ul className="lista">
        {citas.map((c) => (
          <li key={c.id} className="fila">
            <div>
              <strong>{c.service_name}</strong>
              <span>
                {c.appointment_date} · {hora(c.start_time)} · {c.hairdresser_name}
              </span>
              <span className={`estado ${c.status}`}>{c.status}</span>
            </div>
            {c.status === 'CONFIRMED' && <button onClick={() => cancelar(c.id)}>Cancelar</button>}
          </li>
        ))}
      </ul>
      {error && <p className="error">{error}</p>}
    </div>
  )
}

export default MyBookings
