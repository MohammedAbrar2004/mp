// EchoMind Mock Data — realistic data for all sections

export const SOURCES = {
  WHATSAPP: 'whatsapp',
  GMAIL: 'gmail',
  CALENDAR: 'calendar',
  MEET: 'meet',
  MANUAL: 'manual',
};

export const SOURCE_COLORS = {
  whatsapp: '#25D366',
  gmail: '#EA4335',
  calendar: '#4285F4',
  meet: '#00897B',
  manual: '#8892a8',
};

export const SOURCE_LABELS = {
  whatsapp: 'WhatsApp',
  gmail: 'Gmail',
  calendar: 'Calendar',
  meet: 'Meet',
  manual: 'Manual',
};

// ============ MEMORY CHUNKS ============
export const memoryChunks = [
  {
    id: 'mc-001',
    source: 'whatsapp',
    content: "Amaan: Hey, did you see the proposal from Meridian Labs? They want to integrate their API with our pipeline by end of Q2. Looks ambitious but doable. I'll set up a call with their CTO tomorrow.",
    timestamp: '2026-04-16T14:23:00+05:30',
    salience: 0.91,
    mediaType: 'text',
    entities: ['Amaan', 'Meridian Labs'],
    tags: ['proposal', 'api-integration', 'Q2'],
    title: null,
  },
  {
    id: 'mc-002',
    source: 'gmail',
    content: 'Subject: Re: Quarterly Review Deck — Final Version\n\nHi team, attached is the final version of the Q1 review deck. Key highlights: revenue up 23% YoY, customer churn reduced to 4.1%, and the new onboarding flow conversion is at 67%. Please review before Thursday\'s board meeting.',
    timestamp: '2026-04-16T09:15:00+05:30',
    salience: 0.85,
    mediaType: 'document',
    entities: ['Board Meeting'],
    tags: ['quarterly-review', 'revenue', 'metrics'],
    title: 'Q1 Review Deck — Final',
  },
  {
    id: 'mc-003',
    source: 'whatsapp',
    content: 'Abdullah: The design mockups for the dashboard redesign are ready. I\'ve shared the Figma link in the project channel. Let me know if the data visualization section needs more contrast — I went with a darker palette this time.',
    timestamp: '2026-04-15T18:45:00+05:30',
    salience: 0.72,
    mediaType: 'text',
    entities: ['Abdullah'],
    tags: ['design', 'dashboard', 'figma'],
    title: null,
  },
  {
    id: 'mc-004',
    source: 'manual',
    content: 'Meeting notes from deep-dive session on memory retrieval architecture. Decided to go with a hybrid approach: vector similarity for semantic search + keyword matching for exact recall. Need to benchmark embedding models — currently testing BGE-large vs. text-embedding-3-small. Action item: Amaan to set up A/B test by April 20.',
    timestamp: '2026-04-15T11:30:00+05:30',
    salience: 0.95,
    mediaType: 'text',
    entities: ['Amaan'],
    tags: ['architecture', 'embeddings', 'retrieval', 'meeting-notes'],
    title: 'Memory Retrieval Architecture Deep-Dive',
  },
  {
    id: 'mc-005',
    source: 'gmail',
    content: 'Subject: Invoice #4821 — Meridian Labs\n\nPlease find attached the invoice for consulting services rendered in March. Total amount: ₹4,25,000. Payment terms: Net 30. Bank details are included in the PDF.',
    timestamp: '2026-04-14T16:00:00+05:30',
    salience: 0.45,
    mediaType: 'document',
    entities: ['Meridian Labs'],
    tags: ['invoice', 'finance'],
    title: 'Invoice #4821',
  },
  {
    id: 'mc-006',
    source: 'whatsapp',
    content: 'Abrar: Just finished the load testing. The API can handle 1,200 req/s on the current infra without degradation. Beyond that, we see p99 latency spike to 800ms. Should we look into horizontal scaling or optimize the query layer first?',
    timestamp: '2026-04-14T13:20:00+05:30',
    salience: 0.82,
    mediaType: 'text',
    entities: ['Abrar'],
    tags: ['performance', 'load-testing', 'infrastructure'],
    title: null,
  },
  {
    id: 'mc-007',
    source: 'calendar',
    content: 'Board Meeting — Q1 Review Presentation. Attendees: Full leadership team + Meridian Labs representatives. Location: Conference Room A / Google Meet link.',
    timestamp: '2026-04-17T10:00:00+05:30',
    salience: 0.88,
    mediaType: 'text',
    entities: ['Board Meeting', 'Meridian Labs'],
    tags: ['meeting', 'board', 'Q1-review'],
    title: 'Board Meeting — Q1 Review',
  },
  {
    id: 'mc-008',
    source: 'whatsapp',
    content: 'Abdullah: Can we push the design review to Friday? I need one more day to polish the interaction animations. The micro-interactions for the memory browser feel off — want to nail the timing.',
    timestamp: '2026-04-13T22:10:00+05:30',
    salience: 0.51,
    mediaType: 'text',
    entities: ['Abdullah'],
    tags: ['design-review', 'scheduling'],
    title: null,
  },
  {
    id: 'mc-009',
    source: 'gmail',
    content: 'Subject: Offer Letter — Senior ML Engineer\n\nDear Candidate, We are pleased to extend an offer for the position of Senior ML Engineer at our organization. Please find the detailed terms and compensation package attached. We look forward to your response by April 20.',
    timestamp: '2026-04-13T10:00:00+05:30',
    salience: 0.78,
    mediaType: 'document',
    entities: [],
    tags: ['hiring', 'offer-letter', 'ML'],
    title: 'Offer Letter — Senior ML Engineer',
  },
  {
    id: 'mc-010',
    source: 'manual',
    content: 'Personal reflection: The cognitive load of context-switching between Slack, email, and WhatsApp is killing my deep work sessions. Need to batch communication into 2 windows per day — morning and late afternoon. EchoMind should help reduce the need to actively monitor everything.',
    timestamp: '2026-04-12T21:00:00+05:30',
    salience: 0.62,
    mediaType: 'text',
    entities: [],
    tags: ['reflection', 'productivity', 'deep-work'],
    title: 'Productivity Reflection',
  },
  {
    id: 'mc-011',
    source: 'whatsapp',
    content: 'Amaan: The embedding benchmark results are in. BGE-large wins on recall@10 by 8% but text-embedding-3-small is 3x faster and 60% cheaper. For our use case, I recommend going with OpenAI\'s model and compensating with a re-ranker stage.',
    timestamp: '2026-04-12T15:30:00+05:30',
    salience: 0.93,
    mediaType: 'text',
    entities: ['Amaan'],
    tags: ['embeddings', 'benchmark', 'decision'],
    title: null,
  },
  {
    id: 'mc-012',
    source: 'gmail',
    content: 'Subject: Security Audit Report — March 2026\n\nThe monthly security audit has been completed. Summary: 0 critical vulnerabilities found, 2 medium-severity issues in the authentication module (detailed in Section 4.2), and 5 low-severity configuration warnings. All medium issues have remediation timelines assigned.',
    timestamp: '2026-04-11T14:00:00+05:30',
    salience: 0.70,
    mediaType: 'document',
    entities: [],
    tags: ['security', 'audit', 'compliance'],
    title: 'Security Audit Report — March',
  },
  {
    id: 'mc-013',
    source: 'meet',
    content: 'Meeting transcript excerpt — Standup call April 11: Abrar shared progress on the caching layer — Redis cluster is deployed, seeing 40% reduction in DB queries. Abdullah demoed the new entity relationship visualization. Amaan flagged a potential issue with the WhatsApp webhook reliability.',
    timestamp: '2026-04-11T10:30:00+05:30',
    salience: 0.73,
    mediaType: 'text',
    entities: ['Abrar', 'Abdullah', 'Amaan'],
    tags: ['standup', 'progress', 'caching'],
    title: 'Daily Standup — April 11',
  },
  {
    id: 'mc-014',
    source: 'whatsapp',
    content: 'Khaled: Reminder — your dentist appointment is tomorrow at 3 PM. Also, mom called and asked if we\'re coming for dinner this Sunday. I said probably yes. Let me know if that works.',
    timestamp: '2026-04-10T19:45:00+05:30',
    salience: 0.35,
    mediaType: 'text',
    entities: ['Khaled'],
    tags: ['personal', 'reminder', 'family'],
    title: null,
  },
  {
    id: 'mc-015',
    source: 'manual',
    content: 'Idea: Build a "commitment extraction" pipeline that identifies action items, promises, and deadlines from any ingested text. Use an LLM with structured output (function calling) to parse: who committed, what was committed, deadline if mentioned, and confidence score. Feed results into the Commitments section.',
    timestamp: '2026-04-10T08:15:00+05:30',
    salience: 0.88,
    mediaType: 'text',
    entities: [],
    tags: ['idea', 'commitments', 'pipeline', 'LLM'],
    title: 'Commitment Extraction Pipeline Idea',
  },
  {
    id: 'mc-016',
    source: 'gmail',
    content: 'Subject: Re: Partnership Discussion — Nexus AI\n\nThanks for the intro, Amaan. We at Nexus AI are very interested in exploring a data partnership. Our CEO, Omer, would like to schedule a call next week to discuss potential synergies. Would Tuesday work?',
    timestamp: '2026-04-09T11:20:00+05:30',
    salience: 0.80,
    mediaType: 'text',
    entities: ['Amaan', 'Nexus AI', 'Omer'],
    tags: ['partnership', 'business-dev'],
    title: 'Partnership Discussion — Nexus AI',
  },
  {
    id: 'mc-017',
    source: 'calendar',
    content: 'Design Review — Dashboard Redesign v2. Attendees: Abdullah, Abrar, Amaan. Agenda: Review updated mockups, finalize component library, discuss animation timing.',
    timestamp: '2026-04-18T14:00:00+05:30',
    salience: 0.65,
    mediaType: 'text',
    entities: ['Abdullah', 'Abrar', 'Amaan'],
    tags: ['design-review', 'dashboard'],
    title: 'Design Review — Dashboard v2',
  },
  {
    id: 'mc-018',
    source: 'whatsapp',
    content: 'Abrar: Found a nasty race condition in the webhook handler. When two events arrive within 50ms, the deduplication check fails because the DB write from the first event hasn\'t committed yet. Going to add an in-memory lock. Fix should be ready by EOD.',
    timestamp: '2026-04-09T16:50:00+05:30',
    salience: 0.87,
    mediaType: 'text',
    entities: ['Abrar'],
    tags: ['bug', 'webhook', 'race-condition', 'fix'],
    title: null,
  },
  {
    id: 'mc-019',
    source: 'manual',
    content: 'Reading notes from "Designing Data-Intensive Applications" Chapter 10: Batch processing fundamentals. Key takeaway — MapReduce is conceptually simple but operationally complex. Modern systems like Spark/Flink offer better abstractions. Relevant for our ingestion pipeline design.',
    timestamp: '2026-04-08T22:30:00+05:30',
    salience: 0.55,
    mediaType: 'text',
    entities: [],
    tags: ['reading-notes', 'data-engineering', 'learning'],
    title: 'DDIA Chapter 10 Notes',
  },
  {
    id: 'mc-020',
    source: 'gmail',
    content: 'Subject: Team Offsite — May Planning\n\nHi all, I\'m starting to plan our May team offsite. Thinking of a 2-day retreat (May 15-16) focused on roadmap planning for H2 and team bonding. Location options: Lonavala or Alibaug. Please fill out the preference form by April 25.',
    timestamp: '2026-04-08T12:00:00+05:30',
    salience: 0.58,
    mediaType: 'text',
    entities: [],
    tags: ['offsite', 'team', 'planning'],
    title: 'Team Offsite — May Planning',
  },
];

