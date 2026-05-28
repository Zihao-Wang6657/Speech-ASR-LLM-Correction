# 中文语音识别鲁棒性评测与领域词表增强 LLM 纠错

本项目基于 **FunASR/SenseVoice** 搭建一个轻量级中文语音识别实验流程，主要关注：

- 中文 ASR 批量推理；
- Character Error Rate, CER 评测；
- 语速与噪声扰动下的鲁棒性分析；
- 篮球解说领域语音识别评测；
- 基于 LLM 的 ASR 后处理纠错。

本项目不是从零训练 ASR 模型，而是围绕现有语音基础模型构建一个可复现的小型评测与错误分析流程。

---

## 项目亮点

1. **完成普通话自录语音评测**  
   在 11 条自录普通话短句上，FunASR/SenseVoice 在 clean speech 和轻度扰动条件下表现稳定。

2. **构建篮球解说领域测试集**  
   篮球解说语音包含更快语速、领域术语、球员名、球队名和轻微重叠语音，明显比普通话短句更具挑战性。

3. **引入领域词表增强 LLM 纠错**  
   在篮球解说 ASR 输出上，向 LLM 提供篮球领域词表后，平均 CER 从 `0.1879` 降低到 `0.0840`，相对下降约 `55.3%`。

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
├── assets
│   └── Gradio_demo
│       └── test_001.png
│
├── data
│   ├── mandarin
│   │   ├── raw_audio
│   │   ├── processed_audio
│   │   ├── manifests
│   │   └── tmp
│   │
│   └── basketball_commentary
│       ├── source
│       ├── segments
│       └── manifests
│           ├── segment_plan.csv
│           ├── basketball_commentary_manifest.csv
│           └── basketball_lexicon.txt
│
├── FunASR
│
├── notes
│   ├── setup_funasr_demo.md
│   ├── batch_asr_evaluation.md
│   ├── robustness_evaluation.md
│   ├── llm_error_correction.md
│   ├── basketball_commentary_evaluation.md
│   └── basketball_llm_correction.md
│
├── results
│   ├── mandarin
│   └── basketball_commentary
│       ├── asr_results_basketball_commentary.csv
│       └── asr_results_basketball_commentary_llm_corrected.csv
│
├── scripts
│   ├── create_robustness_data.py
│   ├── evaluate_asr.py
│   ├── summarize_asr_results.py
│   ├── llm_correct_asr.py
│   ├── create_basketball_segments.py
│   └── llm_correct_basketball_asr.py
│
└── README.md
```

---

## 文件夹说明

| 路径                                    | 说明                              |
| --------------------------------------- | --------------------------------- |
| `assets/`                               | README 或报告中使用的截图         |
| `data/mandarin/`                        | 普通话自录语音数据集              |
| `data/basketball_commentary/source/`    | 篮球解说原始视频或音频            |
| `data/basketball_commentary/segments/`  | 切分后的篮球解说短音频            |
| `data/basketball_commentary/manifests/` | 篮球解说数据索引和领域词表        |
| `notes/`                                | 实验记录和分析文档                |
| `results/mandarin/`                     | 普通话实验结果                    |
| `results/basketball_commentary/`        | 篮球解说实验结果                  |
| `scripts/`                              | 数据处理、ASR 评测和 LLM 纠错脚本 |

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

### 篮球解说切片

篮球解说原始视频或音频放在：

```text
data/basketball_commentary/source/
```

切片计划文件为：

```text
data/basketball_commentary/manifests/segment_plan.csv
```

格式为：

```csv
utt_id,start,duration,reference
```

运行切片脚本：

```powershell
cd D:\Github_repo\Speech-Project

python scripts\create_basketball_segments.py `
  --source data/basketball_commentary/source/match_001.mp4
```

生成的音频片段存放在：

```text
data/basketball_commentary/segments/
```

生成的 manifest 文件为：

```text
data/basketball_commentary/manifests/basketball_commentary_manifest.csv
```

### 运行篮球解说 ASR 评测

```powershell
python scripts\evaluate_asr.py `
  --manifest data/basketball_commentary/manifests/basketball_commentary_manifest.csv `
  --output results/basketball_commentary/asr_results_basketball_commentary.csv
```

### 篮球解说 ASR 结果

