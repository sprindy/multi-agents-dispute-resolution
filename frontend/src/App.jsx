import React, { useState } from 'react'

/*
  Travel History / Activity UI
  Inspired by ride-hailing activity screens.
  Each trip card has three bottom actions:
    - Rate & tip
    - Rebook
    - Advocate
*/

const riderTrips = [
  {
    id: 1,
    route: '910 Jurong West St 91 to NTU@one-north',
    price: 31.40,
    date: '8 Oct 2026, 18:05',
    status: 'completed',
    hasLightning: true,
  },
  {
    id: 2,
    route: 'China St Pick-up (Next to China Square Central carpark) to Sengkang',
    price: 44.98,
    date: '30 Sep 2026, 23:39',
    status: 'completed',
    hasLightning: false,
  },
  {
    id: 3,
    route: 'Lobby, INSEAD to Blu Jaz - Pekin Street',
    price: 25.90,
    date: '30 Sep 2026, 22:03',
    status: 'completed',
    hasLightning: true,
  },
  {
    id: 4,
    route: 'Lobby, INSEAD to 910 Jurong West St 91',
    price: null,
    date: '30 Sep 2026, 22:00',
    status: 'cancelled',
    hasLightning: false,
  },
  {
    id: 5,
    route: 'North Bridge Rd Entrance, Funan Mall to Graduate Hall, NUS',
    price: 73.60,
    date: '28 Sep 2026, 03:11',
    status: 'completed',
    hasLightning: false,
  },
  {
    id: 6,
    route: 'Lobby, MBS Hotel Tower 3 to Pure K 纯K - Funan Mall',
    price: 14.00,
    date: '27 Sep 2026, 23:48',
    status: 'completed',
    hasLightning: false,
  },
]

const driverTrips = [
  {
    id: 1,
    route: 'NTU@one-north to 910 Jurong West St 91',
    price: 31.40,
    date: '8 Oct 2026, 18:05',
    status: 'completed',
    hasLightning: true,
  },
  {
    id: 2,
    route: 'Sengkang to China St Pick-up (Next to China Square Central carpark)',
    price: 44.98,
    date: '30 Sep 2026, 23:39',
    status: 'completed',
    hasLightning: false,
  },
  {
    id: 3,
    route: 'Blu Jaz - Pekin Street to Lobby, INSEAD',
    price: 25.90,
    date: '30 Sep 2026, 22:03',
    status: 'completed',
    hasLightning: true,
  },
  {
    id: 4,
    route: '910 Jurong West St 91 to Lobby, INSEAD',
    price: null,
    date: '30 Sep 2026, 22:00',
    status: 'cancelled',
    hasLightning: false,
  },
  {
    id: 5,
    route: 'Graduate Hall, NUS to North Bridge Rd Entrance, Funan Mall',
    price: 73.60,
    date: '28 Sep 2026, 03:11',
    status: 'completed',
    hasLightning: false,
  },
  {
    id: 6,
    route: 'Pure K 纯K - Funan Mall to Lobby, MBS Hotel Tower 3',
    price: 14.00,
    date: '27 Sep 2026, 23:48',
    status: 'completed',
    hasLightning: false,
  },
]

/* ---------- Icons ---------- */

function CarIcon({ className = 'w-6 h-6' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M18.92 6.01C18.72 5.42 18.16 5 17.5 5h-11c-.66 0-1.21.42-1.42 1.01L3 12v8a1 1 0 001 1h1a1 1 0 001-1v-1h12v1a1 1 0 001 1h1a1 1 0 001-1v-8l-2.08-5.99zM6.5 16c-.83 0-1.5-.67-1.5-1.5S5.67 13 6.5 13s1.5.67 1.5 1.5S7.33 16 6.5 16zm11 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zM5 11l1.5-4.5h11L19 11H5z" />
    </svg>
  )
}

function LightningIcon({ className = 'w-3 h-3' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
    </svg>
  )
}

function ArrowRightIcon({ className = 'w-4 h-4' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12h14M12 5l7 7-7 7" />
    </svg>
  )
}

function ClockIcon({ className = 'w-5 h-5' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  )
}

