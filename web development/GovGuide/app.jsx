import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import ServiceDetails from './pages/ServiceDetails';
import Stats from './pages/Stats';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="service/:id" element={<ServiceDetails />} />
        <Route path="stats" element={<Stats />} />
        <Route path="*" element={<Home />} />
      </Route>
    </Routes>
  );
}

export default App;