| Sample         |    CER | 主要错误类型                   |
| -------------- | -----: | ------------------------------ |
| basketball_001 | 0.1786 | 球队名、地名与比赛阶段识别错误 |
| basketball_002 | 0.1875 | 球员名识别错误                 |
| basketball_003 | 0.1379 | 篮球术语识别错误               |
| basketball_004 | 0.1250 | 篮球术语与功能词识别错误       |
| basketball_005 | 0.3103 | 违例、球员名和封盖术语识别错误 |

平均 CER：

```text
0.1879
```

相比普通话自录短句，篮球解说语音明显更难。主要错误集中在：

- 球队名和地名，例如“圣安东尼奥”；
- 比赛阶段表达，例如“西决”；
- 球员名，例如“哈腾”“文班”“卡斯尔”；
- 篮球术语，例如“协防”“弧顶”“持球人”“封盖”；
- 快速语速和轻微重叠语音导致的漏识别。

---

## 篮球领域词表增强 LLM 纠错

### 篮球领域词表

词表文件：

```text
data/basketball_commentary/manifests/basketball_lexicon.txt
```

当前词表包括：

```text
圣安东尼奥
马刺
西决
主队
跳到球权
哈腾
文班
卡森
卡斯尔
对位
协防
弧顶
投手
一五挡拆
挡拆
持球人
季后赛
二十四秒违例
封盖
切特
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
  --input results/basketball_commentary/asr_results_basketball_commentary.csv `
  --output results/basketball_commentary/asr_results_basketball_commentary_llm_corrected.csv `
  --lexicon data/basketball_commentary/manifests/basketball_lexicon.txt
```

### 篮球 LLM 纠错结果

| Sample         | CER Before LLM | CER After LLM | 结果             |
| -------------- | -------------: | ------------: | ---------------- |
| basketball_001 |         0.1786 |        0.0000 | 完全修正         |
| basketball_002 |         0.1875 |        0.0000 | 完全修正         |
| basketball_003 |         0.1379 |        0.1034 | 部分修正         |
| basketball_004 |         0.1250 |        0.0750 | 部分修正         |
| basketball_005 |         0.3103 |        0.2414 | 有改善但仍有错误 |

平均 CER：

```text
Before LLM: 0.1879
After LLM:  0.0840
```

相对下降约：

```text
55.3%
```

### 典型纠错案例

#### 完全修正：球队名与比赛阶段

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

#### 部分修正：篮球术语

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

#### 失败风险：过度纠错

```text
ASR:
阿十瓦为力了嗯本丹今天的第一个分盖最终还是算在了切特的身上

LLM:
哈腾卡位了嗯文班今天的第一个封盖最终还是算在了切特的身上
```

其中：

```text
本丹 → 文班
分盖 → 封盖
```

是有效修正，但：

```text
阿十瓦为力了 → 哈腾卡位了
```

是错误补全。正确 reference 应为：

```text
二十四秒违例了
```

这说明领域词表能帮助 LLM 修正部分错误，但在 ASR 输出严重失真时，也可能诱导 LLM 根据语境进行错误猜测。

---

## 结论

本项目完成了一个轻量级中文 ASR 评测与后处理流程。

实验结果表明：

1. FunASR/SenseVoice 在普通话自录短句上表现稳定；
2. 篮球解说语音明显更具挑战性，平均 CER 达到 `0.1879`；
3. 错误主要集中在球员名、球队名、篮球术语、比赛阶段表达和快节奏语音中；
4. 加入篮球领域词表后，LLM 纠错将平均 CER 降低到 `0.0840`，相对下降约 `55.3%`；
5. LLM 后处理适合作为 ASR 系统之后的轻量级纠错模块，但在严重识别错误时存在过度纠错风险。

---

## 局限性

当前项目仍然是一个小型实验，存在以下局限：

- 普通话测试集规模较小；
- 篮球解说测试集目前只有 5 个片段；
- 篮球词表主要围绕当前样本构造，尚不是完整领域词典；
- 未进行 ASR 模型训练或微调；
- LLM 纠错依赖外部 API，且可能产生过度纠错。

后续可以扩展更多篮球解说片段、更多说话人和更完整的篮球术语词表，并进一步分析不同错误类型下 LLM 纠错的有效性。

---

## 致谢

本项目基于 FunASR/SenseVoice 构建。
