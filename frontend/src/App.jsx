import React, { useEffect, useRef, useState } from 'react'

/*
  Travel History / Activity UI
  Inspired by ride-hailing activity screens.
  Each trip card has two bottom actions:
    - Rate & tip
    - Rebook
  Tapping a card opens a detailed trip view.
  "Report an issue" opens a Help Center chat.
*/

const riderTrips = [
  {
    id: 1,
    route: '910 Jurong West St 91 to NTU@one-north',
    price: 31.40,
    date: '08 Oct 2026, 06:04PM',
    status: 'completed',
    hasLightning: true,
    bookingId: 'A-9UAXPJ4GX5JRAV',
    driver: 'Tan Tiong Heng',
    service: 'Standard | Car or taxi',
    distance: '15.72 km',
    duration: '23 min',
    pickup: { place: '910 Jurong West St 91', time: '6:15 PM' },
    dropoff: { place: 'NTU@one-north', time: '6:39 PM' },
    payment: { type: 'VISA', last4: '0518' },
  },
  {
    id: 2,
    route: 'China St Pick-up (Next to China Square Central carpark) to Sengkang',
    price: 44.98,
    date: '30 Sep 2026, 11:39PM',
    status: 'completed',
    hasLightning: false,
    bookingId: 'A-7KPLM2NQW8VXTE',
    driver: 'Lim Ah Kow',
    service: 'Standard | Car or taxi',
    distance: '18.40 km',
    duration: '31 min',
    pickup: { place: 'China St Pick-up', time: '11:39 PM' },
    dropoff: { place: 'Sengkang', time: '12:10 AM' },
    payment: { type: 'VISA', last4: '4242' },
  },
  {
    id: 3,
    route: 'Lobby, INSEAD to Blu Jaz - Pekin Street',
    price: 25.90,
    date: '30 Sep 2026, 10:03PM',
    status: 'completed',
    hasLightning: true,
    bookingId: 'A-3BHFJ9DKL2PQRT',
    driver: 'Sarah Tan',
    service: 'Standard | Car or taxi',
    distance: '6.80 km',
    duration: '14 min',
    pickup: { place: 'Lobby, INSEAD', time: '10:03 PM' },
    dropoff: { place: 'Blu Jaz - Pekin Street', time: '10:17 PM' },
    payment: { type: 'VISA', last4: '0518' },
  },
  {
    id: 4,
    route: 'Lobby, INSEAD to 910 Jurong West St 91',
    price: null,
    date: '30 Sep 2026, 10:00PM',
    status: 'cancelled',
    hasLightning: false,
    bookingId: 'A-5CMXW1ZYP9NBVD',
    driver: 'Not assigned',
    service: 'Standard | Car or taxi',
    distance: '0.00 km',
    duration: '0 min',
    pickup: { place: 'Lobby, INSEAD', time: '10:00 PM' },
    dropoff: { place: '910 Jurong West St 91', time: '—' },
    payment: { type: 'VISA', last4: '0518' },
  },
  {
    id: 5,
    route: 'North Bridge Rd Entrance, Funan Mall to Graduate Hall, NUS',
    price: 73.60,
    date: '28 Sep 2026, 03:11AM',
    status: 'completed',
    hasLightning: false,
    bookingId: 'A-2QWER4TYUI7OPA',
    driver: 'Muhammad Faizal',
    service: 'Standard | Car or taxi',
    distance: '22.50 km',
    duration: '28 min',
    pickup: { place: 'North Bridge Rd Entrance, Funan Mall', time: '3:11 AM' },
    dropoff: { place: 'Graduate Hall, NUS', time: '3:39 AM' },
    payment: { type: 'VISA', last4: '8888' },
  },
  {
    id: 6,
    route: 'Lobby, MBS Hotel Tower 3 to Pure K 纯K - Funan Mall',
    price: 14.00,
    date: '27 Sep 2026, 11:48PM',
    status: 'completed',
    hasLightning: false,
    bookingId: 'A-8ZXCV1BNMA3SDF',
    driver: 'Koh Wei Ling',
    service: 'Standard | Car or taxi',
    distance: '4.20 km',
    duration: '9 min',
    pickup: { place: 'Lobby, MBS Hotel Tower 3', time: '11:48 PM' },
    dropoff: { place: 'Pure K 纯K - Funan Mall', time: '11:57 PM' },
    payment: { type: 'VISA', last4: '1234' },
  },
]

