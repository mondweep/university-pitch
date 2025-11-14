import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Zap,
  Clock,
  DollarSign,
  Activity,
  CheckCircle2,
  TrendingUp,
  PlayCircle,
  RotateCcw,
  Sparkles,
  Target,
  Gauge,
  Award
} from 'lucide-react';

const QUERY = "Find Executive MBA programs for working professionals";

// Performance data from research
const TRADITIONAL_DATA = {
  name: "Traditional RAG",
  color: "gray",
  totalTime: 41.5,
  steps: [
    { name: "Web Crawling", duration: 10, delay: 0 },
    { name: "Content Parsing", duration: 18, delay: 10 },
    { name: "Vector Search", duration: 8, delay: 28 },
    { name: "LLM Processing", duration: 5, delay: 36 }
  ],
  metrics: {
    httpRequests: 24,
    llmCalls: 15,
    tokens: 23000,
    cost: 0.137,
    accuracy: 75
  }
};

const ARW_KG_DATA = {
  name: "ARW + Knowledge Graph",
  color: "green",
  totalTime: 2.244,
  steps: [
    { name: "Manifest Lookup", duration: 0.1, delay: 0 },
    { name: "Graph Navigation", duration: 0.5, delay: 0.1 },
    { name: "Fetch .llm.md", duration: 0.6, delay: 0.6 },
    { name: "Generate Answer", duration: 1.044, delay: 1.2 }
  ],
  metrics: {
    httpRequests: 4,
    llmCalls: 1,
    tokens: 3600,
    cost: 0.014,
    accuracy: 97
  }
};

