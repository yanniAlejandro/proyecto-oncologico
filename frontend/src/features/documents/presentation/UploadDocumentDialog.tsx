import { FileUp } from "lucide-react";
import { type DragEvent, type SubmitEvent, useId, useState } from "react";
import { FormDialog } from "@/components/site/FormDialog";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { formatBytes } from "@/lib/format";
import { type UploadPolicy, validateFile } from "../domain/types";
import type { NewDocumentInput } from "../infrastructure/documents.api";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  policy: UploadPolicy | undefined;
  onSubmit: (input: NewDocumentInput) => void;
  loading: boolean;
  error: string;
}

type Source = "file" | "url";

export function UploadDocumentDialog({ open, onOpenChange, policy, onSubmit, loading, error }: Props) {
  const [source, setSource] = useState<Source>("file");
  const [file, setFile] = useState<File | null>(null);
  const [localError, setLocalError] = useState("");
  const [dragging, setDragging] = useState(false);
  const inputId = useId();
  const accept = policy?.allowed_extensions.join(",");

  const reset = () => {
    setSource("file");
    setFile(null);
    setLocalError("");
    setDragging(false);
  };

  const pick = (candidate: File | null | undefined) => {
    if (!candidate) return;
    setFile(candidate);
    setLocalError(validateFile(candidate, policy) ?? "");
  };

  const onDrop = (e: DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    setDragging(false);
    pick(e.dataTransfer.files[0]);
  };

  const handleSubmit = (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const base = { title: String(form.get("title")).trim(), description: String(form.get("description") || "") };
    if (source === "file") {
      if (!file) return setLocalError("Selecciona un archivo");
      const problem = validateFile(file, policy);
      if (problem) return setLocalError(problem);
      onSubmit({ ...base, file });
    } else {
      onSubmit({ ...base, file_url: String(form.get("file_url")) });
    }
  };

  const formats = policy?.allowed_extensions.map((e) => e.slice(1).toUpperCase()).join(", ");

  return (
    <FormDialog
      open={open}
      onOpenChange={(o) => {
        if (!o) reset();
        onOpenChange(o);
      }}
      title="Nuevo documento"
      onSubmit={handleSubmit}
      loading={loading}
      loadingLabel={source === "file" ? "Subiendo..." : "Guardando..."}
      submitLabel={source === "file" ? "Subir documento" : "Guardar"}
      error={localError || error}
    >
      <Field label="Título">
        <Input name="title" required minLength={3} maxLength={500} />
      </Field>
      <Field label="Descripción">
        <Textarea name="description" rows={2} />
      </Field>

      <fieldset className="grid gap-2">
        <legend className="mb-2 text-[0.88rem] font-semibold text-holh-text">Origen</legend>
        <div className="flex flex-wrap gap-4 text-[0.88rem]">
          {(
            [
              ["file", "Subir archivo"],
              ["url", "Enlace externo"],
            ] as const
          ).map(([value, label]) => (
            <label key={value} className="flex items-center gap-2">
              <input
                type="radio"
                name="source"
                value={value}
                checked={source === value}
                onChange={() => {
                  setSource(value);
                  setLocalError("");
                }}
                className="accent-holh-teal"
              />
              {label}
            </label>
          ))}
        </div>
      </fieldset>

      {source === "file" ? (
        <div className="grid gap-[0.35rem]">
          <label
            htmlFor={inputId}
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            className={cn(
              "flex cursor-pointer flex-col items-center gap-1 rounded-holh border-2 border-dashed border-holh-border bg-holh-cream px-4 py-6 text-center transition-colors",
              dragging && "border-holh-teal bg-holh-tint",
            )}
          >
            <FileUp className="size-7 text-holh-teal" aria-hidden="true" />
            <span className="text-[0.92rem] font-semibold text-holh-blue">
              {file ? file.name : "Arrastra un archivo o haz clic para seleccionarlo"}
            </span>
            <span className="text-[0.8rem] text-holh-muted">
              {file
                ? formatBytes(file.size)
                : `${formats ?? ""}${policy ? ` · máx. ${formatBytes(policy.max_bytes)}` : ""}`}
            </span>
          </label>
          <input
            id={inputId}
            type="file"
            name="file"
            accept={accept}
            className="sr-only"
            onChange={(e) => pick(e.target.files?.[0])}
          />
        </div>
      ) : (
        <Field label="URL del documento">
          <Input name="file_url" type="url" required placeholder="https://..." />
        </Field>
      )}
    </FormDialog>
  );
}