function HomeIcon({ className = 'w-6 h-6' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
      <polyline points="9 22 9 12 15 12 15 22" />
    </svg>
  )
}

function CompassIcon({ className = 'w-6 h-6' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" />
    </svg>
  )
}

function ScanIcon({ className = 'w-7 h-7' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 7V5a2 2 0 012-2h2" />
      <path d="M17 3h2a2 2 0 012 2v2" />
      <path d="M21 17v2a2 2 0 01-2 2h-2" />
      <path d="M7 21H5a2 2 0 01-2-2v-2" />
      <line x1="3" y1="12" x2="21" y2="12" />
    </svg>
  )
}

function MessageIcon({ className = 'w-6 h-6' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
    </svg>
  )
}

function PersonIcon({ className = 'w-5 h-5' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="8" r="4" />
      <path d="M4 20c0-4 4-6 8-6s8 2 8 6" />
    </svg>
  )
}

function SwapIcon({ className = 'w-4 h-4' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M7 10l-4-4 4-4" />
      <path d="M3 6h13a4 4 0 014 4" />
      <path d="M17 14l4 4-4 4" />
      <path d="M21 18H8a4 4 0 01-4-4" />
    </svg>
  )
}

/* ---------- Components ---------- */

function StatusBar() {
  return (
    <div className="flex items-center justify-between px-6 pt-3 pb-2 text-sm font-semibold">
      <span>21:03</span>
      <div className="flex items-center gap-1.5">
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 3C7.46 3 3.34 4.78.29 7.67c-.24.25-.29.63-.13.93l11 18a1 1 0 001.68 0l11-18a1 1 0 00-.13-.93C20.66 4.78 16.54 3 12 3z" />
        </svg>
        <span>5G</span>
        <svg className="w-6 h-3" viewBox="0 0 24 12" fill="currentColor">
          <rect x="2" y="3" width="18" height="7" rx="1.5" />
          <rect x="4" y="5" width="14" height="3" rx="0.5" fill="white" />
        </svg>
      </div>
    </div>
  )
}

function Header({ role, onToggle }) {
  return (
    <div className="flex items-center justify-between px-5 py-3">
      <h1 className="text-3xl font-bold tracking-tight text-gray-900">Activity</h1>
      <div className="flex items-center gap-2">
        <button
          onClick={onToggle}
          className="flex items-center gap-2 rounded-full border border-gray-200 bg-white px-3 py-2 text-sm font-semibold text-gray-700 shadow-sm transition hover:bg-gray-50 active:scale-95"
          title={`Switch to ${role === 'rider' ? 'driver' : 'rider'}`}
        >
          <PersonIcon className="w-5 h-5" />
          <span className="capitalize">{role}</span>
          <SwapIcon className="w-4 h-4 text-gray-400" />
        </button>
        <button className="flex items-center gap-1.5 rounded-full border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm transition hover:bg-gray-50">
          <ClockIcon className="w-4 h-4" />
          History
        </button>
      </div>
    </div>
  )
}

function TripIcon({ hasLightning }) {
  return (
    <div className="relative flex-shrink-0">
      <div className="flex h-11 w-11 items-center justify-center rounded-full bg-brand-lightGreen text-brand-green">
        <CarIcon className="w-6 h-6" />
      </div>
      {hasLightning && (
        <div className="absolute -left-0.5 -top-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-brand-green text-white shadow-sm">
          <LightningIcon className="w-3 h-3" />
        </div>
      )}
    </div>
  )
}

