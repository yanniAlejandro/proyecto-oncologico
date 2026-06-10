import { useState } from 'react';
import type { FormEvent } from 'react';
import { getErrorMessage } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { HospitalLogo } from './HospitalLogo';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function LoginModal({ isOpen, onClose }: LoginModalProps) {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      onClose();
      setEmail('');
      setPassword('');
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal login-modal" onClick={(e) => e.stopPropagation()}>
        <div className="login-modal-brand">
          <HospitalLogo size={48} />
          <div>
            <h2>Acceso institucional</h2>
            <p>Hospital Oncológico de La Habana</p>
          </div>
        </div>
        <form onSubmit={handleSubmit} className="modal-body form-grid">
          {error && <div className="alert alert-error">{error}</div>}
          <label>
            Correo electrónico
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="usuario@holh.sld.cu" />
          </label>
          <label>
            Contraseña
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </label>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Verificando credenciales...' : 'Ingresar al portal'}
          </button>
        </form>
        <button className="modal-close login-modal-close" onClick={onClose}>
          ×
        </button>
      </div>
    </div>
  );
}
