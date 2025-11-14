import { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  DollarSign,
  TrendingDown,
  Calculator,
  Zap,
  ArrowRight,
  Award,
  Building2,
  Users,
  CheckCircle2,
  Info,
  Percent,
  Clock,
  Target
} from 'lucide-react'
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart
} from 'recharts'

const CostCalculatorPage = () => {
  // State management
  const [numPages, setNumPages] = useState(4000)
  const [numInstitutions, setNumInstitutions] = useState(1)
  const [activeView, setActiveView] = useState('breakdown') // breakdown, roi, scale

  // Cost data from research
  const costData = {
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
    }
  }

  // Calculate costs based on inputs
  const calculations = useMemo(() => {
    // Base costs for 4,000 pages (1 institution)
    const baseFactor = numPages / 4000

    const traditionalCost = costData.traditional.total * baseFactor
    const arwCost = costData.arw.total * baseFactor
    const savings = traditionalCost - arwCost
    const savingsPercent = ((savings / traditionalCost) * 100).toFixed(2)

    // Year 1 costs (including enrichment)
    const enrichmentCostPerPage = 14 / 4000 // $14 for 4,000 pages
    const year1Enrichment = enrichmentCostPerPage * numPages
    const year1Traditional = traditionalCost
    const year1ARW = arwCost + year1Enrichment
    const year1Savings = year1Traditional - year1ARW
    const year1ROI = ((year1Savings / year1ARW) * 100).toFixed(0)

    // Payback period in months
    const paybackMonths = (year1ARW / year1Savings) * 12

    // Scale calculations
    const totalInstitutions = numInstitutions
    const scaledTraditional = traditionalCost * totalInstitutions
    const scaledARW = arwCost * totalInstitutions
    const scaledSavings = scaledTraditional - scaledARW

    return {
      traditionalCost,
      arwCost,
      savings,
      savingsPercent,
      year1Traditional,
      year1ARW,
      year1Savings,
      year1ROI,
      paybackMonths,
      scaledTraditional,
      scaledARW,
      scaledSavings
    }
  }, [numPages, numInstitutions, costData])

  // Data for cost breakdown chart
  const breakdownData = [
    {
      name: 'Crawling',
      Traditional: costData.traditional.crawling,
      ARW: costData.arw.manifestFetch
    },
    {
      name: 'Parsing',
      Traditional: costData.traditional.parsing,
      ARW: 0
    },
    {
      name: 'Topic Extraction',
      Traditional: costData.traditional.topicExtraction,
      ARW: costData.arw.topicExtraction
    },
    {
      name: 'Embeddings',
      Traditional: costData.traditional.embeddings,
      ARW: costData.arw.embeddings
    },
    {
      name: 'Personas',
      Traditional: costData.traditional.personas,
      ARW: costData.arw.personas
    }
  ]

  // Data for pie chart
  const traditionalPieData = [
    { name: 'Crawling', value: costData.traditional.crawling, color: '#ef4444' },
    { name: 'Parsing', value: costData.traditional.parsing, color: '#f97316' },
    { name: 'Topic Extraction', value: costData.traditional.topicExtraction, color: '#eab308' },
    { name: 'Embeddings', value: costData.traditional.embeddings, color: '#84cc16' },
    { name: 'Personas', value: costData.traditional.personas, color: '#22c55e' }
  ]

  const arwPieData = [
    { name: 'Manifest Fetch', value: 0.00001, color: '#3b82f6' }, // Tiny slice for visual
    { name: 'Embeddings', value: costData.arw.embeddings, color: '#22c55e' }
  ]

  // Data for scale comparison
  const scaleData = useMemo(() => {
    const data = []
    const maxInst = Math.max(numInstitutions, 100)
    const steps = [1, 10, 25, 50, 75, 100]

    steps.forEach(inst => {
      if (inst <= maxInst) {
        data.push({
          institutions: inst,
          Traditional: (costData.traditional.total * inst) / 1000, // in thousands
          ARW: (costData.arw.total * inst) / 1000,
          Savings: ((costData.traditional.total - costData.arw.total) * inst) / 1000
        })
      }
    })

    // Add current selection if not in steps
    if (!steps.includes(numInstitutions) && numInstitutions <= maxInst) {
      data.push({
        institutions: numInstitutions,
        Traditional: (costData.traditional.total * numInstitutions) / 1000,
        ARW: (costData.arw.total * numInstitutions) / 1000,
        Savings: ((costData.traditional.total - costData.arw.total) * numInstitutions) / 1000
      })
      data.sort((a, b) => a.institutions - b.institutions)
    }

    return data
  }, [numInstitutions, costData])

  // Format currency
  const formatCurrency = (value) => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(2)}M`
    } else if (value >= 1000) {
      return `$${(value / 1000).toFixed(2)}K`
    } else {
      return `$${value.toFixed(2)}`
    }
  }

  // Key metrics data
  const keyMetrics = [
    {
      label: 'Cost Reduction',
      value: '99.97%',
      icon: TrendingDown,
      color: 'text-success-600',
      bgColor: 'bg-success-50',
      description: 'From $1,014 to $0.30'
    },
    {
      label: 'Year 1 ROI',
      value: `${calculations.year1ROI}%`,
      icon: Target,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      description: 'Return on investment'
    },
    {
      label: 'Payback Period',
      value: `${calculations.paybackMonths.toFixed(1)} mo`,
      icon: Clock,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
      description: 'Time to break even'
    },
    {
      label: 'Scale Savings (100)',
      value: formatCurrency((costData.traditional.total - costData.arw.total) * 100),
      icon: Award,
      color: 'text-primary-600',
      bgColor: 'bg-primary-50',
      description: 'At 100 institutions'
    }
  ]

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="text-center space-y-4"
      >
        <div className="inline-flex items-center space-x-2 px-4 py-2 bg-success-100 text-success-800 rounded-full">
          <Calculator className="w-4 h-4" />
          <span className="text-sm font-medium">Cost Analysis Tool</span>
        </div>

        <h1 className="text-4xl md:text-5xl font-bold text-gray-900">
          ARW + Knowledge Graph
          <span className="block text-success-600 mt-2">Cost Calculator</span>
        </h1>

        <p className="text-lg text-gray-600 max-w-3xl mx-auto">
          See how ARW reduces knowledge graph construction costs by{' '}
          <span className="font-bold text-success-600">99.97%</span> - from{' '}
          <span className="font-semibold">$1,014</span> to just{' '}
          <span className="font-semibold text-success-600">$0.30</span> per 4,000 pages
        </p>
      </motion.div>

      {/* Key Metrics Grid */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
      >
        {keyMetrics.map((metric, index) => {
          const Icon = metric.icon
          return (
            <motion.div
              key={metric.label}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4, delay: 0.1 * index }}
              className="card hover:shadow-xl transition-shadow duration-300"
            >
              <div className={`w-12 h-12 ${metric.bgColor} rounded-lg flex items-center justify-center mb-4`}>
                <Icon className={`w-6 h-6 ${metric.color}`} />
              </div>
              <div className="stat-large text-3xl">{metric.value}</div>
              <div className="stat-label mt-2 mb-1">{metric.label}</div>
              <p className="text-xs text-gray-500">{metric.description}</p>
            </motion.div>
          )
        })}
      </motion.div>

      {/* View Tabs */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: 0.3 }}
        className="flex flex-wrap justify-center gap-3"
      >
        {[
          { id: 'breakdown', label: 'Cost Breakdown', icon: DollarSign },
          { id: 'roi', label: 'ROI Calculator', icon: Calculator },
          { id: 'scale', label: 'Scale Simulator', icon: Building2 }
        ].map((view) => {
          const Icon = view.icon
          return (
            <button
              key={view.id}
              onClick={() => setActiveView(view.id)}
              className={`flex items-center space-x-2 px-6 py-3 rounded-lg font-medium transition-all duration-200 ${
                activeView === view.id
                  ? 'bg-primary-600 text-white shadow-lg scale-105'
                  : 'bg-white text-gray-700 border-2 border-gray-200 hover:border-primary-300 hover:bg-primary-50'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span>{view.label}</span>
            </button>
          )
        })}
      </motion.div>

      {/* Cost Breakdown View */}
      {activeView === 'breakdown' && (
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
          className="space-y-6"
        >
          {/* Comparison Cards */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Traditional Approach */}
            <div className="card bg-gradient-to-br from-red-50 to-orange-50 border-red-200">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-2xl font-bold text-gray-900">Traditional Approach</h3>
                  <p className="text-sm text-gray-600 mt-1">Manual crawling + scraping</p>
                </div>
                <div className="text-right">
                  <div className="text-4xl font-bold text-red-600">
                    ${costData.traditional.total.toFixed(2)}
                  </div>
                  <div className="text-xs text-gray-500">per 4,000 pages</div>
                </div>
              </div>

              {/* Cost Items */}
              <div className="space-y-3">
                {[
                  { label: 'Web Crawling', value: costData.traditional.crawling, desc: 'Selenium/Playwright automation' },
                  { label: 'HTML Parsing', value: costData.traditional.parsing, desc: 'Extract text from HTML' },
                  { label: 'Topic Extraction', value: costData.traditional.topicExtraction, desc: 'GPT-4o analysis' },
                  { label: 'Embeddings', value: costData.traditional.embeddings, desc: 'Vector generation' },
                  { label: 'Personas', value: costData.traditional.personas, desc: 'User targeting' }
                ].map((item) => (
                  <div key={item.label} className="flex items-center justify-between p-3 bg-white rounded-lg">
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">{item.label}</div>
                      <div className="text-xs text-gray-500">{item.desc}</div>
                    </div>
                    <div className="text-lg font-bold text-gray-700">
                      ${item.value.toFixed(2)}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* ARW Approach */}
            <div className="card bg-gradient-to-br from-success-50 to-emerald-50 border-success-200">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-2xl font-bold text-gray-900">ARW Approach</h3>
                  <p className="text-sm text-gray-600 mt-1">Agent-ready web manifest</p>
                </div>
                <div className="text-right">
                  <div className="text-4xl font-bold text-success-600">
                    ${costData.arw.total.toFixed(2)}
                  </div>
                  <div className="text-xs text-gray-500">per 4,000 pages</div>
                </div>
              </div>

              {/* Cost Items */}
              <div className="space-y-3">
                {[
                  { label: 'Manifest Fetch', value: costData.arw.manifestFetch, desc: 'Free - single API call', badge: 'FREE' },
                  { label: 'HTML Parsing', value: 0, desc: 'Free - structured JSON', badge: 'FREE' },
                  { label: 'Topic Extraction', value: costData.arw.topicExtraction, desc: 'Free - pre-extracted', badge: 'FREE' },
                  { label: 'Embeddings', value: costData.arw.embeddings, desc: '85% reduction', badge: '-85%' },
                  { label: 'Personas', value: costData.arw.personas, desc: 'Free - from manifest', badge: 'FREE' }
                ].map((item) => (
                  <div key={item.label} className="flex items-center justify-between p-3 bg-white rounded-lg">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <div className="font-medium text-gray-900">{item.label}</div>
                        <span className={`badge text-xs ${
                          item.badge === 'FREE' ? 'badge-success' : 'badge-primary'
                        }`}>
                          {item.badge}
                        </span>
                      </div>
                      <div className="text-xs text-gray-500">{item.desc}</div>
                    </div>
                    <div className="text-lg font-bold text-success-600">
                      ${item.value.toFixed(2)}
                    </div>
                  </div>
                ))}
              </div>

              {/* Savings Banner */}
              <div className="mt-6 p-4 bg-success-600 text-white rounded-lg">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-5 h-5" />
                    <span className="font-semibold">Total Savings</span>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold">
                      ${(costData.traditional.total - costData.arw.total).toFixed(2)}
                    </div>
                    <div className="text-sm opacity-90">99.97% reduction</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Bar Chart */}
          <div className="card">
            <h3 className="text-xl font-bold text-gray-900 mb-6">Cost Component Comparison</h3>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={breakdownData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} label={{ value: 'Cost ($)', angle: -90, position: 'insideLeft' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                  formatter={(value) => `$${value.toFixed(2)}`}
                />
                <Legend />
                <Bar dataKey="Traditional" fill="#ef4444" radius={[8, 8, 0, 0]} />
                <Bar dataKey="ARW" fill="#22c55e" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Pie Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card">
              <h3 className="text-lg font-bold text-gray-900 mb-4 text-center">Traditional Cost Distribution</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={traditionalPieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {traditionalPieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => `$${value.toFixed(2)}`} />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="card">
              <h3 className="text-lg font-bold text-gray-900 mb-4 text-center">ARW Cost Distribution</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={arwPieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name }) => name}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {arwPieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => value === 0.00001 ? '$0.00 (Free)' : `$${value.toFixed(2)}`} />
                </PieChart>
              </ResponsiveContainer>
              <div className="mt-4 p-4 bg-success-50 rounded-lg text-center">
                <p className="text-sm text-success-800">
                  <strong>100% of ARW manifest features are free</strong>
                  <br />
                  <span className="text-xs">Only embeddings generation incurs minimal cost</span>
                </p>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* ROI Calculator View */}
      {activeView === 'roi' && (
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
          className="space-y-6"
        >
          <div className="card bg-gradient-to-br from-purple-50 to-indigo-50">
            <div className="flex items-start space-x-4 mb-6">
              <div className="w-12 h-12 bg-purple-600 rounded-lg flex items-center justify-center">
                <Calculator className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-gray-900">ROI Calculator</h3>
                <p className="text-gray-600 mt-1">
                  Calculate your return on investment based on the number of pages
                </p>
              </div>
            </div>

            {/* Input Controls */}
            <div className="space-y-6">
              <div>
                <label className="flex items-center justify-between mb-3">
                  <span className="font-medium text-gray-900">Number of Pages</span>
                  <span className="text-2xl font-bold text-primary-600">
                    {numPages.toLocaleString()}
                  </span>
                </label>
                <input
                  type="range"
                  min="1000"
                  max="100000"
                  step="1000"
                  value={numPages}
                  onChange={(e) => setNumPages(parseInt(e.target.value))}
                  className="w-full h-3 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-2">
                  <span>1,000</span>
                  <span>50,000</span>
                  <span>100,000</span>
                </div>
              </div>
            </div>
          </div>

          {/* Results Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Traditional Cost */}
            <div className="card bg-red-50 border-red-200">
              <div className="text-center">
                <div className="w-12 h-12 bg-red-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <DollarSign className="w-6 h-6 text-white" />
                </div>
                <div className="text-sm font-medium text-gray-600 uppercase tracking-wider mb-2">
                  Traditional Approach
                </div>
                <div className="text-4xl font-bold text-red-600 mb-2">
                  {formatCurrency(calculations.traditionalCost)}
                </div>
                <div className="text-xs text-gray-500">Year 1 construction cost</div>
              </div>
            </div>

            {/* ARW Cost */}
            <div className="card bg-success-50 border-success-200">
              <div className="text-center">
                <div className="w-12 h-12 bg-success-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Zap className="w-6 h-6 text-white" />
                </div>
                <div className="text-sm font-medium text-gray-600 uppercase tracking-wider mb-2">
                  ARW Approach
                </div>
                <div className="text-4xl font-bold text-success-600 mb-2">
                  {formatCurrency(calculations.year1ARW)}
                </div>
                <div className="text-xs text-gray-500">Year 1 total cost (with $14 enrichment)</div>
              </div>
            </div>

            {/* Savings */}
            <div className="card bg-gradient-to-br from-purple-50 to-indigo-50 border-purple-200">
              <div className="text-center">
                <div className="w-12 h-12 bg-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <TrendingDown className="w-6 h-6 text-white" />
                </div>
                <div className="text-sm font-medium text-gray-600 uppercase tracking-wider mb-2">
                  Total Savings
                </div>
                <div className="text-4xl font-bold text-purple-600 mb-2">
                  {formatCurrency(calculations.year1Savings)}
                </div>
                <div className="text-xs text-gray-500">{calculations.savingsPercent}% reduction</div>
              </div>
            </div>
          </div>

          {/* ROI Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card bg-gradient-to-br from-orange-50 to-yellow-50">
              <div className="flex items-center space-x-4">
                <div className="w-16 h-16 bg-orange-600 rounded-xl flex items-center justify-center">
                  <Percent className="w-8 h-8 text-white" />
                </div>
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-600 uppercase tracking-wider">
                    Year 1 ROI
                  </div>
                  <div className="text-5xl font-bold text-orange-600 mt-1">
                    {calculations.year1ROI}%
                  </div>
                  <div className="text-xs text-gray-500 mt-2">
                    Return on investment in first year
                  </div>
                </div>
              </div>
            </div>

            <div className="card bg-gradient-to-br from-blue-50 to-cyan-50">
              <div className="flex items-center space-x-4">
                <div className="w-16 h-16 bg-blue-600 rounded-xl flex items-center justify-center">
                  <Clock className="w-8 h-8 text-white" />
                </div>
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-600 uppercase tracking-wider">
                    Payback Period
                  </div>
                  <div className="text-5xl font-bold text-blue-600 mt-1">
                    {calculations.paybackMonths.toFixed(1)}
                  </div>
                  <div className="text-xs text-gray-500 mt-2">
                    Months to break even
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Cost Breakdown Chart */}
          <div className="card">
            <h3 className="text-xl font-bold text-gray-900 mb-6">Cost Over Time (3 Years)</h3>
            <ResponsiveContainer width="100%" height={350}>
              <AreaChart
                data={[
                  { year: 'Year 1', Traditional: calculations.traditionalCost, ARW: calculations.year1ARW },
                  { year: 'Year 2', Traditional: calculations.traditionalCost, ARW: calculations.arwCost },
                  { year: 'Year 3', Traditional: calculations.traditionalCost, ARW: calculations.arwCost }
                ]}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="year" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                  formatter={(value) => formatCurrency(value)}
                />
                <Legend />
                <Area type="monotone" dataKey="Traditional" stackId="1" stroke="#ef4444" fill="#ef4444" fillOpacity={0.6} />
                <Area type="monotone" dataKey="ARW" stackId="2" stroke="#22c55e" fill="#22c55e" fillOpacity={0.6} />
              </AreaChart>
            </ResponsiveContainer>
            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <div className="flex items-start space-x-2">
                <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-blue-800">
                  <strong>Note:</strong> Year 1 ARW includes one-time ${(14 * numPages / 4000).toFixed(2)} enrichment cost.
                  Years 2-3 only require minimal embedding updates (${calculations.arwCost.toFixed(2)}).
                </p>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Scale Simulator View */}
      {activeView === 'scale' && (
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
          className="space-y-6"
        >
          <div className="card bg-gradient-to-br from-blue-50 to-indigo-50">
            <div className="flex items-start space-x-4 mb-6">
              <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center">
                <Building2 className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-gray-900">Scale Simulator</h3>
                <p className="text-gray-600 mt-1">
                  See how costs change as you scale to multiple institutions
                </p>
              </div>
            </div>

            {/* Institution Slider */}
            <div className="space-y-6">
              <div>
                <label className="flex items-center justify-between mb-3">
                  <span className="font-medium text-gray-900">Number of Institutions</span>
                  <span className="text-2xl font-bold text-primary-600">
                    {numInstitutions.toLocaleString()}
                  </span>
                </label>
                <input
                  type="range"
                  min="1"
                  max="10000"
                  step="1"
                  value={numInstitutions}
                  onChange={(e) => setNumInstitutions(parseInt(e.target.value))}
                  className="w-full h-3 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-2">
                  <span>1</span>
                  <span>5,000</span>
                  <span>10,000</span>
                </div>
              </div>
            </div>
          </div>

          {/* Scale Comparison Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="card bg-red-50 border-red-200">
              <div className="text-center">
                <div className="text-sm font-medium text-gray-600 uppercase tracking-wider mb-2">
                  Traditional Total Cost
                </div>
                <div className="text-4xl font-bold text-red-600 mb-2">
                  {formatCurrency(calculations.scaledTraditional)}
                </div>
                <div className="text-xs text-gray-500">
                  ${costData.traditional.total.toFixed(2)} × {numInstitutions.toLocaleString()}
                </div>
              </div>
            </div>

            <div className="card bg-success-50 border-success-200">
              <div className="text-center">
                <div className="text-sm font-medium text-gray-600 uppercase tracking-wider mb-2">
                  ARW Total Cost
                </div>
                <div className="text-4xl font-bold text-success-600 mb-2">
                  {formatCurrency(calculations.scaledARW)}
                </div>
                <div className="text-xs text-gray-500">
                  ${costData.arw.total.toFixed(2)} × {numInstitutions.toLocaleString()}
                </div>
              </div>
            </div>

            <div className="card bg-gradient-to-br from-purple-50 to-pink-50 border-purple-200">
              <div className="text-center">
                <div className="text-sm font-medium text-gray-600 uppercase tracking-wider mb-2">
                  Total Savings
                </div>
                <div className="text-4xl font-bold text-purple-600 mb-2">
                  {formatCurrency(calculations.scaledSavings)}
                </div>
                <div className="text-xs text-gray-500">99.97% reduction</div>
              </div>
            </div>
          </div>

          {/* Scale Chart */}
          <div className="card">
            <h3 className="text-xl font-bold text-gray-900 mb-6">Cost Scaling Comparison</h3>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={scaleData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="institutions"
                  tick={{ fontSize: 12 }}
                  label={{ value: 'Number of Institutions', position: 'insideBottom', offset: -5 }}
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  label={{ value: 'Cost ($K)', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                  formatter={(value) => `$${(value * 1000).toLocaleString()}`}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="Traditional"
                  stroke="#ef4444"
                  strokeWidth={3}
                  dot={{ fill: '#ef4444', r: 6 }}
                  activeDot={{ r: 8 }}
                />
                <Line
                  type="monotone"
                  dataKey="ARW"
                  stroke="#22c55e"
                  strokeWidth={3}
                  dot={{ fill: '#22c55e', r: 6 }}
                  activeDot={{ r: 8 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Milestone Markers */}
          <div className="card">
            <h3 className="text-xl font-bold text-gray-900 mb-6">Scale Milestones</h3>
            <div className="space-y-4">
              {[
                { institutions: 10, label: 'Small Publisher' },
                { institutions: 100, label: 'Medium Publisher' },
                { institutions: 1000, label: 'Large Publisher' },
                { institutions: 10000, label: 'Enterprise Scale' }
              ].map((milestone) => {
                const tradCost = costData.traditional.total * milestone.institutions
                const arwCost = costData.arw.total * milestone.institutions
                const savings = tradCost - arwCost

                return (
                  <div
                    key={milestone.institutions}
                    className="p-4 bg-gradient-to-r from-gray-50 to-blue-50 rounded-lg border border-gray-200"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="w-16 h-16 bg-primary-600 rounded-lg flex items-center justify-center">
                          <Users className="w-8 h-8 text-white" />
                        </div>
                        <div>
                          <div className="font-bold text-gray-900 text-lg">{milestone.label}</div>
                          <div className="text-sm text-gray-600">{milestone.institutions.toLocaleString()} institutions</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-success-600">
                          {formatCurrency(savings)}
                        </div>
                        <div className="text-xs text-gray-500">Total savings</div>
                      </div>
                    </div>
                    <div className="mt-3 grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Traditional:</span>
                        <span className="ml-2 font-semibold text-red-600">{formatCurrency(tradCost)}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">ARW:</span>
                        <span className="ml-2 font-semibold text-success-600">{formatCurrency(arwCost)}</span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Enterprise Highlight */}
          {numInstitutions >= 100 && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
              className="card bg-gradient-to-br from-purple-600 to-indigo-600 text-white"
            >
              <div className="flex items-center space-x-4">
                <div className="w-16 h-16 bg-white/20 rounded-xl flex items-center justify-center">
                  <Award className="w-8 h-8 text-white" />
                </div>
                <div className="flex-1">
                  <h3 className="text-2xl font-bold mb-2">Enterprise-Scale Impact</h3>
                  <p className="text-purple-100 text-lg">
                    At {numInstitutions.toLocaleString()} institutions, ARW saves{' '}
                    <span className="font-bold text-white">{formatCurrency(calculations.scaledSavings)}</span>
                    {' '}compared to traditional approaches
                  </p>
                  <div className="mt-4 flex items-center space-x-6 text-sm">
                    <div>
                      <div className="text-purple-200">Cost Reduction</div>
                      <div className="text-2xl font-bold">99.97%</div>
                    </div>
                    <div>
                      <div className="text-purple-200">ROI</div>
                      <div className="text-2xl font-bold">{calculations.year1ROI}%</div>
                    </div>
                    <div>
                      <div className="text-purple-200">Payback</div>
                      <div className="text-2xl font-bold">{calculations.paybackMonths.toFixed(1)} mo</div>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </motion.div>
      )}

      {/* Research Foundation Note */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: 0.5 }}
        className="card bg-gradient-to-br from-gray-50 to-blue-50"
      >
        <div className="flex items-start space-x-4">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center">
              <Info className="w-6 h-6 text-white" />
            </div>
          </div>
          <div>
            <h4 className="font-bold text-gray-900 mb-2">Research-Backed Data</h4>
            <p className="text-gray-700 text-sm leading-relaxed">
              All calculations are based on actual implementation data from London Business School's knowledge graph
              (3,963 nodes, 3,953 edges from 10 pages scaled to 4,000 pages). Traditional costs include Selenium/Playwright
              crawling ($500), HTML parsing ($500), GPT-4o topic extraction ($11.89), and embeddings ($2.00). ARW approach
              eliminates crawling and parsing entirely, provides free topic extraction via manifest, and reduces embedding
              costs by 85% through structured data.
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
              <span className="badge badge-primary">Validated $14 enrichment cost</span>
              <span className="badge badge-success">100% success rate</span>
              <span className="badge bg-purple-100 text-purple-800">Real LBS data</span>
            </div>
          </div>
        </div>
      </motion.div>

      {/* CTA Section */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: 0.6 }}
        className="card bg-gradient-to-br from-primary-600 to-indigo-600 text-white text-center"
      >
        <h3 className="text-3xl font-bold mb-4">Ready to See the Speed Advantage?</h3>
        <p className="text-lg text-primary-100 mb-6 max-w-2xl mx-auto">
          Beyond cost savings, ARW + Knowledge Graphs deliver 95% faster queries (41.5s → 2.2s)
          and 22-point accuracy improvements. Experience the performance difference.
        </p>
        <div className="flex flex-wrap justify-center gap-4">
          <a
            href="/speed-demon"
            className="inline-flex items-center space-x-2 bg-white text-primary-600 px-8 py-4 rounded-lg font-bold hover:bg-primary-50 transition-colors duration-200 shadow-lg hover:shadow-xl"
          >
            <Zap className="w-5 h-5" />
            <span>See Speed Demo</span>
            <ArrowRight className="w-5 h-5" />
          </a>
          <a
            href="/"
            className="inline-flex items-center space-x-2 bg-primary-700 text-white px-8 py-4 rounded-lg font-bold hover:bg-primary-800 transition-colors duration-200 border-2 border-white/20"
          >
            <span>Back to Home</span>
          </a>
        </div>
      </motion.div>
    </div>
  )
}

export default CostCalculatorPage
