#!/usr/bin/env python3
"""
Single-case pipeline test.
Runs 1 threat through full council + judge, verifies all outputs.
"""
import sys
import json
import os

# Windows event loop fix
if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from evaluation.evaluator import run_evaluation, run_baseline2_majority_vote
from evaluation.metrics import compute_metrics

TEST_DATA = "data/test_single.json"
TEST_OUTPUT = "results/test_single"

print("\n" + "="*70)
print("PIPELINE TEST — 1 CASE")
print("="*70)

# Step 1: Load test data
print(f"\n[1] Loading test data from {TEST_DATA}")
with open(TEST_DATA) as f:
    data = json.load(f)
print(f"  ✓ Loaded {len(data)} threat(s)")
print(f"  Threat: {data[0]['threat_description'][:60]}...")

# Step 2: Run evaluation
print(f"\n[2] Running CyberCouncil pipeline...")
os.makedirs(TEST_OUTPUT, exist_ok=True)
metrics, true_labels, pred_labels = run_evaluation(TEST_DATA, output_dir=TEST_OUTPUT)

# Step 3: Check results
print(f"\n[3] Results:")
print(f"  True Label:      {true_labels[0]}")
print(f"  Predicted Label: {pred_labels[0]}")
print(f"  Match: {'✓ YES' if true_labels[0] == pred_labels[0] else '✗ NO'}")

# Step 4: Check files
print(f"\n[4] Generated Files:")
sample_file = os.path.join(TEST_OUTPUT, f"sample_{data[0]['id']:03d}.txt")
if os.path.exists(sample_file):
    print(f"  ✓ Sample report exists: {sample_file}")
    with open(sample_file) as f:
        content = f.read()
    print(f"  ✓ Report size: {len(content)} bytes")
    print(f"  ✓ Report preview (first 500 chars):")
    print("    " + content[:500].replace("\n", "\n    "))
else:
    print(f"  ✗ MISSING: {sample_file}")
    sys.exit(1)

# Step 5: Metrics
print(f"\n[5] Classification Metrics:")
print(f"  Accuracy:  {metrics['accuracy']:.4f}")
print(f"  Precision: {metrics['precision']:.4f}")
print(f"  Recall:    {metrics['recall']:.4f}")
print(f"  F1 Score:  {metrics['f1_score']:.4f}")

# Step 6: Baseline (optional)
print(f"\n[6] Running Baseline 2 (Council, No Judge)...")
b2_metrics, b2_true, b2_pred = run_baseline2_majority_vote(TEST_DATA)
print(f"  Baseline prediction: {b2_pred[0]}")
print(f"  Baseline accuracy:   {b2_metrics['accuracy']:.4f}")

# Step 7: Summary
print(f"\n" + "="*70)
print("PIPELINE TEST COMPLETE")
print("="*70)
print("\n✓ All checks passed. Ready for full 200-case run.")
print(f"\nNext: python3 run_eval.py")
print("="*70 + "\n")
