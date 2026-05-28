import argparse
import csv
import os
import re
from pathlib import Path
from typing import Dict, Iterable, List

import requests


CONSERVATIVE_PROMPT = {
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
}


DEFAULT_PROVIDERS = {
    "deepseek": {
        "api_key_env": "DEEPSEEK_API_KEY",
        "base_url_env": "DEEPSEEK_URL",
        "model_env": "DEEPSEEK_MODEL",
        "default_base_url": "https://api.deepseek.com",
        "default_model": "deepseek-v4-pro",
    },
    "qwen": {
        "api_key_env": "QWEN_API_KEY",
        "base_url_env": "QWEN_URL",
        "model_env": "QWEN_MODEL",
        "default_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "Qwen3.7-Max",
    },
    "kimi": {
        "api_key_env": "KIMI_API_KEY",
        "base_url_env": "KIMI_URL",
        "model_env": "KIMI_MODEL",
        "default_base_url": "https://api.siliconflow.cn/v1",
        "default_model": "Pro/moonshotai/Kimi-K2.6",
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


def safe_filename(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9._-]+", "_", text)
    text = text.strip("._-")
    return text or "model"


def read_input_rows(input_path: Path) -> List[Dict[str, str]]:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with input_path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def resolve_provider_config(provider_name: str) -> Dict[str, str]:
    if provider_name not in DEFAULT_PROVIDERS:
        raise ValueError(
            f"Unknown provider: {provider_name}. "
            f"Available providers: {', '.join(DEFAULT_PROVIDERS)}"
        )

    spec = DEFAULT_PROVIDERS[provider_name]
    api_key = os.getenv(spec["api_key_env"], "")
    base_url = os.getenv(spec["base_url_env"], spec["default_base_url"])
    model = os.getenv(spec["model_env"], spec["default_model"])

    if not api_key:
        raise ValueError(
            f"Missing API key for {provider_name}. "
            f"Please set {spec['api_key_env']}."
        )

    return {
        "provider": provider_name,
        "api_key": api_key,
        "base_url": base_url,
        "model": model,
        "api_key_env": spec["api_key_env"],
        "base_url_env": spec["base_url_env"],
        "model_env": spec["model_env"],
    }


def call_llm(
    hypothesis: str,
    lexicon_text: str,
    provider_config: Dict[str, str],
    timeout: int,
) -> str:
    url = f"{provider_config['base_url'].rstrip('/')}/chat/completions"
    user_prompt = CONSERVATIVE_PROMPT["user_template"].format(
        lexicon_text=lexicon_text,
        hypothesis=hypothesis,
    )

    payload = {
        "model": provider_config["model"],
        "messages": [
            {"role": "system", "content": CONSERVATIVE_PROMPT["system"]},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0,
    }

    headers = {
        "Authorization": f"Bearer {provider_config['api_key']}",
        "Content-Type": "application/json",
    }

    response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()

    data = response.json()
    corrected = data["choices"][0]["message"]["content"]
    return clean_llm_output(corrected)


def write_detail_csv(output_path: Path, rows: Iterable[Dict[str, str]]) -> None:
    fieldnames = [
        "provider",
        "model",
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


def summarize_model(
    provider_config: Dict[str, str],
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
        "provider": provider_config["provider"],
        "model": provider_config["model"],
        "prompt_name": "prompt_b_conservative",
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
        "provider",
        "model",
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


def run_provider(
    provider_config: Dict[str, str],
    input_rows: List[Dict[str, str]],
    lexicon_text: str,
    output_dir: Path,
    timeout: int,
) -> Dict[str, str]:
    detail_rows = []
    provider = provider_config["provider"]
    model = provider_config["model"]

    print(f"[INFO] Provider={provider} | Model={model}")

    for row in input_rows:
        utt_id = row["utt_id"]
        reference = row["reference"]
        hypothesis = row["hypothesis"]
        cer_before = compute_cer(reference, hypothesis)

        print(f"[INFO] {provider} | Correcting {utt_id}")

        try:
            corrected = call_llm(
                hypothesis=hypothesis,
                lexicon_text=lexicon_text,
                provider_config=provider_config,
                timeout=timeout,
            )
            error_message = ""
            status = classify_status(cer_before, compute_cer(reference, corrected))
        except Exception as exc:
            corrected = hypothesis
            error_message = str(exc)
            status = "api_error"
            print(f"[ERROR] {provider} | {utt_id} | {error_message}")

        cer_after = compute_cer(reference, corrected)
        delta_cer = cer_after - cer_before
        changed = normalize_text(hypothesis) != normalize_text(corrected)

        detail_rows.append(
            {
                "provider": provider,
                "model": model,
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

    detail_name = f"{safe_filename(provider)}_{safe_filename(model)}.csv"
    output_path = output_dir / detail_name
    write_detail_csv(output_path, detail_rows)

    print(f"[INFO] Saved detail results: {output_path}")
    return summarize_model(provider_config, detail_rows, output_path)


def parse_providers(raw: str) -> List[str]:
    providers = [item.strip().lower() for item in raw.split(",") if item.strip()]
    if not providers:
        raise ValueError("No providers specified.")
    return providers


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
        default="results/basketball_commentary/model_comparison",
    )
    parser.add_argument(
        "--providers",
        default="deepseek,qwen,kimi",
        help="Comma-separated provider names: deepseek,qwen,kimi",
    )
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    input_path = Path(args.input)
    lexicon_path = Path(args.lexicon)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    input_rows = read_input_rows(input_path)
    if not input_rows:
        raise RuntimeError("No rows found in input CSV.")

    lexicon_text = load_lexicon(lexicon_path)
    provider_names = parse_providers(args.providers)

    summary_rows = []
    for provider_name in provider_names:
        try:
            provider_config = resolve_provider_config(provider_name)
        except Exception as exc:
            print(f"[ERROR] {provider_name} | {exc}")
            continue

        summary_rows.append(
            run_provider(
                provider_config=provider_config,
                input_rows=input_rows,
                lexicon_text=lexicon_text,
                output_dir=output_dir,
                timeout=args.timeout,
            )
        )

    if not summary_rows:
        raise RuntimeError("No provider finished. Please check API environment variables.")

    summary_path = output_dir / "model_comparison_summary.csv"
    write_summary_csv(summary_path, summary_rows)

    print()
    print("[SUMMARY]")
    for row in summary_rows:
        print(
            f"{row['provider']} | {row['model']} | "
            f"before={row['avg_cer_before']} after={row['avg_cer_after']} "
            f"relative_reduction={row['relative_reduction']} "
            f"degraded={row['num_degraded']} exact={row['num_exact']} "
            f"api_error={row['num_api_error']}"
        )
    print(f"[INFO] Summary saved to: {summary_path}")


if __name__ == "__main__":
    main()
