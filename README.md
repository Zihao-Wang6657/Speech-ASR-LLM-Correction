# 中文语音识别鲁棒性评测与领域词表增强 LLM 纠错

本项目基于 **FunASR/SenseVoice** 搭建一个轻量级中文语音识别实验流程，主要关注：

- 中文 ASR 批量推理；
- Character Error Rate, CER 评测；
- 语速与噪声扰动下的鲁棒性分析；
- 篮球解说领域语音识别评测；
- 基于 LLM 的 ASR 后处理纠错。

本项目围绕现有语音基础模型构建一个小型评测与错误分析流程。

---

## 项目亮点

1. **普通话自录语音评测**  
   在 11 条自录普通话短句上，FunASR/SenseVoice 在 clean speech 和轻度扰动条件下表现稳定。

2. **篮球解说领域测试集**  
   构建了 11 条篮球比赛解说短语音片段。相比普通话短句，篮球解说包含更快语速、球员名、球队名、篮球术语和轻微重叠语音，更接近真实领域语音场景。

3. **领域词表增强 LLM 纠错**  
   在篮球解说 ASR 输出上，向 LLM 提供篮球领域词表后，平均 CER 从 `0.1322` 降低到 `0.0845`，相对下降约 `36.1%`。

4. **Prompt Ablation 分析**  
   比较 baseline、conservative、two-stage 和 few-shot 四种篮球领域纠错 prompt。baseline 平均 CER 最低，达到 `0.0787`；conservative 和 few-shot 没有 degraded 样本，稳定性更好。

---

## 整体流程

```text
音频输入
→ FunASR / SenseVoice ASR
→ 原始识别文本
→ CER 评测
→ 错误分析
→ LLM-based ASR correction
→ 纠错前后 CER 对比
```

对于篮球解说语音，本项目进一步加入领域词表：

```text
篮球解说 ASR 输出
+ 篮球领域词表
→ LLM 纠错
→ 纠错后文本
→ CER before/after comparison
```

---

## 项目结构

```text
Speech-Project
│
├── README.md
├── .gitignore
│
├── assets
│   └── Gradio_demo
│       └── test_001.png
│
├── data
│   ├── mandarin
│   │   ├── raw_audio
│   │   ├── processed_audio
│   │   │   ├── speed_0_9
│   │   │   ├── speed_1_1
│   │   │   ├── noise_10db
│   │   │   └── noise_5db
│   │   ├── manifests
│   │   │   ├── test_manifest.csv
│   │   │   ├── test_manifest_speed_0_9.csv
│   │   │   ├── test_manifest_speed_1_1.csv
│   │   │   ├── test_manifest_noise_10db.csv
│   │   │   └── test_manifest_noise_5db.csv
│   │   └── tmp
│   │
│   └── basketball_commentary
│       ├── source
│       ├── segments
│       └── manifests
│           ├── segment_plan.csv
│           ├── segment_plan_match_002.csv
│           ├── basketball_commentary_manifest.csv
│           ├── basketball_commentary_manifest_match_002.csv
│           ├── basketball_commentary_manifest_all.csv
│           └── basketball_lexicon.txt
│
├── notes
│   ├── setup_funasr_demo.md
│   ├── batch_asr_evaluation.md
│   ├── robustness_evaluation.md
│   ├── llm_error_correction.md
│   ├── basketball_commentary_evaluation.md
│   ├── basketball_llm_correction.md
│   ├── prompt_ablation_basketball_llm.md
│   └── model_comparison_basketball_llm.md
│
├── results
│   ├── mandarin
│   └── basketball_commentary
│       ├── asr_results_basketball_commentary.csv
│       ├── asr_results_basketball_commentary_match_002.csv
│       ├── asr_results_basketball_commentary_all.csv
│       ├── asr_results_basketball_commentary_all_llm_corrected.csv
│       └── prompt_ablation
│           ├── prompt_a_baseline.csv
│           ├── prompt_b_conservative.csv
│           ├── prompt_c_two_stage.csv
│           ├── prompt_d_few_shot.csv
│           └── prompt_ablation_summary.csv
│       └── model_comparison
│           └── model_comparison_summary.csv
│
└── scripts
    ├── create_robustness_data.py
    ├── evaluate_asr.py
    ├── summarize_asr_results.py
    ├── llm_correct_asr.py
    ├── create_basketball_segments.py
    ├── llm_correct_basketball_asr.py
    ├── llm_correct_basketball_asr_prompt_ablation.py
    └── llm_correct_basketball_asr_model_comparison.py
```

