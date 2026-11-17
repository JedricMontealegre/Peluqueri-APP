import { useState } from 'react'
import { api } from '../api.js'

function Login({ onLogin }) {
  const [registro, setRegistro] = useState(false)
  const [form, setForm] = useState({ full_name: '', email: '', phone: '', password: '' })
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)

  function cambiar(campo, valor) {
    setForm({ ...form, [campo]: valor })
  }

  async function enviar(evento) {
    evento.preventDefault()
    setError('')
    setCargando(true)
    try {
      if (registro) {
        await api('/auth/register', {
          method: 'POST',
          body: {
            full_name: form.full_name,
            email: form.email,
            phone: form.phone || null,
            password: form.password,
          },
        })
      }
      const data = await api('/auth/login', {
        method: 'POST',
        body: { email: form.email, password: form.password },
      })
      onLogin(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setCargando(false)
    }
  }

  return (
    <form className="card" onSubmit={enviar}>
      <h2>{registro ? 'Crear cuenta' : 'Iniciar sesión'}</h2>

      {registro && (
        <>
          <label>
            Nombre completo
            <input
              required
              minLength={2}
              value={form.full_name}
              onChange={(e) => cambiar('full_name', e.target.value)}
            />
          </label>
          <label>
            Teléfono
            <input
              type="tel"
              value={form.phone}
              onChange={(e) => cambiar('phone', e.target.value)}
            />
          </label>
        </>
      )}

      <label>
        Correo
        <input
          type="email"
          required
          value={form.email}
          onChange={(e) => cambiar('email', e.target.value)}
        />
      </label>
      <label>
        Contraseña
        <input
          type="password"
          required
          minLength={6}
          value={form.password}
          onChange={(e) => cambiar('password', e.target.value)}
        />
      </label>

      {error && <p className="error">{error}</p>}

      <button className="primary" disabled={cargando}>
        {cargando ? 'Enviando...' : registro ? 'Registrarme' : 'Entrar'}
      </button>
      <button type="button" className="link" onClick={() => setRegistro(!registro)}>
        {registro ? 'Ya tengo cuenta' : 'Crear una cuenta'}
      </button>
    </form>
  )
}

export default Login
