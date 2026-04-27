import React, { useState, useRef } from 'react';
import { FileText, Mic, Upload, X, Play, Square, Send, Check, AlertCircle, Loader2 } from 'lucide-react';
import { ingestText, ingestVoice, ingestDocument } from '../../api/client';

function InputField({ label, value, onChange, placeholder, error, multiline = false, type = 'text' }) {
  return (
    <div>
      <label className="text-[10px] text-echo-muted uppercase tracking-wider block mb-1.5">{label}</label>
      {multiline ? (
        <textarea value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} rows={6}
          className={`w-full px-3 py-2 bg-echo-bg border text-sm text-echo-text placeholder:text-echo-muted/40 focus:outline-none glow-input resize-none font-mono ${error ? 'border-red-500/50' : 'border-echo-border'}`}
          style={{ borderRadius: '2px' }} />
      ) : (
        <input type={type} value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder}
          className={`w-full px-3 py-2 bg-echo-bg border text-sm text-echo-text placeholder:text-echo-muted/40 focus:outline-none glow-input ${error ? 'border-red-500/50' : 'border-echo-border'}`}
          style={{ borderRadius: '2px' }} />
      )}
      {error && <p className="text-xs text-red-400 mt-1 flex items-center gap-1"><AlertCircle size={11} /> {error}</p>}
    </div>
  );
}

const TABS = [
  { id: 'text', label: 'Text', icon: FileText },
  { id: 'voice', label: 'Voice Note', icon: Mic },
  { id: 'document', label: 'Document', icon: Upload },
];