// ============ ENTITIES ============
export const entities = [
  {
    id: 'ent-001',
    name: 'Amaan',
    type: 'person',
    mentionCount: 12,
    firstSeen: '2026-03-15T10:00:00+05:30',
    lastSeen: '2026-04-16T14:23:00+05:30',
    role: 'Co-founder & CTO',
    salienceBoost: true,
    linkedChunkIds: ['mc-001', 'mc-004', 'mc-011', 'mc-013', 'mc-016', 'mc-017'],
  },
  {
    id: 'ent-002',
    name: 'Abdullah',
    type: 'person',
    mentionCount: 8,
    firstSeen: '2026-03-18T09:00:00+05:30',
    lastSeen: '2026-04-15T18:45:00+05:30',
    role: 'Lead Designer',
    salienceBoost: true,
    linkedChunkIds: ['mc-003', 'mc-008', 'mc-013', 'mc-017'],
  },
  {
    id: 'ent-003',
    name: 'Abrar',
    type: 'person',
    mentionCount: 7,
    firstSeen: '2026-03-20T11:00:00+05:30',
    lastSeen: '2026-04-14T13:20:00+05:30',
    role: 'Backend Engineer',
    salienceBoost: false,
    linkedChunkIds: ['mc-006', 'mc-013', 'mc-017', 'mc-018'],
  },
  {
    id: 'ent-004',
    name: 'Khaled',
    type: 'person',
    mentionCount: 3,
    firstSeen: '2026-03-25T19:00:00+05:30',
    lastSeen: '2026-04-10T19:45:00+05:30',
    role: 'Partner',
    salienceBoost: false,
    linkedChunkIds: ['mc-014'],
  },
  {
    id: 'ent-005',
    name: 'Meridian Labs',
    type: 'organization',
    mentionCount: 5,
    firstSeen: '2026-03-22T14:00:00+05:30',
    lastSeen: '2026-04-16T14:23:00+05:30',
    role: 'Partner Company',
    salienceBoost: true,
    linkedChunkIds: ['mc-001', 'mc-005', 'mc-007'],
  },
  {
    id: 'ent-006',
    name: 'Nexus AI',
    type: 'organization',
    mentionCount: 2,
    firstSeen: '2026-04-09T11:20:00+05:30',
    lastSeen: '2026-04-09T11:20:00+05:30',
    role: 'Potential Partner',
    salienceBoost: false,
    linkedChunkIds: ['mc-016'],
  },
];

