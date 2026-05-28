import argparse
import csv
from pathlib import Path


def read_result_file(path: Path):
    rows = []

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    return rows


def summarize_file(setting_name: str, path: Path):
    rows = read_result_file(path)

    success_rows = [
        row for row in rows
        if row.get("status", "") == "success" and row.get("cer", "") != ""
    ]

    num_total = len(rows)
    num_success = len(success_rows)

    if num_success == 0:
        avg_cer = None
        max_cer = None
        min_cer = None
    else:
        cer_values = [float(row["cer"]) for row in success_rows]
        avg_cer = sum(cer_values) / len(cer_values)
        max_cer = max(cer_values)
        min_cer = min(cer_values)

    return {
        "setting": setting_name,
        "num_total": num_total,
        "num_success": num_success,
        "average_cer": "" if avg_cer is None else f"{avg_cer:.4f}",
        "min_cer": "" if min_cer is None else f"{min_cer:.4f}",
        "max_cer": "" if max_cer is None else f"{max_cer:.4f}",
        "result_file": str(path),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--output", default="results/asr_summary.csv")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()

    result_files = {
        "Clean": project_root / "results" / "asr_results_clean.csv",
        "Speed 0.9x": project_root / "results" / "asr_results_speed_0_9.csv",
        "Speed 1.1x": project_root / "results" / "asr_results_speed_1_1.csv",
        "Noise 10dB": project_root / "results" / "asr_results_noise_10db.csv",
        "Noise 5dB": project_root / "results" / "asr_results_noise_5db.csv",
    }

    summary_rows = []

    for setting_name, path in result_files.items():
        if not path.exists():
            print(f"[WARNING] Missing result file: {path}")
            continue

        summary = summarize_file(setting_name, path)
        summary_rows.append(summary)

        print(
            f"[OK] {setting_name}: "
            f"num_success={summary['num_success']}, "
            f"average_cer={summary['average_cer']}"
        )

    output_path = project_root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "setting",
        "num_total",
        "num_success",
        "average_cer",
        "min_cer",
        "max_cer",
        "result_file",
    ]

    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"\n[INFO] Summary saved to: {output_path}")


if __name__ == "__main__":
    main()
