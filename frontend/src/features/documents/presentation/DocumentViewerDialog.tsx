import { Download, ExternalLink } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader } from "@/components/ui/dialog";
import { type DocumentItem, documentFileUrl, previewKind } from "../domain/types";

interface Props {
  doc: DocumentItem | null;
  onOpenChange: (open: boolean) => void;
}

/** Visor en el navegador: PDF y texto en iframe, imágenes con <img>. */
export function DocumentViewerDialog({ doc, onOpenChange }: Props) {
  const kind = doc ? previewKind(doc) : null;
  const inlineUrl = doc ? documentFileUrl(doc, "inline") : "";
  // Comprobación previa (HEAD) para no incrustar un JSON de error en el iframe.
  const [status, setStatus] = useState<"checking" | "ok" | "missing">("checking");
  useEffect(() => {
    if (!doc) return;
    const controller = new AbortController();
    setStatus("checking");
    fetch(inlineUrl, { method: "HEAD", signal: controller.signal })
      .then((res) => setStatus(res.ok ? "ok" : "missing"))
      .catch(() => !controller.signal.aborted && setStatus("missing"));
    return () => controller.abort();
  }, [doc, inlineUrl]);
  return (
    <Dialog open={!!doc} onOpenChange={onOpenChange}>
      <DialogContent size="xl" aria-describedby={undefined}>
        {doc && (
          <>
            <DialogHeader
              title={doc.title}
              actions={
                <>
                  <Button asChild variant="outline" size="sm">
                    <a href={inlineUrl} target="_blank" rel="noreferrer">
                      <ExternalLink aria-hidden="true" /> Abrir en pestaña
                    </a>
                  </Button>
                  <Button asChild variant="secondary" size="sm">
                    <a href={documentFileUrl(doc, "attachment")} download={doc.file_name}>
                      <Download aria-hidden="true" /> Descargar
                    </a>
                  </Button>
                </>
              }
            />
            <div className="bg-[#eef2f4] p-3">
              {status === "checking" ? (
                <p className="p-6 text-center text-holh-muted">Cargando vista previa...</p>
              ) : status === "missing" ? (
                <p className="p-6 text-center text-holh-danger" role="alert">
                  El archivo no está disponible. Contacta con el encargado del repositorio.
                </p>
              ) : kind === "image" ? (
                <img src={inlineUrl} alt={doc.title} className="mx-auto max-h-[75vh] max-w-full object-contain" />
              ) : kind ? (
                <>
                  <iframe
                    src={inlineUrl}
                    title={`Vista previa de ${doc.file_name}`}
                    className="block h-[70vh] w-full rounded-holh border-0 bg-white"
                  />
                  <p className="mt-2 text-center text-[0.8rem] text-holh-muted">
                    ¿No se muestra? Algunos navegadores (sobre todo en móvil) no incrustan PDF:{" "}
                    <a href={inlineUrl} target="_blank" rel="noreferrer">
                      ábrelo en una pestaña
                    </a>{" "}
                    o{" "}
                    <a href={documentFileUrl(doc, "attachment")} download={doc.file_name}>
                      descárgalo
                    </a>
                    .
                  </p>
                </>
              ) : (
                <p className="p-6 text-center text-holh-muted">Este formato no tiene vista previa. Descárgalo para abrirlo.</p>
              )}
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
