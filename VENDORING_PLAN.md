# CDN Vendorizing Plan - jaime-cuevas-cv

## Overview

This document outlines the strategy to vendor external CDN dependencies for offline resilience and improved performance.

## Current Dependencies

### High Priority (Easy to Vendor)
1. **D3.js v7** - Knowledge graph visualization
   - URL: https://d3js.org/d3.v7.min.js
   - Size: ~250 KB minified
   - License: ISC
   - Status: Can be easily vendorized

2. **Leaflet 1.9.4** - Geographic map visualization
   - URLs: https://unpkg.com/leaflet@1.9.4/dist/{leaflet.min.js, leaflet.min.css}
   - Assets: Marker images (PNG files)
   - Size: ~150 KB JS + 25 KB CSS + images
   - License: BSD-2-Clause
   - Status: Can be easily vendorized (with image assets)

### Medium Priority (Requires Build Setup)
3. **Tailwind CSS (JIT mode)**
   - URL: https://cdn.tailwindcss.com
   - Size: ~60 KB
   - License: MIT
   - Status: ⚠️ Requires PostCSS build process to pre-compile
   - Recommendation: Keep as CDN for now OR migrate to pre-built Tailwind

4. **Google Fonts**
   - Recommendation: Use system fonts or download WOFF2 files

## Phase 1: Quick Wins (Recommended)

### Steps

1. **Download Dependencies** (Run on your local machine with internet)
   ```bash
   bash scripts/vendor-dependencies.sh
   ```
   
   This will create:
   ```
   lib/
   ├── d3/
   │   └── d3.v7.min.js
   └── leaflet/
       ├── leaflet.min.js
       ├── leaflet.min.css
       └── images/
           ├── marker-icon.png
           ├── marker-icon-2x.png
           └── marker-shadow.png
   ```

2. **Update HTML References** in `index.html`
   
   Replace:
   ```html
   <script src="https://d3js.org/d3.v7.min.js"></script>
   <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
   <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
   ```
   
   With:
   ```html
   <script src="lib/d3/d3.v7.min.js"></script>
   <link rel="stylesheet" href="lib/leaflet/leaflet.min.css">
   <script src="lib/leaflet/leaflet.min.js"></script>
   ```

3. **Update Leaflet CSS Image Paths**
   
   The Leaflet CSS references marker images with relative paths. Update the CSS file:
   ```css
   .leaflet-marker-icon { background-image: url('images/marker-icon.png'); }
   .leaflet-marker-shadow { background-image: url('images/marker-shadow.png'); }
   .leaflet-marker-icon.leaflet-marker-icon-2x { background-image: url('images/marker-icon-2x.png'); }
   ```

4. **Test Visualizations**
   - Open `dist/index.html` in browser
   - Verify knowledge graph loads (D3 force-directed)
   - Verify map loads with markers (Leaflet)
   - Test offline mode (disable network in DevTools)

5. **Commit Changes**
   ```bash
   git add lib/ VENDORING_PLAN.md scripts/vendor-dependencies.sh
   git commit -m "feat(deps): Vendor D3.js and Leaflet for offline resilience"
   ```

## Phase 2: CSS Framework (Optional)

### Options for Tailwind CSS

**Option A: Keep as CDN** (Simplest)
- No changes needed
- Requires internet connection
- Minimal additional work

**Option B: Pre-compile Tailwind**
- Requires: Node.js, npm, PostCSS
- Create `tailwind.config.js` and `postcss.config.js`
- Run: `npx tailwindcss -i input.css -o dist/tailwind.min.css`
- Update HTML to use pre-compiled CSS
- Benefits: Offline support, smaller footprint
- Effort: ~1-2 hours

**Option C: Replace with Simpler Framework**
- Alternative: PicoCSS, Simple.css, etc.
- Benefits: Smaller, no build required
- Tradeoff: Limited customization

**Recommendation**: Stick with Option A for now. Upgrade to Option B if offline-first becomes priority.

## Phase 3: Long-term (Future)

1. **Build Process Setup**
   - Add webpack/vite for CSS compilation
   - Minify and bundle static assets
   - Create .gitignore for build outputs

2. **Service Worker for Offline**
   - Cache all vendored dependencies
   - Cache generated data files
   - Enable full offline mode

3. **Performance Optimization**
   - Lazy-load D3 and Leaflet only when needed
   - Use code splitting for different visualizations

## Benefits Summary

### Phase 1 Benefits
- ✅ Offline graph visualization (D3.js)
- ✅ Offline map visualization (Leaflet)
- ✅ Reduced external CDN dependency
- ✅ Improved privacy (no external tracking)
- ✅ Faster load times (local files)
- ✅ No breaking changes to existing code

### Phase 1 Costs
- ~450 KB added to repository size
- ~30-45 minutes implementation time
- Maintenance of library versions

### Phase 1 Compatibility
- ✅ Works with existing index.html
- ✅ No changes to data pipeline
- ✅ No changes to visualization logic
- ✅ Fully backward compatible

## Implementation Checklist

- [ ] Download dependencies using `vendor-dependencies.sh`
- [ ] Update `<script>` and `<link>` tags in `index.html`
- [ ] Update Leaflet CSS image paths
- [ ] Test graph visualization in browser
- [ ] Test map visualization in browser
- [ ] Test offline mode (disable network)
- [ ] Commit and push changes
- [ ] Create PR for review
- [ ] Merge to main branch

## References

- [D3.js v7 Documentation](https://github.com/d3/d3/wiki)
- [Leaflet 1.9.4 Documentation](https://leafletjs.com/)
- [Tailwind CSS JIT Mode](https://v2.tailwindcss.com/docs/just-in-time-mode)
- [Web Performance Best Practices](https://web.dev/performance/)

## Notes

- The `scripts/vendor-dependencies.sh` script must be run locally (not in remote session due to proxy restrictions)
- All downloaded files are open-source with compatible licenses (ISC, BSD-2-Clause)
- Repository size will increase by ~450 KB, which is acceptable for GitHub LFS limits
- No changes to CI/CD pipeline required

---

**Last Updated**: 2026-09-05  
**Status**: Ready for implementation  
**Priority**: High (Phase 1), Medium (Phases 2-3)
