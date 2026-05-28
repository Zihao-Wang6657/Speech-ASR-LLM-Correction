# 篮球解说语音识别评测

## 目标

本步骤构建一个小型篮球比赛解说语音评测集，用于测试 FunASR/SenseVoice 在体育解说场景下的语音识别效果。

相比普通话自录短句，篮球解说语音更具挑战性，主要体现在：

- 语速更快；
- 情绪更强；
- 可能存在多人解说或轻微重叠语音；
- 包含球员名、球队名、地名和比赛阶段表达；
- 包含篮球术语，例如挡拆、协防、弧顶、封盖、违例、持球人等。

本实验的重点不是证明模型在篮球解说上表现很好，而是观察通用 ASR 模型在真实体育解说场景中的典型错误类型。

---

## 数据文件

原始篮球解说视频或音频文件：

```text
data/basketball_commentary/source/
```

切分后的短语音片段：

```text
data/basketball_commentary/segments/
```

切片计划文件：

```text
data/basketball_commentary/manifests/segment_plan.csv
```

生成的评测 manifest 文件：

```text
data/basketball_commentary/manifests/basketball_commentary_manifest.csv
```

ASR 评测结果文件：

```text
results/basketball_commentary/asr_results_basketball_commentary.csv
```

---

## 切片计划格式

本实验使用的 `segment_plan.csv` 保持四列格式：

```csv
utt_id,start,duration,reference
```

其中：

- `utt_id` 表示片段编号；
- `start` 表示从原始视频或音频中的哪个时间点开始切片；
- `duration` 表示切片持续时间；
- `reference` 表示人工转写的参考文本。

当前使用的 5 个篮球解说片段为：

```csv
utt_id,start,duration,reference
basketball_001,0:00:12,8,首先还是主队圣安东尼奥马刺跳到球权来吧西决的第四场来了嗯
basketball_002,0:00:21,5,对位上哈腾去对文班卡森去防卡斯尔
basketball_003,0:01:02,8,运球往里杀这边协防位置有人哦这球没投对再分出来了弧顶有投手
basketball_004,0:02:35,8.7,两边打来打去都是一五挡拆哎两队挡拆之后持球人的这个效率在今年季后赛一个第一个第二
basketball_005,0:01:40,5.7,二十四秒违例了文班今天的第一个封盖最终还是算在了切特的身上
```

---

## 转写规范

对于多人解说和轻微重叠语音，本实验采用以下规则：

1. 单人清晰解说：完整转写主要内容；
2. 轻微重叠片段：转写主说话人，或按照发言顺序合并清晰可辨的内容；
3. “嗯”“对”“是的”等短附和语，只有在清晰可辨且属于主要内容时才写入 reference；
4. 严重重叠、无法稳定听清的片段，不纳入主要 CER 评测；
5. reference 中不添加“解说 A”“解说 B”等说话人标签。

---

## 切片流程

使用脚本：

```text
scripts/create_basketball_segments.py
```

运行命令：

```powershell
python scripts\create_basketball_segments.py `
  --source data/basketball_commentary/source/match_001.mp4
```

成功后会生成：

```text
data/basketball_commentary/segments/basketball_001.wav
data/basketball_commentary/segments/basketball_002.wav
data/basketball_commentary/segments/basketball_003.wav
data/basketball_commentary/segments/basketball_004.wav
data/basketball_commentary/segments/basketball_005.wav
```

以及：

```text
data/basketball_commentary/manifests/basketball_commentary_manifest.csv
```

---

## ASR 评测命令

在运行评测前，需要先启动 FunASR 后端 API server：

```powershell
conda activate funasr
cd D:\Github_repo\Speech-Project\FunASR\examples\openai_api
python server.py --model sensevoice --device cpu --port 8000
```

然后在项目根目录运行：

```powershell
cd D:\Github_repo\Speech-Project

python scripts\evaluate_asr.py `
  --manifest data/basketball_commentary/manifests/basketball_commentary_manifest.csv `
  --output results/basketball_commentary/asr_results_basketball_commentary.csv
