import argparse
import csv
import os
import re
from pathlib import Path

import requests


def normalize_text(text: str) -> str:
    if text is None:
        return ""

    text = re.sub(r"<\|[^|]*\|>", "", text)
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[，。！？、；：“”‘’（）《》【】,.!?;:\"'()\[\]{}<>/\\|`~@#$%^&*_+=-]", "", text)
    return text.strip()


def edit_distance(ref: str, hyp: str) -> int:
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
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost,
            )

    return dp[n][m]


def compute_cer(reference: str, hypothesis: str) -> float:
    ref = normalize_text(reference)
    hyp = normalize_text(hypothesis)

    if len(ref) == 0:
        return 0.0 if len(hyp) == 0 else 1.0

    return edit_distance(ref, hyp) / len(ref)


def build_prompt(asr_text: str) -> str:
    return f"""你是一个中文语音识别纠错助手。

请根据中文语言习惯，修正语音识别结果中的明显错误，尤其是同音词、近音词、固定搭配和语义不自然的错误。

要求：
1. 只修正明显错误；
2. 不要改写句子；
3. 不要扩写句子；
4. 不要添加解释；
5. 不要输出任何前缀，例如“纠正后：”；
6. 只输出纠正后的文本。

语音识别结果：
{asr_text}
"""


def clean_llm_output(text: str) -> str:
    text = text.strip()
    text = text.strip("「」\"'` ")

    prefixes = [
        "纠正后：",
        "纠正后的文本：",
        "修正后：",
        "输出：",
    ]

    for p in prefixes:
        if text.startswith(p):
            text = text[len(p):].strip()

    return text


def llm_correct(
    asr_text: str,
    api_key: str,
    base_url: str,
    model: str,
    timeout: int = 120,
) -> str:
    url = base_url.rstrip("/") + "/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": build_prompt(asr_text),
            }
        ],
        "temperature": 0.0,
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=timeout,
    )

    response.raise_for_status()
    data = response.json()

    corrected = data["choices"][0]["message"]["content"]
    return clean_llm_output(corrected)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input ASR result CSV file")
    parser.add_argument("--output", required=True, help="Output corrected CSV file")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--api-key", default=os.getenv("LLM_API_KEY", ""))
    parser.add_argument("--base-url", default=os.getenv("LLM_BASE_URL", ""))
    parser.add_argument("--model", default=os.getenv("LLM_MODEL", ""))
    parser.add_argument("--only-errors", action="store_true", help="Only correct samples with CER > 0")
    args = parser.parse_args()

    if not args.api_key:
        raise ValueError("Missing API key. Please set LLM_API_KEY or pass --api-key.")
    if not args.base_url:
        raise ValueError("Missing base URL. Please set LLM_BASE_URL or pass --base-url.")
    if not args.model:
        raise ValueError("Missing model name. Please set LLM_MODEL or pass --model.")

    project_root = Path(args.project_root).resolve()
    input_path = project_root / args.input
    output_path = project_root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    with input_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for item in reader:
            utt_id = item["utt_id"]
            reference = item["reference"]
            hypothesis = item["hypothesis"]
            original_cer = float(item["cer"]) if item["cer"] else 0.0

            if args.only_errors and original_cer == 0.0:
                corrected = hypothesis
                corrected_cer = original_cer
                status = "skipped_no_error"
                print(f"[SKIP] {utt_id} | CER = 0.0000")

            else:
                print(f"[INFO] Correcting {utt_id}")
                print(f"     ASR: {hypothesis}")

                try:
                    corrected = llm_correct(
                        asr_text=hypothesis,
                        api_key=args.api_key,
                        base_url=args.base_url,
                        model=args.model,
                    )

                    corrected_cer = compute_cer(reference, corrected)
                    status = "success"

                    print(f"     CORRECTED: {corrected}")
                    print(f"     CER: {original_cer:.4f} -> {corrected_cer:.4f}")

                except Exception as e:
                    corrected = ""
                    corrected_cer = ""
                    status = f"failed: {e}"
                    print(f"[ERROR] {utt_id}: {e}")

            rows.append({
                "utt_id": utt_id,
                "audio_path": item.get("audio_path", ""),
                "reference": reference,
                "hypothesis": hypothesis,
                "corrected_hypothesis": corrected,
                "normalized_reference": normalize_text(reference),
                "normalized_hypothesis": normalize_text(hypothesis),
                "normalized_corrected_hypothesis": normalize_text(corrected),
                "original_cer": f"{original_cer:.4f}",
                "corrected_cer": "" if corrected_cer == "" else f"{corrected_cer:.4f}",
                "status": status,
            })

    fieldnames = [
        "utt_id",
        "audio_path",
        "reference",
        "hypothesis",
        "corrected_hypothesis",
        "normalized_reference",
        "normalized_hypothesis",
        "normalized_corrected_hypothesis",
        "original_cer",
        "corrected_cer",
        "status",
    ]

    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    valid_rows = [
        r for r in rows
        if r["corrected_cer"] != "" and r["status"] in ["success", "skipped_no_error"]
    ]

    if valid_rows:
        avg_original_cer = sum(float(r["original_cer"]) for r in valid_rows) / len(valid_rows)
        avg_corrected_cer = sum(float(r["corrected_cer"]) for r in valid_rows) / len(valid_rows)

        print("\n[SUMMARY]")
        print(f"Number of samples: {len(valid_rows)}")
        print(f"Average original CER:  {avg_original_cer:.4f}")
        print(f"Average corrected CER: {avg_corrected_cer:.4f}")

    print(f"\n[INFO] Corrected results saved to: {output_path}")


if __name__ == "__main__":
    main()