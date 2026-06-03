import React from 'react';
import { MapPin, CheckCircle, ArrowRight } from 'lucide-react';

export default function ProfileCard({ profile, onClick }) {
  const getInitials = (name) => {
    if (!name) return 'WS';
    const parts = name.trim().split(/\s+/);
    if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  };

  // Safe checks for photo
  const hasPhoto = profile.photos && profile.photos.length > 0;
  const rawPhoto = hasPhoto ? profile.photos[0] : null;
  
  // Always fallback to the website's default placeholder avatar if missing
  const photoUrl = rawPhoto || "https://www.mywastesolution.com/images/user-avatar-placeholder.png";

  const displayRole = profile.task || profile.category || 'Environmental Consultant';
  const displayCategory = profile.category || 'Waste Management';

  // Check if verified in name or has a verified status
  const nameLower = (profile.name || '').toLowerCase();
  const isVerified = nameLower.includes('verified') || profile.scrape_status === 'success';
  const cleanName = (profile.name || 'Unnamed Expert').replace(/\s+Verified/i, '');

  return (
    <div className="profile-card" onClick={onClick}>
      <div className="card-header-horizontal">
        
        {/* Rounded Avatar with double fallbacks */}
        <div className="profile-avatar-wrapper">
          <img 
            src={photoUrl} 
            alt={cleanName} 
            className="profile-avatar-img"
            onError={(e) => {
              // Try to load the generic website placeholder if custom photo fails
              if (e.target.src !== "https://www.mywastesolution.com/images/user-avatar-placeholder.png") {
                e.target.src = "https://www.mywastesolution.com/images/user-avatar-placeholder.png";
              } else {
                // If even the placeholder fails, hide and show initials
                e.target.style.display = 'none';
                const parent = e.target.parentElement;
                if (!parent.querySelector('.profile-avatar-initials')) {
                  const fallback = document.createElement('div');
                  fallback.className = 'profile-avatar-initials';
                  fallback.innerText = getInitials(cleanName);
                  parent.appendChild(fallback);
                }
              }
            }}
          />
        </div>

        {/* Info detail block */}
        <div className="profile-details-column">
          <div className="name-verification-row">
            <h3 className="profile-name-text">{cleanName}</h3>
            
            {isVerified && (
              <span className="verified-badge-label">
                <CheckCircle size={10} fill="currentColor" color="white" />
                Verified
              </span>
            )}

            <span className={`status-badge-inline ${profile.scrape_status || 'success'}`}>
              {profile.scrape_status || 'success'}
            </span>
          </div>

          <div className="profile-role-tagline">
            Role: <strong>{displayRole}</strong>
          </div>

          {/* Waste Solution Categories tags */}
          <div className="cs-card-badges">
            {profile.category && (
              <span className="cs-card-badge legal">
                {displayCategory}
              </span>
            )}
            <span className="cs-card-badge treatment">Compliance</span>
            <span className="cs-card-badge buying">Strategic Expert</span>
          </div>
        </div>

      </div>

      {/* Description text */}
      <p className="profile-desc-block">
        {profile.description || 'Verified environmental and waste management industry professional offering strategic consultancy services.'}
      </p>

      {/* Location Row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--text-secondary)', marginTop: '12px' }}>
        <MapPin size={12} style={{ color: 'var(--primary)' }} />
        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {profile.location || 'New Delhi, Delhi NCR, India'}
        </span>
      </div>

      {/* Skills Pills */}
      <div className="profile-pill-tags">
        {profile.expertise && profile.expertise.slice(0, 2).map((exp, idx) => (
          <span key={`exp-${idx}`} className="profile-pill-tag expertise">
            {exp}
          </span>
        ))}
        {profile.skills && profile.skills.slice(0, 2).map((skill, idx) => (
          <span key={`skill-${idx}`} className="profile-pill-tag">
            {skill}
          </span>
        ))}
      </div>

      {/* Bottom Button */}
      <div className="card-action-bar">
        <button className="cs-view-profile-btn">
          <span>View Profile</span>
          <ArrowRight size={13} />
        </button>
      </div>
    </div>
  );
}
