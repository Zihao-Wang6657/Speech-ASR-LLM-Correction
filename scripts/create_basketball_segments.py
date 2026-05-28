import argparse
import csv
import subprocess
from pathlib import Path


def run_command(cmd):
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)


def cut_segment(source_path: Path, start: str, duration: str, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(source_path),
        "-ss",
        start,
        "-t",
        str(duration),
        "-ac",
        "1",
        "-ar",
        "16000",
        str(output_path),
    ]

    run_command(cmd)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--source", required=True, help="Source basketball commentary video/audio file")
    parser.add_argument(
        "--segment-plan",
        default="data/basketball_commentary/manifests/segment_plan.csv",
    )
    parser.add_argument(
        "--output-dir",
        default="data/basketball_commentary/segments",
    )
    parser.add_argument(
        "--manifest-output",
        default="data/basketball_commentary/manifests/basketball_commentary_manifest.csv",
    )

    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    source_path = project_root / args.source
    segment_plan = project_root / args.segment_plan
    output_dir = project_root / args.output_dir
    manifest_output = project_root / args.manifest_output
    manifest_output.parent.mkdir(parents=True, exist_ok=True)

    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    if not segment_plan.exists():
        raise FileNotFoundError(f"Segment plan not found: {segment_plan}")

    manifest_rows = []

    with segment_plan.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            utt_id = row["utt_id"]
            start = row["start"]
            duration = row["duration"]
            reference = row["reference"]

            output_path = output_dir / f"{utt_id}.wav"

            print(f"[INFO] Cutting {utt_id}: start={start}, duration={duration}")

            cut_segment(
                source_path=source_path,
                start=start,
                duration=duration,
                output_path=output_path,
            )

            relative_audio_path = output_path.relative_to(project_root).as_posix()

            manifest_rows.append(
                {
                    "utt_id": utt_id,
                    "audio_path": relative_audio_path,
                    "reference": reference,
                }
            )

            print(f"[OK] Saved to {relative_audio_path}")

    with manifest_output.open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = ["utt_id", "audio_path", "reference"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest_rows)

    print(f"\n[DONE] Manifest saved to: {manifest_output}")


if __name__ == "__main__":
    main()
