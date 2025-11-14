import { Link } from 'react-router-dom'
import { Calculator, Zap, TrendingDown, TrendingUp, Gauge, Target, ArrowRight, CheckCircle } from 'lucide-react'
import { motion } from 'framer-motion'

const HomePage = () => {
  const stats = [
    { label: 'Cost Reduction', value: '99.97%', icon: TrendingDown, color: 'text-success-600' },
    { label: 'Speed Improvement', value: '95%', icon: TrendingUp, color: 'text-primary-600' },
    { label: 'Accuracy Increase', value: '+22pts', icon: Target, color: 'text-purple-600' },
    { label: 'Time Saved', value: '39.3s', icon: Gauge, color: 'text-orange-600' },
  ]

  const demos = [
    {
      title: 'Cost Calculator',
      description: 'See how ARW+KG reduces knowledge graph construction costs from $1,014 to $0.30 (99.97% savings)',
      icon: Calculator,
      path: '/cost-calculator',
      color: 'from-success-500 to-success-600',
      features: [
        'Interactive cost comparison charts',
        'ROI calculator with real LBS data',
        'Scale simulator (1-10,000 institutions)',
        'Validated $14 enrichment cost'
      ]
    },
    {
      title: 'Speed Demon',
      description: 'Watch a live split-screen race showing 95% faster queries (41.5s → 2.2s) with ARW+KG',
      icon: Zap,
      path: '/speed-demon',
      color: 'from-primary-500 to-primary-600',
      features: [
        'Live performance comparison',
        'Real-time metrics visualization',
        'Knowledge graph navigation',
        '97% accuracy vs 75% traditional'
      ]
    }
  ]

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="text-center space-y-6"
      >
        <div className="inline-block">
          <span className="inline-flex items-center px-4 py-2 rounded-full text-sm font-medium bg-primary-100 text-primary-800">
            Research-Backed Demonstration
          </span>
        </div>

        <h1 className="text-5xl md:text-6xl font-bold text-gray-900">
          ARW + Knowledge Graph
          <span className="block text-primary-600 mt-2">Integration Demo</span>
        </h1>

        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          See how combining Agent-Ready Web (ARW) with Knowledge Graphs creates
          a <span className="font-semibold text-gray-900">10-100x improvement</span> over either approach alone
        </p>

        <div className="flex flex-wrap justify-center gap-4 mt-8">
          <Link to="/cost-calculator" className="btn-primary inline-flex items-center space-x-2">
            <Calculator className="w-5 h-5" />
            <span>Explore Cost Savings</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link to="/speed-demon" className="btn-secondary inline-flex items-center space-x-2">
            <Zap className="w-5 h-5" />
            <span>See Speed Demo</span>
          </Link>
        </div>
      </motion.div>

      {/* Stats Grid */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
      >
        {stats.map((stat, index) => {
          const Icon = stat.icon
          return (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.1 * index }}
              className="card text-center"
            >
              <Icon className={`w-8 h-8 mx-auto mb-3 ${stat.color}`} />
              <div className="stat-large">{stat.value}</div>
              <div className="stat-label mt-2">{stat.label}</div>
            </motion.div>
          )
        })}
      </motion.div>

      {/* Research Foundation */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: 0.4 }}
        className="card bg-gradient-to-br from-blue-50 to-indigo-50"
      >
        <div className="flex items-start space-x-4">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-primary-600 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-6 h-6 text-white" />
            </div>
          </div>
          <div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Built on Real Research</h3>
            <p className="text-gray-700 mb-4">
              This demonstration uses actual data from London Business School's knowledge graph implementation:
              <span className="font-semibold"> 3,963 nodes and 3,953 edges</span> extracted from 10 pages.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <div className="text-2xl font-bold text-primary-600">$14</div>
                <div className="text-sm text-gray-600">Total enrichment cost (validated)</div>
              </div>
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <div className="text-2xl font-bold text-success-600">100%</div>
                <div className="text-sm text-gray-600">Success rate on topic extraction</div>
              </div>
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <div className="text-2xl font-bold text-purple-600">&lt;100ms</div>
                <div className="text-sm text-gray-600">Query latency (3,963 nodes)</div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Demo Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {demos.map((demo, index) => {
          const Icon = demo.icon
          return (
            <motion.div
              key={demo.title}
              initial={{ opacity: 0, x: index === 0 ? -20 : 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.3 + index * 0.1 }}
            >
              <Link to={demo.path} className="block group">
                <div className="card hover:shadow-2xl transition-all duration-300 group-hover:-translate-y-1">
                  <div className={`w-16 h-16 bg-gradient-to-br ${demo.color} rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300`}>
                    <Icon className="w-8 h-8 text-white" />
                  </div>

                  <h3 className="text-2xl font-bold text-gray-900 mb-2">{demo.title}</h3>
                  <p className="text-gray-600 mb-6">{demo.description}</p>

                  <div className="space-y-2 mb-6">
                    {demo.features.map((feature) => (
                      <div key={feature} className="flex items-start space-x-2">
                        <CheckCircle className="w-5 h-5 text-success-600 flex-shrink-0 mt-0.5" />
                        <span className="text-sm text-gray-700">{feature}</span>
                      </div>
                    ))}
                  </div>

                  <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                    <span className="text-primary-600 font-medium group-hover:text-primary-700">
                      Explore Demo
                    </span>
                    <ArrowRight className="w-5 h-5 text-primary-600 group-hover:translate-x-2 transition-transform duration-200" />
                  </div>
                </div>
              </Link>
            </motion.div>
          )
        })}
      </div>

      {/* Key Findings */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: 0.6 }}
        className="card"
      >
        <h3 className="text-2xl font-bold text-gray-900 mb-6">Key Research Findings</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-semibold text-gray-900 mb-3">Economic Impact</h4>
            <ul className="space-y-2 text-gray-700">
              <li className="flex items-start">
                <span className="text-success-600 mr-2">✓</span>
                <span><strong>99.97% cost reduction</strong> in KG construction ($1,014 → $0.30)</span>
              </li>
              <li className="flex items-start">
                <span className="text-success-600 mr-2">✓</span>
                <span><strong>$6.76M savings</strong> at scale (100 institutions)</span>
              </li>
              <li className="flex items-start">
                <span className="text-success-600 mr-2">✓</span>
                <span><strong>1,352% Year 1 ROI</strong> for publishers</span>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 mb-3">Technical Performance</h4>
            <ul className="space-y-2 text-gray-700">
              <li className="flex items-start">
                <span className="text-primary-600 mr-2">✓</span>
                <span><strong>95% faster queries</strong> (41.5s → 2.2s)</span>
              </li>
              <li className="flex items-start">
                <span className="text-primary-600 mr-2">✓</span>
                <span><strong>83% fewer HTTP requests</strong> (24 → 4)</span>
              </li>
              <li className="flex items-start">
                <span className="text-primary-600 mr-2">✓</span>
                <span><strong>22-point accuracy improvement</strong> (75% → 97%)</span>
              </li>
            </ul>
          </div>
        </div>
      </motion.div>
    </div>
  )
}

export default HomePage