// ============ ENTITY RELATIONSHIPS (edges) ============
export const entityRelationships = [
  { source: 'ent-001', target: 'ent-002', strength: 0.85, label: 'works with' },
  { source: 'ent-001', target: 'ent-003', strength: 0.78, label: 'works with' },
  { source: 'ent-001', target: 'ent-005', strength: 0.70, label: 'negotiates with' },
  { source: 'ent-001', target: 'ent-006', strength: 0.45, label: 'introduced to' },
  { source: 'ent-002', target: 'ent-003', strength: 0.60, label: 'collaborates with' },
  { source: 'ent-003', target: 'ent-005', strength: 0.30, label: 'mentioned alongside' },
  { source: 'ent-005', target: 'ent-006', strength: 0.20, label: 'industry peer' },
  { source: 'ent-001', target: 'ent-004', strength: 0.15, label: 'mentioned alongside' },
];

// ============ COMMITMENTS ============
export const commitments = {
  openTasks: [
    {
      id: 'ct-001',
      title: 'Set up embedding model A/B test',
      source: 'manual',
      dueDate: '2026-04-20',
      entities: ['Amaan'],
      status: 'open',
      priority: 'high',
      sourceChunkId: 'mc-004',
    },
    {
      id: 'ct-002',
      title: 'Fix webhook race condition',
      source: 'whatsapp',
      dueDate: '2026-04-16',
      entities: ['Abrar'],
      status: 'open',
      priority: 'high',
      sourceChunkId: 'mc-018',
    },
    {
      id: 'ct-003',
      title: 'Review security audit medium-severity issues',
      source: 'gmail',
      dueDate: '2026-04-22',
      entities: [],
      status: 'open',
      priority: 'medium',
      sourceChunkId: 'mc-012',
    },
    {
      id: 'ct-004',
      title: 'Fill out offsite preference form',
      source: 'gmail',
      dueDate: '2026-04-25',
      entities: [],
      status: 'open',
      priority: 'low',
      sourceChunkId: 'mc-020',
    },
  ],
  upcomingEvents: [
    {
      id: 'ce-001',
      title: 'Board Meeting — Q1 Review',
      source: 'calendar',
      dueDate: '2026-04-17',
      entities: ['Meridian Labs'],
      status: 'upcoming',
      priority: 'high',
      sourceChunkId: 'mc-007',
    },
    {
      id: 'ce-002',
      title: 'Design Review — Dashboard v2',
      source: 'calendar',
      dueDate: '2026-04-18',
      entities: ['Abdullah', 'Abrar', 'Amaan'],
      status: 'upcoming',
      priority: 'medium',
      sourceChunkId: 'mc-017',
    },
    {
      id: 'ce-003',
      title: 'Call with Meridian Labs CTO',
      source: 'whatsapp',
      dueDate: '2026-04-17',
      entities: ['Amaan', 'Meridian Labs'],
      status: 'upcoming',
      priority: 'high',
      sourceChunkId: 'mc-001',
    },
  ],
  promises: [
    {
      id: 'cp-001',
      title: 'Respond to ML Engineer offer letter',
      source: 'gmail',
      dueDate: '2026-04-20',
      entities: [],
      status: 'open',
      priority: 'high',
      sourceChunkId: 'mc-009',
    },
    {
      id: 'cp-002',
      title: 'Schedule call with Nexus AI (Omer)',
      source: 'gmail',
      dueDate: '2026-04-22',
      entities: ['Nexus AI', 'Omer'],
      status: 'open',
      priority: 'medium',
      sourceChunkId: 'mc-016',
    },
    {
      id: 'cp-003',
      title: 'Confirm Sunday dinner with family',
      source: 'whatsapp',
      dueDate: '2026-04-20',
      entities: ['Khaled'],
      status: 'open',
      priority: 'low',
      sourceChunkId: 'mc-014',
    },
    {
      id: 'cp-004',
      title: "Review Abdullah's design mockups and provide feedback",
      source: 'whatsapp',
      dueDate: '2026-04-17',
      entities: ['Abdullah'],
      status: 'open',
      priority: 'medium',
      sourceChunkId: 'mc-003',
    },
    {
      id: 'cp-005',
      title: 'Implement batch communication schedule (2 windows/day)',
      source: 'manual',
      dueDate: null,
      entities: [],
      status: 'open',
      priority: 'low',
      sourceChunkId: 'mc-010',
    },
  ],
};

