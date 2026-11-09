import { Dialog, DialogBody, DialogContent, DialogHeader } from "@/components/ui/dialog";

interface ContentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  content: string;
}

export function ContentDialog({ open, onOpenChange, title, content }: ContentDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent aria-describedby={undefined}>
        <DialogHeader title={title} />
        <DialogBody className="content-view">
          <p className="whitespace-pre-wrap">{content}</p>
        </DialogBody>
      </DialogContent>
    </Dialog>
  );
}
