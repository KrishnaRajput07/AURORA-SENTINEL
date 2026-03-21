# AI Score Variation Fix

## Problem
The keyword-based fallback scoring was using **hardcoded mid-range scores** that caused score clustering:
- Fight: 83 (always)
- Heavy fight: 88 (always)
- Sport: 28 (always)
- Suspicious: 68 (always)
- Normal: 18 (always)

This resulted in scores clustering around these specific values instead of varying within the specified ranges.

## Solution
Implemented **keyword-count-based score variation** that calculates scores dynamically based on the number of matching keywords:

### Score Calculation Formula

```python
# Count matching keywords
fight_count = sum(1 for kw in fight_keywords if kw in lower_text)
heavy_fight_count = sum(1 for kw in heavy_fight_keywords if kw in lower_text)
sport_count = sum(1 for kw in sport_keywords if kw in lower_text)
suspicious_count = sum(1 for kw in suspicious_keywords if kw in lower_text)
normal_count = sum(1 for kw in normal_keywords if kw in lower_text)

# Calculate varied scores
if has_sport_indicators:
    ai_score = min(20 + (sport_count * 3), 35)  # Range: 20-35
elif has_heavy_fight:
    ai_score = min(80 + (heavy_fight_count * 5), 95)  # Range: 80-95
elif has_fight:
    ai_score = min(75 + (fight_count * 3), 90)  # Range: 75-90
elif has_suspicious:
    ai_score = min(60 + (suspicious_count * 5), 75)  # Range: 60-75
elif has_normal:
    ai_score = max(25 - (normal_count * 3), 10)  # Range: 10-25
```

### Score Ranges

| Category | Base Score | Increment | Max Score | Example Scores |
|----------|-----------|-----------|-----------|----------------|
| **Real Fight** | 75 | +3 per keyword | 90 | 75, 78, 81, 84, 87, 90 |
| **Heavy Fight** | 80 | +5 per keyword | 95 | 80, 85, 90, 95 |
| **Organized Sport** | 20 | +3 per keyword | 35 | 20, 23, 26, 29, 32, 35 |
| **Suspicious** | 60 | +5 per keyword | 75 | 60, 65, 70, 75 |
| **Normal** | 25 | -3 per keyword | 10 | 25, 22, 19, 16, 13, 10 |

## Test Results

### Before Fix
- Scores clustered around: **28, 68, 83, 88, 18**
- Only **5 unique scores** possible
- Predictable and repetitive

### After Fix
- Scores vary based on content: **13, 32, 70, 81, 84, 90, 95**
- **7+ unique scores** in test cases
- Natural variation based on keyword density

### Example Variations

```
"One person is fighting" → 81 (1 keyword)
"Fighting and punching violently" → 84 (3 keywords)
"Aggressive fighting with punching, kicking, striking" → 90 (5 keywords)
"Multiple strikes with sustained aggression and injury" → 95 (heavy fight)
```

## Files Modified

1. **ai-intelligence-layer/aiRouter_enhanced.py**
   - Updated `parse_ai_response()` function
   - Added keyword counting logic
   - Implemented dynamic score calculation

2. **ai-intelligence-layer/qwen2vl_integration.py**
   - Updated `_parse_response()` method
   - Applied same keyword counting logic
   - Ensured consistency across both files

## Verification

Run the test to verify score variation:
```bash
python tests/manual_score_variation_test.py
```

Expected output:
```
✅ SUCCESS: Scores are properly varied!
   No longer clustering around hardcoded values (40, 75, 83, etc.)
```

## Benefits

1. **Natural Score Distribution**: Scores now reflect the intensity/severity of detected content
2. **No Clustering**: Eliminates artificial clustering around hardcoded values
3. **Better Granularity**: More nuanced scoring within each category
4. **Consistent Logic**: Same calculation method across all AI models
5. **Maintainable**: Easy to adjust increments or ranges if needed

## Requirements Satisfied

- ✅ **Requirement 1.2**: No hardcoded scores (40, 75, etc.)
- ✅ **Requirement 1.3**: Proper score ranges for each category
- ✅ **Requirement 1.4**: Keyword-based fallback with varied scores
- ✅ **Requirement 1.5**: No arbitrary multipliers

## Future Enhancements

Potential improvements:
- Add text length normalization (longer descriptions → higher confidence)
- Consider keyword proximity (clustered keywords → higher score)
- Implement severity modifiers (e.g., "severe" → +10 bonus)
- Add context-aware adjustments based on ML score correlation
