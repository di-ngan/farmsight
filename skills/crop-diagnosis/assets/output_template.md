# FarmSight Crop Diagnosis

## Field Summary
- **Location:** {latitude}°N, {longitude}°E
- **Season:** {season} ({season_months})
- **Estimated Growth Stage:** {stage} (~{days_after_sowing} days after sowing)
- **Latest Satellite Image:** {latest_image_date} ({data_recency_days} days ago)

## Satellite Evidence (NDVI)
- **Observed NDVI:** {observed_ndvi} (most recent image)
- **Expected Range for Stage:** {expected_ndvi_min}–{expected_ndvi_max}
- **Status:** {ndvi_status}  ← one of: BELOW EXPECTED / WITHIN EXPECTED / ABOVE EXPECTED
- **Trend:** {ndvi_trend}  ← e.g. "Improving over past 4 images" or "Declining — dropped 0.08 in 3 weeks"

## Weather Evidence (Rainfall)
- **30-day Total:** {total_mm_30d} mm
- **Climatological Normal:** ~{normal_mm_30d} mm for this month
- **Anomaly:** {anomaly_indicator}  ← e.g. SEVERE DEFICIT / NORMAL / EXCESS
- **Detail:** {rainfall_warning}

## Diagnosis
**{primary_diagnosis}**

{explanation_2_3_sentences}

## Confidence
**{confidence}** — {confidence_reason}

## Recommended Action
{action_1_to_3_bullets}

---
*Analysis based on Sentinel-2 NDVI and Open-Meteo historical rainfall. Satellite data is {data_recency_days} days old. On-ground inspection recommended to confirm diagnosis.*
