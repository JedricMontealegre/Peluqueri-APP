import { useState } from 'react'
import Login from './components/Login.jsx'
import Booking from './components/Booking.jsx'
import MyBookings from './components/MyBookings.jsx'
import Agenda from './components/Agenda.jsx'
import Admin from './components/Admin.jsx'

const TABS = {
  GUEST: [
    ['reservar', 'Reservar'],
    ['login', 'Ingresar'],
  ],
  CLIENT: [
    ['reservar', 'Reservar'],
    ['mis', 'Mis reservas'],
  ],
  HAIRDRESSER: [['agenda', 'Mi agenda']],
  ADMIN: [['admin', 'Administración']],
}

function leerSesion() {
  try {
    return JSON.parse(localStorage.getItem('session'))
  } catch {
    return null
  }
}

function App() {
  const [session, setSession] = useState(leerSesion)
  const [view, setView] = useState('reservar')

  const role = session ? session.user.role : 'GUEST'
  const tabs = TABS[role]
  const activeView = tabs.some(([id]) => id === view) ? view : tabs[0][0]
  const token = session ? session.access_token : null

  function iniciarSesion(data) {
    localStorage.setItem('session', JSON.stringify(data))
    setSession(data)
    setView(TABS[data.user.role][0][0])
  }

  function cerrarSesion() {
    localStorage.removeItem('session')
    setSession(null)
    setView('reservar')
  }

  return (
    <div className="app">
      <header>
        <h1>Peluqueri-APP</h1>
        {session && (
          <div className="user">
            <span>{session.user.full_name}</span>
            <button className="link" onClick={cerrarSesion}>
              Salir
            </button>
          </div>
        )}
      </header>

      <nav>
        {tabs.map(([id, label]) => (
          <button
            key={id}
            className={id === activeView ? 'tab active' : 'tab'}
            onClick={() => setView(id)}
          >
            {label}
          </button>
        ))}
      </nav>

      <main>
        {activeView === 'reservar' && <Booking token={token} />}
        {activeView === 'login' && <Login onLogin={iniciarSesion} />}
        {activeView === 'mis' && <MyBookings token={token} />}
        {activeView === 'agenda' && <Agenda token={token} />}
        {activeView === 'admin' && <Admin token={token} />}
      </main>
    </div>
  )
}

export default App
