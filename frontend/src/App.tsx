import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Header } from './components/layout/Header';
import { OptimizerDashboardPage } from './pages/OptimizerDashboardPage';
import { VoyageSimulationPage } from './pages/VoyageSimulationPage';
import { useApp } from './context/AppContext';

const AppContent: React.FC = () => {
  const {
    showWeatherLayer,
    showRiskLayer,
    showOceanCurrents,
    setShowWeatherLayer,
    setShowRiskLayer,
    setShowOceanCurrents,
  } = useApp();

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#06131F] text-slate-200 font-sans">
      <Header
        showWeatherLayer={showWeatherLayer}
        showRiskLayer={showRiskLayer}
        showOceanCurrents={showOceanCurrents}
        onToggleWeather={() => setShowWeatherLayer(!showWeatherLayer)}
        onToggleRisk={() => setShowRiskLayer(!showRiskLayer)}
        onToggleOceanCurrents={() => setShowOceanCurrents(!showOceanCurrents)}
      />

      <Routes>
        <Route path="/" element={<OptimizerDashboardPage />} />
        <Route path="/simulation" element={<VoyageSimulationPage />} />
      </Routes>
    </div>
  );
};

const App: React.FC = () => {
  return <AppContent />;
};

export default App;
