import argparse
import json
import os

from prism.data.hf_loader import LMSYSLoader
from prism.metrics.evaluation import EvaluationTracker


def run_research_evaluation(num_samples: int = 10000, dataset_name: str = "OpenAssistant/oasst1"):
    print(
        f"--- PRISM Research: Production-style intent evaluation on {num_samples} records "
        f"from {dataset_name} ---"
    )

    loader = LMSYSLoader(dataset_name=dataset_name)
    tracker = EvaluationTracker()
    ds = loader.load(stream=True)

    print("Processing records...")
    for i, example in enumerate(ds):
        if i >= num_samples:
            break
        tracker.process(example)
        if i % 1000 == 0 and i > 0:
            print(f"Processed {i} records...")

    metrics = tracker.finalize()

    print("\n--- Research Results (Production Metrics) ---")
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f"{key}: {value:.4f}")
        else:
            print(f"{key}: {value}")

    output_dir = "research\\outputs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_path = os.path.join(output_dir, "evaluation_metrics.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"\nSaved metrics to {output_path}")
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-samples", type=int, default=10000)
    parser.add_argument("--dataset-name", type=str, default="OpenAssistant/oasst1")
    args = parser.parse_args()
    run_research_evaluation(num_samples=args.num_samples, dataset_name=args.dataset_name)
