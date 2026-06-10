import { useQuery } from '@tanstack/react-query';
import { contactApi } from '../api/resources';
import { PageHeader } from '../components/PageHeader';

export function ContactPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['contact'],
    queryFn: contactApi.get,
  });

  if (isLoading) return <p className="muted">Cargando información de contacto...</p>;
  if (isError || !data) return <p className="alert alert-error">No se pudo cargar la información de contacto.</p>;

  return (
    <section className="page">
      <PageHeader
        title="Contacto"
        subtitle="Información institucional y canales de comunicación del hospital"
      />
      <div className="contact-card">
        <h3>{data.organization_name}</h3>
        <div className="contact-grid">
          {data.address && (
            <div className="contact-item">
              <span className="contact-icon">📍</span>
              <div>
                <strong>Dirección</strong>
                <span>{data.address}</span>
              </div>
            </div>
          )}
          {data.phone && (
            <div className="contact-item">
              <span className="contact-icon">📞</span>
              <div>
                <strong>Teléfono</strong>
                <span>{data.phone}</span>
              </div>
            </div>
          )}
          {data.email && (
            <div className="contact-item">
              <span className="contact-icon">✉️</span>
              <div>
                <strong>Correo electrónico</strong>
                <a href={`mailto:${data.email}`}>{data.email}</a>
              </div>
            </div>
          )}
          {data.schedule && (
            <div className="contact-item">
              <span className="contact-icon">🕐</span>
              <div>
                <strong>Horario de atención</strong>
                <span>{data.schedule}</span>
              </div>
            </div>
          )}
        </div>
        {data.map_url && (
          <p style={{ marginTop: '1.25rem' }}>
            <a href={data.map_url} target="_blank" rel="noreferrer" className="btn btn-primary">
              Ver ubicación en mapa
            </a>
          </p>
        )}
      </div>
    </section>
  );
}