// ============ CONNECTORS ============
export const connectors = [
  {
    id: 'conn-gmail',
    name: 'Gmail',
    type: 'gmail',
    status: 'active',
    lastSync: '2026-04-16T14:00:00+05:30',
    chunksIngested: 847,
    mode: 'Pull',
    pollInterval: 300,
    error: null,
  },
  {
    id: 'conn-whatsapp',
    name: 'WhatsApp',
    type: 'whatsapp',
    status: 'auth_required',
    lastSync: '2026-04-15T23:45:00+05:30',
    chunksIngested: 1243,
    mode: 'Push',
    pollInterval: null,
    error: 'Session expired. Re-authentication required.',
    trackedChats: [
      { name: 'Team Core', messageCount: 456 },
      { name: 'Amaan', messageCount: 234 },
      { name: 'Abdullah', messageCount: 189 },
      { name: 'Family Group', messageCount: 312 },
      { name: 'Abrar', messageCount: 156 },
    ],
  },
  {
    id: 'conn-calendar',
    name: 'Google Calendar',
    type: 'calendar',
    status: 'inactive',
    lastSync: '2026-04-10T08:00:00+05:30',
    chunksIngested: 156,
    mode: 'Pull',
    pollInterval: 600,
    error: null,
  },
  {
    id: 'conn-meet',
    name: 'Google Meet',
    type: 'meet',
    status: 'inactive',
    lastSync: '2026-04-11T10:30:00+05:30',
    chunksIngested: 42,
    mode: 'Push',
    pollInterval: null,
    error: null,
  },
  {
    id: 'conn-manual',
    name: 'Manual Entry',
    type: 'manual',
    status: 'active',
    lastSync: '2026-04-15T11:30:00+05:30',
    chunksIngested: 98,
    mode: 'Push',
    pollInterval: null,
    error: null,
  },
];

