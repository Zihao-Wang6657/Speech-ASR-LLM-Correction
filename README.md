# 中文 ASR 鲁棒性评测与领域 LLM 纠错

本项目基于 **FunASR / SenseVoice** 搭建一个轻量级中文语音识别评测流程，覆盖普通话自录语音、扰动鲁棒性、篮球解说领域语音，以及基于大语言模型的 ASR 后处理纠错。

项目重点不是训练新的 ASR 模型，而是构建一套可复现的小型实验链路：

```text
音频数据 -> FunASR/SenseVoice ASR -> CER 评测 -> 错误分析
       -> LLM 纠错 -> Prompt Ablation -> 多模型对比
```

本项目使用 **Character Error Rate, CER** 作为主要评价指标，即识别文本与人工参考文本之间的字符级错误率；CER 越低，说明识别或纠错结果越接近人工标注。

## 项目亮点

| 模块 | 核心结果 |
| --- | --- |
| 普通话自录语音 | 构建多条 clean speech 数据, 平均 CER 为 `0.0000`，轻度语速和噪声扰动下整体稳定。 |
| 篮球解说 ASR | 构建多条篮球解说片段，原始平均 CER 为 `0.1322`，错误集中在球员名、球队名、篮球术语和比赛阶段。 |
| 领域词表增强 LLM 纠错 | 加入篮球领域词表后，平均 CER 从 `0.1322` 降到 `0.0845`，相对下降约 `36.1%`。 |
| Prompt Ablation | 对比 baseline、conservative、two-stage、few-shot 四种 prompt；baseline 最低 CER 为 `0.0787`，conservative/few-shot 更稳定。 |
| 多模型 LLM 对比 | 固定 conservative prompt，对比 DeepSeek、Qwen、Kimi；Qwen `qwen3.7-max` 最优，平均 CER 降到 `0.0765`，且无 degraded 样本。 |

## 当前最佳结果

### 篮球解说 LLM 纠错主结果

| Setting | Avg CER | Relative Reduction | 说明 |
| --- | ---: | ---: | --- |
| 原始 ASR | 0.1322 | - | SenseVoice 原始输出 |
| 领域词表增强 LLM | 0.0845 | 36.1% | 使用篮球词表的单 prompt 纠错 |
| Prompt Ablation 最佳平均值 | 0.0787 | 40.51% | baseline prompt，平均 CER 最低 |
| Model Comparison 最佳模型 | 0.0765 | 42.18% | Qwen `qwen3.7-max` + conservative prompt |

### 多模型对比

固定 `prompt_b_conservative`，只改变 LLM provider/model：

| Provider | Model | CER Before | CER After | Relative Reduction | Improved | Degraded | Exact | API Error |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen | qwen3.7-max | 0.1322 | 0.0765 | 42.18% | 4 | 0 | 3 | 0 |
| Kimi | Pro/moonshotai/Kimi-K2.6 | 0.1322 | 0.0859 | 35.06% | 4 | 0 | 3 | 0 |
| DeepSeek | deepseek-v4-pro | 0.1322 | 0.0987 | 25.32% | 2 | 1 | 2 | 0 |

Qwen 首次使用 `Qwen3.7-Max` 时返回 404；改为正确模型 ID `qwen3.7-max` 后调用成功。模型 ID 对大小写敏感。

## 仓库结构

```text
Speech-Project
├── README.md
├── .gitignore
├── assets/
│   └── Gradio_demo/test_001.png
├── data/
│   ├── mandarin/
│   │   ├── raw_audio/
│   │   ├── processed_audio/
│   │   ├── manifests/
│   │   └── tmp/
│   └── basketball_commentary/
│       ├── source/                         # 原始视频/音频，已忽略
│       ├── segments/
│       └── manifests/
│           ├── basketball_commentary_manifest_all.csv
│           └── basketball_lexicon.txt
├── scripts/
│   ├── evaluate_asr.py
│   ├── summarize_asr_results.py
│   ├── create_robustness_data.py
│   ├── create_basketball_segments.py
│   ├── llm_correct_asr.py
│   ├── llm_correct_basketball_asr.py
│   ├── llm_correct_basketball_asr_prompt_ablation.py
│   └── llm_correct_basketball_asr_model_comparison.py
├── notes/
│   ├── setup_funasr_demo.md
│   ├── batch_asr_evaluation.md
│   ├── robustness_evaluation.md
│   ├── llm_error_correction.md
│   ├── basketball_commentary_evaluation.md
│   ├── basketball_llm_correction.md
│   ├── prompt_ablation_basketball_llm.md
│   └── model_comparison_basketball_llm.md
└── results/
    ├── mandarin/
    └── basketball_commentary/
        ├── asr_results_basketball_commentary_all.csv
        ├── asr_results_basketball_commentary_all_llm_corrected.csv
        ├── prompt_ablation/
        ├── model_comparison/
        └── model_comparison_qwen_retry/
```

