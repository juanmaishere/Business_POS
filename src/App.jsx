import React from 'react'
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import OrderPage from './pages/OrderPage'
import KitchenPage from './pages/KitchenPage'
import AdminPage from './pages/AdminPage'

export default function App(){
  return (
    <BrowserRouter>
      <div className="min-h-screen">
        <header className="bg-white shadow p-4 flex items-center justify-between">
          <h1 className="text-xl font-bold">Sansueña POS</h1>
          <nav className="space-x-3">
            <Link className="text-sm" to="/">Mozo</Link>
            <Link className="text-sm" to="/kitchen">Cocina</Link>
            <Link className="text-sm" to="/admin">Admin</Link>
          </nav>
        </header>

        <main className="p-6">
          <Routes>
            <Route path="/" element={<OrderPage/>} />
            <Route path="/kitchen" element={<KitchenPage/>} />
            <Route path="/admin" element={<AdminPage/>} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
