# Evaluation Caching & Resumable Runs

## How It Works

When you run `python3 run_eval.py`, results are automatically cached to `results/eval_cache.json` and `results/baseline2_cache.json`.

**If the run crashes midway (e.g., API timeout, network error):**
- Completed items are saved in cache
- Next run skips already-processed items and resumes from crash point
- Metrics computed from all cached results (old + new)

## Cache Files

| File | Contents |
|------|----------|
| `results/eval_cache.json` | Full Council + Judge results (per sample: threat, agent outputs, judge report, predicted label) |
| `results/baseline2_cache.json` | Baseline 2 results (council without judge) |

Each cache file structure:
```json
{
  "items": {
    "1": { "true_label": "Malware", "predicted_label": "Malware", ... },
    "2": { "true_label": "Phishing", "predicted_label": "Phishing", ... }
  },
  "last_updated": "2026-04-18T10:30:00"
}
```

## Usage

### Start evaluation (will resume if cache exists)
```bash
python3 run_eval.py
```

Output shows cache status:
```
[Cache] eval_cache: 45 items cached
[Cache] baseline2_cache: 45 items cached
```

### Start fresh (clear all caches)
```bash
python3 run_eval.py --clear-cache
```

### Manual cache clear
```bash
rm results/eval_cache.json results/baseline2_cache.json
```

## How Resumption Works

1. Load existing cache from `results/eval_cache.json`
2. Identify which items are already cached
3. Process only NEW items (uncached ones)
4. Save new results to cache immediately (per-item, not batched)
5. After all new items done, compute metrics from entire cache

## What Gets Cached

### Full Council Evaluation
- Input threat description
- Agent A, A₂, B, C, C₂, D outputs + provider info (6 agents)
- Judge final report
- `disagreement_log` — classification conflict (A vs A₂), severity conflict (C vs C₂)
- Predicted threat label

### Baseline 2
- Agent outputs from all 6 agents
- Predicted label (from Agent A primary, index 0)
- True label

## Rejected Samples

If validator rejects a threat (marked as `"status": "rejected"` in cache), it's skipped in metrics computation (same as original behavior).

## Performance

- **First run (50 items, 6 agents, 2 rounds):** ~600 agent calls + 100 judge calls
- **Resume from crash (30 items done, 20 new):** ~240 agent calls + 40 judge calls
- **Resuming complete run:** ~0 API calls (metrics computed from cache)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Item already cached but need to reprocess" | Delete that item from `results/eval_cache.json` manually, or use `--clear-cache` |
| Cache seems corrupted (JSON parse error) | `rm results/eval_cache.json` — cache is auto-recreated on next run |
| Metrics don't match expected | Check `results/eval_cache.json` has all items; use `wc -l` or jq to inspect |
| Old cache items missing `disagreement_log` | `run_eval.py` auto-evicts stale items on startup — they will be re-run automatically |
| Want to force re-run only stale items | Just run `python3 run_eval.py` — stale items are evicted, fresh items are kept |