const SpeedDemonPage = () => {
  const [isRacing, setIsRacing] = useState(false);
  const [raceComplete, setRaceComplete] = useState(false);
  const [traditionalProgress, setTraditionalProgress] = useState(0);
  const [arwProgress, setArwProgress] = useState(0);
  const [traditionalStep, setTraditionalStep] = useState(0);
  const [arwStep, setArwStep] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [traditionalMetrics, setTraditionalMetrics] = useState({
    requests: 0,
    llmCalls: 0,
    tokens: 0,
    cost: 0
  });
  const [arwMetrics, setArwMetrics] = useState({
    requests: 0,
    llmCalls: 0,
    tokens: 0,
    cost: 0
  });

  const startTimeRef = useRef(null);
  const animationFrameRef = useRef(null);

  useEffect(() => {
    if (isRacing && !raceComplete) {
      startTimeRef.current = Date.now();

      const animate = () => {
        const now = Date.now();
        const elapsed = (now - startTimeRef.current) / 1000;
        setElapsedTime(elapsed);

        // Update traditional progress
        const tradProgress = Math.min((elapsed / TRADITIONAL_DATA.totalTime) * 100, 100);
        setTraditionalProgress(tradProgress);

        // Update traditional step
        let tradStepIndex = 0;
        let cumTime = 0;
        for (let i = 0; i < TRADITIONAL_DATA.steps.length; i++) {
          cumTime += TRADITIONAL_DATA.steps[i].duration;
          if (elapsed < cumTime) {
            tradStepIndex = i;
            break;
          }
          if (i === TRADITIONAL_DATA.steps.length - 1) {
            tradStepIndex = i;
          }
        }
        setTraditionalStep(tradStepIndex);

        // Update traditional metrics progressively
        const tradMetricProgress = Math.min(elapsed / TRADITIONAL_DATA.totalTime, 1);
        setTraditionalMetrics({
          requests: Math.floor(TRADITIONAL_DATA.metrics.httpRequests * tradMetricProgress),
          llmCalls: Math.floor(TRADITIONAL_DATA.metrics.llmCalls * tradMetricProgress),
          tokens: Math.floor(TRADITIONAL_DATA.metrics.tokens * tradMetricProgress),
          cost: parseFloat((TRADITIONAL_DATA.metrics.cost * tradMetricProgress).toFixed(3))
        });

        // Update ARW progress
        const arwProgress = Math.min((elapsed / ARW_KG_DATA.totalTime) * 100, 100);
        setArwProgress(arwProgress);

        // Update ARW step
        let arwStepIndex = 0;
        cumTime = 0;
        for (let i = 0; i < ARW_KG_DATA.steps.length; i++) {
          cumTime += ARW_KG_DATA.steps[i].duration;
          if (elapsed < cumTime) {
            arwStepIndex = i;
            break;
          }
          if (i === ARW_KG_DATA.steps.length - 1) {
            arwStepIndex = i;
          }
        }
        setArwStep(arwStepIndex);

        // Update ARW metrics progressively
        const arwMetricProgress = Math.min(elapsed / ARW_KG_DATA.totalTime, 1);
        setArwMetrics({
          requests: Math.floor(ARW_KG_DATA.metrics.httpRequests * arwMetricProgress),
          llmCalls: Math.floor(ARW_KG_DATA.metrics.llmCalls * arwMetricProgress),
          tokens: Math.floor(ARW_KG_DATA.metrics.tokens * arwMetricProgress),
          cost: parseFloat((ARW_KG_DATA.metrics.cost * arwMetricProgress).toFixed(3))
        });

        // Check if race is complete
        if (elapsed >= TRADITIONAL_DATA.totalTime) {
          setTraditionalProgress(100);
          setArwProgress(100);
          setRaceComplete(true);
          setIsRacing(false);
        } else {
          animationFrameRef.current = requestAnimationFrame(animate);
        }
      };

      animationFrameRef.current = requestAnimationFrame(animate);

      return () => {
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current);
        }
      };
    }
  }, [isRacing, raceComplete]);

  const startRace = () => {
    setIsRacing(true);
    setRaceComplete(false);
    setTraditionalProgress(0);
    setArwProgress(0);
    setTraditionalStep(0);
    setArwStep(0);
    setElapsedTime(0);
    setTraditionalMetrics({ requests: 0, llmCalls: 0, tokens: 0, cost: 0 });
    setArwMetrics({ requests: 0, llmCalls: 0, tokens: 0, cost: 0 });
  };

  const resetRace = () => {
    setIsRacing(false);
    setRaceComplete(false);
    setTraditionalProgress(0);
    setArwProgress(0);
    setTraditionalStep(0);
    setArwStep(0);
    setElapsedTime(0);
    setTraditionalMetrics({ requests: 0, llmCalls: 0, tokens: 0, cost: 0 });
    setArwMetrics({ requests: 0, llmCalls: 0, tokens: 0, cost: 0 });
  };

  const calculateImprovement = (traditional, arw) => {
    const improvement = ((traditional - arw) / traditional) * 100;
    return improvement.toFixed(1);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto space-y-8">

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center space-y-4"
        >
          <div className="flex items-center justify-center gap-3">
            <Zap className="w-12 h-12 text-yellow-400" />
            <h1 className="text-5xl font-bold text-white">Speed Demon Race</h1>
            <Zap className="w-12 h-12 text-yellow-400" />
          </div>
          <p className="text-xl text-gray-300">Watch ARW + Knowledge Graph obliterate traditional RAG</p>

          {/* Query Display */}
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 mt-6">
            <div className="flex items-start gap-3">
              <Target className="w-6 h-6 text-blue-400 flex-shrink-0 mt-1" />
              <div className="text-left">
                <div className="text-sm text-gray-400 mb-1">Test Query:</div>
                <div className="text-lg text-white font-medium">{QUERY}</div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Control Buttons */}
        <div className="flex justify-center gap-4">
          {!isRacing && !raceComplete && (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={startRace}
              className="flex items-center gap-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white px-8 py-4 rounded-xl font-bold text-lg shadow-xl hover:shadow-2xl transition-shadow"
            >
              <PlayCircle className="w-6 h-6" />
              Start Race
            </motion.button>
          )}
          {raceComplete && (
            <motion.button
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={resetRace}
              className="flex items-center gap-2 bg-gradient-to-r from-blue-500 to-purple-500 text-white px-8 py-4 rounded-xl font-bold text-lg shadow-xl hover:shadow-2xl transition-shadow"
            >
              <RotateCcw className="w-6 h-6" />
              Race Again
            </motion.button>
          )}
        </div>

        {/* Elapsed Time */}
        {isRacing && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="text-center"
          >
            <div className="inline-block bg-white/10 backdrop-blur-sm rounded-xl px-8 py-4">
              <div className="flex items-center gap-3">
                <Clock className="w-8 h-8 text-blue-400" />
                <div>
                  <div className="text-sm text-gray-400">Elapsed Time</div>
                  <div className="text-3xl font-bold text-white">{elapsedTime.toFixed(2)}s</div>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Split-Screen Race */}
        <div className="grid md:grid-cols-2 gap-6">

          {/* Traditional Approach */}
          <RaceTrack
            data={TRADITIONAL_DATA}
            progress={traditionalProgress}
            currentStep={traditionalStep}
            metrics={traditionalMetrics}
            isRacing={isRacing}
            isComplete={raceComplete}
          />

          {/* ARW + KG Approach */}
          <RaceTrack
            data={ARW_KG_DATA}
            progress={arwProgress}
            currentStep={arwStep}
            metrics={arwMetrics}
            isRacing={isRacing}
            isComplete={raceComplete}
            isWinner={raceComplete}
          />
        </div>

        {/* Performance Comparison Table */}
        <AnimatePresence>
          {raceComplete && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              className="bg-white/10 backdrop-blur-sm rounded-xl p-8"
            >
              <div className="flex items-center justify-center gap-3 mb-6">
                <Award className="w-8 h-8 text-yellow-400" />
                <h2 className="text-3xl font-bold text-white">Final Results</h2>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-white/20">
                      <th className="px-4 py-3 text-left text-gray-300">Metric</th>
                      <th className="px-4 py-3 text-center text-gray-400">Traditional RAG</th>
                      <th className="px-4 py-3 text-center text-green-400">ARW + KG</th>
                      <th className="px-4 py-3 text-center text-yellow-400">Improvement</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-b border-white/10">
                      <td className="px-4 py-4 text-white font-medium">Total Time</td>
                      <td className="px-4 py-4 text-center text-gray-300">{TRADITIONAL_DATA.totalTime}s</td>
                      <td className="px-4 py-4 text-center text-green-400 font-bold">{ARW_KG_DATA.totalTime}s</td>
                      <td className="px-4 py-4 text-center text-yellow-400 font-bold">
                        {calculateImprovement(TRADITIONAL_DATA.totalTime, ARW_KG_DATA.totalTime)}% faster
                      </td>
                    </tr>
                    <tr className="border-b border-white/10">
                      <td className="px-4 py-4 text-white font-medium">HTTP Requests</td>
                      <td className="px-4 py-4 text-center text-gray-300">{TRADITIONAL_DATA.metrics.httpRequests}</td>
                      <td className="px-4 py-4 text-center text-green-400 font-bold">{ARW_KG_DATA.metrics.httpRequests}</td>
                      <td className="px-4 py-4 text-center text-yellow-400 font-bold">
                        {calculateImprovement(TRADITIONAL_DATA.metrics.httpRequests, ARW_KG_DATA.metrics.httpRequests)}% fewer
                      </td>
                    </tr>
                    <tr className="border-b border-white/10">
                      <td className="px-4 py-4 text-white font-medium">LLM Calls</td>
                      <td className="px-4 py-4 text-center text-gray-300">{TRADITIONAL_DATA.metrics.llmCalls}</td>
                      <td className="px-4 py-4 text-center text-green-400 font-bold">{ARW_KG_DATA.metrics.llmCalls}</td>
                      <td className="px-4 py-4 text-center text-yellow-400 font-bold">
                        {calculateImprovement(TRADITIONAL_DATA.metrics.llmCalls, ARW_KG_DATA.metrics.llmCalls)}% fewer
                      </td>
                    </tr>
                    <tr className="border-b border-white/10">
                      <td className="px-4 py-4 text-white font-medium">Tokens Processed</td>
                      <td className="px-4 py-4 text-center text-gray-300">{TRADITIONAL_DATA.metrics.tokens.toLocaleString()}</td>
                      <td className="px-4 py-4 text-center text-green-400 font-bold">{ARW_KG_DATA.metrics.tokens.toLocaleString()}</td>
                      <td className="px-4 py-4 text-center text-yellow-400 font-bold">
                        {calculateImprovement(TRADITIONAL_DATA.metrics.tokens, ARW_KG_DATA.metrics.tokens)}% fewer
                      </td>
                    </tr>
                    <tr className="border-b border-white/10">
                      <td className="px-4 py-4 text-white font-medium">Cost per Query</td>
                      <td className="px-4 py-4 text-center text-gray-300">${TRADITIONAL_DATA.metrics.cost}</td>
                      <td className="px-4 py-4 text-center text-green-400 font-bold">${ARW_KG_DATA.metrics.cost}</td>
                      <td className="px-4 py-4 text-center text-yellow-400 font-bold">
                        {calculateImprovement(TRADITIONAL_DATA.metrics.cost, ARW_KG_DATA.metrics.cost)}% cheaper
                      </td>
                    </tr>
                    <tr>
                      <td className="px-4 py-4 text-white font-medium">Accuracy</td>
                      <td className="px-4 py-4 text-center text-gray-300">{TRADITIONAL_DATA.metrics.accuracy}%</td>
                      <td className="px-4 py-4 text-center text-green-400 font-bold">{ARW_KG_DATA.metrics.accuracy}%</td>
                      <td className="px-4 py-4 text-center text-yellow-400 font-bold">
                        +{(ARW_KG_DATA.metrics.accuracy - TRADITIONAL_DATA.metrics.accuracy).toFixed(1)}% more accurate
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div className="mt-8 text-center">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.5, type: "spring" }}
                  className="inline-block bg-gradient-to-r from-yellow-500 to-orange-500 text-white px-8 py-4 rounded-xl font-bold text-2xl"
                >
                  <div className="flex items-center gap-3">
                    <Sparkles className="w-8 h-8" />
                    <span>ARW + KG is {calculateImprovement(TRADITIONAL_DATA.totalTime, ARW_KG_DATA.totalTime)}% faster!</span>
                    <Sparkles className="w-8 h-8" />
                  </div>
                </motion.div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