```

---

## 实验结果

修正切片边界后，5 个篮球解说片段的 ASR 评测结果如下：

| Sample | CER | Main Error Type |
|---|---:|---|
| basketball_001 | 0.1786 | 球队名、地名与比赛阶段识别错误 |
| basketball_002 | 0.1875 | 球员名识别错误 |
| basketball_003 | 0.1379 | 篮球术语识别错误 |
| basketball_004 | 0.1250 | 篮球术语与功能词识别错误 |
| basketball_005 | 0.3103 | 违例、球员名和封盖术语识别错误 |

平均 CER：

```text
0.1879
```

---

## 典型错误分析

### 1. 球队名、地名和比赛阶段错误

```text
Reference: 首先还是主队圣安东尼奥马刺跳到球权来吧西决的第四场来了嗯
ASR:       首先还是助队山东密奥马刺跳到球权来吧七决的第四场来了嗯
```

典型错误：

```text
主队 → 助队
圣安东尼奥 → 山东密奥
西决 → 七决
```

这些错误说明，通用 ASR 模型在识别体育解说中的球队名、地名和比赛阶段表达时可能不稳定。

---

### 2. 球员名错误

```text
Reference: 对位上哈腾去对文班卡森去防卡斯尔
ASR:       对位上哈滕去对文班卡森恩去防卡瑟尔
```

典型错误：

```text
哈腾 → 哈滕
卡森去 → 卡森恩去
卡斯尔 → 卡瑟尔
```

球员名和译名容易受到发音、语速和模型词表覆盖范围的影响。

---

### 3. 篮球术语错误

```text
Reference: 运球往里杀这边协防位置有人哦这球没投对再分出来了弧顶有投手
ASR:       运球往里杀这边前方位置有人哦这球没投对但分出来了湖顶有投手
```

典型错误：

```text
协防 → 前方
弧顶 → 湖顶
```

这些错误说明，篮球术语对于通用 ASR 模型具有一定领域挑战性。

---

### 4. 篮球术语与功能词错误

```text
Reference: 两边打来打去都是一五挡拆哎两队挡拆之后持球人的这个效率在今年季后赛一个第一个第二
ASR:       两边打来打去都是一五挡拆对哎两队挡拆之后十修人的这个效率啊在今年季后赛一个第一第二
```

典型错误：

```text
持球人 → 十修人
第一个第二 → 第一第二
插入了“对”“啊”等功能性语气词
```

该样本说明，在快节奏解说中，ASR 可能会将篮球术语识别为发音相近但语义不合理的词，也可能插入或遗漏部分语气词。

---

### 5. 违例、球员名和封盖术语错误

```text
Reference: 二十四秒违例了文班今天的第一个封盖最终还是算在了切特的身上
ASR:       阿十瓦为力了嗯本丹今天的第一个分盖最终还是算在了切特的身上
```

典型错误：

```text
二十四秒违例 → 阿十瓦为力
文班 → 本丹
封盖 → 分盖
```

该样本虽然在修正切片边界后 CER 明显下降，但仍然是当前测试集中最困难的片段。这说明篮球解说中的快速表达、球员名和专业术语仍然会显著影响 ASR 效果。

---

## 切片边界对结果的影响

在初始切片中，部分片段存在约 0.5 到 0.7 秒的内容缺失，导致 CER 偏高。修正 `basketball_004` 和 `basketball_005` 的持续时间后，平均 CER 从：

```text
0.2680
```

下降到：

```text
0.1879
```

这说明真实语音评测中，切片边界会显著影响 CER 结果。如果音频片段与 reference 没有精确对齐，CER 可能会高估模型错误。

因此，在构建 ASR 评测集时，需要确保每个音频片段与对应 reference 尽量严格匹配。

---

## 当前结论

篮球解说语音明显比普通话自录短句更具挑战性。当前 5 个篮球解说片段的平均 CER 为 0.1879，远高于普通话自录数据集在 clean speech 下的 0.0000。

这说明体育解说场景中的领域术语、球员名、球队名、快速语速和可能的重叠语音都会显著影响 ASR 效果。

后续项目已将篮球解说测试集扩展到 11 个片段，并合并为总 manifest：

```text
data/basketball_commentary/manifests/basketball_commentary_manifest_all.csv
```

扩展后的 ASR 总结果为：

```text
results/basketball_commentary/asr_results_basketball_commentary_all.csv
```

11 条样本的平均 CER 为：

```text
0.1322
```

在此基础上，项目进一步引入 basketball terminology-aware LLM correction，并完成了 prompt ablation 分析。相关记录见：

```text
notes/basketball_llm_correction.md
notes/prompt_ablation_basketball_llm.md
```
