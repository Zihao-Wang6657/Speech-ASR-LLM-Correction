# 篮球解说 LLM 纠错 Model Comparison 实验

## 1. 实验目标

本实验在同一批篮球解说 ASR 输出上，固定 prompt、固定领域词表、固定 CER 计算方式，只改变 LLM 模型或服务商，比较不同模型在中文篮球解说 ASR 后处理纠错中的表现。

控制变量：

```text
输入 ASR 结果：固定
篮球领域词表：固定
Prompt：固定为 prompt_b_conservative
temperature：固定为 0.0
CER 计算逻辑：与前序实验一致
```

变化变量：

```text
LLM provider / model
```

本实验不会把 API key 写入代码或文档。所有密钥均通过 PowerShell 环境变量传入。

## 2. 固定 Prompt

本实验固定使用 prompt ablation 中稳定性较好的：

```text
prompt_b_conservative
```

选择原因：

1. 在 prompt ablation 中没有 degraded 样本；
2. 平均 CER 从 `0.1322` 降到 `0.0859`；
3. 与 baseline 相比更不容易破坏原本正确的 ASR 输出；
4. 适合用于跨模型比较，减少 prompt 激进程度对结果的干扰。

## 3. 输入与输出

输入 ASR 结果：

```text
results/basketball_commentary/asr_results_basketball_commentary_all.csv
```

篮球领域词表：

```text
data/basketball_commentary/manifests/basketball_lexicon.txt
```

模型对比输出目录：

```text
results/basketball_commentary/model_comparison/
```

脚本：

```text
scripts/llm_correct_basketball_asr_model_comparison.py
```

脚本会为每个 provider/model 输出一个明细 CSV，并生成总表：

```text
results/basketball_commentary/model_comparison/model_comparison_summary.csv
```

## 4. 环境变量

请在 PowerShell 中设置各模型服务的环境变量。不要把 API key 写进脚本、README、notes 或提交记录。

DeepSeek：

```powershell
$env:DEEPSEEK_API_KEY="your_deepseek_api_key"
$env:DEEPSEEK_URL="https://api.deepseek.com"
$env:DEEPSEEK_MODEL="deepseek-v4-pro"
```

Qwen：

```powershell
$env:QWEN_API_KEY="your_qwen_api_key"
$env:QWEN_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
$env:QWEN_MODEL="Qwen3.7-Max"
```

Kimi：

```powershell
$env:KIMI_API_KEY="your_kimi_api_key"
$env:KIMI_URL="https://api.siliconflow.cn/v1"
$env:KIMI_MODEL="Pro/moonshotai/Kimi-K2.6"
```

## 5. 运行命令

在项目根目录运行：

```powershell
cd D:\Github_repo\Speech-Project

python scripts\llm_correct_basketball_asr_model_comparison.py `
  --input results/basketball_commentary/asr_results_basketball_commentary_all.csv `
  --lexicon data/basketball_commentary/manifests/basketball_lexicon.txt `
  --output-dir results/basketball_commentary/model_comparison `
  --providers deepseek,qwen,kimi
```

如果只想先测试某一个 provider：

```powershell
python scripts\llm_correct_basketball_asr_model_comparison.py `
  --input results/basketball_commentary/asr_results_basketball_commentary_all.csv `
  --lexicon data/basketball_commentary/manifests/basketball_lexicon.txt `
  --output-dir results/basketball_commentary/model_comparison `
  --providers deepseek
```

## 6. 输出字段

每个明细 CSV 包含：

| 字段 | 含义 |
| --- | --- |
| provider | 模型服务商，例如 deepseek、qwen、kimi |
| model | 实际调用的模型名 |
| utt_id | 样本编号 |
| reference | 人工参考文本，仅用于事后 CER 计算 |
| hypothesis | 原始 ASR 输出，传给 LLM 的文本 |
| corrected_hypothesis | LLM 纠错后的文本 |
| cer_before | 纠错前 CER |
| cer_after | 纠错后 CER |
| delta_cer | `cer_after - cer_before` |
| changed | 纠错前后归一化文本是否不同 |
| status | exact / improved / degraded / unchanged / api_error |
| error_message | API 失败时的错误信息 |

summary CSV 包含：

