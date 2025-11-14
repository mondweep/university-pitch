// Real LBS Knowledge Graph Data
// Based on actual research: 3,963 nodes, 3,953 edges

export const graphStats = {
  totalNodes: 3963,
  totalEdges: 3953,
  nodeTypes: {
    Page: 10,
    Section: 50,
    ContentItem: 3743,
    Topic: 160
  },
  topics: [
    { id: 'topic_mba', name: 'MBA Programs', frequency: 45, importance: 0.95 },
    { id: 'topic_exec_mba', name: 'Executive MBA', frequency: 38, importance: 0.92 },
    { id: 'topic_leadership', name: 'Leadership', frequency: 52, importance: 0.90 },
    { id: 'topic_finance', name: 'Finance', frequency: 67, importance: 0.88 },
    { id: 'topic_strategy', name: 'Strategy', frequency: 43, importance: 0.87 },
    { id: 'topic_marketing', name: 'Marketing', frequency: 39, importance: 0.85 },
    { id: 'topic_entrepreneurship', name: 'Entrepreneurship', frequency: 31, importance: 0.83 },
    { id: 'topic_analytics', name: 'Analytics & Data', frequency: 28, importance: 0.82 },
    { id: 'topic_sustainability', name: 'Sustainability', frequency: 24, importance: 0.78 },
    { id: 'topic_innovation', name: 'Innovation', frequency: 35, importance: 0.80 },
  ]
};

// Sample nodes for visualization
export const sampleNodes = [
  { id: 'page_mba', type: 'Page', title: 'MBA Programme', topics: ['topic_mba', 'topic_leadership', 'topic_finance'], personas: ['aspiring_executive', 'career_changer'] },
  { id: 'page_exec_mba', type: 'Page', title: 'Executive MBA', topics: ['topic_exec_mba', 'topic_leadership', 'topic_strategy'], personas: ['working_executive'] },
  { id: 'page_finance', type: 'Page', title: 'Finance Faculty', topics: ['topic_finance'], personas: ['aspiring_executive', 'researcher'] },
  { id: 'page_leadership', type: 'Page', title: 'Leadership Development', topics: ['topic_leadership'], personas: ['aspiring_executive', 'working_executive'] },
  { id: 'page_admissions', type: 'Page', title: 'Admissions', topics: ['topic_mba', 'topic_exec_mba'], personas: ['prospective_student'] },
  { id: 'page_careers', type: 'Page', title: 'Career Outcomes', topics: ['topic_mba'], personas: ['career_changer', 'prospective_student'] },
  { id: 'page_alumni', type: 'Page', title: 'Alumni Network', topics: ['topic_mba', 'topic_exec_mba'], personas: ['alumni'] },
  { id: 'page_research', type: 'Page', title: 'Research Centers', topics: ['topic_finance', 'topic_strategy', 'topic_innovation'], personas: ['researcher'] },
];

// Sample edges for visualization
export const sampleEdges = [
  { from: 'page_mba', to: 'topic_mba', type: 'HAS_TOPIC', weight: 0.95 },
  { from: 'page_mba', to: 'topic_leadership', type: 'HAS_TOPIC', weight: 0.85 },
  { from: 'page_mba', to: 'topic_finance', type: 'HAS_TOPIC', weight: 0.80 },
  { from: 'page_mba', to: 'page_exec_mba', type: 'RELATES_TO', weight: 0.72 },
  { from: 'page_mba', to: 'page_admissions', type: 'PREREQUISITE', weight: 1.0 },
  { from: 'page_mba', to: 'page_careers', type: 'RELATES_TO', weight: 0.65 },
  { from: 'page_exec_mba', to: 'topic_exec_mba', type: 'HAS_TOPIC', weight: 0.95 },
  { from: 'page_exec_mba', to: 'topic_leadership', type: 'HAS_TOPIC', weight: 0.90 },
  { from: 'page_exec_mba', to: 'topic_strategy', type: 'HAS_TOPIC', weight: 0.85 },
  { from: 'page_exec_mba', to: 'page_mba', type: 'RELATES_TO', weight: 0.72 },
  { from: 'page_leadership', to: 'topic_leadership', type: 'HAS_TOPIC', weight: 1.0 },
  { from: 'page_finance', to: 'topic_finance', type: 'HAS_TOPIC', weight: 1.0 },
  { from: 'page_research', to: 'topic_finance', type: 'HAS_TOPIC', weight: 0.90 },
  { from: 'page_research', to: 'topic_strategy', type: 'HAS_TOPIC', weight: 0.85 },
  { from: 'page_research', to: 'topic_innovation', type: 'HAS_TOPIC', weight: 0.80 },
];

// Actual cost data from research
export const costData = {
  traditional: {
    crawling: 500,
    parsing: 500,
    topicExtraction: 11.89,
    embeddings: 2.00,
    personas: 0.11,
    total: 1014.00
  },
  arw: {
    manifestFetch: 0,
    topicExtraction: 0, // Free from ARW
    embeddings: 0.30, // 85% reduction
    personas: 0, // Free from ARW
    total: 0.30
  },
  savings: {
    absolute: 1013.70,
    percentage: 99.97
  }
};

// Performance metrics from research
export const performanceMetrics = {
  traditional: {
    time: 41.5,
    httpRequests: 24,
    llmCalls: 15,
    tokens: 23000,
    cost: 0.137,
    accuracy: 75
  },
  arwKg: {
    time: 2.244,
    httpRequests: 4,
    llmCalls: 1,
    tokens: 3600,
    cost: 0.014,
    accuracy: 97
  },
  improvements: {
    timeReduction: 94.6,
    requestReduction: 83.3,
    llmReduction: 93.3,
    tokenReduction: 84.3,
    costReduction: 89.8,
    accuracyIncrease: 22
  }
};
