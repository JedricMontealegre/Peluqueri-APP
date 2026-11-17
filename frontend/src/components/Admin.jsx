import { useCallback, useEffect, useState } from 'react'
import { api, hora, DIAS } from '../api.js'

function Admin({ token }) {
  const [peluqueros, setPeluqueros] = useState([])
  const [peluquero, setPeluquero] = useState('')
  const [horarios, setHorarios] = useState([])
  const [nuevo, setNuevo] = useState({ dia: '0', inicio: '08:00', fin: '18:00' })
  const [citaId, setCitaId] = useState('')
  const [mensaje, setMensaje] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    api('/admin/peluqueros', { token })
      .then((lista) => {
        setPeluqueros(lista)
        if (lista.length) setPeluquero(String(lista[0].id))
      })
      .catch((e) => setError(e.message))
  }, [token])

  const cargarHorarios = useCallback(() => {
    if (!peluquero) return
    api(`/admin/horarios?hairdresser_id=${peluquero}`, { token })
      .then(setHorarios)
      .catch((e) => setError(e.message))
  }, [peluquero, token])

  useEffect(() => {
    cargarHorarios()
  }, [cargarHorarios])

  async function accion(funcion, texto) {
    setError('')
    setMensaje('')
    try {
      await funcion()
      setMensaje(texto)
      cargarHorarios()
    } catch (e) {
      setError(e.message)
    }
  }

  function crear(evento) {
    evento.preventDefault()
    accion(
      () =>
        api('/admin/horarios', {
          method: 'POST',
          token,
          body: {
            hairdresser_id: Number(peluquero),
            day_of_week: Number(nuevo.dia),
            start_time: nuevo.inicio,
            end_time: nuevo.fin,
          },
        }),
      'Horario creado',
    )
  }

  function cambiarDisponible(h) {
    accion(
      () =>
        api(`/admin/horarios/${h.id}`, {
          method: 'PUT',
          token,
          body: { is_available: !h.is_available },
        }),
      'Horario actualizado',
    )
  }

  function borrar(h) {
    accion(() => api(`/admin/horarios/${h.id}`, { method: 'DELETE', token }), 'Horario eliminado')
  }

  function cancelarCita(evento) {
    evento.preventDefault()
    accion(
      () => api(`/reservas/${citaId}/cancelar`, { method: 'PATCH', token }),
      `Cita ${citaId} cancelada`,
    )
  }

  return (
    <>
      <div className="card">
        <h2>Horarios de peluqueros</h2>
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

        <ul className="lista">
          {horarios.map((h) => (
            <li key={h.id} className="fila">
              <div>
                <strong>{DIAS[h.day_of_week]}</strong>
                <span>
                  {hora(h.start_time)} - {hora(h.end_time)}
                  {h.is_available ? '' : ' (desactivado)'}
                </span>
              </div>
              <div className="botones">
                <button onClick={() => cambiarDisponible(h)}>
                  {h.is_available ? 'Desactivar' : 'Activar'}
                </button>
                <button onClick={() => borrar(h)}>Borrar</button>
              </div>
            </li>
          ))}
        </ul>

        <form onSubmit={crear}>
          <h3>Nuevo horario</h3>
          <label>
            Día
            <select value={nuevo.dia} onChange={(e) => setNuevo({ ...nuevo, dia: e.target.value })}>
              {DIAS.map((d, i) => (
                <option key={d} value={i}>
                  {d}
                </option>
              ))}
            </select>
          </label>
          <label>
            Inicio
            <input
              type="time"
              required
              value={nuevo.inicio}
              onChange={(e) => setNuevo({ ...nuevo, inicio: e.target.value })}
            />
          </label>
          <label>
            Fin
            <input
              type="time"
              required
              value={nuevo.fin}
              onChange={(e) => setNuevo({ ...nuevo, fin: e.target.value })}
            />
          </label>
          <button className="primary">Agregar</button>
        </form>
      </div>

      <form className="card" onSubmit={cancelarCita}>
        <h2>Cancelar una cita</h2>
        <label>
          Número de cita
          <input
            type="number"
            min="1"
            required
            value={citaId}
            onChange={(e) => setCitaId(e.target.value)}
          />
        </label>
        <button className="primary">Cancelar cita</button>
      </form>

      {mensaje && <p className="ok">{mensaje}</p>}
      {error && <p className="error">{error}</p>}
    </>
  )
}

export default Admin
