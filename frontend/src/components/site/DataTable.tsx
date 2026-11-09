import type { ReactNode } from "react";

interface DataTableProps {
  columns: string[];
  caption: string;
  isEmpty: boolean;
  emptyMessage: string;
  children: ReactNode;
}

/**
 * Tabla del portal (.data-table) con caption accesible. Va dentro de `.table-wrap` (scroll horizontal a
 * cualquier ancho, p. ej. en el panel con la barra lateral) y avisa del scroll en móvil (BUG-002).
 */
export function DataTable({ columns, caption, isEmpty, emptyMessage, children }: DataTableProps) {
  return (
    <>
      <p className="table-scroll-hint" aria-hidden="true">
        Desliza la tabla horizontalmente para ver todas las columnas →
      </p>
      <div className="table-wrap">
        <table className="data-table">
          <caption className="sr-only">{caption}</caption>
          <thead>
            <tr>
              {columns.map((c) => (
                <th key={c} scope="col">
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {children}
            {isEmpty && (
              <tr>
                <td colSpan={columns.length} className="muted">
                  {emptyMessage}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