// ============ INGESTION RUNS ============
export const ingestionRuns = [
  { id: 'ir-001', timestamp: '2026-04-16T14:00:00+05:30', connector: 'Gmail', chunks: 12, duration: '4.2s', status: 'success' },
  { id: 'ir-002', timestamp: '2026-04-16T12:00:00+05:30', connector: 'Gmail', chunks: 8, duration: '3.1s', status: 'success' },
  { id: 'ir-003', timestamp: '2026-04-15T23:45:00+05:30', connector: 'WhatsApp', chunks: 0, duration: '1.5s', status: 'error' },
  { id: 'ir-004', timestamp: '2026-04-15T18:00:00+05:30', connector: 'Gmail', chunks: 15, duration: '5.8s', status: 'success' },
  { id: 'ir-005', timestamp: '2026-04-15T11:30:00+05:30', connector: 'Manual', chunks: 1, duration: '0.3s', status: 'success' },
  { id: 'ir-006', timestamp: '2026-04-14T14:00:00+05:30', connector: 'Gmail', chunks: 6, duration: '2.9s', status: 'success' },
  { id: 'ir-007', timestamp: '2026-04-14T09:00:00+05:30', connector: 'WhatsApp', chunks: 23, duration: '8.4s', status: 'success' },
  { id: 'ir-008', timestamp: '2026-04-13T14:00:00+05:30', connector: 'Gmail', chunks: 4, duration: '1.8s', status: 'success' },
  { id: 'ir-009', timestamp: '2026-04-12T20:00:00+05:30', connector: 'WhatsApp', chunks: 31, duration: '11.2s', status: 'success' },
  { id: 'ir-010', timestamp: '2026-04-11T10:30:00+05:30', connector: 'Meet', chunks: 1, duration: '15.3s', status: 'success' },
];