| 字段 | 含义 |
| --- | --- |
| provider | 模型服务商 |
| model | 模型名 |
| prompt_name | 固定为 `prompt_b_conservative` |
| num_samples | 样本数 |
| avg_cer_before | 平均纠错前 CER |
| avg_cer_after | 平均纠错后 CER |
| relative_reduction | 相对 CER 下降 |
| num_improved | CER 降低样本数 |
| num_degraded | CER 变差样本数 |
| num_unchanged | CER 不变样本数 |
| num_exact | 纠错后 CER 为 0 的样本数 |
| num_api_error | API 调用失败样本数 |
| output_file | 对应明细 CSV 路径 |

## 7. Summary 表格

本次实验已于 2026-05-28 运行完成，结果来自：

```text
results/basketball_commentary/model_comparison/model_comparison_summary.csv
```

| provider | model | avg_cer_before | avg_cer_after | relative_reduction | num_improved | num_degraded | num_unchanged | num_exact | num_api_error |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| deepseek | deepseek-v4-pro | 0.1322 | 0.0987 | 0.2532 | 2 | 1 | 6 | 2 | 0 |
| qwen | qwen3.7-max | 0.1322 | 0.0765 | 0.4218 | 4 | 0 | 4 | 3 | 0 |
| kimi | Pro/moonshotai/Kimi-K2.6 | 0.1322 | 0.0859 | 0.3506 | 4 | 0 | 4 | 3 | 0 |

注意：Qwen 首次运行时使用了 `Qwen3.7-Max`，11 条样本均返回 404 API error。将模型 ID 改为小写 `qwen3.7-max` 后，API 调用成功，结果保存在：

```text
results/basketball_commentary/model_comparison_qwen_retry/
```

## 8. 关键样本分析

### basketball_006

Reference:

```text
这样的话通过罚球雷霆队在第一节开场还是拿到两分的领先
```

ASR:

```text
这样的话通过罚球已形队在第二节开场还是拿到两分的领先
```

| provider | corrected_hypothesis | CER after | status |
| --- | --- | ---: | --- |
| deepseek | 这样的话通过罚球已形队在第二节开场还是拿到两分的领先 | 0.1154 | unchanged |
| kimi | 这样的话通过罚球已形队在第二节开场还是拿到两分的领先 | 0.1154 | unchanged |
| qwen | 这样的话通过罚球已形队在第二节开场还是拿到两分的领先 | 0.1154 | unchanged |

DeepSeek、Qwen 和 Kimi 都没有把“已形队”改成“已经”，说明固定 conservative prompt 后，三个模型都避免了该样本中过度追求语言通顺的错误纠正。但三者也都没有恢复正确实体 `雷霆队`，也没有修正 `第二节 -> 第一节`，因此 CER 保持不变。

### basketball_008

该样本原始 CER 为 0：

```text
Reference:
一个赌博式的传球没有能够塞过去

ASR:
一个赌博式的传球没有能够塞 过去
```

| provider | corrected_hypothesis | CER after | status |
| --- | --- | ---: | --- |
| deepseek | 一个赌博式传球没有能够塞过去 | 0.0667 | degraded |
| kimi | 一个赌博式的传球没有能够塞过去 | 0.0000 | exact |
| qwen | 一个赌博式的传球没有能够塞过去 | 0.0000 | exact |

DeepSeek 删除了“的”，破坏了原本正确的样本，形成唯一 degraded case。Qwen 和 Kimi 都保持 exact，说明在当前 conservative prompt 下，这两个模型对原本正确文本更稳。

## 9. 结论

本次有效模型比较中，Qwen 表现最好：

1. Qwen 的平均 CER after 最低，为 `0.0765`；
2. Qwen 没有 degraded 样本；
3. Qwen 与 Kimi 的 exact 样本数均为 3；
4. DeepSeek 平均 CER after 为 `0.0987`，仍有一定改善，但存在 1 条 degraded；
5. Qwen 首次失败的原因是模型 ID 大小写不匹配，改为 `qwen3.7-max` 后调用成功。

综合来看，在固定 `prompt_b_conservative` 的条件下，Qwen 是当前三家设置中平均 CER 最低的模型；Kimi 表现也稳定，且同样没有 degraded 样本；DeepSeek 可以作为有效但略激进的对照。
