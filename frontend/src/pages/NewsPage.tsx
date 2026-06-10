import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { newsApi } from '../api/resources';
import { LoginModal } from '../components/LoginModal';
import { useAuth } from '../context/AuthContext';

export function NewsPage() {
  const { user } = useAuth();
  const [showLogin, setShowLogin] = useState(false);
  const { data: news = [], isLoading } = useQuery({
    queryKey: ['news'],
    queryFn: () => newsApi.list(),
  });

  return (
    <section className="page">
      <div className="landing-hero">
        <div className="landing-hero-content">
          <span className="landing-badge">Bienvenido</span>
          <h2>Hospital Oncológico de La Habana</h2>
          <p>
            Portal de información clínica para profesionales de la salud. Acceda a noticias institucionales,
            guías de diagnóstico, protocolos de tratamiento y documentación de referencia.
          </p>
          {!user && (
            <button className="btn btn-primary btn-lg" onClick={() => setShowLogin(true)}>
              Acceso para personal médico
            </button>
          )}
        </div>
        <div className="landing-hero-stats">
          <div className="stat-card">
            <span className="stat-number">{news.length}</span>
            <span className="stat-label">Noticias activas</span>
          </div>
          <div className="stat-card">
            <span className="stat-number">24/7</span>
            <span className="stat-label">Recursos disponibles</span>
          </div>
        </div>
      </div>

      <div className="section-heading">
        <h3>Noticias institucionales</h3>
        <p>Comunicados y novedades del hospital</p>
      </div>

      {isLoading ? (
        <p className="muted">Cargando noticias...</p>
      ) : (
        <div className="card-grid">
          {news.map((item) => (
            <article key={item.id} className="card news-card">
              <div className="card-accent" />
              <h3>{item.title}</h3>
              {item.summary && <p className="summary">{item.summary}</p>}
              <p className="content-preview">{item.content.slice(0, 180)}...</p>
              <footer>
                <span className="card-date">{new Date(item.created_at).toLocaleDateString('es-ES')}</span>
                {item.author_name && <span className="card-author">{item.author_name}</span>}
              </footer>
            </article>
          ))}
          {news.length === 0 && <p className="muted">No hay noticias publicadas.</p>}
        </div>
      )}

      <LoginModal isOpen={showLogin} onClose={() => setShowLogin(false)} />
    </section>
  );
}
