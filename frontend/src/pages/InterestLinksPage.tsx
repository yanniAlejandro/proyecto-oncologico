import { useQuery } from '@tanstack/react-query';
import { linksApi } from '../api/resources';
import { PageHeader } from '../components/PageHeader';

export function InterestLinksPage() {
  const { data: links = [], isLoading } = useQuery({
    queryKey: ['interest-links'],
    queryFn: linksApi.list,
  });

  return (
    <section className="page">
      <PageHeader
        title="Enlaces de Interés"
        subtitle="Recursos externos de referencia para profesionales de la salud"
      />
      {isLoading ? (
        <p className="muted">Cargando enlaces...</p>
      ) : (
        <div className="links-list">
          {links.map((link) => (
            <a key={link.id} href={link.url} target="_blank" rel="noreferrer" className="link-card">
              <h3>{link.title}</h3>
              {link.description && <p>{link.description}</p>}
              <span className="link-url">{link.url}</span>
            </a>
          ))}
          {links.length === 0 && <p className="muted">No hay enlaces disponibles.</p>}
        </div>
      )}
    </section>
  );
}