// ============ FAILED JOBS ============
export const failedJobs = [
  {
    id: 'fj-001',
    timestamp: '2026-04-15T23:45:00+05:30',
    connector: 'WhatsApp',
    error: 'WebSocket connection closed unexpectedly. Session token expired. Re-authentication required via QR code scan.',
    retryCount: 3,
    lastRetry: '2026-04-16T00:15:00+05:30',
  },
  {
    id: 'fj-002',
    timestamp: '2026-04-14T02:30:00+05:30',
    connector: 'Gmail',
    error: 'Rate limit exceeded (429). Google API quota reached for the day. Auto-retry scheduled for next quota reset at midnight UTC.',
    retryCount: 1,
    lastRetry: '2026-04-14T03:00:00+05:30',
  },
];

// ============ QUERY HISTORY ============
export const queryHistory = [
  {
    id: 'q-001',
    query: 'What did Amaan say about the embedding benchmarks?',
    timestamp: '2026-04-16T15:30:00+05:30',
    model: 'Gemini',
    latency: 1.8,
    answer: 'Based on your WhatsApp conversation from April 12, Amaan shared the embedding benchmark results. **BGE-large outperformed on recall@10 by 8%**, but OpenAI\'s text-embedding-3-small was **3x faster and 60% cheaper**. His recommendation was to go with the OpenAI model and compensate with a re-ranker stage to maintain retrieval quality.\n\nThis aligns with the decision made during your architecture deep-dive session on April 15, where the team agreed on a hybrid retrieval approach combining vector similarity with keyword matching.',
    sourceChunkIds: ['mc-011', 'mc-004', 'mc-001'],
  },
  {
    id: 'q-002',
    query: 'When is the board meeting?',
    timestamp: '2026-04-16T14:00:00+05:30',
    model: 'Gemini',
    latency: 1.2,
    answer: 'Your **Board Meeting for the Q1 Review** is scheduled for **April 17, 2026 at 10:00 AM**. The meeting will include the full leadership team and representatives from Meridian Labs. The final Q1 review deck has already been circulated — revenue was up 23% YoY with customer churn at 4.1%.',
    sourceChunkIds: ['mc-007', 'mc-002'],
  },
  {
    id: 'q-003',
    query: 'What are the open security issues?',
    timestamp: '2026-04-15T16:00:00+05:30',
    model: 'Groq',
    latency: 2.1,
    answer: 'According to the March 2026 security audit report: **0 critical vulnerabilities** were found. There are **2 medium-severity issues** in the authentication module (detailed in Section 4.2 of the report), and **5 low-severity configuration warnings**. All medium issues have remediation timelines assigned.',
    sourceChunkIds: ['mc-012'],
  },
  {
    id: 'q-004',
    query: 'Summarize what Abrar has been working on',
    timestamp: '2026-04-14T18:00:00+05:30',
    model: 'Gemini',
    latency: 2.4,
    answer: 'Abrar has been focused on three main areas:\n\n1. **Load Testing**: Completed API load tests showing the system handles 1,200 req/s without degradation. Beyond that, p99 latency spikes to 800ms.\n\n2. **Caching Layer**: Deployed a Redis cluster that reduced DB queries by 40%.\n\n3. **Bug Fix**: Discovered and is fixing a race condition in the webhook handler where events arriving within 50ms cause deduplication failures. He\'s implementing an in-memory lock.',
    sourceChunkIds: ['mc-006', 'mc-013', 'mc-018'],
  },
  {
    id: 'q-005',
    query: 'What partnerships are we exploring?',
    timestamp: '2026-04-12T11:00:00+05:30',
    model: 'Groq',
    latency: 0.9,
    answer: 'You\'re currently exploring two partnerships:\n\n1. **Meridian Labs** — They want to integrate their API with your pipeline by end of Q2. Amaan is setting up a call with their CTO.\n\n2. **Nexus AI** — Their CEO Omer expressed interest in a data partnership. A call is being scheduled for next week (Tuesday proposed).',
    sourceChunkIds: ['mc-001', 'mc-016'],
  },
];

