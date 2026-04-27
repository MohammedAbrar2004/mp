import React, { useEffect } from 'react';
import { X } from 'lucide-react';

export default function Modal({ isOpen, onClose, title, children, size = 'md' }) {
  useEffect(() => {
    if (isOpen) {
      const handleEsc = (e) => { if (e.key === 'Escape') onClose(); };
      window.addEventListener('keydown', handleEsc);
      return () => window.removeEventListener('keydown', handleEsc);
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-fade-in" />
      <div
        className={`relative ${sizeClasses[size]} w-full bg-echo-panel border border-echo-border animate-fade-in overflow-hidden`}
        onClick={(e) => e.stopPropagation()}
        style={{ borderRadius: '2px' }}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-echo-border">
          <h3 className="text-echo-bright font-medium text-sm">{title}</h3>
          <button
            onClick={onClose}
            className="p-1 text-echo-muted hover:text-echo-bright transition-colors"
          >
            <X size={16} />
          </button>
        </div>
        <div className="p-5 max-h-[70vh] overflow-y-auto">
          {children}
        </div>
      </div>
    </div>
  );
}