---

## 文件夹说明

| 路径                                    | 说明                                 |
| --------------------------------------- | ------------------------------------ |
| `assets/`                               | README 或报告中使用的截图            |
| `data/mandarin/`                        | 普通话自录语音数据集                 |
| `data/basketball_commentary/source/`    | 篮球解说原始视频或音频               |
| `data/basketball_commentary/segments/`  | 切分后的篮球解说短音频               |
| `data/basketball_commentary/manifests/` | 篮球解说数据索引、切片计划和领域词表 |
| `notes/`                                | 实验记录和分析文档                   |
| `results/mandarin/`                     | 普通话实验结果                       |
| `results/basketball_commentary/`        | 篮球解说实验结果                     |
| `scripts/`                              | 数据处理、ASR 评测和 LLM 纠错脚本    |

---

## 环境配置

创建并激活 conda 环境：

```powershell
conda create -n funasr python=3.10 -y
conda activate funasr
```

安装依赖：

```powershell
pip install funasr fastapi uvicorn python-multipart gradio torch torchaudio requests numpy soundfile
```

在 Windows 上，读取 `.m4a`、`.mp4` 等音频或视频格式需要安装 `ffmpeg`：

```powershell
conda install -c conda-forge ffmpeg -y
```

检查 `ffmpeg` 是否可用：

```powershell
ffmpeg -version
```

---

## 启动 FunASR 后端服务

在第一个 PowerShell 窗口中运行：

```powershell
conda activate funasr
cd D:\Github_repo\Speech-Project\FunASR\examples\openai_api
python server.py --model sensevoice --device cpu --port 8000
```

如果需要运行官方 Gradio demo，可在第二个 PowerShell 窗口中运行：

```powershell
conda activate funasr
cd D:\Github_repo\Speech-Project\FunASR\examples\openai_api
python gradio_app.py --base-url http://localhost:8000
```

---

## 数据集格式

本项目使用 manifest 文件管理测试集。基本格式为：

```csv
utt_id,audio_path,reference
test_001,data/mandarin/raw_audio/test_001.m4a,今天我们测试一下中文语音识别系统
```

其中：

- `utt_id` 表示语音样本编号；
- `audio_path` 表示音频路径；
- `reference` 表示人工转写文本。

---

## 评测指标

本项目主要使用 **Character Error Rate, CER** 作为评测指标：

```text
CER = (S + D + I) / N
```

其中：

- `S` 表示替换错误数；
- `D` 表示删除错误数；
- `I` 表示插入错误数；
- `N` 表示参考文本字符数。

对于中文 ASR，CER 通常比 WER 更适合。

---

## 普通话自录语音实验

### 运行 clean speech 评测

```powershell
cd D:\Github_repo\Speech-Project

python scripts\evaluate_asr.py `
  --manifest data/mandarin/manifests/test_manifest.csv `
  --output results/mandarin/asr_results_clean.csv
```

### 运行语速和噪声扰动评测

```powershell
python scripts\evaluate_asr.py `
  --manifest data/mandarin/manifests/test_manifest_speed_0_9.csv `
  --output results/mandarin/asr_results_speed_0_9.csv
```

```powershell
python scripts\evaluate_asr.py `
  --manifest data/mandarin/manifests/test_manifest_speed_1_1.csv `
  --output results/mandarin/asr_results_speed_1_1.csv
```

```powershell
python scripts\evaluate_asr.py `
  --manifest data/mandarin/manifests/test_manifest_noise_10db.csv `
  --output results/mandarin/asr_results_noise_10db.csv
```

