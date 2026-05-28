import argparse
import csv
import json
import re
from pathlib import Path

import requests


def normalize_text(text: str) -> str:
    """
    Normalize Chinese ASR text for CER calculation.
    This removes spaces, punctuation, and SenseVoice special tags.
    """
    if text is None:
        return ""

    # Remove SenseVoice tags such as <|zh|>, <|NEUTRAL|>, etc.
    text = re.sub(r"<\|[^|]*\|>", "", text)

    # Remove whitespace
    text = re.sub(r"\s+", "", text)

    # Remove common Chinese and English punctuation
    text = re.sub(r"[，。！？、；：“”‘’（）《》【】,.!?;:\"'()\[\]{}<>/\\|`~@#$%^&*_+=-]", "", text)

    return text.strip()


def edit_distance(ref: str, hyp: str) -> int:
    """
    Character-level edit distance.
    """
    n, m = len(ref), len(hyp)
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,       # deletion
                dp[i][j - 1] + 1,       # insertion
                dp[i - 1][j - 1] + cost # substitution
            )

    return dp[n][m]


def compute_cer(reference: str, hypothesis: str) -> float:
    ref = normalize_text(reference)
    hyp = normalize_text(hypothesis)

    if len(ref) == 0:
        return 0.0 if len(hyp) == 0 else 1.0

    return edit_distance(ref, hyp) / len(ref)


def transcribe_audio(
    audio_path: Path,
    base_url: str,
    model: str = "sensevoice",
    response_format: str = "verbose_json",
    timeout: int = 300,
) -> dict:
    """
    Call FunASR OpenAI-compatible transcription API.
    """
    url = base_url.rstrip("/") + "/v1/audio/transcriptions"

    with audio_path.open("rb") as f:
        files = {
            "file": (audio_path.name, f, "application/octet-stream")
        }
        data = {
            "model": model,
            "response_format": response_format,
        }

        response = requests.post(
            url,
            files=files,
            data=data,
            timeout=timeout,
        )

    response.raise_for_status()
    return response.json()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="data/test_manifest.csv")
    parser.add_argument("--output", default="results/asr_results_clean.csv")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--model", default="sensevoice")
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    manifest_path = project_root / args.manifest
    output_path = project_root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    with manifest_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for item in reader:
            utt_id = item["utt_id"]
            audio_path = project_root / item["audio_path"]
            reference = item["reference"]

            print(f"[INFO] Processing {utt_id}: {audio_path}")

            try:
                payload = transcribe_audio(
                    audio_path=audio_path,
                    base_url=args.base_url,
                    model=args.model,
                )
                hypothesis = payload.get("text", "")
                cer = compute_cer(reference, hypothesis)

                rows.append({
                    "utt_id": utt_id,
                    "audio_path": item["audio_path"],
                    "reference": reference,
                    "hypothesis": hypothesis,
                    "normalized_reference": normalize_text(reference),
                    "normalized_hypothesis": normalize_text(hypothesis),
                    "cer": f"{cer:.4f}",
                    "status": "success",
                    "raw_json": json.dumps(payload, ensure_ascii=False),
                })

                print(f"[OK] {utt_id} | CER = {cer:.4f}")
                print(f"     REF: {reference}")
                print(f"     HYP: {hypothesis}")

            except Exception as e:
                rows.append({
                    "utt_id": utt_id,
                    "audio_path": item["audio_path"],
                    "reference": reference,
                    "hypothesis": "",
                    "normalized_reference": normalize_text(reference),
                    "normalized_hypothesis": "",
                    "cer": "",
                    "status": f"failed: {e}",
                    "raw_json": "",
                })

                print(f"[ERROR] {utt_id}: {e}")

    fieldnames = [
        "utt_id",
        "audio_path",
        "reference",
        "hypothesis",
        "normalized_reference",
        "normalized_hypothesis",
        "cer",
        "status",
        "raw_json",
    ]

    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    success_rows = [r for r in rows if r["status"] == "success"]
    if success_rows:
        avg_cer = sum(float(r["cer"]) for r in success_rows) / len(success_rows)
        print(f"\n[SUMMARY] {len(success_rows)} samples processed successfully.")
        print(f"[SUMMARY] Average CER = {avg_cer:.4f}")
    else:
        print("\n[SUMMARY] No sample was processed successfully.")

    print(f"[INFO] Results saved to: {output_path}")


if __name__ == "__main__":
    main()
