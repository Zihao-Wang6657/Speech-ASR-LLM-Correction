 
import argparse
import csv
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf


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


def convert_to_wav(input_path: Path, output_path: Path, sample_rate: int = 16000):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        str(output_path),
    ]
    run_command(cmd)


def speed_perturb(input_path: Path, output_path: Path, speed: float, sample_rate: int = 16000):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-filter:a",
        f"atempo={speed}",
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        str(output_path),
    ]
    run_command(cmd)


def add_white_noise(
    input_path: Path,
    output_path: Path,
    snr_db: float,
    temp_dir: Path,
    sample_rate: int = 16000,
    seed: int = 42,
):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)

    temp_wav = temp_dir / f"{input_path.stem}_tmp.wav"
    convert_to_wav(input_path, temp_wav, sample_rate=sample_rate)

    audio, sr = sf.read(temp_wav)

    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    rng = np.random.default_rng(seed)
    noise = rng.normal(0, 1, size=audio.shape)

    signal_power = np.mean(audio ** 2)
    noise_power = np.mean(noise ** 2)

    target_noise_power = signal_power / (10 ** (snr_db / 10))
    noise = noise * np.sqrt(target_noise_power / (noise_power + 1e-12))

    noisy_audio = audio + noise
    noisy_audio = np.clip(noisy_audio, -1.0, 1.0)

    sf.write(output_path, noisy_audio, sr)


def load_manifest(manifest_path: Path):
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def save_manifest(rows, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["utt_id", "audio_path", "reference"]

    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--manifest", default="data/test_manifest.csv")
    parser.add_argument("--sample-rate", type=int, default=16000)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    manifest_path = project_root / args.manifest

    rows = load_manifest(manifest_path)

    processed_root = project_root / "data" / "processed_audio"
    manifest_root = project_root / "data" / "manifests"
    temp_dir = project_root / "data" / "tmp"

    variants = {
        "speed_0_9": {"type": "speed", "value": 0.9},
        "speed_1_1": {"type": "speed", "value": 1.1},
        "noise_10db": {"type": "noise", "value": 10.0},
        "noise_5db": {"type": "noise", "value": 5.0},
    }

    for variant_name, config in variants.items():
        print(f"\n[INFO] Creating variant: {variant_name}")

        variant_rows = []

        for idx, item in enumerate(rows):
            utt_id = item["utt_id"]
            input_audio = project_root / item["audio_path"]
            reference = item["reference"]

            output_audio = processed_root / variant_name / f"{utt_id}.wav"

            if config["type"] == "speed":
                speed_perturb(
                    input_path=input_audio,
                    output_path=output_audio,
                    speed=config["value"],
                    sample_rate=args.sample_rate,
                )

            elif config["type"] == "noise":
                add_white_noise(
                    input_path=input_audio,
                    output_path=output_audio,
                    snr_db=config["value"],
                    temp_dir=temp_dir,
                    sample_rate=args.sample_rate,
                    seed=42 + idx,
                )

            relative_output_path = output_audio.relative_to(project_root).as_posix()

            variant_rows.append({
                "utt_id": utt_id,
                "audio_path": relative_output_path,
                "reference": reference,
            })

            print(f"[OK] {utt_id} -> {relative_output_path}")

        output_manifest = manifest_root / f"test_manifest_{variant_name}.csv"
        save_manifest(variant_rows, output_manifest)

        print(f"[INFO] Manifest saved to: {output_manifest}")

    print("\n[DONE] Robustness audio data created.")


if __name__ == "__main__":
    main()