import argparse
import csv
import os
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import requests


PROMPTS: Dict[str, Dict[str, str]] = {
    "prompt_a_baseline": {
        "file": "prompt_a_baseline.csv",
        "system": (
            "你是一个中文篮球比赛解说语音识别结果的后处理纠错器。"
            "你的任务是根据篮球语境和给定术语词表，修正 ASR 输出中的明显识别错误。"
            "不要润色，不要改写句子，不要添加原文中没有的信息。"
            "只在非常可能是 ASR 错误时修改。"
            "只输出纠正后的文本，不要解释。"
        ),
        "user_template": """请纠正下面的中文篮球解说 ASR 结果。

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
""",
    },
    "prompt_b_conservative": {
        "file": "prompt_b_conservative.csv",
        "system": (
            "你是一个非常保守的中文篮球解说 ASR 后处理纠错器。"
            "只有当 ASR 输出和篮球词表中的词高度相关、明显音近，或者上下文强烈支持篮球实体/术语时才修改。"
            "不要为了让句子更通顺而改写。"
            "如果不确定，请保持原文。"
            "只输出最终文本，不要解释。"
        ),
        "user_template": """请保守纠正下面的中文篮球解说 ASR 结果。

篮球领域词表：
{lexicon_text}

ASR 输出：
{hypothesis}

要求：
1. 只在有充分依据时修正 ASR 错误。
2. 修改应优先限于明显音近或语境高度匹配的篮球术语、球员名、球队名、比赛阶段表达。
3. 不要为了语言更自然、更通顺而改写。
4. 不要补充 ASR 中没有明确线索的内容。
5. 如果无法判断，请逐字保留 ASR 输出。
6. 只输出纠正后的文本，不要解释。
""",
    },
    "prompt_c_two_stage": {
        "file": "prompt_c_two_stage.csv",
        "system": (
            "你是一个中文篮球解说 ASR 后处理纠错器。"
            "你需要先在内部判断是否有足够依据修改，再输出最终纠正文本。"
            "最终答案只能包含纠正后的文本，不能包含判断过程、解释、编号或前缀。"
        ),
        "user_template": """请对下面的中文篮球解说 ASR 结果进行两阶段纠错。

篮球领域词表：
{lexicon_text}

ASR 输出：
{hypothesis}

内部步骤：
1. 先判断 ASR 输出中是否存在明显识别错误。
2. 再判断每个候选修改是否有足够依据：是否与篮球词表相关、是否音近、是否符合当前篮球解说语境。
3. 只有依据充分时才修改；如果只是让句子更通顺，或者依据不足，请保持原文。

输出要求：
1. 最终只输出纠正后的文本。
2. 不要输出解释、分析、步骤、前缀或引号。
""",
    },
    "prompt_d_few_shot": {
        "file": "prompt_d_few_shot.csv",
        "system": (
            "你是一个中文篮球解说 ASR 后处理纠错器。"
            "你会根据篮球领域词表和少量示例，修正明显 ASR 错误。"
            "只在有明确篮球语境、音近或词表依据时修改。"
            "不要为了通顺而改写。"
            "只输出纠正后的文本，不要解释。"
        ),
        "user_template": """请纠正下面的中文篮球解说 ASR 结果。

篮球领域词表：
{lexicon_text}

正向示例：
ASR: 山东密奥
纠正: 圣安东尼奥

ASR: 七决
纠正: 西决

ASR: 哈滕
纠正: 哈腾

ASR: 湖顶
纠正: 弧顶

警示示例：
不要把“已形队”改成“已经”，因为这只是语言更通顺，不一定是正确篮球实体。
遇到这类情况，只有在明确能对应篮球词表实体或比赛语境时才修改；否则保持原文。

待纠正 ASR 输出：
{hypothesis}

要求：
1. 优先修正球队名、球员名、比赛阶段和篮球术语中的明显音近错误。
2. 不要补充没有 ASR 线索的内容。
3. 不要为了通顺而改写。
4. 只输出纠正后的文本，不要解释。
""",
    },
}


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


def clean_llm_output(text: str) -> str:
    text = text.strip()
    text = text.strip("`")
    text = text.strip()
    text = text.strip("“”\"'「」 ")

    prefixes = [
        "纠正后：",
        "纠正后的文本：",
        "修正后：",
        "最终文本：",
        "输出：",
    ]

    for prefix in prefixes:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()

    return text.strip("“”\"'「」 ")


def call_llm(
    hypothesis: str,
    lexicon_text: str,
    prompt_config: Dict[str, str],
    api_key: str,
    base_url: str,
    model: str,
    timeout: int,
) -> str:
    url = f"{base_url.rstrip('/')}/chat/completions"
    user_prompt = prompt_config["user_template"].format(
        lexicon_text=lexicon_text,
        hypothesis=hypothesis,
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt_config["system"]},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()

    data = response.json()
    corrected = data["choices"][0]["message"]["content"]
    return clean_llm_output(corrected)


def classify_status(cer_before: float, cer_after: float) -> str:
    eps = 1e-12

    if abs(cer_after) <= eps:
        return "exact"
    if cer_after < cer_before - eps:
        return "improved"
    if cer_after > cer_before + eps:
        return "degraded"
    return "unchanged"


def format_float(value: float) -> str:
    return f"{value:.4f}"


