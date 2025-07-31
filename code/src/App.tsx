import { useState, useEffect } from 'react';
import {
  LocationSearch,
  MapComponent,
  ControlPanel,
  PotholeStatsPanel,
  FilterPanel,
  Timeline,
  Footer,
  LoadingSpinner,
  ErrorDisplay
} from './components';
import UploadPage from './components/UploadPage';
import type { Location, Pothole, PotholeStatus, PotholeSeverity } from './types';
import { DEFAULT_LOCATION } from './constants';
import { potholeApiService } from './services/potholeApiService';
import './App.css';

function App() {
  const [currentPage, setCurrentPage] = useState<'map' | 'upload'>('map');
  const [currentLocation, setCurrentLocation] = useState<Location>(DEFAULT_LOCATION);
  const [showSatellite, setShowSatellite] = useState(false);
  const [showMajorRoadsOnly, setShowMajorRoadsOnly] = useState(false);
  const [statusFilter, setStatusFilter] = useState<PotholeStatus | 'all'>('all');
  const [severityFilter, setSeverityFilter] = useState<PotholeSeverity | 'all'>('all');
  const [dateRange, setDateRange] = useState<{ start: Date; end: Date } | undefined>();
  const [potholes, setPotholes] = useState<Pothole[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Load potholes data with optimization
  useEffect(() => {
    const loadPotholes = async () => {
      setLoading(true);
      setError(null);

      try {
        // Use simplified loading - no pagination
        const filters = {
          status: statusFilter !== 'all' ? statusFilter : undefined,
          severity: severityFilter !== 'all' ? severityFilter : undefined,
        };

        const potholesList = await potholeApiService.getPotholes(filters);
        setPotholes(potholesList);
        console.log(`App: Loaded ${potholesList.length} potholes for UI`);
      } catch (err) {
        console.error('Failed to load potholes:', err);
        setError('Failed to load pothole data. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    loadPotholes();
  }, [statusFilter, severityFilter, refreshTrigger]);

  const handleLocationSelect = (location: Location) => {
    setCurrentLocation(location);
  };

  const handleToggleSatellite = () => {
    setShowSatellite(prev => !prev);
  };

  const handleToggleRoads = () => {
    setShowMajorRoadsOnly(prev => !prev);
  };

  const handleResetLocation = () => {
    setCurrentLocation(DEFAULT_LOCATION);
  };

  const handleStatusFilter = (status: PotholeStatus | 'all') => {
    setStatusFilter(status);
  };

  const handleSeverityFilter = (severity: PotholeSeverity | 'all') => {
    setSeverityFilter(severity);
  };

  const handleDateRangeChange = (start: Date, end: Date) => {
    setDateRange({ start, end });
  };

  const handleRetry = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  const handleNavigateToUpload = () => {
    setCurrentPage('upload');
  };

  const handleNavigateToMap = () => {
    setCurrentPage('map');
    // Refresh data when returning to map
    setRefreshTrigger(prev => prev + 1);
  };

  // Render upload page
  if (currentPage === 'upload') {
    return <UploadPage onNavigateToMap={handleNavigateToMap} />;
  }

  return (
    <div className="app">
      {/* Floating Search Bar */}
      <div className="floating-search">
        <LocationSearch
          onLocationSelect={handleLocationSelect}
          placeholder="Search for any location..."
        />
      </div>

      {/* Main Content */}
      <main className="app-main">
        <div className="map-section">
          <MapComponent
            location={currentLocation}
            showSatellite={showSatellite}
            showMajorRoadsOnly={showMajorRoadsOnly}
            statusFilter={statusFilter}
            severityFilter={severityFilter}
            dateRange={dateRange}
            refreshTrigger={refreshTrigger}
          />

          {/* Timeline at bottom of map */}
          <div className="timeline-container">
            <Timeline
              potholes={potholes}
              onDateRangeChange={handleDateRangeChange}
            />
          </div>
        </div>

        <aside className="controls-section">
          <ControlPanel
            showSatellite={showSatellite}
            showMajorRoadsOnly={showMajorRoadsOnly}
            onToggleSatellite={handleToggleSatellite}
            onToggleRoads={handleToggleRoads}
            onResetLocation={handleResetLocation}
            onNavigateToUpload={handleNavigateToUpload}
            currentLocation={currentLocation}
          />

          <FilterPanel
            onStatusFilter={handleStatusFilter}
            onSeverityFilter={handleSeverityFilter}
            selectedStatus={statusFilter}
            selectedSeverity={severityFilter}
          />

          <PotholeStatsPanel />

          {loading && (
            <div className="stats-loading">
              <LoadingSpinner />
              <span>Loading data...</span>
            </div>
          )}

          {error && (
            <ErrorDisplay
              error={error}
              onRetry={handleRetry}
              className="compact-error"
            />
          )}
        </aside>
      </main>

      <Footer />
    </div>
  );
}

export default App;
