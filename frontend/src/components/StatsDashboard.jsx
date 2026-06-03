import React from 'react';
import { Users, CheckCircle, Image, Sparkles, MapPin, Tag } from 'lucide-react';

export default function StatsDashboard({ stats, loading }) {
  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '100px 0', color: 'var(--text-secondary)' }}>
        <p>Loading overview statistics...</p>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="no-results">
        <p>No statistics data available. Verify backend is running.</p>
      </div>
    );
  }

  // Calculate percentages safely
  const photoCoveragePercent = stats.total_profiles > 0 
    ? Math.round((stats.profiles_with_photos / stats.total_profiles) * 100)
    : 0;

  const successPercent = stats.total_profiles > 0
    ? Math.round((stats.scraped_success / stats.total_profiles) * 100)
    : 0;

  const partialPercent = stats.total_profiles > 0
    ? Math.round((stats.scraped_partial / stats.total_profiles) * 100)
    : 0;

  const errorPercent = stats.total_profiles > 0
    ? Math.round((stats.scraped_error / stats.total_profiles) * 100)
    : 0;

  // Transform object dictionaries to sorted arrays for charting
  const categories = Object.entries(stats.by_category || {})
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  const maxCategoryCount = categories.length > 0 ? Math.max(...categories.map(c => c[1])) : 1;

  const locations = Object.entries(stats.by_location || {})
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  const maxLocationCount = locations.length > 0 ? Math.max(...locations.map(l => l[1])) : 1;

  return (
    <div className="stats-dashboard">
      
      {/* Top Cards grid */}
      <div className="stats-grid-top">
        <div className="stat-card">
          <div className="stat-icon-wrapper" style={{ color: 'var(--text-primary)', backgroundColor: 'var(--bg-tertiary)' }}>
            <Users size={24} />
          </div>
          <div>
            <div className="stat-num">{stats.total_profiles}</div>
            <div className="stat-label">Total Profiles</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper" style={{ color: 'var(--primary)', backgroundColor: 'var(--primary-light)' }}>
            <CheckCircle size={24} />
          </div>
          <div>
            <div className="stat-num">{stats.scraped_success}</div>
            <div className="stat-label">Scraped Successfully</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper" style={{ color: 'var(--verified-color)', backgroundColor: 'var(--verified-bg)' }}>
            <Image size={24} />
          </div>
          <div>
            <div className="stat-num">{stats.total_photos}</div>
            <div className="stat-label">Total Photos</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper" style={{ color: 'var(--warning-text)', backgroundColor: 'var(--warning-bg)' }}>
            <Sparkles size={24} />
          </div>
          <div>
            <div className="stat-num">{stats.profiles_with_photos}</div>
            <div className="stat-label">Profiles with Photos</div>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="dashboard-sections">
        {/* Scrape Status chart */}
        <div className="chart-card">
          <h2 className="chart-card-title">Scraper Process Quality</h2>
          <div className="chart-bar-list">
            <div className="chart-bar-row">
              <div className="chart-bar-labels">
                <span>Completed Scrapes (Success)</span>
                <span>{stats.scraped_success} ({successPercent}%)</span>
              </div>
              <div className="chart-bar-track">
                <div className="chart-bar-fill" style={{ width: `${successPercent}%`, background: 'var(--primary)' }}></div>
              </div>
            </div>

            <div className="chart-bar-row">
              <div className="chart-bar-labels">
                <span>Incomplete Scrapes (Partial)</span>
                <span>{stats.scraped_partial} ({partialPercent}%)</span>
              </div>
              <div className="chart-bar-track">
                <div className="chart-bar-fill" style={{ width: `${partialPercent}%`, background: 'var(--warning-text)' }}></div>
              </div>
            </div>

            <div className="chart-bar-row">
              <div className="chart-bar-labels">
                <span>Failed Pages (Error)</span>
                <span>{stats.scraped_error} ({errorPercent}%)</span>
              </div>
              <div className="chart-bar-track">
                <div className="chart-bar-fill" style={{ width: `${errorPercent}%`, background: 'var(--danger)' }}></div>
              </div>
            </div>
          </div>

          <div className="coverage-display" style={{ marginTop: '40px' }}>
            <div className="radial-progress">
              <svg width="140" height="140" viewBox="0 0 140 140" style={{ transform: 'rotate(-90deg)' }}>
                <circle cx="70" cy="70" r="55" stroke="var(--bg-tertiary)" strokeWidth="12" fill="transparent" />
                <circle 
                  cx="70" 
                  cy="70" 
                  r="55" 
                  stroke="var(--primary)" 
                  strokeWidth="12" 
                  fill="transparent" 
                  strokeDasharray={2 * Math.PI * 55}
                  strokeDashoffset={2 * Math.PI * 55 * (1 - photoCoveragePercent / 100)}
                  strokeLinecap="round"
                  style={{ transition: 'stroke-dashoffset 0.8s ease' }}
                />
              </svg>
              <div className="radial-text">{photoCoveragePercent}%</div>
            </div>
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)' }}>Photo Coverage Rate</span>
          </div>
        </div>

        {/* Categories and Locations */}
        <div className="chart-card">
          <h2 className="chart-card-title">Top Specialty Categories</h2>
          <div className="chart-bar-list" style={{ marginBottom: '32px' }}>
            {categories.length > 0 ? categories.map(([category, count]) => {
              const widthPct = Math.round((count / maxCategoryCount) * 100);
              return (
                <div className="chart-bar-row" key={category}>
                  <div className="chart-bar-labels">
                    <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><Tag size={14} style={{ color: 'var(--primary)' }} /> {category}</span>
                    <span>{count}</span>
                  </div>
                  <div className="chart-bar-track">
                    <div className="chart-bar-fill" style={{ width: `${widthPct}%` }}></div>
                  </div>
                </div>
              );
            }) : (
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', fontStyle: 'italic' }}>No categories identified yet. Scraper must process profiles first.</p>
            )}
          </div>

          <h2 className="chart-card-title">Top Expert Locations</h2>
          <div className="chart-bar-list">
            {locations.length > 0 ? locations.map(([loc, count]) => {
              const widthPct = Math.round((count / maxLocationCount) * 100);
              // Clean location string for display
              const displayLoc = loc.replace(/^Address:\s*/i, '').split(',').slice(-2).join(',').trim() || loc;
              return (
                <div className="chart-bar-row" key={loc}>
                  <div className="chart-bar-labels">
                    <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><MapPin size={14} style={{ color: 'var(--primary)' }} /> {displayLoc}</span>
                    <span>{count}</span>
                  </div>
                  <div className="chart-bar-track">
                    <div className="chart-bar-fill" style={{ width: `${widthPct}%`, background: 'linear-gradient(135deg, var(--primary), var(--primary-hover))' }}></div>
                  </div>
                </div>
              );
            }) : (
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', fontStyle: 'italic' }}>No location distributions available.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
