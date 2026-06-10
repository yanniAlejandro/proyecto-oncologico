import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { HospitalLogo } from './HospitalLogo';

const navItems = [
  { to: '/', label: 'Noticias' },
  { to: '/guias-diagnostico', label: 'Guías de Diagnóstico' },
  { to: '/protocolos-tratamiento', label: 'Protocolos' },
  { to: '/documentos', label: 'Documentos' },
  { to: '/enlaces', label: 'Enlaces' },
  { to: '/contacto', label: 'Contacto' },
];

export function Layout() {
  const { user, logout, canManageContent, isAdmin } = useAuth();

  return (
    <div className="app-shell">
      <div className="institutional-bar">
        <div className="institutional-bar-inner">
          <span>Sistema Nacional de Salud Pública · Cuba</span>
          <span>La Habana</span>
        </div>
      </div>

      <header className="app-header">
        <div className="header-inner">
          <NavLink to="/" className="brand">
            <HospitalLogo />
            <div>
              <h1>Hospital Oncológico de La Habana</h1>
              <p>Portal institucional de recursos clínicos</p>
            </div>
          </NavLink>

          <div className="header-right">
            <div className="user-area">
              {user ? (
                <>
                  <div className="user-badge">
                    <span className="user-name">{user.full_name}</span>
                    <span className="user-role">{user.role}</span>
                  </div>
                  <button className="btn btn-header" onClick={logout}>
                    Cerrar sesión
                  </button>
                </>
              ) : (
                <span className="guest-badge">Acceso público</span>
              )}
            </div>
          </div>
        </div>

        <nav className="main-nav">
          <div className="main-nav-inner">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) => (isActive ? 'active' : '')}
              >
                {item.label}
              </NavLink>
            ))}
            {canManageContent && (
              <NavLink to="/gestion/noticias" className={({ isActive }) => `nav-admin ${isActive ? 'active' : ''}`}>
                Gestión Noticias
              </NavLink>
            )}
            {isAdmin && (
              <NavLink to="/gestion/usuarios" className={({ isActive }) => `nav-admin ${isActive ? 'active' : ''}`}>
                Gestión Usuarios
              </NavLink>
            )}
          </div>
        </nav>
      </header>

      <main className="app-main">
        <Outlet />
      </main>

      <footer className="app-footer">
        <div className="footer-inner">
          <div className="footer-brand">
            <HospitalLogo size={40} />
            <div>
              <strong>Hospital Oncológico de La Habana</strong>
              <p>Comprometidos con la atención oncológica integral</p>
            </div>
          </div>
          <div className="footer-info">
            <p>Calzada de Finlay, La Habana, Cuba</p>
            <p>© {new Date().getFullYear()} Hospital Oncológico de La Habana</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