def read_input_rows(input_path: Path) -> List[Dict[str, str]]:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with input_path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_detail_csv(output_path: Path, rows: Iterable[Dict[str, str]]) -> None:
    fieldnames = [
        "utt_id",
        "reference",
        "hypothesis",
        "corrected_hypothesis",
        "cer_before",
        "cer_after",
        "delta_cer",
        "changed",
        "status",
        "error_message",
    ]

    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summarize_prompt(
    prompt_name: str,
    detail_rows: List[Dict[str, str]],
    output_file: Path,
) -> Dict[str, str]:
    num_samples = len(detail_rows)
    avg_before = sum(float(row["cer_before"]) for row in detail_rows) / num_samples
    avg_after = sum(float(row["cer_after"]) for row in detail_rows) / num_samples
    relative_reduction = (
        (avg_before - avg_after) / avg_before if avg_before > 0 else 0.0
    )

    return {
        "prompt_name": prompt_name,
        "num_samples": str(num_samples),
        "avg_cer_before": format_float(avg_before),
        "avg_cer_after": format_float(avg_after),
        "relative_reduction": format_float(relative_reduction),
        "num_improved": str(sum(row["status"] == "improved" for row in detail_rows)),
        "num_degraded": str(sum(row["status"] == "degraded" for row in detail_rows)),
        "num_unchanged": str(sum(row["status"] == "unchanged" for row in detail_rows)),
        "num_exact": str(sum(row["status"] == "exact" for row in detail_rows)),
        "num_api_error": str(sum(row["status"] == "api_error" for row in detail_rows)),
        "output_file": str(output_file),
    }


def write_summary_csv(output_path: Path, rows: Iterable[Dict[str, str]]) -> None:
    fieldnames = [
        "prompt_name",
        "num_samples",
        "avg_cer_before",
        "avg_cer_after",
        "relative_reduction",
        "num_improved",
        "num_degraded",
        "num_unchanged",
        "num_exact",
        "num_api_error",
        "output_file",
    ]

    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_prompt(
    prompt_name: str,
    prompt_config: Dict[str, str],
    input_rows: List[Dict[str, str]],
    lexicon_text: str,
    output_dir: Path,
    api_config: Tuple[str, str, str, int],
) -> Dict[str, str]:
    api_key, base_url, model, timeout = api_config
    detail_rows = []

    for row in input_rows:
        utt_id = row["utt_id"]
        reference = row["reference"]
        hypothesis = row["hypothesis"]
        cer_before = compute_cer(reference, hypothesis)

        print(f"[INFO] {prompt_name} | Correcting {utt_id}")

        try:
            corrected = call_llm(
                hypothesis=hypothesis,
                lexicon_text=lexicon_text,
                prompt_config=prompt_config,
                api_key=api_key,
                base_url=base_url,
                model=model,
                timeout=timeout,
            )
            error_message = ""
            status = classify_status(cer_before, compute_cer(reference, corrected))
        except Exception as exc:
            corrected = hypothesis
            error_message = str(exc)
            status = "api_error"
            print(f"[ERROR] {prompt_name} | {utt_id} | {error_message}")

        cer_after = compute_cer(reference, corrected)
        delta_cer = cer_after - cer_before
        changed = normalize_text(hypothesis) != normalize_text(corrected)

        detail_rows.append(
            {
                "utt_id": utt_id,
                "reference": reference,
                "hypothesis": hypothesis,
                "corrected_hypothesis": corrected,
                "cer_before": format_float(cer_before),
                "cer_after": format_float(cer_after),
                "delta_cer": format_float(delta_cer),
                "changed": str(changed),
                "status": status,
                "error_message": error_message,
            }
        )

        print(
            f"[OK] before={cer_before:.4f} after={cer_after:.4f} status={status}"
        )

    output_path = output_dir / prompt_config["file"]
    write_detail_csv(output_path, detail_rows)

    print(f"[INFO] Saved detail results: {output_path}")
    return summarize_prompt(prompt_name, detail_rows, output_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="results/basketball_commentary/asr_results_basketball_commentary_all.csv",
    )
    parser.add_argument(
        "--lexicon",
        default="data/basketball_commentary/manifests/basketball_lexicon.txt",
    )
    parser.add_argument(
        "--output-dir",
        default="results/basketball_commentary/prompt_ablation",
    )
    parser.add_argument("--api-key", default=os.getenv("LLM_API_KEY", ""))
    parser.add_argument(
        "--base-url",
        default=os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
    )
    parser.add_argument("--model", default=os.getenv("LLM_MODEL", "deepseek-chat"))
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    if not args.api_key:
        raise ValueError("Missing API key. Please set LLM_API_KEY.")

    input_path = Path(args.input)
    lexicon_path = Path(args.lexicon)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    input_rows = read_input_rows(input_path)
    if not input_rows:
        raise RuntimeError("No rows found in input CSV.")

    lexicon_text = load_lexicon(lexicon_path)
    api_config = (args.api_key, args.base_url, args.model, args.timeout)

    summary_rows = []
    for prompt_name, prompt_config in PROMPTS.items():
        summary_rows.append(
            run_prompt(
                prompt_name=prompt_name,
                prompt_config=prompt_config,
                input_rows=input_rows,
                lexicon_text=lexicon_text,
                output_dir=output_dir,
                api_config=api_config,
            )
        )

    summary_path = output_dir / "prompt_ablation_summary.csv"
    write_summary_csv(summary_path, summary_rows)

    print()
    print("[SUMMARY]")
    for row in summary_rows:
        print(
            f"{row['prompt_name']} | before={row['avg_cer_before']} "
            f"after={row['avg_cer_after']} "
            f"relative_reduction={row['relative_reduction']} "
            f"degraded={row['num_degraded']} exact={row['num_exact']}"
        )
    print(f"[INFO] Summary saved to: {summary_path}")


if __name__ == "__main__":
    main()