```powershell
python scripts\evaluate_asr.py `
  --manifest data/mandarin/manifests/test_manifest_noise_5db.csv `
  --output results/mandarin/asr_results_noise_5db.csv
```

### 普通话实验结果

| Setting        | Samples | Average CER | Max CER |
| -------------- | ------: | ----------: | ------: |
| Clean          |      11 |      0.0000 |  0.0000 |
| Speed 0.9x     |      11 |      0.0000 |  0.0000 |
| Speed 1.1x     |      11 |      0.0051 |  0.0556 |
| Noise 10dB SNR |      11 |      0.0000 |  0.0000 |
| Noise 5dB SNR  |      11 |      0.0065 |  0.0714 |

这里的 `10dB` 和 `5dB` 指的是 SNR, Signal-to-Noise Ratio，即信噪比。SNR 越低，说明噪声相对越强，因此 `Noise 5dB SNR` 比 `Noise 10dB SNR` 更具挑战性。

---

## 普通话 LLM 纠错结果

在普通话扰动实验中，LLM 可以修正明显违反中文固定搭配的错误，但对语义上仍然合理的错误较保守。

| Setting       | Sample   | ASR Error | LLM Correction | CER Before | CER After |
| ------------- | -------- | --------- | -------------- | ---------: | --------: |
| Speed 1.1x    | test_010 | 神经气爽  | 神清气爽       |     0.0556 |    0.0000 |
| Noise 5dB SNR | test_008 | 论文书稿  | 论文书稿       |     0.0714 |    0.0714 |

---

## 篮球解说语音实验

### 数据构建

篮球解说原始视频或音频放在：

```text
data/basketball_commentary/source/
```

切片计划文件为：

```text
data/basketball_commentary/manifests/segment_plan.csv
data/basketball_commentary/manifests/segment_plan_match_002.csv
```

切片计划格式为：

```csv
utt_id,start,duration,reference
```

运行切片脚本：

```powershell
cd D:\Github_repo\Speech-Project

python scripts\create_basketball_segments.py `
  --source data/basketball_commentary/source/match_001.mp4
```

对于第二段视频：

```powershell
python scripts\create_basketball_segments.py `
  --source data/basketball_commentary/source/match_002.mp4 `
  --segment-plan data/basketball_commentary/manifests/segment_plan_match_002.csv `
  --manifest-output data/basketball_commentary/manifests/basketball_commentary_manifest_match_002.csv
```

合并后的总 manifest 为：

```text
data/basketball_commentary/manifests/basketball_commentary_manifest_all.csv
```

### 运行篮球解说 ASR 评测

```powershell
python scripts\evaluate_asr.py `
  --manifest data/basketball_commentary/manifests/basketball_commentary_manifest_all.csv `
  --output results/basketball_commentary/asr_results_basketball_commentary_all.csv
```

### 篮球解说 ASR 结果

扩展后的篮球解说测试集包含 11 个片段。原始 ASR 结果如下：

| Sample         |    CER | 主要错误类型                   |
| -------------- | -----: | ------------------------------ |
| basketball_001 | 0.1786 | 球队名、地名与比赛阶段识别错误 |
| basketball_002 | 0.1875 | 球员名识别错误                 |
| basketball_003 | 0.1379 | 篮球术语识别错误               |
| basketball_004 | 0.1250 | 篮球术语与功能词识别错误       |
| basketball_005 | 0.3103 | 违例、球员名和封盖术语识别错误 |
| basketball_006 | 0.1154 | 球队名和比赛节次识别错误       |
| basketball_007 | 0.0500 | 球员名和语气词识别错误         |
| basketball_008 | 0.0000 | 原始识别正确                   |
| basketball_009 | 0.2333 | 球员名和漏识别错误             |
| basketball_010 | 0.0909 | 语气词写法差异                 |
| basketball_011 | 0.0256 | 近义词识别差异                 |

平均 CER：

```text
0.1322
```

相比普通话自录短句，篮球解说语音明显更难。主要错误集中在：

