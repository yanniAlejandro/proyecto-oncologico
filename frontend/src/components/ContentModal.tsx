interface ContentModalProps {
  isOpen: boolean;
  title: string;
  content: string;
  onClose: () => void;
}

export function ContentModal({ isOpen, title, content, onClose }: ContentModalProps) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-lg" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{title}</h2>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>
        <div className="modal-body content-view">
          <p style={{ whiteSpace: 'pre-wrap' }}>{content}</p>
        </div>
      </div>
    </div>
  );
}