// ============ SALIENCE CONFIG ============
export const salienceConfig = {
  globalThreshold: 0.4,
  decayHalfLife: 30,
  keywordRules: [
    { id: 'kr-001', keyword: 'urgent', weight: 2.0 },
    { id: 'kr-002', keyword: 'deadline', weight: 1.8 },
    { id: 'kr-003', keyword: 'revenue', weight: 1.5 },
    { id: 'kr-004', keyword: 'bug', weight: 1.6 },
    { id: 'kr-005', keyword: 'partnership', weight: 1.4 },
  ],
  entityTypeWeights: {
    people: 1.5,
    places: 0.8,
    organizations: 1.3,
    dates: 1.0,
    customTags: 1.1,
  },
  sourceWeights: {
    whatsapp: 1.0,
    gmail: 1.2,
    calendar: 1.1,
    meet: 1.3,
    manual: 1.5,
  },
};

// ============ USER PROFILE ============
export const userProfile = {
  name: 'Abdul',
  phone: '+91 98765 43210',
  email: 'abdul@echomind.app',
  aboutMe: 'Building EchoMind — a personal cognitive memory system. Interested in AI, productivity systems, and knowledge management. I run a small tech team building data-intensive applications.',
  role: 'Founder & Product Engineer',
  aiModel: 'gemini',
  responseStyle: 'balanced',
  answerPersona: 'Answer as a knowledgeable assistant who understands my work context and personal life, prioritizing actionable insights.',
  preferences: {
    proactiveCommitments: true,
    autoTagEntities: true,
    includeCitations: true,
    voiceInputDefault: false,
    darkMode: true,
  },
};