- 球队名和地名，例如“圣安东尼奥”“雷霆”；
- 比赛阶段表达，例如“西决”“第一节”；
- 球员名，例如“哈腾”“文班”“卡斯尔”“亚历山大”；
- 篮球术语，例如“协防”“弧顶”“持球人”“封盖”“中距离”；
- 快速语速和轻微重叠语音导致的漏识别。

---

## 篮球领域词表增强 LLM 纠错

### 篮球领域词表

词表文件：

```text
data/basketball_commentary/manifests/basketball_lexicon.txt
```

当前词表包括篮球解说中出现的球队名、球员名、比赛阶段表达和篮球术语，例如：

```text
圣安东尼奥
马刺
西决
雷霆
哈腾
文班
卡森
卡斯尔
福克斯
亚历山大
协防
弧顶
投手
一五挡拆
挡拆
持球人
二十四秒违例
封盖
双塔
防守
篮板
中距离
挑战
```

该词表向 LLM 提供篮球领域先验。LLM 纠错时只接收 ASR 输出和领域词表，不接收完整 reference。reference 仅用于纠错后的 CER 计算。

### 运行 LLM 纠错

设置 API 环境变量：

```powershell
$env:LLM_API_KEY="your_api_key"
$env:LLM_BASE_URL="https://api.deepseek.com"
$env:LLM_MODEL="deepseek-chat"
```

运行纠错脚本：

```powershell
python scripts\llm_correct_basketball_asr.py `
  --input results/basketball_commentary/asr_results_basketball_commentary_all.csv `
  --output results/basketball_commentary/asr_results_basketball_commentary_all_llm_corrected.csv `
  --lexicon data/basketball_commentary/manifests/basketball_lexicon.txt
```

### 篮球 LLM 纠错结果

| Sample         | CER Before LLM | CER After LLM | 结果         |
| -------------- | -------------: | ------------: | ------------ |
| basketball_001 |         0.1786 |        0.0000 | 完全修正     |
| basketball_002 |         0.1875 |        0.0000 | 完全修正     |
| basketball_003 |         0.1379 |        0.1034 | 部分修正     |
| basketball_004 |         0.1250 |        0.1000 | 部分修正     |
| basketball_005 |         0.3103 |        0.1724 | 明显改善     |
| basketball_006 |         0.1154 |        0.1538 | 纠错后变差   |
| basketball_007 |         0.0500 |        0.0500 | 基本无改善   |
| basketball_008 |         0.0000 |        0.0000 | 原始识别正确 |
| basketball_009 |         0.2333 |        0.2333 | 无改善       |
| basketball_010 |         0.0909 |        0.0909 | 无改善       |
| basketball_011 |         0.0256 |        0.0256 | 无改善       |

平均 CER：

```text
Before LLM: 0.1322
After LLM:  0.0845
```

相对下降约：

```text
36.1%
```

---

## 典型案例

### 1. 完全修正：球队名与比赛阶段

```text
ASR:
首先还是助队山东密奥马刺跳到球权来吧七决的第四场来了嗯

LLM:
首先还是主队圣安东尼奥马刺跳到球权来吧西决的第四场来了嗯
```

主要修正：

```text
助队 → 主队
山东密奥 → 圣安东尼奥
七决 → 西决
```

### 2. 部分修正：篮球术语

```text
ASR:
运球往里杀这边前方位置有人哦这球没投对但分出来了湖顶有投手

LLM:
运球往里杀这边前方位置有人哦这球没投对但分出来了弧顶有投手
```

成功修正：

```text
湖顶 → 弧顶
```

但仍未修正：

```text
前方 → 协防
但分出来了 → 再分出来了
```

### 3. 明显改善：球员名和术语

```text
ASR:
阿十瓦为力了嗯本丹今天的第一个分盖最终还是算在了切特的身上

LLM:
阿十瓦为力了文班今天的第一个封盖最终还是算在了切特的身上
```

成功修正：

```text
本丹 → 文班
分盖 → 封盖
```

但未能恢复：

```text
阿十瓦为力了 → 二十四秒违例了
```

### 4. 失败案例：纠错后变差

```text
ASR:
这样的话通过罚球已形队在第二节开场还是拿到两分的领先