const RaceTrack = ({ data, progress, currentStep, metrics, isRacing, isComplete, isWinner }) => {
  const colorClasses = {
    gray: {
      bg: "bg-gray-600",
      progress: "bg-gray-400",
      text: "text-gray-300",
      border: "border-gray-500",
      glow: "shadow-gray-500/50"
    },
    green: {
      bg: "bg-green-600",
      progress: "bg-gradient-to-r from-green-400 to-emerald-400",
      text: "text-green-400",
      border: "border-green-500",
      glow: "shadow-green-500/50"
    }
  };

  const colors = colorClasses[data.color];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`bg-white/10 backdrop-blur-sm rounded-xl p-6 space-y-6 ${
        isWinner && isComplete ? 'ring-4 ring-yellow-400 shadow-2xl shadow-yellow-400/50' : ''
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className={`text-2xl font-bold ${colors.text}`}>{data.name}</h3>
          <p className="text-sm text-gray-400 mt-1">{data.totalTime}s total time</p>
        </div>
        {isWinner && isComplete && (
          <motion.div
            initial={{ rotate: 0, scale: 0 }}
            animate={{ rotate: 360, scale: 1 }}
            transition={{ type: "spring" }}
          >
            <Award className="w-12 h-12 text-yellow-400" />
          </motion.div>
        )}
      </div>

      {/* Progress Bar */}
      <div>
        <div className="flex justify-between text-sm mb-2">
          <span className="text-gray-400">Progress</span>
          <span className="text-white font-bold">{progress.toFixed(1)}%</span>
        </div>
        <div className={`h-6 ${colors.bg} rounded-full overflow-hidden`}>
          <motion.div
            className={`h-full ${colors.progress} ${isComplete ? colors.glow : ''} shadow-lg`}
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.3, ease: "easeOut" }}
          />
        </div>
      </div>

      {/* Current Steps */}
      <div className="space-y-3">
        <div className="text-sm text-gray-400 font-medium">Processing Steps:</div>
        {data.steps.map((step, index) => {
          const isActive = index === currentStep && isRacing;
          const isDone = index < currentStep || isComplete;

          return (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`flex items-center gap-3 p-3 rounded-lg ${
                isActive ? `bg-${data.color}-500/20 border ${colors.border}` : 'bg-white/5'
              }`}
            >
              {isDone ? (
                <CheckCircle2 className={`w-5 h-5 ${colors.text}`} />
              ) : isActive ? (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                >
                  <Activity className={`w-5 h-5 ${colors.text}`} />
                </motion.div>
              ) : (
                <div className="w-5 h-5 border-2 border-gray-600 rounded-full" />
              )}
              <div className="flex-1">
                <div className={`text-sm font-medium ${isDone || isActive ? 'text-white' : 'text-gray-500'}`}>
                  {step.name}
                </div>
                <div className="text-xs text-gray-500">{step.duration}s</div>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Real-time Metrics */}
      {(isRacing || isComplete) && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="grid grid-cols-2 gap-3 pt-4 border-t border-white/10"
        >
          <MetricCard icon={Gauge} label="HTTP Requests" value={metrics.requests} />
          <MetricCard icon={Zap} label="LLM Calls" value={metrics.llmCalls} />
          <MetricCard icon={Activity} label="Tokens" value={metrics.tokens.toLocaleString()} />
          <MetricCard icon={DollarSign} label="Cost" value={`$${metrics.cost.toFixed(3)}`} />
        </motion.div>
      )}

      {/* Accuracy (shown at end) */}
      {isComplete && (
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className={`text-center p-4 bg-${data.color}-500/20 rounded-lg border ${colors.border}`}
        >
          <div className="flex items-center justify-center gap-2">
            <TrendingUp className={`w-5 h-5 ${colors.text}`} />
            <span className="text-sm text-gray-400">Accuracy:</span>
            <span className={`text-2xl font-bold ${colors.text}`}>{data.metrics.accuracy}%</span>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};

const MetricCard = ({ icon: Icon, label, value }) => (
  <div className="bg-white/5 rounded-lg p-3">
    <div className="flex items-center gap-2 mb-1">
      <Icon className="w-4 h-4 text-gray-400" />
      <div className="text-xs text-gray-400">{label}</div>
    </div>
    <div className="text-lg font-bold text-white">{value}</div>
  </div>
);

export default SpeedDemonPage;
