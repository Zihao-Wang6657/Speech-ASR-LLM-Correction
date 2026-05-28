# Batch ASR Evaluation / 批量 ASR 评测

## 中文说明

### 目标

本步骤的目标是将 FunASR/SenseVoice 的语音识别过程从 Gradio 页面中的手动测试，转为脚本化、可复现的批量评测流程。

当前流程为：

```text
data/mandarin/manifests/test_manifest.csv
→ scripts/evaluate_asr.py
→ FunASR API
→ ASR output
→ CER calculation
→ results/mandarin/asr_results_clean.csv
```

### 项目路径

项目根目录：

```text
D:\Github_repo\Speech-Project
```

评测脚本：

```text
scripts/evaluate_asr.py
```

测试集索引文件：

```text
data/mandarin/manifests/test_manifest.csv
```

输出结果文件：

```text
results/mandarin/asr_results_clean.csv
```

### 使用的本地 API

评测脚本调用本地 FunASR OpenAI-compatible API：

```text
http://localhost:8000/v1/audio/transcriptions
```

在运行评测脚本之前，需要先启动 FunASR 后端服务：

```powershell
conda activate funasr
cd D:\Github_repo\Speech-Project\FunASR\examples\openai_api
python server.py --model sensevoice --device cpu --port 8000
```

### 批量评测命令

在另一个 PowerShell 窗口中运行：

```powershell
conda activate funasr
cd D:\Github_repo\Speech-Project

python scripts\evaluate_asr.py `
  --manifest data/mandarin/manifests/test_manifest.csv `
  --output results/mandarin/asr_results_clean.csv
```

### 测试集

当前普通话自录测试集包含 11 条中文短语音，文件存放在：

```text
data/mandarin/raw_audio/
```

测试集索引文件为：

```text
data/mandarin/manifests/test_manifest.csv
```

其中每一行包含：

```text
utt_id, audio_path, reference
```

分别表示样本编号、音频路径和人工标注的参考文本。

### 评测指标

本阶段使用 Character Error Rate, CER 作为主要评测指标：

```text
CER = (S + D + I) / N
```

其中：

- `S` 表示替换错误数；
- `D` 表示删除错误数；
- `I` 表示插入错误数；
- `N` 表示参考文本的字符数。

### 当前结果

当前 11 条 clean speech 测试样本均被正确识别，平均 CER 为 0.0000。

| Setting      | Number of Samples | Average CER |
| ------------ | ----------------: | ----------: |
| Clean speech |                11 |      0.0000 |

### 结果说明

该结果说明：

1. `data/mandarin/manifests/test_manifest.csv` 可以被脚本正确读取；
2. 本地 FunASR API 可以被脚本成功调用；
3. ASR 输出可以被正确保存到 `results/mandarin/asr_results_clean.csv`；
4. CER 计算流程可以正常运行；
5. 当前 clean speech 测试集较简单，FunASR/SenseVoice 能够完全正确识别。

因此，当前阶段已经完成了基础的 clean speech ASR 批量评测。后续实验进一步构造了语速扰动和噪声扰动语音，以测试模型鲁棒性。

---

## English Version

### Goal

The goal of this step is to convert the FunASR/SenseVoice recognition process from manual Gradio testing into a script-based and reproducible batch evaluation pipeline.

The current pipeline is:

```text
data/mandarin/manifests/test_manifest.csv
→ scripts/evaluate_asr.py
→ FunASR API
→ ASR output
→ CER calculation
→ results/mandarin/asr_results_clean.csv
```

### Project Path

Project root:

```text
D:\Github_repo\Speech-Project
```

Evaluation script:

```text
scripts/evaluate_asr.py
```

Test manifest:

```text
data/mandarin/manifests/test_manifest.csv
```

Output file:

```text
results/mandarin/asr_results_clean.csv
```

### Local API

The evaluation script calls the local FunASR OpenAI-compatible API:

```text
http://localhost:8000/v1/audio/transcriptions
```

Before running the evaluation script, the FunASR backend server should be started:

```powershell
conda activate funasr
cd D:\Github_repo\Speech-Project\FunASR\examples\openai_api
python server.py --model sensevoice --device cpu --port 8000
```

### Batch Evaluation Command

Run the following command in another PowerShell window:

```powershell
conda activate funasr
cd D:\Github_repo\Speech-Project

python scripts\evaluate_asr.py `
  --manifest data/mandarin/manifests/test_manifest.csv `
  --output results/mandarin/asr_results_clean.csv
```

### Test Set

The current self-recorded Mandarin test set contains 11 short utterances. The audio files are stored in:

```text
data/mandarin/raw_audio/
```

The test set is organized by:

```text
data/mandarin/manifests/test_manifest.csv
```

Each row contains:

```text
utt_id, audio_path, reference
```

which correspond to the sample ID, audio path, and manually annotated reference text.

### Evaluation Metric

The main evaluation metric is Character Error Rate, CER:

```text
CER = (S + D + I) / N
```

where:

- `S` is the number of substitutions;
- `D` is the number of deletions;
- `I` is the number of insertions;
- `N` is the number of characters in the reference text.

### Current Result

All 11 clean speech samples were correctly recognized. The average CER is 0.0000.

| Setting      | Number of Samples | Average CER |
| ------------ | ----------------: | ----------: |
| Clean speech |                11 |      0.0000 |

### Summary

This result verifies that:

1. `data/mandarin/manifests/test_manifest.csv` can be correctly loaded by the evaluation script;
2. the local FunASR API can be successfully called;
3. ASR outputs can be saved to `results/mandarin/asr_results_clean.csv`;
4. CER calculation works correctly;
5. the current clean speech test set is relatively simple, and FunASR/SenseVoice can recognize it accurately.

Therefore, the basic clean speech batch ASR evaluation stage is complete. The following experiments construct more challenging audio inputs, such as speed-perturbed and noisy speech, to evaluate ASR robustness.