LLM:
这样的话通过罚球已经在第二节开场还是拿到两分的领先
```

正确 reference 中应为：

```text
雷霆队
第一节
```

该样本说明，LLM 有时会把错误文本改成语言上更自然的表达，但没有恢复正确的领域实体，导致 CER 反而上升。

---

## 篮球 LLM 纠错 Prompt Ablation

为了进一步分析 prompt 策略对领域 ASR 纠错的影响，本项目新增了 prompt ablation 实验，比较四种提示方式：

| Prompt | 名称 | 设计重点 |
| ------ | ---- | -------- |
| A | baseline | 复用领域词表增强纠错 prompt，优先修正明显篮球实体和术语错误 |
| B | conservative | 只在词表相关、明显音近或上下文证据充分时修改，不为了通顺改写 |
| C | two-stage | 要求模型先内部判断是否需要修改和依据是否充分，再输出最终文本 |
| D | few-shot | 加入成功纠错示例和失败警示，提醒模型不要把“已形队”改成“已经” |

运行命令：

```powershell
python scripts\llm_correct_basketball_asr_prompt_ablation.py `
  --input results/basketball_commentary/asr_results_basketball_commentary_all.csv `
  --lexicon data/basketball_commentary/manifests/basketball_lexicon.txt `
  --output-dir results/basketball_commentary/prompt_ablation
```

Prompt ablation 汇总结果：

| Prompt | Samples | CER Before | CER After | Relative Reduction | Improved | Degraded | Unchanged | Exact |
| ------ | ------: | ---------: | --------: | -----------------: | -------: | -------: | --------: | ----: |
| prompt_a_baseline | 11 | 0.1322 | 0.0787 | 40.51% | 5 | 1 | 3 | 2 |
| prompt_b_conservative | 11 | 0.1322 | 0.0859 | 35.06% | 4 | 0 | 4 | 3 |
| prompt_c_two_stage | 11 | 0.1322 | 0.0923 | 30.16% | 6 | 0 | 4 | 1 |
| prompt_d_few_shot | 11 | 0.1322 | 0.0859 | 35.06% | 4 | 0 | 4 | 3 |

主要发现：

- `prompt_a_baseline` 的平均 CER 最低，从 `0.1322` 降到 `0.0787`；
- `prompt_b_conservative` 和 `prompt_d_few_shot` 没有 degraded 样本，更适合作为稳定纠错策略；
- `basketball_006` 中，四种 prompt 都没有再把“已形队”改成“已经”；baseline 和 two-stage 进一步恢复为“雷霆队”，但仍未修正“第二节 -> 第一节”；
- baseline 唯一 degraded 样本是 `basketball_008`，该样本原始 CER 为 0，但 baseline 删除了“的”，说明较激进的纠错可能破坏原本正确的输出。

详细实验记录见：

```text
notes/prompt_ablation_basketball_llm.md
```

---

## 篮球 LLM 模型对比

在 prompt ablation 之后，本项目加入固定 prompt 下的模型对比实验。该实验固定使用稳定性较好的 `prompt_b_conservative`，比较 DeepSeek、Qwen、Kimi 等模型在同一批篮球解说 ASR 输出上的纠错效果。

脚本：

```text
scripts/llm_correct_basketball_asr_model_comparison.py
```

实验记录：

```text
notes/model_comparison_basketball_llm.md
```

运行前需要在 PowerShell 中设置各 provider 的环境变量。API key 只通过环境变量传入，不写入代码或文档。

```powershell
$env:DEEPSEEK_API_KEY="your_deepseek_api_key"
$env:DEEPSEEK_URL="https://api.deepseek.com"
$env:DEEPSEEK_MODEL="deepseek-v4-pro"

$env:QWEN_API_KEY="your_qwen_api_key"
$env:QWEN_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
$env:QWEN_MODEL="Qwen3.7-Max"

$env:KIMI_API_KEY="your_kimi_api_key"
$env:KIMI_URL="https://api.siliconflow.cn/v1"
$env:KIMI_MODEL="Pro/moonshotai/Kimi-K2.6"
```