// ============ CONNECTOR LOGS (mock) ============
export const connectorLogs = {
  gmail: [
    '[2026-04-16 14:00:02] INFO: Starting Gmail sync cycle',
    '[2026-04-16 14:00:03] INFO: Fetching messages since 2026-04-16T12:00:00Z',
    '[2026-04-16 14:00:05] INFO: Found 12 new messages',
    '[2026-04-16 14:00:06] INFO: Processing message: "Re: Quarterly Review Deck"',
    '[2026-04-16 14:00:08] INFO: Chunking complete — 12 chunks created',
    '[2026-04-16 14:00:09] INFO: Embedding generation started',
    '[2026-04-16 14:00:12] INFO: Embeddings stored successfully',
    '[2026-04-16 14:00:12] INFO: Sync cycle complete. Duration: 4.2s',
  ],
  whatsapp: [
    '[2026-04-15 23:45:01] INFO: WebSocket connection check',
    '[2026-04-15 23:45:02] ERROR: WebSocket connection closed (code: 1006)',
    '[2026-04-15 23:45:02] WARN: Session token may be expired',
    '[2026-04-15 23:45:03] INFO: Attempting reconnection (attempt 1/3)',
    '[2026-04-15 23:45:05] ERROR: Reconnection failed — invalid session',
    '[2026-04-15 23:45:05] ERROR: Authentication required. Please scan QR code.',
    '[2026-04-15 23:45:06] INFO: Marking connector status as AUTH_REQUIRED',
  ],
  calendar: [
    '[2026-04-10 08:00:01] INFO: Starting Calendar sync',
    '[2026-04-10 08:00:03] INFO: Fetched 3 events for next 7 days',
    '[2026-04-10 08:00:04] INFO: Sync complete. Duration: 2.1s',
    '[2026-04-10 08:00:04] INFO: Connector paused by user',
  ],
  meet: [
    '[2026-04-11 10:30:00] INFO: Meeting recording detected',
    '[2026-04-11 10:30:05] INFO: Transcription started (Whisper large-v3)',
    '[2026-04-11 10:30:45] INFO: Transcription complete — 1 chunk created',
    '[2026-04-11 10:31:00] INFO: Sync complete. Duration: 15.3s',
    '[2026-04-11 10:31:01] INFO: Connector paused — no active listener',
  ],
  manual: [
    '[2026-04-15 11:30:00] INFO: Manual entry received',
    '[2026-04-15 11:30:01] INFO: Processing text input (847 chars)',
    '[2026-04-15 11:30:01] INFO: Entity extraction: found 1 entity',
    '[2026-04-15 11:30:02] INFO: Chunk created and stored. Duration: 0.3s',
  ],
};

// ============ TRACKED CHATS ============
export const trackedChats = [
  { id: 'tc-001', name: 'Team Core', messageCount: 456, active: true },
  { id: 'tc-002', name: 'Amaan', messageCount: 234, active: true },
  { id: 'tc-003', name: 'Abdullah', messageCount: 189, active: true },
  { id: 'tc-004', name: 'Family Group', messageCount: 312, active: true },
  { id: 'tc-005', name: 'Abrar', messageCount: 156, active: true },
];

// ============ HELPER FUNCTIONS ============
export const formatRelativeTime = (timestamp) => {
  const now = new Date('2026-04-16T18:30:00+05:30');
  const then = new Date(timestamp);
  const diffMs = now - then;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return then.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
};

export const formatDate = (timestamp) => {
  return new Date(timestamp).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
};

export const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const getSalienceColor = (score) => {
  if (score >= 0.75) return '#00e5cc';
  if (score >= 0.5) return '#f59e0b';
  return '#4b5563';
};

export const getSalienceLabel = (score) => {
  if (score >= 0.75) return 'High';
  if (score >= 0.5) return 'Medium';
  return 'Low';
};
