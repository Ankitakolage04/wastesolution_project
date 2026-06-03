import React, { useState, useEffect } from 'react';
import { LayoutDashboard, Users, Search, RefreshCw, ChevronLeft, ChevronRight, Tag, MapPin, Globe } from 'lucide-react';
import StatsDashboard from './components/StatsDashboard';
import ProfileCard from './components/ProfileCard';
import ProfileModal from './components/ProfileModal';

// Configurable API base url
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function App() {
  const [activeTab, setActiveTab] = useState('profiles'); // 'profiles' | 'dashboard'
  
  // Data States
  const [profiles, setProfiles] = useState([]);
  const [stats, setStats] = useState(null);
  const [totalProfiles, setTotalProfiles] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedProfile, setSelectedProfile] = useState(null);
  
  // Filter Dropdowns Lists
  const [categoriesList, setCategoriesList] = useState([]);
  const [tasksList, setTasksList] = useState([]);
  const [locationsList, setLocationsList] = useState([]);
  
  // Filter Values States
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedTask, setSelectedTask] = useState('');
  const [selectedLocation, setSelectedLocation] = useState('');
  const [sortBy, setSortBy] = useState('scraped_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [currentPage, setCurrentPage] = useState(1);
  
  // Loading and Error States
  const [loadingProfiles, setLoadingProfiles] = useState(false);
  const [loadingStats, setLoadingStats] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  // 1. Fetch dropdown options (on mount)
  useEffect(() => {
    async function fetchFilters() {
      try {
        const [catsRes, tasksRes, locsRes] = await Promise.all([
          fetch(`${API_BASE_URL}/profiles/filters/categories`),
          fetch(`${API_BASE_URL}/profiles/filters/tasks`),
          fetch(`${API_BASE_URL}/profiles/filters/locations`),
        ]);
        
        if (catsRes.ok) {
          const catsData = await catsRes.json();
          setCategoriesList(Object.keys(catsData));
        }
        if (tasksRes.ok) {
          const tasksData = await tasksRes.json();
          setTasksList(Object.keys(tasksData));
        }
        if (locsRes.ok) {
          const locsData = await locsRes.json();
          setLocationsList(Object.keys(locsData));
        }
      } catch (err) {
        console.error('Failed to load filter options:', err);
      }
    }
    fetchFilters();
  }, []);

  // 2. Fetch profiles (on filters/pagination change)
  useEffect(() => {
    if (activeTab !== 'profiles') return;

    async function fetchProfilesList() {
      setLoadingProfiles(true);
      setErrorMsg(null);
      try {
        const params = new URLSearchParams({
          page: currentPage.toString(),
          page_size: '12',
          sort_by: sortBy,
          sort_order: sortOrder,
        });

        if (searchQuery.trim()) params.append('q', searchQuery);
        if (selectedCategory) params.append('category', selectedCategory);
        if (selectedTask) params.append('task', selectedTask);
        if (selectedLocation) params.append('location', selectedLocation);

        const res = await fetch(`${API_BASE_URL}/profiles?${params.toString()}`);
        if (!res.ok) {
          throw new Error(`Server returned code ${res.status}`);
        }
        const data = await res.json();
        setProfiles(data.results || []);
        setTotalProfiles(data.total || 0);
        setTotalPages(data.pages || 1);
      } catch (err) {
        console.error('Error loading profiles:', err);
        setErrorMsg('Could not fetch expert profiles. Ensure the backend FastAPI server is running.');
      } finally {
        setLoadingProfiles(false);
      }
    }

    const timer = setTimeout(() => {
      fetchProfilesList();
    }, 300); // debounce input queries

    return () => clearTimeout(timer);
  }, [searchQuery, selectedCategory, selectedTask, selectedLocation, sortBy, sortOrder, currentPage, activeTab]);

  // 3. Fetch Overview Statistics (when dashboard is active or on mount)
  const fetchOverviewStats = async () => {
    setLoadingStats(true);
    try {
      const res = await fetch(`${API_BASE_URL}/profiles/stats/overview`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Error fetching statistics:', err);
    } finally {
      setLoadingStats(false);
    }
  };

  useEffect(() => {
    fetchOverviewStats();
  }, [activeTab]);

  // Reset all filters
  const resetFilters = () => {
    setSearchQuery('');
    setSelectedCategory('');
    setSelectedTask('');
    setSelectedLocation('');
    setSortBy('scraped_at');
    setSortOrder('desc');
    setCurrentPage(1);
  };

  return (
    <div className="app-container">
      {/* 1. Green Promo Top Bar */}
      <div className="promo-bar" id="adharaTopBar">
        <a href="https://adhara-viveka.com" target="_blank" rel="noopener noreferrer">
          Planning to start a business in environmental sector? Get industry insights &amp; market data
          <span className="promo-badge">Visit Adhara Viveka &rarr;</span>
        </a>
      </div>

      {/* 2. Main Header navigation */}
      <header className="main-header">
        <div className="header-inner">
          <a href="#" onClick={(e) => { e.preventDefault(); setActiveTab('profiles'); }} className="logo-link" title="Waste management consultants">
            <img className="logo-img" src="https://www.mywastesolution.com/images/mws/transperant-logo.webp" alt="mywastesolution logo" />
          </a>

          <nav className="header-nav">
            <a href="#" className={`nav-link ${activeTab === 'profiles' ? 'active' : ''}`} onClick={(e) => { e.preventDefault(); setActiveTab('profiles'); }}>Consultants</a>
            <a href="#" className={`nav-link ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={(e) => { e.preventDefault(); setActiveTab('dashboard'); }}>Stats Dashboard</a>
            <a href="https://www.mywastesolution.com/companies" target="_blank" rel="noopener noreferrer" className="nav-link">Service Providers</a>
            <a href="https://www.mywastesolution.com/machines-plants-and-equipments" target="_blank" rel="noopener noreferrer" className="nav-link">Online Marketplace</a>
            <a href="https://www.mywastesolution.com/consultancy-requirements" target="_blank" rel="noopener noreferrer" className="nav-link">Requirements</a>
            <a href="https://www.mywastesolution.com/consultancies" target="_blank" rel="noopener noreferrer" className="post-req-btn">Post Requirement</a>
            <a href="https://www.mywastesolution.com/login" target="_blank" rel="noopener noreferrer" className="login-link">Login</a>
          </nav>
        </div>
      </header>

      {/* 3. Sub-Header navigation bar */}
      <div className="sub-header">
        <div className="sub-header-inner">
          <a href="#" className={`sub-nav-link ${activeTab === 'profiles' ? 'active' : ''}`} onClick={(e) => { e.preventDefault(); setActiveTab('profiles'); }}>Consultants Directory</a>
          <a href="#" className={`sub-nav-link ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={(e) => { e.preventDefault(); setActiveTab('dashboard'); }}>System Aggregations</a>
          <a href="https://www.mywastesolution.com/companies" target="_blank" rel="noopener noreferrer" className="sub-nav-link">Environmental Companies</a>
          <a href="https://www.mywastesolution.com/machines-plants-and-equipments" target="_blank" rel="noopener noreferrer" className="sub-nav-link">Marketplace</a>
        </div>
      </div>

      {/* 4. Hero Banner */}
      {activeTab === 'profiles' ? (
        <section className="hero-banner">
          <h1 className="hero-title">Find Expert <span>Waste Management Consultants</span> in India</h1>
          <p className="hero-subtitle">Verified Consultants for Compliance, Treatment, and Strategic Waste Solutions</p>
        </section>
      ) : (
        <section className="hero-banner">
          <h1 className="hero-title">System <span>Scraper Statistics</span> & Overview</h1>
          <p className="hero-subtitle">Real-time statistics of circular economy experts from MongoDB database</p>
        </section>
      )}

      {/* 5. Main Content wrapper */}
      <main className="main-wrapper">
        {activeTab === 'profiles' ? (
          <div className="directory-layout">
            
            {/* Sidebar Filters */}
            <aside className="filters-sidebar">
              
              {/* Category Filter */}
              <div className="filter-block">
                <div className="filter-title">
                  <span>Categories</span>
                  <Tag size={14} />
                </div>
                <div className="filter-list">
                  <label className="filter-item">
                    <div className="filter-item-left">
                      <input 
                        type="radio" 
                        name="category"
                        checked={selectedCategory === ''} 
                        onChange={() => { setSelectedCategory(''); setCurrentPage(1); }} 
                        className="filter-radio" 
                      />
                      <span>All Categories</span>
                    </div>
                  </label>
                  {categoriesList.map(cat => (
                    <label key={cat} className="filter-item">
                      <div className="filter-item-left">
                        <input 
                          type="radio" 
                          name="category"
                          checked={selectedCategory === cat} 
                          onChange={() => { setSelectedCategory(cat); setCurrentPage(1); }} 
                          className="filter-radio" 
                        />
                        <span>{cat}</span>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {/* Task/Specialty Filter */}
              <div className="filter-block">
                <div className="filter-title">
                  <span>Specialties / Tasks</span>
                  <Users size={14} />
                </div>
                <div className="filter-list">
                  <label className="filter-item">
                    <div className="filter-item-left">
                      <input 
                        type="radio" 
                        name="task"
                        checked={selectedTask === ''} 
                        onChange={() => { setSelectedTask(''); setCurrentPage(1); }} 
                        className="filter-radio" 
                      />
                      <span>All Specialties</span>
                    </div>
                  </label>
                  {tasksList.map(task => (
                    <label key={task} className="filter-item">
                      <div className="filter-item-left">
                        <input 
                          type="radio" 
                          name="task"
                          checked={selectedTask === task} 
                          onChange={() => { setSelectedTask(task); setCurrentPage(1); }} 
                          className="filter-radio" 
                        />
                        <span>{task}</span>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {/* Location Filter */}
              <div className="filter-block">
                <div className="filter-title">
                  <span>Locations</span>
                  <MapPin size={14} />
                </div>
                <div className="filter-list">
                  <label className="filter-item">
                    <div className="filter-item-left">
                      <input 
                        type="radio" 
                        name="location"
                        checked={selectedLocation === ''} 
                        onChange={() => { setSelectedLocation(''); setCurrentPage(1); }} 
                        className="filter-radio" 
                      />
                      <span>All Locations</span>
                    </div>
                  </label>
                  {locationsList.map(loc => (
                    <label key={loc} className="filter-item">
                      <div className="filter-item-left">
                        <input 
                          type="radio" 
                          name="location"
                          checked={selectedLocation === loc} 
                          onChange={() => { setSelectedLocation(loc); setCurrentPage(1); }} 
                          className="filter-radio" 
                        />
                        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '180px' }}>{loc}</span>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

            </aside>

            {/* Results Grid Area */}
            <div className="results-container">
              
              {/* Search Toolbar */}
              <div className="cs-toolbar">
                <div className="search-input-wrapper">
                  <Search size={16} className="search-input-icon" />
                  <input 
                    type="text" 
                    placeholder="Search by expert name, bio keywords..."
                    value={searchQuery}
                    onChange={(e) => { setSearchQuery(e.target.value); setCurrentPage(1); }}
                    className="cs-search-input"
                  />
                </div>

                <div className="sort-selects">
                  <select value={sortBy} onChange={(e) => setSortBy(e.target.value)} className="cs-sort-select">
                    <option value="scraped_at">Sort By: Scrape Date</option>
                    <option value="name">Sort By: Name</option>
                    <option value="location">Sort By: Location</option>
                  </select>
                  <select value={sortOrder} onChange={(e) => setSortOrder(e.target.value)} className="cs-sort-select">
                    <option value="desc">Descending</option>
                    <option value="asc">Ascending</option>
                  </select>
                </div>
              </div>

              {/* Error messages if any */}
              {errorMsg && (
                <div style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--danger)', color: '#b91c1c', padding: '16px', borderRadius: '12px', marginBottom: '24px' }}>
                  {errorMsg}
                </div>
              )}

              {/* Meta stats bar */}
              <div className="results-meta">
                <div className="cs-count-badge">
                  <Users size={13} />
                  <span><strong>{totalProfiles}</strong> experts available</span>
                </div>
                {(searchQuery || selectedCategory || selectedTask || selectedLocation) && (
                  <button onClick={resetFilters} className="clear-filters-link">
                    Clear Filters
                  </button>
                )}
              </div>

              {/* Cards list container */}
              {loadingProfiles ? (
                <div style={{ display: 'flex', justifyContent: 'center', padding: '100px 0', color: 'var(--text-secondary)' }}>
                  <p>Retrieving matching expert profiles...</p>
                </div>
              ) : profiles.length > 0 ? (
                <div>
                  <div className="profiles-grid">
                    {profiles.map(prof => (
                      <ProfileCard 
                        key={prof._id} 
                        profile={prof} 
                        onClick={() => setSelectedProfile(prof)}
                      />
                    ))}
                  </div>

                  {/* Pagination */}
                  {totalPages > 1 && (
                    <div className="pagination-controls">
                      <button 
                        onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                        disabled={currentPage === 1 || loadingProfiles}
                        className="pagination-btn"
                        aria-label="Previous page"
                      >
                        <ChevronLeft size={18} />
                      </button>
                      <span style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 600 }}>
                        Page {currentPage} of {totalPages}
                      </span>
                      <button 
                        onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                        disabled={currentPage === totalPages || loadingProfiles}
                        className="pagination-btn"
                        aria-label="Next page"
                      >
                        <ChevronRight size={18} />
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <div className="no-results">
                  <p>No expert profiles matched your current filters.</p>
                  <p style={{ marginTop: '8px', fontSize: '13px', color: 'var(--text-muted)' }}>Try selecting other categories or clearing your search queries.</p>
                </div>
              )}

            </div>

          </div>
        ) : (
          <StatsDashboard stats={stats} loading={loadingStats} />
        )}
      </main>

      {/* 6. Footer section */}
      <footer className="main-footer">
        <div className="footer-inner">
          <div className="footer-logo">My Waste Solution</div>
          <ul className="footer-links">
            <li><a href="https://www.mywastesolution.com/terms-and-conditions" target="_blank" rel="noopener noreferrer" className="footer-link">Terms &amp; Conditions</a></li>
            <li><a href="https://www.mywastesolution.com/privacy-policy" target="_blank" rel="noopener noreferrer" className="footer-link">Privacy Policy</a></li>
            <li><a href="https://www.mywastesolution.com/dmca-policy" target="_blank" rel="noopener noreferrer" className="footer-link">DMCA Policy</a></li>
            <li><a href="https://www.mywastesolution.com/cookie-policy" target="_blank" rel="noopener noreferrer" className="footer-link">Cookie Policy</a></li>
            <li><a href="https://www.mywastesolution.com/refund-policy" target="_blank" rel="noopener noreferrer" className="footer-link">Refund Policy</a></li>
          </ul>
          <div className="footer-copyright">
            &copy; 2026 My Waste Solution. All rights reserved. Database Dashboard.
          </div>
        </div>
      </footer>

      {/* Modal Profile viewer */}
      {selectedProfile && (
        <ProfileModal 
          profile={selectedProfile} 
          onClose={() => setSelectedProfile(null)}
        />
      )}
    </div>
  );
}
