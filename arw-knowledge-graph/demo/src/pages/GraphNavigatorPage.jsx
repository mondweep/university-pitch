import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Network,
  User,
  Filter,
  BarChart3,
  Info,
  Play,
  Pause,
  RotateCcw,
  Eye,
  List,
  Zap,
  Target,
  GitBranch,
  Circle,
  Square,
  Triangle,
  Search,
  MapPin,
  TrendingUp,
  Sparkles,
  ChevronRight,
  CheckCircle2
} from 'lucide-react';
import { graphStats, sampleNodes, sampleEdges } from '../data/lbsKnowledgeGraph';

// Extended nodes with topics
const enrichedNodes = [
  ...sampleNodes,
  // Add Topic nodes
  { id: 'topic_mba', type: 'Topic', title: 'MBA Programs', topics: ['topic_mba'], personas: [] },
  { id: 'topic_exec_mba', type: 'Topic', title: 'Executive MBA', topics: ['topic_exec_mba'], personas: [] },
  { id: 'topic_leadership', type: 'Topic', title: 'Leadership', topics: ['topic_leadership'], personas: [] },
  { id: 'topic_finance', type: 'Topic', title: 'Finance', topics: ['topic_finance'], personas: [] },
  { id: 'topic_strategy', type: 'Topic', title: 'Strategy', topics: ['topic_strategy'], personas: [] },
  { id: 'topic_innovation', type: 'Topic', title: 'Innovation', topics: ['topic_innovation'], personas: [] },
];

// Persona definitions
const personas = [
  {
    id: 'aspiring_executive',
    name: 'Aspiring Executive',
    description: 'Recent graduate looking to accelerate career',
    color: 'blue',
    journey: ['page_admissions', 'page_mba', 'topic_leadership', 'page_leadership', 'page_careers']
  },
  {
    id: 'career_changer',
    name: 'Career Changer',
    description: 'Professional pivoting to new industry',
    color: 'purple',
    journey: ['page_admissions', 'page_mba', 'topic_finance', 'page_finance', 'page_careers']
  },
  {
    id: 'working_executive',
    name: 'Working Executive',
    description: 'Senior professional seeking advancement',
    color: 'green',
    journey: ['page_exec_mba', 'topic_leadership', 'topic_strategy', 'page_leadership', 'page_alumni']
  },
  {
    id: 'researcher',
    name: 'Academic Researcher',
    description: 'Scholar exploring business topics',
    color: 'yellow',
    journey: ['page_research', 'topic_finance', 'topic_innovation', 'page_finance']
  },
  {
    id: 'prospective_student',
    name: 'Prospective Student',
    description: 'Exploring MBA options',
    color: 'pink',
    journey: ['page_admissions', 'page_mba', 'page_careers', 'page_alumni']
  }
];

// Node type configurations
const nodeTypeConfig = {
  Page: {
    color: 'bg-red-500',
    border: 'border-red-600',
    text: 'text-red-100',
    icon: Square,
    size: 'large'
  },
  Topic: {
    color: 'bg-blue-500',
    border: 'border-blue-600',
    text: 'text-blue-100',
    icon: Circle,
    size: 'medium'
  },
  Section: {
    color: 'bg-green-500',
    border: 'border-green-600',
    text: 'text-green-100',
    icon: Triangle,
    size: 'small'
  }
};

