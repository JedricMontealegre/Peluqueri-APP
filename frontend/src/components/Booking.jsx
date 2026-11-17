import { useEffect, useState } from 'react'
import { api, hora } from '../api.js'

function hoy() {
  const d = new Date()
  const mes = String(d.getMonth() + 1).padStart(2, '0')
  const dia = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${mes}-${dia}`
}

function Booking({ token }) {
  const [paso, setPaso] = useState(1)
  const [servicios, setServicios] = useState([])
  const [peluqueros, setPeluqueros] = useState([])
  const [servicio, setServicio] = useState(null)
  const [peluquero, setPeluquero] = useState('')
  const [fecha, setFecha] = useState(hoy())
  const [franjas, setFranjas] = useState([])
  const [franja, setFranja] = useState(null)
  const [invitado, setInvitado] = useState({ nombre: '', telefono: '', correo: '' })
  const [cita, setCita] = useState(null)
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)

  useEffect(() => {
    api('/servicios').then(setServicios).catch((e) => setError(e.message))
    api('/peluqueros/disponibles')
      .then((lista) => {
        setPeluqueros(lista)
        if (lista.length) setPeluquero(String(lista[0].id))
      })
      .catch((e) => setError(e.message))
  }, [])

  function elegirServicio(s) {
    setServicio(s)
    setError('')
    setPaso(2)
  }

  async function verHorarios() {
    setError('')
    setCargando(true)
    try {
      const data = await api(
        `/disponibilidad?peluquero_id=${peluquero}&fecha=${fecha}&servicio_id=${servicio.id}`,
      )
      setFranjas(data.slots)
      setFranja(null)
      setPaso(3)
    } catch (e) {
      setError(e.message)
    } finally {
      setCargando(false)
    }
  }

  async function confirmar(evento) {
    evento.preventDefault()
    setError('')
    setCargando(true)
    try {
      const body = {
        hairdresser_id: Number(peluquero),
        service_id: servicio.id,
        appointment_date: fecha,
        start_time: franja.start_time,
      }
      if (!token) {
        body.guest_name = invitado.nombre
        body.guest_phone = invitado.telefono
        body.guest_email = invitado.correo || null
      }
      const creada = await api('/reservas', { method: 'POST', body, token })
      setCita(creada)
    } catch (e) {
      setError(e.message)
    } finally {
      setCargando(false)
    }
  }

  function reiniciar() {
    setPaso(1)
    setServicio(null)
    setFranja(null)
    setCita(null)
    setError('')
  }

  if (cita) {
    return (
      <div className="card">
        <h2>¡Cita confirmada!</h2>
        <p>
          <strong>{cita.service_name}</strong> con {cita.hairdresser_name}
        </p>
        <p>
          {cita.appointment_date} a las {hora(cita.start_time)}
        </p>
        <p>Número de cita: {cita.id}</p>
        {!token && (
          <p className="nota">
            Guarda el número de cita y tu teléfono: los necesitas para cancelarla.
          </p>
        )}
        <button className="primary" onClick={reiniciar}>
          Agendar otra
        </button>
      </div>
    )
  }

  return (
    <div className="card">
      <p className="pasos">Paso {paso} de 4</p>

      {paso === 1 && (
        <>
          <h2>Elige un servicio</h2>
          <ul className="lista">
            {servicios.map((s) => (
              <li key={s.id}>
                <button className="opcion" onClick={() => elegirServicio(s)}>
                  <strong>{s.name}</strong>
                  <span>
                    {s.duration_minutes} min · ${s.price.toLocaleString('es-CO')}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </>
      )}

      {paso === 2 && (
        <>
          <h2>Elige fecha y peluquero</h2>
          <label>
            Peluquero
            <select value={peluquero} onChange={(e) => setPeluquero(e.target.value)}>
              {peluqueros.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.full_name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Fecha
            <input
              type="date"
              min={hoy()}
              value={fecha}
              onChange={(e) => setFecha(e.target.value)}
            />
          </label>
          <div className="botones">
            <button onClick={() => setPaso(1)}>Atrás</button>
            <button
              className="primary"
              disabled={!peluquero || !fecha || cargando}
              onClick={verHorarios}
            >
              {cargando ? 'Buscando...' : 'Ver horarios'}
            </button>
          </div>
        </>
      )}

      {paso === 3 && (
        <>
          <h2>Elige una hora</h2>
          {franjas.length === 0 && <p>No hay horarios libres ese día.</p>}
          <div className="franjas">
            {franjas.map((f) => (
              <button
                key={f.start_time}
                className={franja && franja.start_time === f.start_time ? 'franja activa' : 'franja'}
                onClick={() => setFranja(f)}
              >
                {hora(f.start_time)}
              </button>
            ))}
          </div>
          <div className="botones">
            <button onClick={() => setPaso(2)}>Atrás</button>
            <button className="primary" disabled={!franja} onClick={() => setPaso(4)}>
              Siguiente
            </button>
          </div>
        </>
      )}

      {paso === 4 && (
        <form onSubmit={confirmar}>
          <h2>Confirma tu cita</h2>
          <p>
            {servicio.name} · {fecha} · {hora(franja.start_time)}
          </p>

          {!token && (
            <>
              <label>
                Nombre
                <input
                  required
                  minLength={2}
                  value={invitado.nombre}
                  onChange={(e) => setInvitado({ ...invitado, nombre: e.target.value })}
                />
              </label>
              <label>
                Teléfono
                <input
                  type="tel"
                  required
                  minLength={6}
                  value={invitado.telefono}
                  onChange={(e) => setInvitado({ ...invitado, telefono: e.target.value })}
                />
              </label>
              <label>
                Correo (opcional)
                <input
                  type="email"
                  value={invitado.correo}
                  onChange={(e) => setInvitado({ ...invitado, correo: e.target.value })}
                />
              </label>
            </>
          )}

          <div className="botones">
            <button type="button" onClick={() => setPaso(3)}>
              Atrás
            </button>
            <button className="primary" disabled={cargando}>
              {cargando ? 'Reservando...' : 'Confirmar'}
            </button>
          </div>
        </form>
      )}

      {error && <p className="error">{error}</p>}
    </div>
  )
}

export default Booking