运行命令：

```powershell
python scripts\llm_correct_basketball_asr_model_comparison.py `
  --input results/basketball_commentary/asr_results_basketball_commentary_all.csv `
  --lexicon data/basketball_commentary/manifests/basketball_lexicon.txt `
  --output-dir results/basketball_commentary/model_comparison `
  --providers deepseek,qwen,kimi
```

该实验重点比较：

- 平均纠错后 CER；
- degraded samples 数量；
- exact samples 数量；
- `basketball_006` 是否避免过度纠错；
- `basketball_008` 这种原本正确样本是否被破坏。

当前模型对比结果：

| Provider | Model | CER Before | CER After | Relative Reduction | Improved | Degraded | Exact | API Error |
| -------- | ----- | ---------: | --------: | -----------------: | -------: | -------: | ----: | --------: |
| DeepSeek | deepseek-v4-pro | 0.1322 | 0.0987 | 25.32% | 2 | 1 | 2 | 0 |
| Qwen | qwen3.7-max | 0.1322 | 0.0765 | 42.18% | 4 | 0 | 3 | 0 |
| Kimi | Pro/moonshotai/Kimi-K2.6 | 0.1322 | 0.0859 | 35.06% | 4 | 0 | 3 | 0 |

本轮有效比较中，Qwen 的平均 CER after 最低且没有 degraded 样本，是当前固定 conservative prompt 下表现最好的模型候选。Kimi 同样没有 degraded，稳定性也较好。DeepSeek 也有改善，但会破坏 `basketball_008` 这类原本正确样本。Qwen 首次使用 `Qwen3.7-Max` 时返回 404，将模型 ID 改为 `qwen3.7-max` 后调用成功。

---

## 结论

本项目完成了一个轻量级中文 ASR 评测与后处理流程。

实验结果表明：

1. FunASR/SenseVoice 在普通话自录短句上表现稳定；
2. 篮球解说语音明显更具挑战性，扩展后 11 条样本的平均 CER 为 `0.1322`；
3. 错误主要集中在球员名、球队名、篮球术语、比赛阶段表达和快节奏语音中；
4. 加入篮球领域词表后，LLM 纠错将平均 CER 降低到 `0.0845`，相对下降约 `36.1%`；
5. Prompt ablation 进一步将最佳平均 CER 降低到 `0.0787`，同时显示 conservative / few-shot prompt 可以减少 degraded samples；
6. 在固定 conservative prompt 的模型对比中，Qwen 当前表现最好，平均 CER after 为 `0.0765`，且没有 degraded 样本；
7. LLM 后处理适合作为 ASR 系统之后的轻量级纠错模块，但在严重识别错误、漏识别或语义模糊时存在无效纠错和过度纠错风险。

---

## 局限性

当前项目仍然是一个小型实验，存在以下局限：

- 普通话测试集规模较小；
- 篮球解说测试集目前只有 11 个片段；
- 篮球词表主要围绕当前样本构造，尚不是完整领域词典；
- 未进行 ASR 模型训练或微调；
- LLM 纠错依赖外部 API，且可能产生无效纠错或过度纠错；
- Qwen 模型 ID 对大小写敏感，需使用 `qwen3.7-max` 这类正确模型 ID；错误大小写会导致 API 404。

后续可以扩展更多篮球解说片段、更多说话人和更完整的篮球术语词表，并进一步分析不同错误类型下 LLM 纠错的有效性。下一步可在同一批 ASR 输出和同一个最佳 prompt 下比较不同 LLM 模型，观察 avg CER after、degraded samples 和 exact samples 的差异。更远期可以探索 speaker diarization、overlapped speech detection 和 ASR timestamp alignment，用于分析多人解说或重叠语音。

---

## 致谢

本项目基于 FunASR/SenseVoice 构建。