## 环境配置

### Conda 环境

```powershell
conda create -n funasr python=3.10 -y
conda activate funasr
```

### Python 依赖

```powershell
pip install funasr fastapi uvicorn python-multipart gradio torch torchaudio requests numpy soundfile
```

### FFmpeg

Windows 下读取 `.m4a`、`.mp4` 等格式需要安装 `ffmpeg`：

```powershell
conda install -c conda-forge ffmpeg -y
ffmpeg -version
```

## 启动 FunASR OpenAI-compatible API

在一个 PowerShell 窗口中启动服务：

```powershell
conda activate funasr
cd D:\Github_repo\Speech-Project\FunASR\examples\openai_api
python server.py --model sensevoice --device cpu --port 8000
```

如果需要官方 Gradio demo：

```powershell
conda activate funasr
cd D:\Github_repo\Speech-Project\FunASR\examples\openai_api
python gradio_app.py --base-url http://localhost:8000
```

## 数据格式

本项目使用 manifest CSV 管理测试集：

```csv
utt_id,audio_path,reference
test_001,data/mandarin/raw_audio/test_001.m4a,今天我们测试一下中文语音识别系统
```

字段说明：

| 字段 | 说明 |
| --- | --- |
| `utt_id` | 样本编号 |
| `audio_path` | 音频路径 |
| `reference` | 人工参考文本 |

所有包含中文的 CSV / Markdown 文件均使用 UTF-8 或 UTF-8 with BOM 读写，以减少 WPS/Excel 中文乱码问题。

## 评测指标

本项目主要使用 **Character Error Rate, CER**：

```text
CER = (S + D + I) / N
```

其中 `S` 为替换错误，`D` 为删除错误，`I` 为插入错误，`N` 为 reference 字符数。对于中文 ASR，小规模实验中 CER 比 WER 更直接。

## 普通话自录语音实验

### 运行 ASR 评测

```powershell
cd D:\Github_repo\Speech-Project

python scripts\evaluate_asr.py `
  --manifest data/mandarin/manifests/test_manifest.csv `
  --output results/mandarin/asr_results_clean.csv
```

扰动数据评测示例：

```powershell
python scripts\evaluate_asr.py `
  --manifest data/mandarin/manifests/test_manifest_speed_1_1.csv `
  --output results/mandarin/asr_results_speed_1_1.csv
```

```powershell
python scripts\evaluate_asr.py `
  --manifest data/mandarin/manifests/test_manifest_noise_5db.csv `
  --output results/mandarin/asr_results_noise_5db.csv
```

### 普通话结果

| Setting | Samples | Average CER | Max CER |
| --- | ---: | ---: | ---: |
| Clean | 11 | 0.0000 | 0.0000 |
| Speed 0.9x | 11 | 0.0000 | 0.0000 |
| Speed 1.1x | 11 | 0.0051 | 0.0556 |
| Noise 10dB SNR | 11 | 0.0000 | 0.0000 |
| Noise 5dB SNR | 11 | 0.0065 | 0.0714 |

`10dB` 和 `5dB` 指信噪比 SNR。SNR 越低，噪声相对越强。

## 篮球解说 ASR 实验

### 数据构建

原始视频或音频放在：

```text
data/basketball_commentary/source/
```

切片计划：

```text
data/basketball_commentary/manifests/segment_plan.csv
data/basketball_commentary/manifests/segment_plan_match_002.csv
```

切片命令示例：

```powershell
python scripts\create_basketball_segments.py `
  --source data/basketball_commentary/source/match_001.mp4
```

第二段视频：

```powershell
python scripts\create_basketball_segments.py `
  --source data/basketball_commentary/source/match_002.mp4 `
  --segment-plan data/basketball_commentary/manifests/segment_plan_match_002.csv `
  --manifest-output data/basketball_commentary/manifests/basketball_commentary_manifest_match_002.csv
```

合并后的总 manifest：

```text
data/basketball_commentary/manifests/basketball_commentary_manifest_all.csv
```

### 运行篮球解说 ASR

```powershell
python scripts\evaluate_asr.py `
  --manifest data/basketball_commentary/manifests/basketball_commentary_manifest_all.csv `
  --output results/basketball_commentary/asr_results_basketball_commentary_all.csv
```

### 原始 ASR 结果

