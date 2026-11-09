import { type SubmitEvent, useEffect, useRef, useState } from "react";
import { FormDialog } from "@/components/site/FormDialog";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { getErrorMessage } from "@/shared/api/transport";
import {
  IMAGE_TYPES,
  type ImageChoice,
  isHttpUrl,
  type LinkPreview,
  type Publication,
  type PublicationInput,
  validateImageFile,
} from "../domain/types";
import type { PublicationsApi } from "../infrastructure/publications.api";

type PreviewState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "found"; preview: LinkPreview }
  | { status: "manual"; message: string };

type ImageMode = "keep" | "page" | "upload" | "none";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  item: Publication | null;
  api: Pick<PublicationsApi, "preview">;
  onSubmit: (input: PublicationInput) => void;
  saving: boolean;
  error: string;
}

const MANUAL_MESSAGE =
  "No se pudo obtener la vista previa de ese enlace. Escribe el título a mano y, si quieres, sube una imagen.";

export function PublicationFormDialog({ open, onOpenChange, item, api, onSubmit, saving, error }: Props) {
  const [url, setUrl] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [preview, setPreview] = useState<PreviewState>({ status: "idle" });
  const [imageMode, setImageMode] = useState<ImageMode>("none");
  const [file, setFile] = useState<File | null>(null);
  const [localError, setLocalError] = useState("");
  const lastFetched = useRef("");
  // Lo que escribió el usuario no se pisa con la vista previa.
  const touched = useRef({ title: false, description: false });

  useEffect(() => {
    if (!open) return;
    setUrl(item?.url ?? "");
    setTitle(item?.title ?? "");
    setDescription(item?.description ?? "");
    setPreview({ status: "idle" });
    setImageMode(item?.image_url ? "keep" : "none");
    setFile(null);
    setLocalError("");
    lastFetched.current = item?.url ?? "";
    touched.current = { title: !!item, description: !!item };
  }, [open, item]);

  const fetchPreview = async (target: string) => {
    const clean = target.trim();
    if (!isHttpUrl(clean) || clean === lastFetched.current) return;
    lastFetched.current = clean;
    setPreview({ status: "loading" });
    try {
      const result = await api.preview(clean);
      if (!result.found) {
        setPreview({ status: "manual", message: MANUAL_MESSAGE });
        return;
      }
      setPreview({ status: "found", preview: result });
      if (result.title && !touched.current.title) setTitle(result.title);
      if (result.description && !touched.current.description) setDescription(result.description);
      if (result.image_url) setImageMode("page");
    } catch (err) {
      setPreview({ status: "manual", message: `${getErrorMessage(err)}. ${MANUAL_MESSAGE}` });
    }
  };

  const pageImage = preview.status === "found" ? preview.preview.image_url : null;

  const handleSubmit = (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLocalError("");
    if (!isHttpUrl(url)) return setLocalError("La URL debe empezar por http:// o https://");
    if (title.trim().length < 3) return setLocalError("El título debe tener al menos 3 caracteres");
    let image: ImageChoice = { kind: "none" };
    if (imageMode === "keep") image = { kind: "keep" };
    else if (imageMode === "page" && pageImage) image = { kind: "page", url: pageImage };
    else if (imageMode === "upload") {
      if (!file) return setLocalError("Selecciona una imagen o elige otra opción");
      const invalid = validateImageFile(file);
      if (invalid) return setLocalError(invalid);
      image = { kind: "upload", file };
    }
    onSubmit({ title, url, description, image });
  };

  const options: { value: ImageMode; label: string; show: boolean }[] = [
    { value: "keep", label: "Mantener la imagen actual", show: !!item?.image_url },
    { value: "page", label: "Usar la imagen de la página", show: !!pageImage },
    { value: "upload", label: "Subir una imagen", show: true },
    { value: "none", label: "Sin imagen", show: true },
  ];

  return (
    <FormDialog
      open={open}
      onOpenChange={onOpenChange}
      title={item ? "Editar publicación" : "Nueva publicación"}
      onSubmit={handleSubmit}
      loading={saving}
      submitLabel="Publicar"
      error={localError || error}
    >
      <Field label="Enlace (URL)">
        <div className="flex gap-2">
          <Input
            name="url"
            type="url"
            inputMode="url"
            placeholder="https://..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onPaste={(e) => {
              const pasted = e.clipboardData.getData("text");
              if (pasted) void fetchPreview(pasted);
            }}
            onBlur={() => void fetchPreview(url)}
            required
          />
          <Button
            variant="outline"
            onClick={() => {
              lastFetched.current = "";
              void fetchPreview(url);
            }}
            disabled={!isHttpUrl(url) || preview.status === "loading"}
          >
            {preview.status === "loading" ? "Leyendo..." : "Vista previa"}
          </Button>
        </div>
      </Field>

      {preview.status === "manual" && (
        <p role="status" className="m-0 text-[0.85rem] text-holh-muted">
          {preview.message}
        </p>
      )}

      {preview.status === "found" && (
        <div className="publication-preview" aria-label="Vista previa del enlace">
          {pageImage && (
            <img
              src={pageImage}
              alt=""
              referrerPolicy="no-referrer"
              onError={(e) => (e.currentTarget.style.display = "none")}
            />
          )}
          <div>
            {preview.preview.site_name && <span className="publication-domain">{preview.preview.site_name}</span>}
            <strong>{preview.preview.title ?? "Sin título"}</strong>
          </div>
        </div>
      )}

      <Field label="Título">
        <Input
          name="title"
          value={title}
          onChange={(e) => {
            touched.current.title = true;
            setTitle(e.target.value);
          }}
          required
          minLength={3}
          maxLength={500}
        />
      </Field>
      <Field label="Descripción">
        <Textarea
          name="description"
          rows={3}
          value={description}
          onChange={(e) => {
            touched.current.description = true;
            setDescription(e.target.value);
          }}
        />
      </Field>

      <fieldset className="grid gap-2 border-0 p-0">
        <legend className="mb-1 text-[0.88rem] font-semibold text-holh-text">Imagen</legend>
        {options
          .filter((o) => o.show)
          .map((o) => (
            <label key={o.value} className="flex items-center gap-2 text-[0.88rem] text-holh-text">
              <input
                type="radio"
                name="image_mode"
                value={o.value}
                checked={imageMode === o.value}
                onChange={() => setImageMode(o.value)}
                className="accent-holh-teal"
              />
              {o.label}
            </label>
          ))}
        {imageMode === "upload" && (
          <Input
            type="file"
            aria-label="Archivo de imagen"
            accept={IMAGE_TYPES.join(",")}
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        )}
        {imageMode === "page" && (
          <p className="m-0 text-[0.8rem] text-holh-muted">
            Se guardará una copia en el servidor del portal; no depende de la web original.
          </p>
        )}
      </fieldset>
    </FormDialog>
  );
}