export default function IngestView() {
  const [activeTab, setActiveTab] = useState('text');
  const [submitted, setSubmitted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [errors, setErrors] = useState({});

  // Text tab state
  const [textContent, setTextContent] = useState('');
  const [textTitle, setTextTitle] = useState('');
  const [textSource, setTextSource] = useState('manual');
  const [textTags, setTextTags] = useState('');
  const [textPeople, setTextPeople] = useState('');

  // Voice tab state
  const [isRecording, setIsRecording] = useState(false);
  const [hasRecording, setHasRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [voiceTitle, setVoiceTitle] = useState('');
  const [voiceTags, setVoiceTags] = useState('');
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const durationTimerRef = useRef(null);

  // Doc tab state
  const [uploadedFile, setUploadedFile] = useState(null);
  const [docTitle, setDocTitle] = useState('');
  const [docAuthor, setDocAuthor] = useState('');
  const [docTags, setDocTags] = useState('');
  const [docDesc, setDocDesc] = useState('');
  const [isDragOver, setIsDragOver] = useState(false);

  const handleSubmit = async () => {
    const newErrors = {};
    if (activeTab === 'text' && !textContent.trim()) newErrors.textContent = 'Content is required';
    if (activeTab === 'voice' && !hasRecording) newErrors.recording = 'Please record a voice note first';
    if (activeTab === 'document' && !uploadedFile) newErrors.file = 'Please upload a document';

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setIsSubmitting(true);
    setSubmitError('');
    setErrors({});

    try {
      if (activeTab === 'text') {
        await ingestText({ content: textContent, title: textTitle, source_label: textSource, tags: textTags, people: textPeople });
        setTextContent(''); setTextTitle(''); setTextTags(''); setTextPeople('');
      } else if (activeTab === 'voice') {
        const file = new File([audioBlob], 'voice_note.webm', { type: audioBlob.type || 'audio/webm' });
        await ingestVoice({ file, title: voiceTitle, tags: voiceTags });
        setAudioBlob(null); setHasRecording(false); setVoiceTitle(''); setVoiceTags(''); setRecordingDuration(0);
      } else if (activeTab === 'document') {
        await ingestDocument({ file: uploadedFile, title: docTitle, author: docAuthor, tags: docTags, description: docDesc });
        setUploadedFile(null); setDocTitle(''); setDocAuthor(''); setDocTags(''); setDocDesc('');
      }
      setSubmitted(true);
      setTimeout(() => setSubmitted(false), 3000);
    } catch (err) {
      setSubmitError('Submission failed. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      mediaRecorderRef.current = mr;
      audioChunksRef.current = [];
      mr.ondataavailable = (e) => audioChunksRef.current.push(e.data);
      mr.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
        setHasRecording(true);
        stream.getTracks().forEach((t) => t.stop());
      };
      mr.start();
      setIsRecording(true);
      setHasRecording(false);
      setRecordingDuration(0);
      durationTimerRef.current = setInterval(() => setRecordingDuration((d) => d + 1), 1000);
    } catch {
      setErrors({ recording: 'Microphone access denied.' });
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
    clearInterval(durationTimerRef.current);
  };

  const toggleRecording = () => {
    if (isRecording) stopRecording();
    else startRecording();
  };

  const handleFileDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer?.files?.[0] || e.target?.files?.[0];
    if (file) setUploadedFile(file);
  };

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div className="flex border-b border-echo-border">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button key={id} onClick={() => { setActiveTab(id); setErrors({}); setSubmitError(''); }}
            className={`flex items-center gap-2 px-5 py-3 text-xs font-medium transition-all duration-150 border-b-2 ${activeTab === id ? 'text-cyan-glow border-cyan-glow' : 'text-echo-muted border-transparent hover:text-echo-text'}`}>
            <Icon size={14} />{label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-2xl mx-auto space-y-5">
          {/* TEXT TAB */}
          {activeTab === 'text' && (
            <>
              <InputField label="Content" value={textContent} onChange={setTextContent} placeholder="Paste or type your memory content here..." multiline error={errors.textContent} />
              <div className="grid grid-cols-2 gap-4">
                <InputField label="Title (optional)" value={textTitle} onChange={setTextTitle} placeholder="Optional title" />
                <div>
                  <label className="text-[10px] text-echo-muted uppercase tracking-wider block mb-1.5">Source Label</label>
                  <select value={textSource} onChange={(e) => setTextSource(e.target.value)}
                    className="w-full px-3 py-2 bg-echo-bg border border-echo-border text-sm text-echo-text focus:outline-none glow-input" style={{ borderRadius: '2px' }}>
                    <option value="manual">Manual</option>
                    <option value="meeting-notes">Meeting Notes</option>
                    <option value="reading">Reading Notes</option>
                    <option value="idea">Idea</option>
                    <option value="reflection">Reflection</option>
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <InputField label="Tags (comma-separated)" value={textTags} onChange={setTextTags} placeholder="e.g. design, feedback, Q2" />
                <InputField label="People mentioned" value={textPeople} onChange={setTextPeople} placeholder="e.g. Arjun, Priya" />
              </div>
            </>
          )}

          {/* VOICE TAB */}
          {activeTab === 'voice' && (
            <>
              <div className="flex flex-col items-center py-8">
                <button onClick={toggleRecording}
                  className={`w-24 h-24 flex items-center justify-center border-2 transition-all duration-300 ${isRecording ? 'bg-red-500/20 border-red-500 record-pulse' : 'bg-echo-bg border-echo-border hover:border-cyan-glow/40'}`}
                  style={{ borderRadius: '2px' }}>
                  {isRecording ? <Square size={32} className="text-red-400" /> : <Mic size={32} className="text-echo-muted" />}
                </button>
                <p className="text-sm text-echo-muted mt-4">
                  {isRecording ? `Recording... ${recordingDuration}s` : hasRecording ? 'Recording complete' : 'Click to start recording'}
                </p>

                {isRecording && (
                  <div className="flex items-end gap-1 h-8 mt-4">
                    {Array.from({ length: 16 }).map((_, i) => (
                      <div key={i} className="wave-bar" style={{ animationDelay: `${i * 0.08}s` }} />
                    ))}
                  </div>
                )}

                {hasRecording && !isRecording && (
                  <div className="mt-4 flex items-center gap-3 p-3 bg-echo-bg border border-echo-border w-full max-w-sm" style={{ borderRadius: '2px' }}>
                    <Play size={16} className="text-cyan-glow" />
                    <div className="flex-1 h-1 bg-echo-border" style={{ borderRadius: '2px' }} />
                    <span className="text-xs font-mono text-echo-muted">{recordingDuration}s</span>
                    <button onClick={() => { setHasRecording(false); setAudioBlob(null); }} className="p-1 text-echo-muted hover:text-red-400 transition-colors">
                      <X size={14} />
                    </button>
                  </div>
                )}
              </div>

              {errors.recording && (
                <p className="text-xs text-red-400 text-center flex items-center justify-center gap-1"><AlertCircle size={11} /> {errors.recording}</p>
              )}

              {hasRecording && (
                <div className="grid grid-cols-2 gap-4">
                  <InputField label="Title (optional)" value={voiceTitle} onChange={setVoiceTitle} placeholder="Voice note title" />
                  <InputField label="Tags" value={voiceTags} onChange={setVoiceTags} placeholder="e.g. idea, pipeline" />
                </div>
              )}
            </>
          )}

          {/* DOCUMENT TAB */}
          {activeTab === 'document' && (
            <>
              {!uploadedFile ? (
                <div onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }} onDragLeave={() => setIsDragOver(false)} onDrop={handleFileDrop}
                  className={`border-2 border-dashed p-12 text-center transition-all duration-200 ${isDragOver ? 'border-cyan-glow/60 bg-cyan-glow/5' : 'border-echo-border hover:border-echo-muted/40'}`}
                  style={{ borderRadius: '2px' }}>
                  <Upload size={32} className="mx-auto text-echo-muted mb-3" />
                  <p className="text-sm text-echo-muted mb-2">Drag & drop a PDF or DOC file here</p>
                  <p className="text-xs text-echo-muted/60 mb-4">or</p>
                  <label className="px-4 py-2 text-xs text-cyan-glow border border-cyan-glow/30 hover:bg-cyan-glow/10 transition-colors cursor-pointer" style={{ borderRadius: '2px' }}>
                    Browse Files
                    <input type="file" className="hidden" accept=".pdf,.doc,.docx" onChange={handleFileDrop} />
                  </label>
                  {errors.file && <p className="text-xs text-red-400 mt-3 flex items-center justify-center gap-1"><AlertCircle size={11} /> {errors.file}</p>}
                </div>
              ) : (
                <>
                  <div className="flex items-center gap-3 p-4 bg-echo-bg border border-echo-border" style={{ borderRadius: '2px' }}>
                    <FileText size={20} className="text-cyan-glow" />
                    <div className="flex-1">
                      <p className="text-sm text-echo-bright font-medium">{uploadedFile.name}</p>
                      <span className="text-xs font-mono text-echo-muted">{(uploadedFile.size / 1024).toFixed(1)} KB</span>
                    </div>
                    <button onClick={() => setUploadedFile(null)} className="p-1 text-echo-muted hover:text-red-400 transition-colors">
                      <X size={14} />
                    </button>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <InputField label="Document Title" value={docTitle} onChange={setDocTitle} placeholder="Title" />
                    <InputField label="Author" value={docAuthor} onChange={setDocAuthor} placeholder="Author name" />
                  </div>
                  <InputField label="Tags (comma-separated)" value={docTags} onChange={setDocTags} placeholder="e.g. report, finance" />
                  <InputField label="Description" value={docDesc} onChange={setDocDesc} placeholder="Brief description..." multiline />
                </>
              )}
            </>
          )}
        </div>
      </div>

      {/* Submit CTA */}
      <div className="border-t border-echo-border p-4 flex items-center justify-end gap-3">
        {submitError && <p className="text-xs text-red-400 font-mono">{submitError}</p>}
        {submitted ? (
          <div className="flex items-center gap-2 px-5 py-2.5 bg-green-500/15 text-green-400 text-sm font-medium" style={{ borderRadius: '2px' }}>
            <Check size={16} /> Submitted to Memory
          </div>
        ) : (
          <button onClick={handleSubmit} disabled={isSubmitting}
            className="flex items-center gap-2 px-5 py-2.5 bg-cyan-glow/15 text-cyan-glow border border-cyan-glow/30 hover:bg-cyan-glow/25 transition-all text-sm font-medium disabled:opacity-50"
            style={{ borderRadius: '2px' }}>
            {isSubmitting ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
            Submit to Memory
          </button>
        )}
      </div>
    </div>
  );
}