扩展后的篮球解说测试集包含 11 个片段，平均 CER 为 `0.1322`。

| Sample | CER | 主要错误类型 |
| --- | ---: | --- |
| basketball_001 | 0.1786 | 球队名、地名与比赛阶段 |
| basketball_002 | 0.1875 | 球员名 |
| basketball_003 | 0.1379 | 篮球术语 |
| basketball_004 | 0.1250 | 篮球术语与功能词 |
| basketball_005 | 0.3103 | 违例、球员名、封盖术语 |
| basketball_006 | 0.1154 | 球队名和比赛节次 |
| basketball_007 | 0.0500 | 球员名和语气词 |
| basketball_008 | 0.0000 | 原始识别正确 |
| basketball_009 | 0.2333 | 球员名和漏识别 |
| basketball_010 | 0.0909 | 语气词写法差异 |
| basketball_011 | 0.0256 | 近义词识别差异 |

典型错误包括：

- 球队名和地名：`圣安东尼奥`、`雷霆`；
- 比赛阶段：`西决`、`第一节`；
- 球员名：`哈腾`、`文班`、`卡斯尔`、`亚历山大`；
- 篮球术语：`协防`、`弧顶`、`持球人`、`封盖`、`中距离`；
- 快语速和轻微重叠语音导致的漏识别。

## 篮球领域词表增强 LLM 纠错

词表文件：

```text
data/basketball_commentary/manifests/basketball_lexicon.txt
```

词表示例：

```text
圣安东尼奥
马刺
西决
雷霆
哈腾
文班
卡森
卡斯尔
亚历山大
协防
弧顶
一五挡拆
持球人
二十四秒违例
封盖
中距离
```

LLM 纠错只接收 ASR `hypothesis` 和篮球领域词表，不接收 `reference`。`reference` 仅用于事后 CER 计算。

### 环境变量

不要把 API key 写入代码或文档。使用 PowerShell 环境变量：

```powershell
$env:LLM_API_KEY="your_api_key"
$env:LLM_BASE_URL="https://api.deepseek.com"
$env:LLM_MODEL="deepseek-chat"
```

### 运行领域词表纠错

```powershell
python scripts\llm_correct_basketball_asr.py `
  --input results/basketball_commentary/asr_results_basketball_commentary_all.csv `
  --output results/basketball_commentary/asr_results_basketball_commentary_all_llm_corrected.csv `
  --lexicon data/basketball_commentary/manifests/basketball_lexicon.txt
```

结果：

| Metric | Value |
| --- | ---: |
| CER before LLM | 0.1322 |
| CER after LLM | 0.0845 |
| Relative reduction | 36.1% |

典型成功纠错：

```text
山东密奥 -> 圣安东尼奥
七决 -> 西决
哈滕 -> 哈腾
卡瑟尔 -> 卡斯尔
湖顶 -> 弧顶
本丹 -> 文班
分盖 -> 封盖
```

典型风险样本：

```text
ASR: 这样的话通过罚球已形队在第二节开场还是拿到两分的领先
LLM: 这样的话通过罚球已经在第二节开场还是拿到两分的领先
```

该样本说明，LLM 可能把错误文本改成语言上更通顺但领域上不正确的表达。

## Prompt Ablation

脚本：

```text
scripts/llm_correct_basketball_asr_prompt_ablation.py
```

运行命令：

```powershell
python scripts\llm_correct_basketball_asr_prompt_ablation.py `
  --input results/basketball_commentary/asr_results_basketball_commentary_all.csv `
  --lexicon data/basketball_commentary/manifests/basketball_lexicon.txt `
  --output-dir results/basketball_commentary/prompt_ablation
```

结果汇总：

| Prompt | CER Before | CER After | Relative Reduction | Improved | Degraded | Unchanged | Exact |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| prompt_a_baseline | 0.1322 | 0.0787 | 40.51% | 5 | 1 | 3 | 2 |
| prompt_b_conservative | 0.1322 | 0.0859 | 35.06% | 4 | 0 | 4 | 3 |
| prompt_c_two_stage | 0.1322 | 0.0923 | 30.16% | 6 | 0 | 4 | 1 |
| prompt_d_few_shot | 0.1322 | 0.0859 | 35.06% | 4 | 0 | 4 | 3 |

结论：

- baseline 平均 CER 最低，但存在 1 条 degraded；
- conservative 和 few-shot 没有 degraded，更适合作为稳定纠错策略；
- `basketball_006` 中，四种 prompt 都避免了 `已形队 -> 已经`；
- `basketball_008` 原本 CER 为 0，baseline 删除“的”后变差，说明激进纠错可能破坏正确文本。

