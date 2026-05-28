import argparse
import csv
import os
import re
import requests
from pathlib import Path


def normalize_text(text: str) -> str:
    if text is None:
        return ""

    text = str(text).strip().lower()
    text = re.sub(r"\s+", "", text)

    punctuation = r"""[，。！？、；：“”‘’（）《》【】,.!?;:"'()\[\]<>]"""
    text = re.sub(punctuation, "", text)

    return text


def edit_distance(a: str, b: str) -> int:
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i

    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost,
            )

    return dp[m][n]


def compute_cer(reference: str, hypothesis: str) -> float:
    ref = normalize_text(reference)
    hyp = normalize_text(hypothesis)

    if len(ref) == 0:
        return 0.0 if len(hyp) == 0 else 1.0

    return edit_distance(ref, hyp) / len(ref)


def load_lexicon(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Lexicon file not found: {path}")

    terms = []
    with path.open("r", encoding="utf-8-sig") as f:
        for line in f:
            term = line.strip()
            if term:
                terms.append(term)

    return "、".join(terms)


def call_llm(hypothesis: str, lexicon_text: str) -> str:
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com").rstrip("/")
    model = os.getenv("LLM_MODEL", "deepseek-chat")

    if not api_key:
        raise RuntimeError("Environment variable LLM_API_KEY is not set.")

    url = f"{base_url}/chat/completions"

    system_prompt = (
        "你是一个中文篮球比赛解说语音识别结果的后处理纠错器。"
        "你的任务是根据篮球语境和给定术语词表，修正 ASR 输出中的明显识别错误。"
        "不要润色，不要改写句子，不要添加原文中没有的信息。"
        "只在非常可能是 ASR 错误时修改。"
        "只输出纠正后的文本，不要解释。"
    )

    user_prompt = f"""请纠正下面的中文篮球解说 ASR 结果。

篮球领域词表：
{lexicon_text}

ASR 输出：
{hypothesis}

要求：
1. 只修正明显的语音识别错误。
2. 优先考虑篮球术语、球员名、球队名、比赛阶段表达。
3. 不要根据想象补充新内容。
4. 不要输出解释。
5. 只输出纠正后的文本。
"""

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    response = requests.post(url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()

    data = response.json()
    corrected = data["choices"][0]["message"]["content"].strip()

    corrected = corrected.strip("`")
    corrected = corrected.strip()
    corrected = corrected.strip("“”\"'")

    return corrected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="results/basketball_commentary/asr_results_basketball_commentary.csv",
    )
    parser.add_argument(
        "--output",
        default="results/basketball_commentary/asr_results_basketball_commentary_llm_corrected.csv",
    )
    parser.add_argument(
        "--lexicon",
        default="data/basketball_commentary/manifests/basketball_lexicon.txt",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    lexicon_path = Path(args.lexicon)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    lexicon_text = load_lexicon(lexicon_path)

    rows = []

    with input_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            utt_id = row["utt_id"]
            reference = row["reference"]
            hypothesis = row["hypothesis"]

            print(f"[INFO] Correcting {utt_id}")

            corrected = call_llm(hypothesis, lexicon_text)

            original_cer = compute_cer(reference, hypothesis)
            corrected_cer = compute_cer(reference, corrected)

            row["cer_before_llm"] = f"{original_cer:.4f}"
            row["llm_corrected_hypothesis"] = corrected
            row["llm_corrected_cer"] = f"{corrected_cer:.4f}"
            row["llm_changed"] = str(normalize_text(hypothesis) != normalize_text(corrected))

            print(f"[OK] {utt_id} | CER before = {original_cer:.4f} | CER after = {corrected_cer:.4f}")
            print(f"     HYP: {hypothesis}")
            print(f"     LLM: {corrected}")

            rows.append(row)

    if len(rows) == 0:
        raise RuntimeError("No rows found in input CSV.")

    fieldnames = list(rows[0].keys())

    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    avg_before = sum(float(row["cer_before_llm"]) for row in rows) / len(rows)
    avg_after = sum(float(row["llm_corrected_cer"]) for row in rows) / len(rows)

    print()
    print(f"[SUMMARY] Average CER before LLM = {avg_before:.4f}")
    print(f"[SUMMARY] Average CER after LLM  = {avg_after:.4f}")
    print(f"[INFO] Results saved to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