const GraphNavigatorPage = () => {
  // View state
  const [viewMode, setViewMode] = useState('semantic'); // 'semantic' or 'traditional'

  // Filter state
  const [selectedTopics, setSelectedTopics] = useState([]);
  const [selectedPersona, setSelectedPersona] = useState(null);

  // Animation state
  const [isAnimating, setIsAnimating] = useState(false);
  const [animationStep, setAnimationStep] = useState(0);
  const [selectedNode, setSelectedNode] = useState(null);

  // Graph layout state
  const [nodePositions, setNodePositions] = useState({});
  const svgRef = useRef(null);

  // Initialize node positions with force-directed layout simulation
  useEffect(() => {
    const positions = {};
    const centerX = 500;
    const centerY = 400;
    const radius = 250;

    enrichedNodes.forEach((node, index) => {
      const angle = (index / enrichedNodes.length) * 2 * Math.PI;
      const r = node.type === 'Topic' ? radius * 0.5 : radius;

      positions[node.id] = {
        x: centerX + r * Math.cos(angle) + (Math.random() - 0.5) * 50,
        y: centerY + r * Math.sin(angle) + (Math.random() - 0.5) * 50
      };
    });

    setNodePositions(positions);
  }, []);

  // Animate persona journey
  useEffect(() => {
    let interval;
    if (isAnimating && selectedPersona) {
      const persona = personas.find(p => p.id === selectedPersona);
      if (persona && animationStep < persona.journey.length) {
        interval = setInterval(() => {
          setAnimationStep(prev => {
            if (prev >= persona.journey.length - 1) {
              setIsAnimating(false);
              return prev;
            }
            return prev + 1;
          });
        }, 1500);
      }
    }
    return () => clearInterval(interval);
  }, [isAnimating, animationStep, selectedPersona]);

  // Filter nodes based on selected topics
  const filteredNodes = selectedTopics.length > 0
    ? enrichedNodes.filter(node =>
        node.topics.some(topic => selectedTopics.includes(topic)) ||
        node.type === 'Topic' && selectedTopics.includes(node.id)
      )
    : enrichedNodes;

  // Filter edges based on filtered nodes
  const filteredEdges = sampleEdges.filter(edge =>
    filteredNodes.some(n => n.id === edge.from) &&
    filteredNodes.some(n => n.id === edge.to)
  );

  // Get persona journey path
  const getPersonaJourney = () => {
    if (!selectedPersona) return [];
    const persona = personas.find(p => p.id === selectedPersona);
    return persona ? persona.journey : [];
  };

  const toggleTopic = (topicId) => {
    setSelectedTopics(prev =>
      prev.includes(topicId)
        ? prev.filter(t => t !== topicId)
        : [...prev, topicId]
    );
  };

  const startAnimation = () => {
    setAnimationStep(0);
    setIsAnimating(true);
  };

  const resetAnimation = () => {
    setAnimationStep(0);
    setIsAnimating(false);
  };

  const selectPersona = (personaId) => {
    setSelectedPersona(personaId);
    setAnimationStep(0);
    setIsAnimating(false);
  };

  // Check if node is in current journey path
  const isNodeInJourney = (nodeId) => {
    const journey = getPersonaJourney();
    return journey.includes(nodeId);
  };

  // Check if node is currently highlighted in animation
  const isNodeActive = (nodeId) => {
    const journey = getPersonaJourney();
    return isAnimating && journey[animationStep] === nodeId;
  };

  // Check if edge is in journey path
  const isEdgeInJourney = (edge) => {
    const journey = getPersonaJourney();
    if (!isAnimating || animationStep === 0) return false;
    return journey[animationStep - 1] === edge.from && journey[animationStep] === edge.to;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-900 to-slate-900 p-8">
      <div className="max-w-[1800px] mx-auto space-y-6">

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center space-y-4"
        >
          <div className="flex items-center justify-center gap-3">
            <Network className="w-12 h-12 text-cyan-400" />
            <h1 className="text-5xl font-bold text-white">Knowledge Graph Navigator</h1>
            <Network className="w-12 h-12 text-cyan-400" />
          </div>
          <p className="text-xl text-gray-300">
            Interactive visualization of LBS website as a semantic knowledge graph
          </p>
        </motion.div>

        {/* Control Panel */}
        <div className="grid lg:grid-cols-3 gap-6">

          {/* View Mode Toggle */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-white/10 backdrop-blur-sm rounded-xl p-6"
          >
            <div className="flex items-center gap-2 mb-4">
              <Eye className="w-5 h-5 text-cyan-400" />
              <h3 className="text-lg font-bold text-white">View Mode</h3>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => setViewMode('traditional')}
                className={`p-4 rounded-lg font-medium transition-all ${
                  viewMode === 'traditional'
                    ? 'bg-gradient-to-r from-gray-500 to-gray-600 text-white shadow-lg'
                    : 'bg-white/5 text-gray-400 hover:bg-white/10'
                }`}
              >
                <List className="w-6 h-6 mx-auto mb-2" />
                Traditional
              </button>
              <button
                onClick={() => setViewMode('semantic')}
                className={`p-4 rounded-lg font-medium transition-all ${
                  viewMode === 'semantic'
                    ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-lg'
                    : 'bg-white/5 text-gray-400 hover:bg-white/10'
                }`}
              >
                <Network className="w-6 h-6 mx-auto mb-2" />
                Semantic
              </button>
            </div>

            <div className="mt-4 p-3 bg-white/5 rounded-lg">
              <div className="text-sm text-gray-400">
                {viewMode === 'traditional'
                  ? 'Flat list navigation - linear search through pages'
                  : 'Graph-based navigation - follow semantic relationships'}
              </div>
            </div>
          </motion.div>

          {/* Persona Selector */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white/10 backdrop-blur-sm rounded-xl p-6"
          >
            <div className="flex items-center gap-2 mb-4">
              <User className="w-5 h-5 text-purple-400" />
              <h3 className="text-lg font-bold text-white">Persona Journey</h3>
            </div>

            <select
              value={selectedPersona || ''}
              onChange={(e) => selectPersona(e.target.value || null)}
              className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white mb-4 focus:outline-none focus:ring-2 focus:ring-purple-400"
            >
              <option value="">Select a persona...</option>
              {personas.map(persona => (
                <option key={persona.id} value={persona.id}>
                  {persona.name}
                </option>
              ))}
            </select>

            {selectedPersona && (
              <div className="space-y-3">
                <div className="p-3 bg-white/5 rounded-lg text-sm text-gray-300">
                  {personas.find(p => p.id === selectedPersona)?.description}
                </div>

                <div className="flex gap-2">
                  {!isAnimating ? (
                    <button
                      onClick={startAnimation}
                      className="flex-1 flex items-center justify-center gap-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white px-4 py-3 rounded-lg font-medium hover:shadow-lg transition-shadow"
                    >
                      <Play className="w-4 h-4" />
                      Animate Journey
                    </button>
                  ) : (
                    <button
                      onClick={() => setIsAnimating(false)}
                      className="flex-1 flex items-center justify-center gap-2 bg-gradient-to-r from-orange-500 to-red-500 text-white px-4 py-3 rounded-lg font-medium hover:shadow-lg transition-shadow"
                    >
                      <Pause className="w-4 h-4" />
                      Pause
                    </button>
                  )}
                  <button
                    onClick={resetAnimation}
                    className="flex items-center justify-center gap-2 bg-white/10 text-white px-4 py-3 rounded-lg font-medium hover:bg-white/20 transition-colors"
                  >
                    <RotateCcw className="w-4 h-4" />
                  </button>
                </div>

                {isAnimating && (
                  <div className="p-3 bg-green-500/20 border border-green-500 rounded-lg">
                    <div className="text-sm text-green-300 mb-2">
                      Step {animationStep + 1} of {getPersonaJourney().length}
                    </div>
                    <div className="text-white font-medium">
                      {enrichedNodes.find(n => n.id === getPersonaJourney()[animationStep])?.title}
                    </div>
                  </div>
                )}
              </div>
            )}
          </motion.div>

          {/* Graph Statistics */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white/10 backdrop-blur-sm rounded-xl p-6"
          >
            <div className="flex items-center gap-2 mb-4">
              <BarChart3 className="w-5 h-5 text-yellow-400" />
              <h3 className="text-lg font-bold text-white">Graph Statistics</h3>
            </div>

            <div className="space-y-3">
              <StatCard
                label="Total Nodes"
                value={graphStats.totalNodes.toLocaleString()}
                icon={GitBranch}
                color="text-cyan-400"
              />
              <StatCard
                label="Total Edges"
                value={graphStats.totalEdges.toLocaleString()}
                icon={Network}
                color="text-purple-400"
              />
              <StatCard
                label="Visible Nodes"
                value={filteredNodes.length}
                icon={Eye}
                color="text-green-400"
              />
              <StatCard
                label="Visible Edges"
                value={filteredEdges.length}
                icon={GitBranch}
                color="text-blue-400"
              />
            </div>
          </motion.div>
        </div>

        {/* Topic Filters */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white/10 backdrop-blur-sm rounded-xl p-6"
        >
          <div className="flex items-center gap-2 mb-4">
            <Filter className="w-5 h-5 text-orange-400" />
            <h3 className="text-lg font-bold text-white">Topic Filters</h3>
            {selectedTopics.length > 0 && (
              <button
                onClick={() => setSelectedTopics([])}
                className="ml-auto text-sm text-gray-400 hover:text-white transition-colors"
              >
                Clear All
              </button>
            )}
          </div>

          <div className="flex flex-wrap gap-3">
            {graphStats.topics.map(topic => {
              const isSelected = selectedTopics.includes(topic.id);
              return (
                <button
                  key={topic.id}
                  onClick={() => toggleTopic(topic.id)}
                  className={`px-4 py-2 rounded-lg font-medium transition-all ${
                    isSelected
                      ? 'bg-gradient-to-r from-orange-500 to-red-500 text-white shadow-lg scale-105'
                      : 'bg-white/10 text-gray-300 hover:bg-white/20'
                  }`}
                >
                  {topic.name}
                  <span className="ml-2 text-xs opacity-75">({topic.frequency})</span>
                </button>
              );
            })}
          </div>
        </motion.div>

        {/* Main Content Area */}
        <div className="grid lg:grid-cols-4 gap-6">

          {/* Graph Visualization */}
          <div className="lg:col-span-3">
            <AnimatePresence mode="wait">
              {viewMode === 'semantic' ? (
                <motion.div
                  key="semantic"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="bg-white/10 backdrop-blur-sm rounded-xl p-6"
                >
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-bold text-white">Semantic Graph View</h3>
                    <div className="flex items-center gap-4 text-sm">
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 bg-red-500 rounded"></div>
                        <span className="text-gray-300">Page</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 bg-blue-500 rounded-full"></div>
                        <span className="text-gray-300">Topic</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 bg-green-500 rounded-full"></div>
                        <span className="text-gray-300">Section</span>
                      </div>
                    </div>
                  </div>

                  {/* SVG Graph */}
                  <div className="bg-slate-900/50 rounded-lg overflow-hidden" style={{ height: '600px' }}>
                    <svg
                      ref={svgRef}
                      width="100%"
                      height="100%"
                      viewBox="0 0 1000 800"
                      className="cursor-move"
                    >
                      {/* Draw edges first (behind nodes) */}
                      <g className="edges">
                        {filteredEdges.map((edge, index) => {
                          const from = nodePositions[edge.from];
                          const to = nodePositions[edge.to];
                          if (!from || !to) return null;

                          const isJourneyEdge = isEdgeInJourney(edge);
                          const isInPath = getPersonaJourney().includes(edge.from) &&
                                          getPersonaJourney().includes(edge.to);

                          return (
                            <motion.line
                              key={`${edge.from}-${edge.to}-${index}`}
                              x1={from.x}
                              y1={from.y}
                              x2={to.x}
                              y2={to.y}
                              stroke={isJourneyEdge ? '#10b981' : isInPath ? '#6366f1' : '#475569'}
                              strokeWidth={isJourneyEdge ? 3 : isInPath ? 2 : 1}
                              strokeOpacity={isJourneyEdge ? 1 : isInPath ? 0.6 : 0.3}
                              initial={{ pathLength: 0 }}
                              animate={{ pathLength: 1 }}
                              transition={{ duration: 0.5, delay: index * 0.02 }}
                            />
                          );
                        })}
                      </g>

                      {/* Draw nodes */}
                      <g className="nodes">
                        {filteredNodes.map((node, index) => {
                          const pos = nodePositions[node.id];
                          if (!pos) return null;

                          const config = nodeTypeConfig[node.type];
                          const isActive = isNodeActive(node.id);
                          const isInPath = isNodeInJourney(node.id);
                          const isSelected = selectedNode?.id === node.id;

                          const size = config.size === 'large' ? 16 : config.size === 'medium' ? 12 : 8;
                          const displaySize = isActive ? size * 1.5 : isSelected ? size * 1.3 : size;

                          return (
                            <g
                              key={node.id}
                              transform={`translate(${pos.x}, ${pos.y})`}
                              onClick={() => setSelectedNode(node)}
                              className="cursor-pointer"
                            >
                              {/* Glow effect for active nodes */}
                              {(isActive || isInPath) && (
                                <circle
                                  r={displaySize + 8}
                                  fill={isActive ? '#10b981' : '#6366f1'}
                                  opacity="0.3"
                                >
                                  <animate
                                    attributeName="r"
                                    values={`${displaySize + 8};${displaySize + 12};${displaySize + 8}`}
                                    dur="2s"
                                    repeatCount="indefinite"
                                  />
                                </circle>
                              )}

                              {/* Node circle/shape */}
                              <motion.circle
                                r={displaySize}
                                fill={isActive ? '#10b981' : isInPath ? '#6366f1' : '#ef4444'}
                                stroke={isSelected ? '#fbbf24' : 'white'}
                                strokeWidth={isSelected ? 3 : 1.5}
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                transition={{ delay: index * 0.02, type: 'spring' }}
                                className={node.type === 'Page' ? 'opacity-90' : 'opacity-80'}
                              />

                              {/* Node label */}
                              <text
                                y={displaySize + 20}
                                textAnchor="middle"
                                fill="white"
                                fontSize="12"
                                fontWeight={isActive || isSelected ? 'bold' : 'normal'}
                                className="pointer-events-none select-none"
                              >
                                {node.title.length > 15 ? node.title.substring(0, 15) + '...' : node.title}
                              </text>
                            </g>
                          );
                        })}
                      </g>
                    </svg>
                  </div>
                </motion.div>
              ) : (
                <motion.div
                  key="traditional"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="bg-white/10 backdrop-blur-sm rounded-xl p-6"
                >
                  <h3 className="text-xl font-bold text-white mb-4">Traditional List View</h3>
                  <div className="space-y-2 max-h-[600px] overflow-y-auto">
                    {filteredNodes.filter(n => n.type === 'Page').map((node, index) => (
                      <motion.div
                        key={node.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                        className={`p-4 rounded-lg cursor-pointer transition-all ${
                          selectedNode?.id === node.id
                            ? 'bg-blue-500/30 border-2 border-blue-400'
                            : 'bg-white/5 hover:bg-white/10'
                        }`}
                        onClick={() => setSelectedNode(node)}
                      >
                        <div className="flex items-center gap-3">
                          <Square className="w-5 h-5 text-red-400" />
                          <div>
                            <div className="text-white font-medium">{node.title}</div>
                            <div className="text-sm text-gray-400">
                              {node.topics.length} topics • Page
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>

                  <div className="mt-4 p-4 bg-yellow-500/20 border border-yellow-500 rounded-lg">
                    <div className="flex items-start gap-3">
                      <Info className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-1" />
                      <div className="text-sm text-yellow-100">
                        <strong>Traditional navigation</strong> requires linear search through all pages.
                        No semantic relationships shown. Users must know exact page names.
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Node Details Panel */}
          <div className="lg:col-span-1">
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4 }}
              className="bg-white/10 backdrop-blur-sm rounded-xl p-6 sticky top-8"
            >
              <div className="flex items-center gap-2 mb-4">
                <Info className="w-5 h-5 text-blue-400" />
                <h3 className="text-lg font-bold text-white">Node Details</h3>
              </div>

              {selectedNode ? (
                <div className="space-y-4">
                  <div>
                    <div className="text-sm text-gray-400 mb-1">Title</div>
                    <div className="text-white font-medium text-lg">{selectedNode.title}</div>
                  </div>

                  <div>
                    <div className="text-sm text-gray-400 mb-1">Type</div>
                    <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-lg ${nodeTypeConfig[selectedNode.type].color} ${nodeTypeConfig[selectedNode.type].text}`}>
                      {React.createElement(nodeTypeConfig[selectedNode.type].icon, { className: 'w-4 h-4' })}
                      {selectedNode.type}
                    </div>
                  </div>

                  <div>
                    <div className="text-sm text-gray-400 mb-2">Topics ({selectedNode.topics.length})</div>
                    <div className="flex flex-wrap gap-2">
                      {selectedNode.topics.map(topicId => {
                        const topic = graphStats.topics.find(t => t.id === topicId);
                        return topic ? (
                          <span key={topicId} className="px-2 py-1 bg-blue-500/20 text-blue-300 text-xs rounded">
                            {topic.name}
                          </span>
                        ) : null;
                      })}
                    </div>
                  </div>

                  <div>
                    <div className="text-sm text-gray-400 mb-2">Related Nodes</div>
                    <div className="space-y-2">
                      {sampleEdges
                        .filter(edge => edge.from === selectedNode.id || edge.to === selectedNode.id)
                        .slice(0, 5)
                        .map((edge, idx) => {
                          const relatedId = edge.from === selectedNode.id ? edge.to : edge.from;
                          const relatedNode = enrichedNodes.find(n => n.id === relatedId);
                          return relatedNode ? (
                            <div
                              key={idx}
                              className="flex items-center gap-2 text-sm p-2 bg-white/5 rounded hover:bg-white/10 cursor-pointer transition-colors"
                              onClick={() => setSelectedNode(relatedNode)}
                            >
                              <ChevronRight className="w-4 h-4 text-gray-400" />
                              <span className="text-white">{relatedNode.title}</span>
                            </div>
                          ) : null;
                        })}
                    </div>
                  </div>

                  {selectedNode.personas && selectedNode.personas.length > 0 && (
                    <div>
                      <div className="text-sm text-gray-400 mb-2">Relevant Personas</div>
                      <div className="space-y-1">
                        {selectedNode.personas.map(personaId => {
                          const persona = personas.find(p => p.id === personaId);
                          return persona ? (
                            <div key={personaId} className="text-sm text-purple-300 flex items-center gap-2">
                              <User className="w-3 h-3" />
                              {persona.name}
                            </div>
                          ) : null;
                        })}
                      </div>
                    </div>
                  )}

                  <button
                    className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white px-4 py-3 rounded-lg font-medium hover:shadow-lg transition-shadow"
                  >
                    <MapPin className="w-4 h-4" />
                    Navigate to Node
                  </button>
                </div>
              ) : (
                <div className="text-center py-12">
                  <Search className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                  <p className="text-gray-400">
                    Click a node to view details
                  </p>
                </div>
              )}
            </motion.div>
          </div>
        </div>

        {/* Performance Insights */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-gradient-to-r from-green-500/20 to-emerald-500/20 border border-green-500 rounded-xl p-6"
        >
          <div className="flex items-start gap-4">
            <Sparkles className="w-8 h-8 text-green-400 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="text-xl font-bold text-white mb-2">Why Knowledge Graphs Matter</h3>
              <div className="grid md:grid-cols-3 gap-6 text-sm">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Zap className="w-5 h-5 text-yellow-400" />
                    <span className="font-medium text-white">94.6% Faster</span>
                  </div>
                  <p className="text-gray-300">
                    Semantic navigation eliminates crawling and parsing. Direct path to relevant content.
                  </p>
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Target className="w-5 h-5 text-blue-400" />
                    <span className="font-medium text-white">97% Accuracy</span>
                  </div>
                  <p className="text-gray-300">
                    Pre-structured relationships ensure agents find exactly what they need every time.
                  </p>
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingUp className="w-5 h-5 text-purple-400" />
                    <span className="font-medium text-white">Persona-Aware</span>
                  </div>
                  <p className="text-gray-300">
                    Graph structure enables personalized journeys based on user intent and context.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

const StatCard = ({ label, value, icon: Icon, color }) => (
  <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
    <div>
      <div className="text-sm text-gray-400">{label}</div>
      <div className="text-xl font-bold text-white">{value}</div>
    </div>
    <Icon className={`w-6 h-6 ${color}`} />
  </div>
);

export default GraphNavigatorPage;
