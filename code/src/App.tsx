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
  ErrorDisplay,
  GovLoginModal,
  GovMapComponent
} from './components';
import UploadPage from './components/UploadPage';
import type {
  Location,
  Pothole,
  PotholeStatus,
  PotholeSeverity,
  GovAuthCredentials,
  GovSignupData,
  RoadSegmentForm
} from './types';
import { DEFAULT_LOCATION } from './constants';
import { potholeApiService } from './services/potholeApiService';
import { govApiService } from './services/govApiService';
import './App.css';

function App() {
  const [currentPage, setCurrentPage] = useState<'map' | 'upload' | 'gov-auth' | 'road-health'>('map');
  const [showGovLogin, setShowGovLogin] = useState(false);
  const [isGovAuthenticated, setIsGovAuthenticated] = useState(false);
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
  const [roadHealthEnabled, setRoadHealthEnabled] = useState(false);

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

  const handleDateRangeChange = (start: Date | null, end: Date | null) => {
    if (start && end) {
      setDateRange({ start, end });
    } else {
      setDateRange(undefined); // Clear date range to show all potholes
    }
  };

  const handleRetry = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  const handleNavigateToUpload = () => {
    setCurrentPage('upload');
  };

  const handleNavigateToMap = () => {
    setCurrentPage('map');
  };

  // Government Authorization Handlers
  const handleNavigateToGovAuth = () => {
    setShowGovLogin(true);
  };

  // Road Health Handler
  const handleNavigateToRoadHealth = () => {
    setRoadHealthEnabled(true);
  };

  const handleRoadHealthFilter = (enabled: boolean) => {
    setRoadHealthEnabled(enabled);
  };

  const handleGovLogin = async (credentials: GovAuthCredentials): Promise<void> => {
    try {
      await govApiService.login(credentials);
      setIsGovAuthenticated(true);
      setShowGovLogin(false);
      setCurrentPage('gov-auth');
    } catch (error) {
      throw error; // Re-throw to be handled by the modal
    }
  };

  const handleGovSignup = async (data: GovSignupData): Promise<void> => {
    try {
      await govApiService.signup(data);
      // After successful signup, user should login
    } catch (error) {
      throw error; // Re-throw to be handled by the modal
    }
  };

  const handleGovLogout = () => {
    govApiService.logout();
    setIsGovAuthenticated(false);
    setCurrentPage('map');
  };

  const handleRoadSegmentSubmit = async (points: [number, number][], formData: RoadSegmentForm): Promise<void> => {
    try {
      await govApiService.createRoadSegment(points, formData);
    } catch (error) {
      throw error;
    }
  };

  // Check government authentication on app load
  useEffect(() => {
    if (govApiService.isAuthenticated()) {
      setIsGovAuthenticated(true);
    }
  }, []);

  // Render upload page
  if (currentPage === 'upload') {
    return <UploadPage onNavigateToMap={handleNavigateToMap} />;
  }

  // Render government authorization map (only if authenticated)
  if (currentPage === 'gov-auth' && isGovAuthenticated) {
    return (
      <GovMapComponent
        onSubmitSegment={handleRoadSegmentSubmit}
        onExit={handleGovLogout}
      />
    );
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
            roadHealthEnabled={roadHealthEnabled}
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
            onNavigateToGovAuth={handleNavigateToGovAuth}
            onNavigateToRoadHealth={handleNavigateToRoadHealth}
            currentLocation={currentLocation}
          />

          <FilterPanel
            onStatusFilter={handleStatusFilter}
            onSeverityFilter={handleSeverityFilter}
            onRoadHealthFilter={handleRoadHealthFilter}
            selectedStatus={statusFilter}
            selectedSeverity={severityFilter}
            roadHealthEnabled={roadHealthEnabled}
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

      {/* Government Login Modal */}
      <GovLoginModal
        isOpen={showGovLogin}
        onClose={() => setShowGovLogin(false)}
        onLogin={handleGovLogin}
        onSignup={handleGovSignup}
      />
    </div>
  );
}

export default App;