## 多模型 LLM 对比

脚本：

```text
scripts/llm_correct_basketball_asr_model_comparison.py
```

固定 prompt：

```text
prompt_b_conservative
```

### 环境变量

```powershell
$env:DEEPSEEK_API_KEY="your_deepseek_api_key"
$env:DEEPSEEK_URL="https://api.deepseek.com"
$env:DEEPSEEK_MODEL="deepseek-v4-pro"

$env:QWEN_API_KEY="your_qwen_api_key"
$env:QWEN_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
$env:QWEN_MODEL="qwen3.7-max"

$env:KIMI_API_KEY="your_kimi_api_key"
$env:KIMI_URL="https://api.siliconflow.cn/v1"
$env:KIMI_MODEL="Pro/moonshotai/Kimi-K2.6"
```

### 运行命令

```powershell
python scripts\llm_correct_basketball_asr_model_comparison.py `
  --input results/basketball_commentary/asr_results_basketball_commentary_all.csv `
  --lexicon data/basketball_commentary/manifests/basketball_lexicon.txt `
  --output-dir results/basketball_commentary/model_comparison `
  --providers deepseek,qwen,kimi
```

Qwen 首次因模型 ID 大小写错误失败后，使用 `qwen3.7-max` 单独重跑：

```powershell
python scripts\llm_correct_basketball_asr_model_comparison.py `
  --input results/basketball_commentary/asr_results_basketball_commentary_all.csv `
  --lexicon data/basketball_commentary/manifests/basketball_lexicon.txt `
  --output-dir results/basketball_commentary/model_comparison_qwen_retry `
  --providers qwen
```

### 模型对比结果

| Provider | Model | CER Before | CER After | Relative Reduction | Improved | Degraded | Exact | API Error |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen | qwen3.7-max | 0.1322 | 0.0765 | 42.18% | 4 | 0 | 3 | 0 |
| Kimi | Pro/moonshotai/Kimi-K2.6 | 0.1322 | 0.0859 | 35.06% | 4 | 0 | 3 | 0 |
| DeepSeek | deepseek-v4-pro | 0.1322 | 0.0987 | 25.32% | 2 | 1 | 2 | 0 |

结论：

- Qwen `qwen3.7-max` 当前平均 CER 最低，且没有 degraded 样本；
- Kimi 同样没有 degraded，稳定性较好；
- DeepSeek 有提升，但会破坏 `basketball_008` 这类原本正确样本；
- Qwen 模型 ID 对大小写敏感，错误大小写会导致 API 404。

## 实验记录

| 文档 | 内容 |
| --- | --- |
| `notes/setup_funasr_demo.md` | FunASR / SenseVoice demo 和服务启动记录 |
| `notes/batch_asr_evaluation.md` | 普通话 clean speech 批量 ASR 评测 |
| `notes/robustness_evaluation.md` | 语速与噪声扰动鲁棒性评测 |
| `notes/llm_error_correction.md` | 普通话 LLM ASR 纠错 |
| `notes/basketball_commentary_evaluation.md` | 篮球解说 ASR 数据构建与评测 |
| `notes/basketball_llm_correction.md` | 篮球领域词表增强 LLM 纠错 |
| `notes/prompt_ablation_basketball_llm.md` | 篮球 LLM prompt ablation |
| `notes/model_comparison_basketball_llm.md` | DeepSeek / Qwen / Kimi 模型对比 |

## 安全与 Git 注意事项

- 不要把 API key 写入代码、README 或 notes；
- 不要提交 `.env`、`*.key` 等密钥文件；
- 不要提交 FunASR 官方仓库源码；
- 不要提交篮球比赛原始视频或音频；
- `data/basketball_commentary/source/` 已在 `.gitignore` 中忽略；
- 中文 CSV / Markdown 使用 UTF-8 或 UTF-8 with BOM。

## 局限性与后续工作

当前项目仍是小型实验，主要局限包括：

- 普通话与篮球解说样本规模都较小；
- 篮球词表主要围绕当前样本构造，尚不是完整领域词典；
- 未进行 ASR 模型训练或微调；
- LLM 纠错依赖外部 API，结果可能受模型版本更新影响；
- 对多人重叠语音、说话人分离和时间戳对齐尚未展开深入实验。

后续可以扩展更多篮球解说片段、更多说话人和更完整的篮球术语词表；也可以探索 speaker diarization、overlapped speech detection、ASR timestamp alignment，用于分析多人解说或重叠语音场景。

## 致谢

本项目基于 FunASR / SenseVoice 构建。FunASR 提供语音识别工具链，SenseVoice 提供多语种语音理解模型能力。
