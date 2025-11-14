# Netlify Deployment Guide

Complete guide to deploying the ARW+KG Demo to Netlify.

## 📋 Prerequisites

- Git repository with demo code
- Netlify account (free tier is sufficient)
- Node.js 18+ installed locally (for testing)

## 🚀 Deployment Steps

### Method 1: Netlify UI (Easiest)

1. **Go to Netlify**
   - Visit [app.netlify.com](https://app.netlify.com)
   - Sign in or create account (free)

2. **Add New Site**
   - Click "Add new site" → "Import an existing project"
   - Choose "Deploy with GitHub"
   - Authorize Netlify to access your repositories

3. **Select Repository**
   - Find: `mondweep/university-pitch`
   - Click to select

4. **Configure Build Settings**
   ```
   Base directory: arw-knowledge-graph/demo
   Build command: npm run build
   Publish directory: arw-knowledge-graph/demo/dist
   ```

5. **Deploy**
   - Click "Deploy site"
   - Wait 1-2 minutes for build
   - Your site is live! 🎉

### Method 2: Netlify CLI

```bash
# Navigate to demo directory
cd arw-knowledge-graph/demo

# Install Netlify CLI globally
npm install -g netlify-cli

# Login to Netlify
netlify login

# Initialize new Netlify site
netlify init

# Or deploy to existing site
netlify deploy --prod

# Follow prompts:
# - Build command: npm run build
# - Publish directory: dist
```

### Method 3: Git-Based Continuous Deployment

1. **Connect Git Repository**
   - Push code to GitHub (already done)
   - In Netlify: "New site from Git"
   - Select repository

2. **Configure Auto-Deploy**
   - Netlify will auto-deploy on every push to main branch
   - Build settings stored in `netlify.toml`

3. **Branch Deploys** (Optional)
   - Enable branch deploys in Netlify settings
   - Each PR gets preview URL

## ⚙️ Build Configuration

Your `netlify.toml` is already configured:

```toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

[build.environment]
  NODE_VERSION = "18"
```

## 🔧 Troubleshooting

### Build Fails

**Error**: "Command failed with exit code 1"

```bash
# Test build locally first
cd arw-knowledge-graph/demo
npm install
npm run build

# If successful locally, check Netlify build log for specifics
```

### Missing Dependencies

**Error**: "Cannot find module 'react'"

```bash
# Ensure package.json is in correct location
# Should be: arw-knowledge-graph/demo/package.json

# Verify base directory in Netlify:
# Base directory: arw-knowledge-graph/demo
```

### Routes Not Working

**Error**: "Page not found" on `/cost-calculator`

- ✅ This is already handled by `netlify.toml` redirects
- Redirects all routes to `index.html` (SPA mode)

### Slow Build Times

**Normal build time**: 1-2 minutes

To speed up:
```bash
# Enable dependency caching (automatic on Netlify)
# Use build plugins (optional)
```

## 📊 Post-Deployment

### 1. Test Your Site

Visit your Netlify URL and verify:
- ✅ Home page loads
- ✅ Navigation works
- ✅ Cost Calculator functional
- ✅ Speed Demon animation runs
- ✅ Charts render correctly
- ✅ Mobile responsive

### 2. Custom Domain (Optional)

```
Netlify Dashboard → Domain Settings → Add custom domain
```

Example: `arw-demo.yourdomain.com`

### 3. Analytics (Optional)

Enable Netlify Analytics:
```
Site Settings → Analytics → Enable
```

### 4. Performance Optimization

Already optimized:
- ✅ Vite code splitting
- ✅ Tree shaking
- ✅ Minification
- ✅ Gzip compression (Netlify automatic)

## 🎯 Expected Results

**Build time**: 60-90 seconds
**Bundle size**: ~150KB gzipped
**Lighthouse scores**: 
- Performance: 95+
- Accessibility: 95+
- Best Practices: 95+
- SEO: 90+

## 🔄 Updating the Site

### Via Git Push

```bash
# Make changes to code
git add .
git commit -m "Update demo"
git push

# Netlify automatically rebuilds (if continuous deployment enabled)
```

### Via Netlify CLI

```bash
# Build and deploy in one command
netlify deploy --prod
```

### Via Netlify UI

```
Deploys → Trigger deploy → Deploy site
```

## 🌐 Sharing Your Demo

Once deployed, share with stakeholders:

```
Your Live Demo: https://[your-site-name].netlify.app

Example talking points:
- "See the 99.97% cost reduction in action"
- "Watch the live speed race (41.5s → 2.2s)"
- "Interactive ROI calculator with real LBS data"
```

## 📱 Mobile Testing

Your site is fully responsive. Test on:
- iOS Safari
- Android Chrome
- Tablet devices

All demos work on mobile with touch-friendly controls.

## 🎨 Customization After Deploy

### Update Branding

Edit `src/components/shared/Layout.jsx`:
```jsx
// Change site title
<h1>Your Institution + KG Demo</h1>

// Update colors in tailwind.config.js
primary: { 500: '#YOUR_COLOR' }
```

### Update Data

Edit `src/data/lbsKnowledgeGraph.js`:
```javascript
// Add your institution's data
export const graphStats = {
  totalNodes: YOUR_NODES,
  totalEdges: YOUR_EDGES,
  // ...
}
```

Redeploy after changes: `git push` or `netlify deploy --prod`

## ✅ Deployment Checklist

Before sharing with stakeholders:

- [ ] Site builds successfully
- [ ] All pages load without errors
- [ ] Navigation works
- [ ] Cost Calculator calculates correctly
- [ ] Speed Demon race animation runs
- [ ] Charts render properly
- [ ] Mobile responsive
- [ ] Fast load times (<2s)
- [ ] Custom domain configured (optional)
- [ ] SSL certificate active (automatic on Netlify)

---

**Questions?** Check Netlify docs: [docs.netlify.com](https://docs.netlify.com)

**Your demo is ready to wow stakeholders!** 🚀
