# Robustness Evaluation / 鲁棒性评测

## 中文说明

### 目标

本步骤的目标是在 clean speech 评测之外，进一步测试 FunASR/SenseVoice 在语速变化和噪声扰动下的鲁棒性。

我们构造了四类扰动语音：

```text
speed_0_9
speed_1_1
noise_10db
noise_5db
```

其中：

- `speed_0_9` 表示语音速度变为原来的 0.9 倍；
- `speed_1_1` 表示语音速度变为原来的 1.1 倍；
- `noise_10db` 表示加入 SNR = 10dB 的白噪声；
- `noise_5db` 表示加入 SNR = 5dB 的白噪声。

需要注意的是，这里的 `10dB` 和 `5dB` 指的是 SNR, Signal-to-Noise Ratio，即信噪比。SNR 越高，说明语音信号相对于噪声越强；SNR 越低，说明噪声相对越强。因此，`noise_5db` 的噪声强度高于 `noise_10db`。

### 数据与结果文件

生成的扰动语音文件存放在：

```text
data/mandarin/processed_audio/
```

对应的 manifest 文件存放在：

```text
data/mandarin/manifests/
```

评测结果存放在：

```text
results/mandarin/
```

主要结果文件包括：

```text
results/mandarin/asr_results_clean.csv
results/mandarin/asr_results_speed_0_9.csv
results/mandarin/asr_results_speed_1_1.csv
results/mandarin/asr_results_noise_10db.csv
results/mandarin/asr_results_noise_5db.csv
results/mandarin/asr_summary.csv
```

### 运行命令

运行 speed 0.9x 评测：

```powershell
python scripts\evaluate_asr.py `
  --manifest data/mandarin/manifests/test_manifest_speed_0_9.csv `
  --output results/mandarin/asr_results_speed_0_9.csv
```

运行 speed 1.1x 评测：

```powershell
python scripts\evaluate_asr.py `
  --manifest data/mandarin/manifests/test_manifest_speed_1_1.csv `
  --output results/mandarin/asr_results_speed_1_1.csv
```

运行 noise 10dB SNR 评测：

```powershell
python scripts\evaluate_asr.py `
  --manifest data/mandarin/manifests/test_manifest_noise_10db.csv `
  --output results/mandarin/asr_results_noise_10db.csv
```

运行 noise 5dB SNR 评测：

```powershell
python scripts\evaluate_asr.py `
  --manifest data/mandarin/manifests/test_manifest_noise_5db.csv `
  --output results/mandarin/asr_results_noise_5db.csv
```

### 实验结果

| Setting        | Number of Samples | Average CER | Min CER | Max CER |
| -------------- | ----------------: | ----------: | ------: | ------: |
| Clean          |                11 |      0.0000 |  0.0000 |  0.0000 |
| Speed 0.9x     |                11 |      0.0000 |  0.0000 |  0.0000 |
| Speed 1.1x     |                11 |      0.0051 |  0.0000 |  0.0556 |
| Noise 10dB SNR |                11 |      0.0000 |  0.0000 |  0.0000 |
| Noise 5dB SNR  |                11 |      0.0065 |  0.0000 |  0.0714 |

### 结果分析

在当前 11 条自录中文短语音上，FunASR/SenseVoice 在干净语音、较慢语速和较高信噪比噪声条件下表现稳定，平均 CER 均为 0.0000。

当语速提升到 1.1 倍时，平均 CER 上升到 0.0051。这说明语速加快可能引入少量识别错误。

在噪声扰动实验中，SNR = 10dB 时平均 CER 仍为 0.0000；当 SNR 降低到 5dB 时，即噪声相对更强时，平均 CER 上升到 0.0065。这说明较低信噪比条件会对 ASR 准确率产生一定影响。

不过，由于当前测试集规模较小，且语音内容较短、发音较清晰，因此该结果不能代表模型在真实复杂场景下的完整性能。后续可以进一步加入更多说话人、更长语音、真实背景噪声和更口语化的表达。

### 当前结论

当前实验验证了本项目的鲁棒性评测流程，包括：

1. 自动生成语速扰动和噪声扰动语音；
2. 为不同扰动条件生成 manifest 文件；
3. 批量调用 FunASR API；
4. 计算不同条件下的 CER；
5. 汇总不同实验设置的评测结果。

