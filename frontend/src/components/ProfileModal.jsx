import React, { useState } from 'react';
import { X, MapPin, Mail, Globe, Briefcase, Award, Shield, FileText, ChevronLeft, ChevronRight, Link2, ImageIcon, Sparkles, CheckCircle } from 'lucide-react';

export default function ProfileModal({ profile, onClose }) {
  const [photoIndex, setPhotoIndex] = useState(0);

  if (!profile) return null;

  const hasPhotos = profile.photos && profile.photos.length > 0;
  
  // Use crawled photo list, or fallback to the website's default avatar if empty
  const photoUrls = hasPhotos ? profile.photos : ["https://www.mywastesolution.com/images/user-avatar-placeholder.png"];

  const handlePrevPhoto = (e) => {
    e.stopPropagation();
    setPhotoIndex((prev) => (prev === 0 ? photoUrls.length - 1 : prev - 1));
  };

  const handleNextPhoto = (e) => {
    e.stopPropagation();
    setPhotoIndex((prev) => (prev === photoUrls.length - 1 ? 0 : prev + 1));
  };

  // Helper to extract initials for placeholder avatar
  const getInitials = (name) => {
    if (!name) return 'WS';
    const parts = name.trim().split(/\s+/);
    if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  };

  // Format scraped date
  const formatScrapedDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' });
    } catch (e) {
      return dateStr;
    }
  };

  const nameLower = (profile.name || '').toLowerCase();
  const isVerified = nameLower.includes('verified') || profile.scrape_status === 'success';
  const cleanName = (profile.name || 'Unnamed Expert').replace(/\s+Verified/i, '');

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} aria-label="Close modal">
          <X size={20} />
        </button>

        <div className="modal-body">
          {/* Modal Header/Hero */}
          <div className="modal-hero">
            <div className="modal-img-wrapper">
              <img 
                src={photoUrls[0]} 
                alt={cleanName} 
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                onError={(e) => {
                  if (e.target.src !== "https://www.mywastesolution.com/images/user-avatar-placeholder.png") {
                    e.target.src = "https://www.mywastesolution.com/images/user-avatar-placeholder.png";
                  } else {
                    e.target.style.display = 'none';
                    const parent = e.target.parentElement;
                    if (!parent.querySelector('.profile-avatar-initials')) {
                      const fallback = document.createElement('div');
                      fallback.className = 'profile-avatar-initials';
                      fallback.style.fontSize = '2.5rem';
                      fallback.innerText = getInitials(cleanName);
                      parent.appendChild(fallback);
                    }
                  }
                }}
              />
            </div>

            <div className="modal-details">
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                <h2 className="modal-name">{cleanName}</h2>
                {isVerified && (
                  <span className="verified-badge-label" style={{ marginBottom: '6px' }}>
                    <CheckCircle size={10} fill="currentColor" color="white" />
                    Verified Expert
                  </span>
                )}
              </div>
              
              <div className="modal-info-meta">
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <MapPin size={14} style={{ color: 'var(--primary)' }} />
                  {profile.location || 'New Delhi, Delhi NCR, India'}
                </span>
                
                {profile.contact_email && (
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Mail size={14} style={{ color: 'var(--primary)' }} />
                    <a href={`mailto:${profile.contact_email}`} className="meta-link">{profile.contact_email}</a>
                  </span>
                )}

                {profile.website && (
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Globe size={14} style={{ color: 'var(--primary)' }} />
                    <a href={profile.website} target="_blank" rel="noopener noreferrer" className="meta-link">Visit Website</a>
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Grid Layout split */}
          <div className="section-grid">
            {/* Left Column: Details */}
            <div>
              <div className="modal-section-title">
                <FileText size={16} style={{ color: 'var(--primary)' }} /> About / Overview
              </div>
              <p className="modal-bio">{profile.description || 'Verified waste management consultant providing professional advisory, compliance support, CTE/CTO licensing, EPR audits, and strategic green industry insights.'}</p>

              {/* Experience Timeline */}
              {profile.experience && profile.experience.length > 0 && (
                <div>
                  <div className="modal-section-title">
                    <Briefcase size={16} style={{ color: 'var(--primary)' }} /> Work Experience
                  </div>
                  <div className="timeline-list">
                    {profile.experience.map((exp, idx) => {
                      if (typeof exp === 'object') {
                        return (
                          <div className="timeline-item" key={idx}>
                            <div className="timeline-title">{exp.title || 'Environmental Expert'}</div>
                            <div className="timeline-subtitle">
                              {exp.company || 'Circular Economy Solution'} {exp.duration ? `(${exp.duration})` : ''}
                            </div>
                          </div>
                        );
                      }
                      return (
                        <div className="timeline-item" key={idx}>
                          <div className="timeline-title">{exp}</div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Education Timeline */}
              {profile.education && profile.education.length > 0 && (
                <div>
                  <div className="modal-section-title">
                    <Award size={16} style={{ color: 'var(--primary)' }} /> Education & Credentials
                  </div>
                  <div className="timeline-list">
                    {profile.education.map((edu, idx) => {
                      if (typeof edu === 'object') {
                        return (
                          <div className="timeline-item" key={idx}>
                            <div className="timeline-title">{edu.degree || 'Degree'}</div>
                            <div className="timeline-subtitle">
                              {edu.institution || 'University'} {edu.year ? `(${edu.year})` : ''}
                            </div>
                          </div>
                        );
                      }
                      return (
                        <div className="timeline-item" key={idx}>
                          <div className="timeline-title">{edu}</div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            {/* Right Column: Carousel & Meta */}
            <div>
              {/* Photo Carousel */}
              <div className="modal-section-title">
                <ImageIcon size={16} style={{ color: 'var(--primary)' }} /> Media Gallery ({photoUrls.length})
              </div>
              
              <div className="gallery-carousel">
                <img 
                  src={photoUrls[photoIndex]} 
                  alt={`${cleanName} gallery ${photoIndex + 1}`} 
                  className="carousel-image" 
                  onError={(e) => {
                    e.target.src = "https://www.mywastesolution.com/images/user-avatar-placeholder.png";
                  }}
                />
                {photoUrls.length > 1 && (
                  <>
                    <button className="carousel-btn left" onClick={handlePrevPhoto}>
                      <ChevronLeft size={16} />
                    </button>
                    <button className="carousel-btn right" onClick={handleNextPhoto}>
                      <ChevronRight size={16} />
                    </button>
                  </>
                )}
              </div>

              {/* AI Details & Tags */}
              <div style={{ marginTop: '24px' }}>
                <div className="modal-section-title">
                  <Sparkles size={16} style={{ color: 'var(--primary)' }} /> AI Classification
                </div>
                <div style={{ backgroundColor: 'var(--bg-primary)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)', fontSize: '13px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>AI Task:</span>
                    <span style={{ fontWeight: 700, color: 'var(--primary)' }}>{profile.task || 'None'}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>AI Category:</span>
                    <span style={{ fontWeight: 700 }}>{profile.category || 'None'}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>LLM Provider:</span>
                    <span style={{ color: 'var(--text-secondary)', textTransform: 'uppercase' }}>{profile.llm_provider || 'Not Processed'}</span>
                  </div>
                </div>
              </div>

              {/* Scraping Meta details */}
              <div style={{ marginTop: '24px' }}>
                <div className="modal-section-title">
                  <Shield size={16} style={{ color: 'var(--primary)' }} /> Source Audit
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <div>
                    <strong>Scraped Date:</strong> {formatScrapedDate(profile.scraped_at)}
                  </div>
                  <div>
                    <strong>Profile ID:</strong> <code style={{ fontSize: '11px', padding: '2px 4px', backgroundColor: 'var(--bg-tertiary)', borderRadius: '3px' }}>{profile._id}</code>
                  </div>
                  <a 
                    href={profile.profile_url} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    style={{ 
                      display: 'inline-flex', 
                      alignItems: 'center', 
                      gap: '6px', 
                      color: 'var(--primary)', 
                      textDecoration: 'none', 
                      marginTop: '8px',
                      fontWeight: 600
                    }}
                  >
                    <Link2 size={13} /> View Original Web Page
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
