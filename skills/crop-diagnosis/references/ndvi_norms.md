# Paddy NDVI Norms by Growth Stage

Reference values for tropical indica paddy (Kerala conditions).
Source: Adapted from IRRI and published remote-sensing studies on South Asian paddy.

## Kharif Season (Jun–Oct sowing)

| Stage | DAS Range | Expected NDVI | Notes |
|---|---|---|---|
| Nursery | 0–21 | 0.10–0.35 | Low canopy cover; bare soil mixed in |
| Transplanting / Establishment | 21–35 | 0.20–0.45 | Sparse canopy post-transplant; normal dip |
| Tillering | 35–65 | 0.40–0.75 | Rapid canopy expansion; peak growth phase |
| Panicle Initiation | 65–85 | 0.55–0.80 | Dense canopy; highest NDVI period |
| Heading / Flowering | 85–100 | 0.50–0.78 | Slight decline as flag leaf senescence begins |
| Grain Filling | 100–115 | 0.35–0.65 | Steady decline; grains accumulating starch |
| Ripening | 115–130 | 0.15–0.45 | Rapid senescence; yellowing normal |

## Rabi Season (Nov–Mar sowing)

| Stage | DAS Range | Expected NDVI | Notes |
|---|---|---|---|
| Nursery | 0–21 | 0.10–0.35 | Same as Kharif |
| Transplanting / Establishment | 21–35 | 0.20–0.45 | Same as Kharif |
| Tillering | 35–65 | 0.40–0.72 | Slightly lower ceiling than Kharif (cooler, less radiation) |
| Panicle Initiation | 65–85 | 0.55–0.78 | Peak |
| Heading / Flowering | 85–100 | 0.48–0.75 | |
| Grain Filling | 100–115 | 0.32–0.62 | |
| Ripening | 115–125 | 0.12–0.42 | Faster maturation in drier Rabi conditions |

## Interpretation Rules

- **NDVI < lower bound for stage:** Likely stress — drought, waterlogging, pest, disease, or nutrient deficiency
- **NDVI > upper bound for stage:** Possible over-fertilization (N), late variety, or weed competition
- **NDVI declining faster than expected:** Flag for blast disease, brown planthopper, or zinc deficiency
- **Low NDVI at Tillering with adequate rainfall:** Strongly suggests nutrient deficiency (N/Zn) or transplant shock
- **Very low NDVI (< 0.2) at any vegetative stage:** Emergency — possible crop failure, field flooding, or total pest damage

## Cloud Cover Caveats
- Palakkad is in monsoon shadow but still receives ~1700mm/year. Cloud-free Sentinel-2 images may be sparse Jun–Sep.
- If latest image is >30 days old, NDVI assessment carries low confidence — note this explicitly in diagnosis.
- NDVI from images with 15–20% cloud cover may be slightly depressed vs. clear-sky values — adjust interpretation accordingly.