const driverTrips = [
  {
    id: 1,
    route: 'NTU@one-north to 910 Jurong West St 91',
    price: 31.40,
    date: '08 Oct 2026, 06:04PM',
    status: 'completed',
    hasLightning: true,
    bookingId: 'A-9UAXPJ4GX5JRAV',
    driver: 'Passenger: Tan Tiong Heng',
    service: 'Standard | Car or taxi',
    distance: '15.72 km',
    duration: '23 min',
    pickup: { place: 'NTU@one-north', time: '6:15 PM' },
    dropoff: { place: '910 Jurong West St 91', time: '6:39 PM' },
    payment: { type: 'VISA', last4: '0518' },
  },
  {
    id: 2,
    route: 'Sengkang to China St Pick-up (Next to China Square Central carpark)',
    price: 44.98,
    date: '30 Sep 2026, 11:39PM',
    status: 'completed',
    hasLightning: false,
    bookingId: 'A-7KPLM2NQW8VXTE',
    driver: 'Passenger: Lim Ah Kow',
    service: 'Standard | Car or taxi',
    distance: '18.40 km',
    duration: '31 min',
    pickup: { place: 'Sengkang', time: '11:39 PM' },
    dropoff: { place: 'China St Pick-up', time: '12:10 AM' },
    payment: { type: 'VISA', last4: '4242' },
  },
  {
    id: 3,
    route: 'Blu Jaz - Pekin Street to Lobby, INSEAD',
    price: 25.90,
    date: '30 Sep 2026, 10:03PM',
    status: 'completed',
    hasLightning: true,
    bookingId: 'A-3BHFJ9DKL2PQRT',
    driver: 'Passenger: Sarah Tan',
    service: 'Standard | Car or taxi',
    distance: '6.80 km',
    duration: '14 min',
    pickup: { place: 'Blu Jaz - Pekin Street', time: '10:03 PM' },
    dropoff: { place: 'Lobby, INSEAD', time: '10:17 PM' },
    payment: { type: 'VISA', last4: '0518' },
  },
  {
    id: 4,
    route: '910 Jurong West St 91 to Lobby, INSEAD',
    price: null,
    date: '30 Sep 2026, 10:00PM',
    status: 'cancelled',
    hasLightning: false,
    bookingId: 'A-5CMXW1ZYP9NBVD',
    driver: 'Not assigned',
    service: 'Standard | Car or taxi',
    distance: '0.00 km',
    duration: '0 min',
    pickup: { place: '910 Jurong West St 91', time: '10:00 PM' },
    dropoff: { place: 'Lobby, INSEAD', time: '—' },
    payment: { type: 'VISA', last4: '0518' },
  },
  {
    id: 5,
    route: 'Graduate Hall, NUS to North Bridge Rd Entrance, Funan Mall',
    price: 73.60,
    date: '28 Sep 2026, 03:11AM',
    status: 'completed',
    hasLightning: false,
    bookingId: 'A-2QWER4TYUI7OPA',
    driver: 'Passenger: Muhammad Faizal',
    service: 'Standard | Car or taxi',
    distance: '22.50 km',
    duration: '28 min',
    pickup: { place: 'Graduate Hall, NUS', time: '3:11 AM' },
    dropoff: { place: 'North Bridge Rd Entrance, Funan Mall', time: '3:39 AM' },
    payment: { type: 'VISA', last4: '8888' },
  },
  {
    id: 6,
    route: 'Pure K 纯K - Funan Mall to Lobby, MBS Hotel Tower 3',
    price: 14.00,
    date: '27 Sep 2026, 11:48PM',
    status: 'completed',
    hasLightning: false,
    bookingId: 'A-8ZXCV1BNMA3SDF',
    driver: 'Passenger: Koh Wei Ling',
    service: 'Standard | Car or taxi',
    distance: '4.20 km',
    duration: '9 min',
    pickup: { place: 'Pure K 纯K - Funan Mall', time: '11:48 PM' },
    dropoff: { place: 'Lobby, MBS Hotel Tower 3', time: '11:57 PM' },
    payment: { type: 'VISA', last4: '1234' },
  },
]

