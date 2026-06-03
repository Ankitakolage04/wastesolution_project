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
                {profile.location && (
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <MapPin size={14} style={{ color: 'var(--primary)' }} />
                    {profile.location}
                  </span>
                )}
                
                {profile.contact_email && !profile.contact_email.toLowerCase().includes('mywastesolution.com') && (
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

              {/* Tagline / Bio Quote */}
              {profile.description && (
                <div style={{ marginTop: '12px', borderLeft: '3px solid var(--primary)', paddingLeft: '12px', fontStyle: 'italic', color: 'var(--text-secondary)', fontSize: '14px', lineHeight: '1.5' }}>
                  “{profile.description.split('.')[0]}.”
                </div>
              )}

              {/* Quick Stats Badges */}
              <div style={{ display: 'flex', gap: '8px', marginTop: '16px', flexWrap: 'wrap' }}>
                {profile.experience?.length > 0 && (
                  <span style={{ display: 'inline-flex', padding: '4px 10px', background: '#f3f4f6', borderRadius: '4px', fontSize: '11px', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {profile.experience.length * 3}+ years experience
                  </span>
                )}
                {profile.skills?.length > 0 && (
                  <span style={{ display: 'inline-flex', padding: '4px 10px', background: 'var(--primary-light)', borderRadius: '4px', fontSize: '11px', fontWeight: 700, color: 'var(--primary)' }}>
                    {profile.skills.length} skills
                  </span>
                )}
                {profile.task && (
                  <span style={{ display: 'inline-flex', padding: '4px 10px', background: '#eff6ff', borderRadius: '4px', fontSize: '11px', fontWeight: 700, color: '#2563eb' }}>
                    {profile.task}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Grid Layout split */}
          <div className="section-grid" style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 2fr) minmax(0, 1fr)', gap: '24px', marginTop: '24px' }}>
            {/* Left Column: Details */}
            <div>
              {/* About Section */}
              <div className="modal-section-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-primary)', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px', marginBottom: '12px' }}>
                <FileText size={16} style={{ color: 'var(--primary)' }} /> About
              </div>
              <p className="modal-bio" style={{ fontSize: '13.5px', color: 'var(--text-secondary)', lineHeight: '1.7', marginBottom: '24px', whiteSpace: 'pre-line' }}>
                {profile.description || 'No detailed biography provided.'}
              </p>

              {/* Skills & Expertise Section */}
              {(profile.skills?.length > 0 || profile.expertise?.length > 0) && (
                <div style={{ marginBottom: '24px' }}>
                  <div className="modal-section-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-primary)', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px', marginBottom: '12px' }}>
                    <Award size={16} style={{ color: 'var(--primary)' }} /> Skills &amp; Expertise
                  </div>
                  
                  {/* Categorized Skills rendering */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <div>
                      <div style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                        Expertise Areas
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                        {profile.expertise?.length > 0 ? (
                          profile.expertise.map((exp, idx) => (
                            <span key={`exp-${idx}`} style={{ display: 'inline-block', padding: '4px 10px', background: 'var(--primary-light)', border: '1px solid var(--primary-border)', borderRadius: '6px', fontSize: '11.5px', fontWeight: 600, color: 'var(--primary)' }}>
                              {exp}
                            </span>
                          ))
                        ) : (
                          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>No expertise tags listed</span>
                        )}
                      </div>
                    </div>

                    <div>
                      <div style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                        Core Skills
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                        {profile.skills?.length > 0 ? (
                          profile.skills.map((skill, idx) => (
                            <span key={`skill-${idx}`} style={{ display: 'inline-block', padding: '4px 10px', background: '#f3f4f6', border: '1px solid var(--border-color)', borderRadius: '6px', fontSize: '11.5px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                              {skill}
                            </span>
                          ))
                        ) : (
                          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>No skills tags listed</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Experience Timeline */}
              {profile.experience && profile.experience.length > 0 && (
                <div style={{ marginBottom: '24px' }}>
                  <div className="modal-section-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-primary)', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px', marginBottom: '12px' }}>
                    <Briefcase size={16} style={{ color: 'var(--primary)' }} /> Work Experience
                  </div>
                  <div className="timeline-list" style={{ display: 'flex', flexDirection: 'column', gap: '16px', borderLeft: '2px solid var(--border-color)', paddingLeft: '16px', marginLeft: '8px' }}>
                    {profile.experience.map((exp, idx) => {
                      if (typeof exp === 'object' && exp !== null) {
                        return (
                          <div className="timeline-item" key={idx} style={{ position: 'relative' }}>
                            <div style={{ position: 'absolute', left: '-23px', top: '4px', width: '12px', height: '12px', borderRadius: '50%', backgroundColor: 'var(--primary)', border: '2px solid white' }} />
                            <div className="timeline-title" style={{ fontSize: '13.5px', fontWeight: 700, color: 'var(--text-primary)' }}>{exp.title || 'Environmental Expert'}</div>
                            <div className="timeline-subtitle" style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                              {exp.company || 'Circular Economy Solution'} {exp.duration ? `• ${exp.duration}` : ''}
                            </div>
                            {exp.raw && <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px', fontStyle: 'italic' }}>{exp.raw}</div>}
                          </div>
                        );
                      }
                      return (
                        <div className="timeline-item" key={idx} style={{ position: 'relative' }}>
                          <div style={{ position: 'absolute', left: '-23px', top: '4px', width: '12px', height: '12px', borderRadius: '50%', backgroundColor: 'var(--primary)', border: '2px solid white' }} />
                          <div className="timeline-title" style={{ fontSize: '13.5px', fontWeight: 700, color: 'var(--text-primary)' }}>{exp}</div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Education Timeline */}
              {profile.education && profile.education.length > 0 && (
                <div style={{ marginBottom: '24px' }}>
                  <div className="modal-section-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-primary)', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px', marginBottom: '12px' }}>
                    <Award size={16} style={{ color: 'var(--primary)' }} /> Education &amp; Credentials
                  </div>
                  <div className="timeline-list" style={{ display: 'flex', flexDirection: 'column', gap: '16px', borderLeft: '2px solid var(--border-color)', paddingLeft: '16px', marginLeft: '8px' }}>
                    {profile.education.map((edu, idx) => {
                      if (typeof edu === 'object' && edu !== null) {
                        return (
                          <div className="timeline-item" key={idx} style={{ position: 'relative' }}>
                            <div style={{ position: 'absolute', left: '-23px', top: '4px', width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#2563eb', border: '2px solid white' }} />
                            <div className="timeline-title" style={{ fontSize: '13.5px', fontWeight: 700, color: 'var(--text-primary)' }}>{edu.degree || 'Degree'}</div>
                            <div className="timeline-subtitle" style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                              {edu.institution || 'University'} {edu.year ? `• ${edu.year}` : ''}
                            </div>
                            {edu.raw && <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px', fontStyle: 'italic' }}>{edu.raw}</div>}
                          </div>
                        );
                      }
                      return (
                        <div className="timeline-item" key={idx} style={{ position: 'relative' }}>
                          <div style={{ position: 'absolute', left: '-23px', top: '4px', width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#2563eb', border: '2px solid white' }} />
                          <div className="timeline-title" style={{ fontSize: '13.5px', fontWeight: 700, color: 'var(--text-primary)' }}>{edu}</div>
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
              <div className="modal-section-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-primary)', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px', marginBottom: '12px' }}>
                <ImageIcon size={16} style={{ color: 'var(--primary)' }} /> Media Gallery ({photoUrls.length})
              </div>
              
              <div className="gallery-carousel" style={{ position: 'relative', height: '200px', backgroundColor: 'var(--bg-tertiary)', borderRadius: '8px', overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <img 
                  src={photoUrls[photoIndex]} 
                  alt={`${cleanName} gallery ${photoIndex + 1}`} 
                  style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
                  onError={(e) => {
                    e.target.src = "https://www.mywastesolution.com/images/user-avatar-placeholder.png";
                  }}
                />
                {photoUrls.length > 1 && (
                  <>
                    <button className="carousel-btn left" onClick={handlePrevPhoto} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', background: 'rgba(255,255,255,0.9)', border: 'none', borderRadius: '50%', width: '28px', height: '28px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', boxShadow: 'var(--shadow-sm)' }}>
                      <ChevronLeft size={16} />
                    </button>
                    <button className="carousel-btn right" onClick={handleNextPhoto} style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', background: 'rgba(255,255,255,0.9)', border: 'none', borderRadius: '50%', width: '28px', height: '28px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', boxShadow: 'var(--shadow-sm)' }}>
                      <ChevronRight size={16} />
                    </button>
                  </>
                )}
              </div>

              {/* Sponsored Banner: Adhara Viveka */}
              <div style={{ marginTop: '24px', padding: '16px', background: 'linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)', border: '1px solid var(--primary-border)', borderRadius: '12px' }}>
                <div style={{ fontSize: '10px', fontWeight: 800, color: 'var(--primary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>
                  Sponsored Resource
                </div>
                <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)', lineHeight: '1.4', marginBottom: '6px' }}>
                  Planning a waste business? Research before you invest.
                </h4>
                <p style={{ fontSize: '11.5px', color: 'var(--text-secondary)', lineHeight: '1.4', marginBottom: '12px' }}>
                  Feasibility reports, market analysis &amp; business planning across 8+ sectors.
                </p>
                <a 
                  href="https://adhara-viveka.com" 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontWeight: 700, color: 'var(--primary)', textDecoration: 'none' }}
                >
                  Explore Adhara Viveka &rarr;
                </a>
              </div>

              {/* AI Details & Tags */}
              <div style={{ marginTop: '24px' }}>
                <div className="modal-section-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-primary)', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px', marginBottom: '12px' }}>
                  <Sparkles size={16} style={{ color: 'var(--primary)' }} /> AI Classification
                </div>
                <div style={{ backgroundColor: 'white', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)', fontSize: '13px' }}>
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
                <div className="modal-section-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-primary)', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px', marginBottom: '12px' }}>
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
