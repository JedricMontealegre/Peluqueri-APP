import { useEffect, useState } from 'react'
import { api, hora } from '../api.js'

function hoy() {
  const d = new Date()
  const mes = String(d.getMonth() + 1).padStart(2, '0')
  const dia = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${mes}-${dia}`
}

function Agenda({ token }) {
  const [fecha, setFecha] = useState(hoy())
  const [citas, setCitas] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    const filtro = fecha ? `?fecha=${fecha}` : ''
    api(`/peluqueros/mis-citas${filtro}`, { token })
      .then((data) => {
        setCitas(data)
        setError('')
      })
      .catch((e) => setError(e.message))
  }, [fecha, token])

  return (
    <div className="card">
      <h2>Mi agenda</h2>
      <label>
        Fecha
        <input type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} />
      </label>
      <button className="link" onClick={() => setFecha('')}>
        Ver todas las fechas
      </button>

      {citas.length === 0 && <p>No hay citas.</p>}
      <ul className="lista">
        {citas.map((c) => (
          <li key={c.id} className="fila">
            <div>
              <strong>
                {hora(c.start_time)} - {hora(c.end_time)} · {c.service_name}
              </strong>
              <span>
                {c.appointment_date} · {c.client_name}
                {c.is_guest ? ' (invitado)' : ''}
              </span>
              <span>{c.client_phone}</span>
              <span className={`estado ${c.status}`}>{c.status}</span>
            </div>
          </li>
        ))}
      </ul>
      {error && <p className="error">{error}</p>}
    </div>
  )
}

export default Agenda