function ActionButton({ label, variant, onClick }) {
  const variants = {
    rate: 'text-brand-green hover:bg-brand-lightGreen',
    rebook: 'text-brand-blue hover:bg-blue-50',
    advocate: 'text-brand-indigo hover:bg-indigo-50',
  }

  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-1 rounded-lg px-3 py-1.5 text-sm font-semibold transition ${variants[variant]}`}
    >
      {label}
      <ArrowRightIcon className="w-4 h-4" />
    </button>
  )
}

function TripCard({ trip, onAction }) {
  const isCancelled = trip.status === 'cancelled'

  return (
    <div className="px-5 py-4">
      <div className="flex gap-4">
        <TripIcon hasLightning={trip.hasLightning} />

        <div className="flex flex-1 flex-col">
          <div className="flex items-start justify-between gap-3">
            <div className="flex flex-col">
              {isCancelled && (
                <span className="mb-0.5 text-sm font-bold text-red-500">Cancelled</span>
              )}
              <h3 className="text-[15px] font-semibold leading-snug text-gray-900">
                {trip.route}
              </h3>
            </div>
            {!isCancelled && (
              <span className="whitespace-nowrap text-[15px] font-semibold text-gray-900">
                S${trip.price.toFixed(2)}
              </span>
            )}
          </div>

          <p className="mt-1 text-sm text-gray-500">{trip.date}</p>

          <div className="mt-3 flex flex-wrap items-center gap-1">
            <ActionButton
              label="Rate & tip"
              variant="rate"
              onClick={() => onAction('Rate & tip', trip.route)}
            />
            <ActionButton
              label="Rebook"
              variant="rebook"
              onClick={() => onAction('Rebook', trip.route)}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

function BottomNav() {
  return (
    <div className="absolute bottom-0 left-0 right-0 border-t border-gray-100 bg-white px-2 pb-safe pt-2">
      <div className="flex items-center justify-around">
        <NavItem icon={<HomeIcon />} label="Home" />
        <NavItem icon={<CompassIcon />} label="Moments" />

        {/* Center scan/pay button */}
        <button className="relative -mt-6 flex h-14 w-14 items-center justify-center rounded-full bg-brand-green text-white shadow-lg shadow-brand-green/30 transition hover:scale-105 active:scale-95">
          <ScanIcon className="w-7 h-7" />
        </button>

        <NavItem icon={<CompassIcon className="w-6 h-6" />} label="Activity" active />
        <NavItem icon={<MessageIcon />} label="Messages" badge={1} />
      </div>
    </div>
  )
}

function NavItem({ icon, label, active, badge }) {
  return (
    <button className="relative flex flex-col items-center gap-1 px-3 py-1.5">
      <div className={`${active ? 'text-brand-green' : 'text-gray-400'}`}>{icon}</div>
      <span className={`text-[10px] font-medium ${active ? 'text-brand-green' : 'text-gray-400'}`}>
        {label}
      </span>
      {badge && (
        <span className="absolute right-1.5 top-0.5 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
          {badge}
        </span>
      )}
    </button>
  )
}

function Toast({ message, onClose }) {
  if (!message) return null
  return (
    <div className="absolute left-4 right-4 top-4 z-50 animate-[fadeIn_0.2s_ease-out]">
      <div className="rounded-xl bg-gray-900 px-4 py-3 text-sm font-medium text-white shadow-xl">
        <div className="flex items-center justify-between gap-3">
          <span>{message}</span>
          <button onClick={onClose} className="text-gray-400 hover:text-white">×</button>
        </div>
      </div>
    </div>
  )
}

/* ---------- Main App ---------- */

function App() {
  const [toast, setToast] = useState(null)
  const [role, setRole] = useState('rider')

  const handleAction = (action, route) => {
    setToast(`${action}: ${route}`)
    setTimeout(() => setToast(null), 3000)
  }

  const handleToggle = () => {
    setRole((prev) => (prev === 'rider' ? 'driver' : 'rider'))
  }

  const trips = role === 'rider' ? riderTrips : driverTrips

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100 p-0 sm:p-6">
      <div className="relative w-full max-w-md overflow-hidden bg-white sm:min-h-[800px] sm:rounded-[2.5rem] sm:shadow-soft">
        <StatusBar />
        <Header role={role} onToggle={handleToggle} />

        <h2 className="px-5 pb-2 pt-1 text-lg font-bold text-gray-900">
          {role === 'rider' ? 'Recent' : 'Recent Drives'}
        </h2>

        <div className="h-[calc(100vh-220px)] overflow-y-auto pb-28 no-scrollbar sm:h-[600px]">
          {trips.map((trip) => (
            <TripCard key={trip.id} trip={trip} onAction={handleAction} />
          ))}
        </div>

        <BottomNav />
        <Toast message={toast} onClose={() => setToast(null)} />
      </div>
    </div>
  )
}

export default App
