import argparse
import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from ml import config


DEFAULT_METRICS = ("accuracy", "f1_weighted", "f1_macro")


def load_json(path: Path) -> Dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc


def parse_metric_names(raw_metrics: Iterable[str]) -> List[str]:
    metrics: List[str] = []
    for raw_metric in raw_metrics:
        for metric in raw_metric.split(","):
            cleaned = metric.strip()
            if cleaned and cleaned not in metrics:
                metrics.append(cleaned)
    if not metrics:
        raise ValueError("No metrics provided.")
    return metrics


def parse_threshold_overrides(raw_thresholds: Iterable[str]) -> Dict[str, float]:
    thresholds: Dict[str, float] = {}
    for raw in raw_thresholds:
        for item in raw.split(","):
            cleaned = item.strip()
            if not cleaned:
                continue
            if "=" not in cleaned:
                raise ValueError(
                    f"Invalid threshold format '{cleaned}'. Use METRIC=VALUE."
                )
            metric, value = cleaned.split("=", 1)
            metric = metric.strip()
            if not metric:
                raise ValueError(f"Invalid metric name in threshold '{cleaned}'.")
            try:
                parsed_value = float(value.strip())
            except ValueError as exc:
                raise ValueError(
                    f"Invalid threshold value in '{cleaned}'. Expected a float."
                ) from exc
            if parsed_value < 0:
                raise ValueError(
                    f"Threshold for '{metric}' must be >= 0, got {parsed_value}."
                )
            thresholds[metric] = parsed_value
    return thresholds


def extract_metric(payload: Dict[str, object], metric_name: str) -> float:
    if metric_name not in payload:
        raise KeyError(metric_name)
    value = payload[metric_name]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(
            f"Metric '{metric_name}' must be numeric in metrics payload, got {type(value).__name__}."
        )
    if not math.isfinite(float(value)):
        raise ValueError(f"Metric '{metric_name}' must be finite, got {value}.")
    return float(value)


def compare_metrics(
    baseline_payload: Dict[str, object],
    current_payload: Dict[str, object],
    metrics: List[str],
    default_threshold: float,
    threshold_overrides: Dict[str, float],
) -> Tuple[List[Dict[str, float]], List[str]]:
    rows: List[Dict[str, float]] = []
    errors: List[str] = []
    for metric in metrics:
        try:
            baseline_value = extract_metric(baseline_payload, metric)
            current_value = extract_metric(current_payload, metric)
        except (KeyError, ValueError) as exc:
            errors.append(f"{metric}: {exc}")
            continue

        delta = current_value - baseline_value
        drop = max(0.0, baseline_value - current_value)
        threshold = threshold_overrides.get(metric, default_threshold)
        regressed = drop > threshold

        rows.append(
            {
                "metric": metric,
                "baseline": baseline_value,
                "current": current_value,
                "delta": delta,
                "drop": drop,
                "threshold": threshold,
                "regressed": regressed,
            }
        )
    return rows, errors


def print_results(rows: List[Dict[str, float]]) -> None:
    print("Metric Regression Check")
    print("=" * 72)
    print(
        f"{'metric':<18}{'baseline':>10}{'current':>10}{'delta':>10}"
        f"{'drop':>10}{'max_drop':>10}{'status':>12}"
    )
    print("-" * 72)
    for row in rows:
        status = "REGRESSION" if row["regressed"] else "OK"
        print(
            f"{row['metric']:<18}"
            f"{row['baseline']:>10.4f}"
            f"{row['current']:>10.4f}"
            f"{row['delta']:>10.4f}"
            f"{row['drop']:>10.4f}"
            f"{row['threshold']:>10.4f}"
            f"{status:>12}"
        )
    print("-" * 72)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare baseline vs current evaluation metrics and fail when drops "
            "exceed configured thresholds."
        )
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=config.CHECKPOINT_DIR / "baseline_evaluation_metrics.json",
        help=(
            "Path to baseline metrics JSON. "
            "Default: checkpoints/baseline_evaluation_metrics.json"
        ),
    )
    parser.add_argument(
        "--current",
        type=Path,
        default=config.CHECKPOINT_DIR / "evaluation_metrics.json",
        help="Path to current metrics JSON. Default: checkpoints/evaluation_metrics.json",
    )
    parser.add_argument(
        "--metrics",
        nargs="+",
        default=list(DEFAULT_METRICS),
        help=(
            "Metrics to compare. Supports comma-separated values and/or multiple "
            "arguments. Default: accuracy f1_weighted f1_macro"
        ),
    )
    parser.add_argument(
        "--default-threshold",
        type=float,
        default=0.01,
        help="Maximum allowed drop for compared metrics unless overridden (default: 0.01).",
    )
    parser.add_argument(
        "--threshold",
        action="append",
        default=[],
        metavar="METRIC=VALUE",
        help=(
            "Per-metric max drop override, e.g. --threshold accuracy=0.02. "
            "Repeat or pass comma-separated pairs."
        ),
    )
    parser.add_argument(
        "--allow-missing-metrics",
        action="store_true",
        help="Skip missing/invalid metrics instead of failing.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.default_threshold < 0:
        print(f"ERROR: --default-threshold must be >= 0, got {args.default_threshold}")
        return 2

    try:
        metrics = parse_metric_names(args.metrics)
        threshold_overrides = parse_threshold_overrides(args.threshold)
        baseline_payload = load_json(args.baseline)
        current_payload = load_json(args.current)
        rows, errors = compare_metrics(
            baseline_payload=baseline_payload,
            current_payload=current_payload,
            metrics=metrics,
            default_threshold=args.default_threshold,
            threshold_overrides=threshold_overrides,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2

    if errors:
        print("Metric loading issues:")
        for error in errors:
            print(f"  - {error}")
        if not args.allow_missing_metrics:
            return 2

    if not rows:
        print("No comparable metrics found.")
        return 2

    print(f"Baseline: {args.baseline}")
    print(f"Current:  {args.current}")
    print_results(rows)

    regressions = [row for row in rows if row["regressed"]]
    if regressions:
        print(
            f"Detected {len(regressions)} regression(s) exceeding configured threshold(s)."
        )
        return 1

    print("No regressions exceeded configured threshold(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