下一步可以基于出现错误的样本，加入 LLM-based ASR error correction，观察 LLM 后处理是否能够修正扰动条件下的识别错误。

---

## English Version

### Goal

The goal of this step is to evaluate the robustness of FunASR/SenseVoice under speed perturbation and noisy speech conditions, in addition to clean speech evaluation.

We constructed four types of perturbed speech:

```text
speed_0_9
speed_1_1
noise_10db
noise_5db
```

where:

- `speed_0_9` means the speech speed is changed to 0.9x;
- `speed_1_1` means the speech speed is changed to 1.1x;
- `noise_10db` means white noise is added with SNR = 10dB;
- `noise_5db` means white noise is added with SNR = 5dB.

Here, `10dB` and `5dB` refer to SNR, Signal-to-Noise Ratio. A higher SNR means the speech signal is stronger relative to the noise, while a lower SNR means the relative noise level is stronger. Therefore, `noise_5db` is noisier than `noise_10db`.

### Data and Result Files

The generated perturbed audio files are stored in:

```text
data/mandarin/processed_audio/
```

The corresponding manifest files are stored in:

```text
data/mandarin/manifests/
```

The evaluation results are stored in:

```text
results/mandarin/
```

Main result files include:

```text
results/mandarin/asr_results_clean.csv
results/mandarin/asr_results_speed_0_9.csv
results/mandarin/asr_results_speed_1_1.csv
results/mandarin/asr_results_noise_10db.csv
results/mandarin/asr_results_noise_5db.csv
results/mandarin/asr_summary.csv
```

### Commands

Evaluate speed 0.9x:

```powershell
python scripts\evaluate_asr.py `
  --manifest data/mandarin/manifests/test_manifest_speed_0_9.csv `
  --output results/mandarin/asr_results_speed_0_9.csv
```

Evaluate speed 1.1x:

```powershell
python scripts\evaluate_asr.py `
  --manifest data/mandarin/manifests/test_manifest_speed_1_1.csv `
  --output results/mandarin/asr_results_speed_1_1.csv
```

Evaluate noise 10dB SNR:

```powershell
python scripts\evaluate_asr.py `
  --manifest data/mandarin/manifests/test_manifest_noise_10db.csv `
  --output results/mandarin/asr_results_noise_10db.csv
```

Evaluate noise 5dB SNR:

```powershell
python scripts\evaluate_asr.py `
  --manifest data/mandarin/manifests/test_manifest_noise_5db.csv `
  --output results/mandarin/asr_results_noise_5db.csv
```

### Results

| Setting        | Number of Samples | Average CER | Min CER | Max CER |
| -------------- | ----------------: | ----------: | ------: | ------: |
| Clean          |                11 |      0.0000 |  0.0000 |  0.0000 |
| Speed 0.9x     |                11 |      0.0000 |  0.0000 |  0.0000 |
| Speed 1.1x     |                11 |      0.0051 |  0.0000 |  0.0556 |
| Noise 10dB SNR |                11 |      0.0000 |  0.0000 |  0.0000 |
| Noise 5dB SNR  |                11 |      0.0065 |  0.0000 |  0.0714 |

### Analysis

On the current 11 manually recorded Mandarin short utterances, FunASR/SenseVoice performs robustly under clean speech, slower speech, and higher-SNR noise conditions, with an average CER of 0.0000.

When the speech speed is increased to 1.1x, the average CER increases to 0.0051. This suggests that faster speech may introduce a small number of recognition errors.

For noisy speech, the average CER remains 0.0000 under 10dB SNR. When the SNR decreases to 5dB, meaning that the relative noise level becomes stronger, the average CER increases to 0.0065. This indicates that lower-SNR conditions can affect ASR accuracy.

However, the current test set is small, short, and relatively clean. Therefore, the results should not be interpreted as a complete evaluation of the model under real-world conditions. Future work can include more speakers, longer utterances, real background noise, and more spontaneous speech.

### Conclusion

This experiment verifies the robustness evaluation pipeline of this project, including:

1. generating speed-perturbed and noisy audio data;
2. creating manifest files for different settings;
3. calling the FunASR API in batch mode;
4. computing CER under different conditions;
5. summarizing results across different settings.

The next step is to apply LLM-based ASR error correction to the samples with recognition errors and analyze whether LLM post-processing can correct ASR mistakes under perturbed conditions.
