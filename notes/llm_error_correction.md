# LLM-based ASR Error Correction / 基于 LLM 的语音识别纠错

## 中文说明

### 目标

本步骤的目标是在 FunASR/SenseVoice 的 ASR 输出基础上，加入 LLM 后处理模块，测试大语言模型是否能够修正中文语音识别中的明显错误。

LLM 纠错模块只接收 ASR 输出文本，不接收人工标注的 reference。reference 仅用于纠错后的 CER 评测，因此不会产生数据泄漏。

当前流程为：

```text
ASR hypothesis
→ LLM correction
→ corrected hypothesis
→ CER before/after comparison
```

### 使用模型

本实验使用 DeepSeek API 进行 LLM 纠错。脚本通过 OpenAI-compatible API 调用模型。

环境变量示例：

```powershell
$env:LLM_API_KEY="your_api_key"
$env:LLM_BASE_URL="https://api.deepseek.com"
$env:LLM_MODEL="deepseek-chat"
```

### 输入与输出文件

Speed 1.1x 条件下的输入文件：

```text
results/mandarin/asr_results_speed_1_1.csv
```

Speed 1.1x 条件下的输出文件：

```text
results/mandarin/asr_results_speed_1_1_llm_corrected.csv
```

Noise 5dB SNR 条件下的输入文件：

```text
results/mandarin/asr_results_noise_5db.csv
```

Noise 5dB SNR 条件下的输出文件：

```text
results/mandarin/asr_results_noise_5db_llm_corrected.csv
```

### 运行命令

对 speed 1.1x 条件下的 ASR 结果进行纠错：

```powershell
python scripts\llm_correct_asr.py `
  --input results/mandarin/asr_results_speed_1_1.csv `
  --output results/mandarin/asr_results_speed_1_1_llm_corrected.csv `
  --only-errors
```

对 noise 5dB SNR 条件下的 ASR 结果进行纠错：

```powershell
python scripts\llm_correct_asr.py `
  --input results/mandarin/asr_results_noise_5db.csv `
  --output results/mandarin/asr_results_noise_5db_llm_corrected.csv `
  --only-errors
```

### 纠错结果

| Setting       | Sample   | Reference                            | ASR Output                           | LLM-corrected Output                 | CER Before | CER After |
| ------------- | -------- | ------------------------------------ | ------------------------------------ | ------------------------------------ | ---------: | --------: |
| Speed 1.1x    | test_010 | 坚持每天锻炼三十分钟让我感到神清气爽 | 坚持每天锻炼三十分钟让我感到神经气爽 | 坚持每天锻炼三十分钟让我感到神清气爽 |     0.0556 |    0.0000 |
| Noise 5dB SNR | test_008 | 明天记得把你的论文初稿发给我         | 明天记得把你的论文书稿发给我         | 明天记得把你的论文书稿发给我         |     0.0714 |    0.0714 |

### 结果分析

LLM 成功修正了 “神经气爽 → 神清气爽” 这一错误。该错误明显违反中文固定搭配，因此模型能够根据语言习惯进行纠正。

但是，LLM 没有修正 “论文书稿 → 论文初稿”。原因可能是 “论文书稿” 虽然不如 “论文初稿” 自然，但在语义上仍然可以成立，因此模型没有将其判断为明显错误。

这说明 LLM 纠错对明显不自然或违反固定搭配的 ASR 错误较有效；但当错误文本在语义上仍然合理时，LLM 可能会保持保守，不主动修改。

---

## English Version

### Goal

The goal of this step is to add an LLM-based post-correction module on top of FunASR/SenseVoice ASR outputs and evaluate whether a large language model can correct obvious Mandarin ASR errors.

The LLM correction module only takes the ASR hypothesis as input. It does not access the human-annotated reference transcript. The reference is used only for post-hoc CER evaluation, so there is no data leakage.

The current pipeline is:

```text
ASR hypothesis
→ LLM correction
→ corrected hypothesis
→ CER before/after comparison
```

### Model

This experiment uses the DeepSeek API for LLM-based correction through an OpenAI-compatible API interface.

Example environment variables:

```powershell
$env:LLM_API_KEY="your_api_key"
$env:LLM_BASE_URL="https://api.deepseek.com"
$env:LLM_MODEL="deepseek-chat"
```

### Input and Output Files

Input file under the speed 1.1x setting:

```text
results/mandarin/asr_results_speed_1_1.csv
```

Output file under the speed 1.1x setting:

```text
results/mandarin/asr_results_speed_1_1_llm_corrected.csv
```

Input file under the noise 5dB SNR setting:

```text
results/mandarin/asr_results_noise_5db.csv
```

Output file under the noise 5dB SNR setting:

```text
results/mandarin/asr_results_noise_5db_llm_corrected.csv
```

### Commands

Correct ASR results under the speed 1.1x setting:

```powershell
python scripts\llm_correct_asr.py `
  --input results/mandarin/asr_results_speed_1_1.csv `
  --output results/mandarin/asr_results_speed_1_1_llm_corrected.csv `
  --only-errors
```

Correct ASR results under the noise 5dB SNR setting:

```powershell
python scripts\llm_correct_asr.py `
  --input results/mandarin/asr_results_noise_5db.csv `
  --output results/mandarin/asr_results_noise_5db_llm_corrected.csv `
  --only-errors
```

### Results

| Setting       | Sample   | Reference                            | ASR Output                           | LLM-corrected Output                 | CER Before | CER After |
| ------------- | -------- | ------------------------------------ | ------------------------------------ | ------------------------------------ | ---------: | --------: |
| Speed 1.1x    | test_010 | 坚持每天锻炼三十分钟让我感到神清气爽 | 坚持每天锻炼三十分钟让我感到神经气爽 | 坚持每天锻炼三十分钟让我感到神清气爽 |     0.0556 |    0.0000 |
| Noise 5dB SNR | test_008 | 明天记得把你的论文初稿发给我         | 明天记得把你的论文书稿发给我         | 明天记得把你的论文书稿发给我         |     0.0714 |    0.0714 |

### Analysis

The LLM successfully corrected the error “神经气爽 → 神清气爽”, which is an obvious idiomatic error in Mandarin.

However, it failed to correct “论文书稿 → 论文初稿”. This may be because “论文书稿” is still semantically plausible, although less natural than “论文初稿”. As a result, the LLM did not consider it an obvious ASR error.

This suggests that LLM-based ASR correction is useful for obvious idiomatic or semantically unnatural errors, but it may be conservative when the ASR output remains plausible.
