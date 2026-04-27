import React from 'react';
import { MessageSquare, Mail, Calendar, Video, PenTool, FileText } from 'lucide-react';
import { SOURCE_COLORS } from '../../data/mockData';

const iconMap = {
  whatsapp: MessageSquare,
  gmail: Mail,
  calendar: Calendar,
  meet: Video,
  manual: PenTool,
  document: FileText,
};

export default function SourceIcon({ source, size = 16, className = '' }) {
  const Icon = iconMap[source] || FileText;
  const color = SOURCE_COLORS[source] || '#8892a8';

  return (
    <Icon
      size={size}
      style={{ color }}
      className={`flex-shrink-0 ${className}`}
    />
  );
}
