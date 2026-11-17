# Frontend

Interfaz de Peluqueri-APP hecha con React y Vite, sin librerías adicionales.

## Desarrollo local

```bash
npm install
npm run dev
```

La dirección de la API se toma de la variable `VITE_API_URL`. Si no existe, usa `http://localhost:8000/api/v1`.

## Estructura

```
src/
├── main.jsx               punto de entrada
├── App.jsx                sesión, pestañas según el rol
├── api.js                 función para llamar a la API y utilidades
├── index.css              estilos
└── components/
    ├── Booking.jsx        reserva en 4 pasos
    ├── Login.jsx          inicio de sesión y registro
    ├── MyBookings.jsx     reservas del cliente
    ├── Agenda.jsx         agenda del peluquero
    └── Admin.jsx          horarios y cancelación de citas
```
