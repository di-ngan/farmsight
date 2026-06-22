---
name: crop-diagnosis
description: |
  Synthesizes NDVI trend and rainfall data against a paddy crop profile to produce
  a plain-language crop stress diagnosis. Use when asked to diagnose, analyze,
  or synthesize satellite and weather evidence for crop health.
  Do NOT use for raw data retrieval or location queries.
version: 1.0.0
allowed-tools: Read
---

## When to use
- NDVI series and rainfall series have already been collected into session state
- The farmer's question is about crop health, stress, or recommended action

## Inputs (from session state)
- `ndvi_result`: JSON with `ndvi_series` (list of {date, ndvi_mean}), `latest_image_date`, `data_recency_days`
- `rainfall_result`: JSON with `rainfall_series`, `total_mm_30d`, `anomaly_indicator`, `warning`
- `season`: "kharif" or "rabi"
- `question`: farmer's free-text question

## Workflow

### Step 1 — Identify growth stage
- Use `season` and assume sowing on season start (Jun 1 for Kharif, Nov 1 for Rabi)
- Compute days-after-sowing (DAS) from today's date
- Match DAS to the stage in `references/ndvi_norms.md`

### Step 2 — Assess NDVI status
- Compare observed `ndvi_mean` (most recent image) to expected range for current stage
- Check trend direction: improving, stable, or declining across the series
- Note data recency — if image is >30 days old, flag uncertainty

### Step 3 — Assess rainfall status
- Use `anomaly_indicator` from rainfall_result:
  - `severe_deficit` → drought stress highly likely
  - `moderate_deficit` → water stress possible
  - `normal` → rainfall adequate
  - `excess` → waterlogging / submergence risk
  - `flood_risk` → extreme excess, root damage likely
- Cross-reference with growth stage's `water_requirement_mm_per_week`

### Step 4 — Cross-reference and diagnose
- Low NDVI + drought → drought stress
- Low NDVI + excess rain → waterlogging-induced root/nutrient uptake failure
- Low NDVI + normal rain → pest/disease or nutrient deficiency (especially N or Zn)
- NDVI below range for stage with no weather explanation → flag for visual inspection
- Assign confidence: high (strong signal in both NDVI and rainfall), medium (one signal unclear), low (imagery stale >30 days or data gaps)

### Step 5 — Produce output
Use the format in `assets/output_template.md` exactly.