const riderIssueCategories = [
  'Route deviation',
  'No-show / cancellation charge',
  'Fare / pricing dispute',
  'Property damage / cleaning fee',
  'Safety / driver misconduct',
]

const driverIssueCategories = [
  'Route deviation',
  'No-show / cancellation charge',
  'Fare / pricing dispute',
  'Property damage / cleaning fee',
  'Safety / misconduct dispute',
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

function ChevronLeftIcon({ className = 'w-6 h-6' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M15 18l-6-6 6-6" />
    </svg>
  )
}

function ChevronDownIcon({ className = 'w-5 h-5' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 9l6 6 6-6" />
    </svg>
  )
}

function ChevronRightIcon({ className = 'w-5 h-5' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 18l6-6-6-6" />
    </svg>
  )
}

function StarIcon({ className = 'w-8 h-8' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
    </svg>
  )
}

function CopyIcon({ className = 'w-5 h-5' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
      <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
    </svg>
  )
}

function DownloadIcon({ className = 'w-6 h-6' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  )
}

function HeadsetIcon({ className = 'w-6 h-6' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 18v-6a9 9 0 0118 0v6" />
      <path d="M21 19a2 2 0 01-2 2h-1a2 2 0 01-2-2v-3a2 2 0 012-2h3zM3 19a2 2 0 002 2h1a2 2 0 002-2v-3a2 2 0 00-2-2H3z" />
    </svg>
  )
}

function RedoIcon({ className = 'w-6 h-6' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 7v6h-6" />
      <path d="M3 17a9 9 0 019-9 9 9 0 016.24 2.5L21 13" />
    </svg>
  )
}

function CloseIcon({ className = 'w-6 h-6' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  )
}

function SparklesIcon({ className = 'w-4 h-4' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 3L14.5 8.5L20 11L14.5 13.5L12 19L9.5 13.5L4 11L9.5 8.5Z" />
    </svg>
  )
}

function SendIcon({ className = 'w-5 h-5' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  )
}

function MapPinIcon({ className = 'w-5 h-5', color = 'currentColor' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill={color} stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z" />
      <circle cx="12" cy="10" r="3" fill="white" />
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

function TripCard({ trip, onAction, onSelect }) {
  const isCancelled = trip.status === 'cancelled'

  return (
    <div
      className="cursor-pointer px-5 py-4 transition active:bg-gray-50"
      onClick={() => onSelect(trip)}
    >
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
              onClick={(e) => {
                e.stopPropagation()
                onAction('Rate & tip', trip.route)
              }}
            />
            <ActionButton
              label="Rebook"
              variant="rebook"
              onClick={(e) => {
                e.stopPropagation()
                onAction('Rebook', trip.route)
              }}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

function DetailHeader({ date, onBack }) {
  return (
    <div className="flex items-center px-5 py-3">
      <button
        onClick={onBack}
        className="flex h-9 w-9 items-center justify-center rounded-full text-gray-800 transition hover:bg-gray-100"
      >
        <ChevronLeftIcon className="w-6 h-6" />
      </button>
      <div className="flex flex-1 items-center justify-center gap-1">
        <span className="text-base font-bold text-gray-900">{date}</span>
        <ChevronDownIcon className="w-4 h-4 text-gray-500" />
      </div>
      <div className="w-9" />
    </div>
  )
}

function BookingIdRow({ id, onCopy }) {
  return (
    <div className="flex items-center justify-between px-5 py-3">
      <span className="text-gray-500">Booking ID</span>
      <button
        onClick={onCopy}
        className="flex items-center gap-1.5 text-sm font-semibold text-gray-900 transition hover:text-brand-green"
      >
        {id}
        <CopyIcon className="w-4 h-4 text-gray-400" />
      </button>
    </div>
  )
}

function RatingCard() {
  return (
    <div className="mx-5 rounded-2xl border border-gray-200 bg-white p-4">
      <p className="text-sm leading-relaxed text-gray-700">
        Help us improve your Grab experience by rating this ride.
      </p>
      <div className="mt-3 flex justify-center gap-2">
        {[1, 2, 3, 4, 5].map((star) => (
          <button key={star} className="text-gray-300 transition hover:text-yellow-400">
            <StarIcon className="w-8 h-8" />
          </button>
        ))}
      </div>
    </div>
  )
}

function DriverRow({ name }) {
  const initials = name
    .split(' ')
    .map((n) => n[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()

  return (
    <div className="flex items-center gap-3 px-5 py-4">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-blue-400 to-purple-500 text-sm font-bold text-white">
        {initials || '?'}
      </div>
      <span className="font-semibold text-gray-900">{name}</span>
    </div>
  )
}

function MapPlaceholder() {
  return (
    <svg className="h-full w-full" viewBox="0 0 400 200" preserveAspectRatio="xMidYMid slice">
      {/* Water */}
      <rect width="400" height="200" fill="#E0F2FE" />
      {/* Land masses */}
      <path d="M-20,140 Q60,110 130,130 T260,115 T420,145 V220 H-20 Z" fill="#DCFCE7" />
      <path d="M260,-20 Q300,40 280,100 T320,220 H420 V-20 Z" fill="#DCFCE7" />
      {/* Roads */}
      <path d="M-10,80 Q80,85 140,75 T260,90 T410,70" fill="none" stroke="white" strokeWidth="3" />
      <path d="M50,-10 Q60,60 55,120 T70,210" fill="none" stroke="white" strokeWidth="2" />
      {/* Route */}
      <path
        d="M80,60 C120,55 150,110 210,115 S290,150 340,135"
        fill="none"
        stroke="#00B14F"
        strokeWidth="6"
        strokeLinecap="round"
      />
      {/* Pins */}
      <g transform="translate(80,60)">
        <circle r="14" fill="#3B82F6" stroke="white" strokeWidth="2" />
        <circle r="5" fill="white" />
      </g>
      <g transform="translate(340,135)">
        <circle r="14" fill="#EF4444" stroke="white" strokeWidth="2" />
        <circle r="5" fill="white" />
      </g>
      {/* Watermark */}
      <text x="10" y="190" fontSize="10" fill="#64748B" fontFamily="sans-serif">
        GrabMaps
      </text>
    </svg>
  )
}

function LocationRow({ type, place, time }) {
  return (
    <div className="flex gap-3 py-2">
      <div className="mt-0.5 flex-shrink-0">
        {type === 'pickup' ? (
          <MapPinIcon className="w-5 h-5" color="#3B82F6" />
        ) : (
          <MapPinIcon className="w-5 h-5" color="#EF4444" />
        )}
      </div>
      <div>
        <p className="font-semibold text-gray-900">{place}</p>
        <p className="text-sm text-gray-500">{time}</p>
      </div>
    </div>
  )
}

function MapCard({ trip }) {
  return (
    <div className="mx-5 overflow-hidden rounded-2xl border border-gray-200 bg-white">
      <div className="relative h-48 w-full bg-blue-50">
        <MapPlaceholder />
      </div>
      <div className="flex items-center justify-between px-4 py-3">
        <span className="text-sm font-semibold text-gray-800">{trip.service}</span>
        <span className="text-sm text-gray-500">
          {trip.distance} · {trip.duration}
        </span>
      </div>
      <div className="border-t border-gray-100 px-4 py-3">
        <LocationRow type="pickup" place={trip.pickup.place} time={trip.pickup.time} />
        <LocationRow type="dropoff" place={trip.dropoff.place} time={trip.dropoff.time} />
      </div>
    </div>
  )
}

function PaymentCard({ payment }) {
  return (
    <div className="mx-5 flex items-center gap-3 rounded-2xl border border-gray-200 bg-white px-4 py-3">
      <div className="flex h-8 w-12 items-center justify-center rounded-md bg-blue-900 text-xs font-bold text-white">
        VISA
      </div>
      <span className="font-semibold text-gray-900">{payment.last4}</span>
    </div>
  )
}

function TotalRow({ price }) {
  return (
    <button className="mx-5 flex items-center justify-between rounded-2xl border border-gray-200 bg-white px-4 py-4 transition hover:bg-gray-50">
      <span className="text-lg font-semibold text-gray-900">Total</span>
      <div className="flex items-center gap-1 text-lg font-bold text-gray-900">
        S${price.toFixed(2)}
        <ChevronRightIcon className="w-5 h-5 text-gray-400" />
      </div>
    </button>
  )
}

function DetailActionRow({ icon, label, onClick }) {
  return (
    <button
      onClick={onClick}
      className="flex w-full items-center justify-between border-b border-gray-100 px-4 py-4 transition hover:bg-gray-50 last:border-0"
    >
      <div className="flex items-center gap-3">
        <div className="text-gray-700">{icon}</div>
        <span className="font-semibold text-gray-900">{label}</span>
      </div>
      <ChevronRightIcon className="w-5 h-5 text-gray-400" />
    </button>
  )
}

function DetailActionList({ onExport, onReport, onRebook }) {
  return (
    <div className="mx-5 overflow-hidden rounded-2xl border border-gray-200 bg-white">
      <DetailActionRow icon={<DownloadIcon className="w-6 h-6" />} label="Export receipt" onClick={onExport} />
      <DetailActionRow icon={<HeadsetIcon className="w-6 h-6" />} label="Report an issue" onClick={onReport} />
      <DetailActionRow icon={<RedoIcon className="w-6 h-6" />} label="Rebook" onClick={onRebook} />
    </div>
  )
}

function TripDetail({ trip, onBack, onAction, onReport }) {
  const isCancelled = trip.status === 'cancelled'

  return (
    <div className="h-[calc(100vh-120px)] overflow-y-auto pb-8 no-scrollbar sm:h-[680px]">
      <DetailHeader date={trip.date} onBack={onBack} />
      <BookingIdRow
        id={trip.bookingId}
        onCopy={() => onAction('Copied booking ID', trip.bookingId)}
      />
      {!isCancelled && <RatingCard />}
      <DriverRow name={trip.driver} />
      <MapCard trip={trip} />
      <div className="mt-4">
        <PaymentCard payment={trip.payment} />
      </div>
      {!isCancelled && (
        <div className="mt-4">
          <TotalRow price={trip.price} />
        </div>
      )}
      <div className="mt-4">
        <DetailActionList
          onExport={() => onAction('Export receipt', trip.route)}
          onReport={onReport}
          onRebook={() => onAction('Rebook', trip.route)}
        />
      </div>
      <div className="h-6" />
    </div>
  )
}

function HelpCenterHeader({ onClose }) {
  return (
    <div className="flex items-center px-5 py-3">
      <button
        onClick={onClose}
        className="flex h-9 w-9 items-center justify-center rounded-full text-gray-800 transition hover:bg-gray-100"
      >
        <CloseIcon className="w-6 h-6" />
      </button>
      <span className="flex-1 text-center text-lg font-bold text-gray-900">Help Center</span>
      <div className="w-9" />
    </div>
  )
}

function TripSummary({ trip }) {
  const destination = trip.route.split(' to ').pop()
  return (
    <div className="mx-5 flex items-center gap-3 rounded-xl border border-gray-100 bg-gray-50 px-4 py-3">
      <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-brand-lightGreen text-brand-green">
        <CarIcon className="w-5 h-5" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="truncate text-sm font-bold text-gray-900">Ride to {destination}</p>
        <p className="text-xs text-gray-500">{trip.date}</p>
      </div>
      <span className="flex-shrink-0 text-sm font-bold text-gray-900">
        {trip.price ? `S$${trip.price.toFixed(2)}` : '-'}
      </span>
    </div>
  )
}

function ChatBubble({ sender, text }) {
  const isBot = sender === 'bot'
  return (
    <div className={`mb-3 flex ${isBot ? 'justify-start' : 'justify-end'}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
          isBot
            ? 'rounded-tl-none bg-gray-100 text-gray-800'
            : 'rounded-tr-none bg-brand-lightGreen text-brand-green'
        }`}
      >
        {text}
      </div>
    </div>
  )
}

function HelpCenter({ trip, onClose, role }) {
  const issueCategories = role === 'driver' ? driverIssueCategories : riderIssueCategories
  const [messages, setMessages] = useState([
    { sender: 'bot', text: `Hello, ${role === 'driver' ? 'Driver' : 'Rider'}123 👋` },
    { sender: 'bot', text: "Thanks for reaching out! Choose an option below or describe your issue in one single message, and we'll try to find the right solution for you. 🙏" },
  ])
  const [input, setInput] = useState('')
  const scrollRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  const handleCategory = (category) => {
    setMessages((prev) => [...prev, { sender: 'user', text: category }])
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { sender: 'bot', text: `Thanks for reporting "${category}". Our support team will review this and get back to you shortly.` },
      ])
    }, 500)
  }

  const handleSend = () => {
    const text = input.trim()
    if (!text) return
    setMessages((prev) => [...prev, { sender: 'user', text }])
    setInput('')
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { sender: 'bot', text: "Thanks for your message. We've passed it to our support team." },
      ])
    }, 500)
  }

  return (
    <div className="flex h-[calc(100vh-40px)] flex-col sm:h-[760px]">
      <HelpCenterHeader onClose={onClose} />
      <TripSummary trip={trip} />

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-3 no-scrollbar">
        <div className="mb-3 flex items-center gap-1 text-xs text-gray-500">
          <SparklesIcon className="w-3.5 h-3.5" />
          Powered by AI
        </div>
        {messages.map((msg, idx) => (
          <ChatBubble key={idx} sender={msg.sender} text={msg.text} />
        ))}
        <div className="mt-2 flex flex-col items-end gap-2">
          {issueCategories.map((category) => (
            <button
              key={category}
              onClick={() => handleCategory(category)}
              className="max-w-[85%] rounded-2xl bg-brand-lightGreen px-4 py-2 text-right text-sm font-semibold text-brand-green transition hover:bg-green-100"
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      <div className="border-t border-gray-100 bg-white px-4 py-3">
        <div className="flex items-center gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Type a message"
            className="flex-1 rounded-full border border-gray-300 px-4 py-2.5 text-sm outline-none focus:border-brand-green"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim()}
            className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-brand-green text-white transition hover:bg-green-600 disabled:opacity-50"
          >
            <SendIcon className="w-5 h-5" />
          </button>
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
  const [selectedTrip, setSelectedTrip] = useState(null)
  const [showHelpCenter, setShowHelpCenter] = useState(false)

  const handleAction = (action, route) => {
    setToast(`${action}: ${route}`)
    setTimeout(() => setToast(null), 3000)
  }

  const handleToggle = () => {
    setRole((prev) => (prev === 'rider' ? 'driver' : 'rider'))
    setSelectedTrip(null)
    setShowHelpCenter(false)
  }

  const handleSelectTrip = (trip) => {
    setSelectedTrip(trip)
    setShowHelpCenter(false)
  }

  const handleBackFromDetail = () => {
    setSelectedTrip(null)
    setShowHelpCenter(false)
  }

  const trips = role === 'rider' ? riderTrips : driverTrips

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100 p-0 sm:p-6">
      <div className="relative w-full max-w-md overflow-hidden bg-white sm:min-h-[800px] sm:rounded-[2.5rem] sm:shadow-soft">
        <StatusBar />

        {showHelpCenter && selectedTrip ? (
          <HelpCenter trip={selectedTrip} role={role} onClose={() => setShowHelpCenter(false)} />
        ) : selectedTrip ? (
          <TripDetail
            trip={selectedTrip}
            onBack={handleBackFromDetail}
            onAction={handleAction}
            onReport={() => setShowHelpCenter(true)}
          />
        ) : (
          <>
            <Header role={role} onToggle={handleToggle} />

            <h2 className="px-5 pb-2 pt-1 text-lg font-bold text-gray-900">
              {role === 'rider' ? 'Recent' : 'Recent Drives'}
            </h2>

            <div className="h-[calc(100vh-220px)] overflow-y-auto pb-28 no-scrollbar sm:h-[600px]">
              {trips.map((trip) => (
                <TripCard
                  key={trip.id}
                  trip={trip}
                  onAction={handleAction}
                  onSelect={handleSelectTrip}
                />
              ))}
            </div>

            <BottomNav />
          </>
        )}

        <Toast message={toast} onClose={() => setToast(null)} />
      </div>
    </div>
  )
}

export default App
