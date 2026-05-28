# 篮球解说 ASR 的领域词表增强 LLM 纠错

## 目标

本步骤在篮球解说 ASR 结果的基础上，引入 **basketball terminology-aware LLM correction**，测试大语言模型在给定篮球领域词表后，是否能够修正体育解说场景中的语音识别错误。

当前流程为：

```text
篮球解说 ASR 输出
→ 加入篮球领域词表
→ LLM 纠错
→ 纠错后文本
→ CER before/after comparison
```

需要强调的是，LLM 纠错时只接收 ASR hypothesis 和篮球领域词表，不接收人工标注的 reference。reference 仅用于纠错后的 CER 评测，因此不会直接发生 reference 泄漏。

---

## 输入与输出文件

篮球解说 ASR 结果文件：

```text
results/basketball_commentary/asr_results_basketball_commentary_all.csv
```

篮球领域词表文件：

```text
data/basketball_commentary/manifests/basketball_lexicon.txt
```

LLM 纠错结果文件：

```text
results/basketball_commentary/asr_results_basketball_commentary_all_llm_corrected.csv
```

使用的脚本：

```text
scripts/llm_correct_basketball_asr.py
```

---

## 篮球领域词表

当前使用的领域词表包括篮球解说中常见的球队名、球员名、比赛阶段表达和篮球术语，例如：

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

该词表用于向 LLM 提供篮球领域先验。当前词表规模仍然较小，主要用于验证领域词表增强的 LLM 后处理是否有效。更严格的后续实验可以扩展为更一般的篮球术语表，而不是只覆盖当前测试样本中出现的词。

---

## 运行命令

首先设置 DeepSeek API 环境变量：

```powershell
$env:LLM_API_KEY="your_api_key"
$env:LLM_BASE_URL="https://api.deepseek.com"
$env:LLM_MODEL="deepseek-chat"
```

然后在项目根目录运行：

```powershell
cd D:\Github_repo\Speech-Project

python scripts\llm_correct_basketball_asr.py `
  --input results/basketball_commentary/asr_results_basketball_commentary_all.csv `
  --output results/basketball_commentary/asr_results_basketball_commentary_all_llm_corrected.csv `
  --lexicon data/basketball_commentary/manifests/basketball_lexicon.txt
```

查看纠错结果：

```powershell
Import-Csv .\results\basketball_commentary\asr_results_basketball_commentary_all_llm_corrected.csv |
Select-Object utt_id,reference,hypothesis,llm_corrected_hypothesis,cer_before_llm,llm_corrected_cer,llm_changed |
Format-List
```

---

## 实验结果

扩展后的篮球解说测试集共包含 11 个片段。LLM 纠错前后 CER 如下：

| Sample         | CER Before LLM | CER After LLM | Result       |
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

相对下降约为：

```text
36.1%
```

结果表明，在扩展后的 11 条篮球解说片段上，领域词表增强 LLM 纠错仍然能够显著降低平均 CER，但提升幅度比 5 条样本时更低，也更真实地反映了该方法的不稳定性。

---

## 典型纠错案例

### 1. 球队名、地名和比赛阶段完全修正

```text
Reference:
首先还是主队圣安东尼奥马刺跳到球权来吧西决的第四场来了嗯

ASR:
首先还是助队山东密奥马刺跳到球权来吧七决的第四场来了嗯

LLM-corrected:
首先还是主队圣安东尼奥马刺跳到球权来吧西决的第四场来了嗯
```

主要修正包括：

```text
助队 → 主队
山东密奥 → 圣安东尼奥
七决 → 西决
```

该结果说明，篮球领域词表能够帮助 LLM 修正球队名、地名和比赛阶段表达中的明显 ASR 错误。

---

### 2. 球员名完全修正

```text
Reference:
对位上哈腾去对文班卡森去防卡斯尔

ASR:
对位上哈滕去对文班卡森恩去防卡瑟尔

LLM-corrected:
对位上哈腾去对文班卡森去防卡斯尔
```

主要修正包括：

```text
哈滕 → 哈腾
卡森恩去 → 卡森去
卡瑟尔 → 卡斯尔
```

该结果说明，LLM 在给定球员名词表后，能够有效修正音近但写法错误的球员名。

---

### 3. 篮球术语部分修正

```text
Reference:
运球往里杀这边协防位置有人哦这球没投对再分出来了弧顶有投手

ASR:
运球往里杀这边前方位置有人哦这球没投对但分出来了湖顶有投手

LLM-corrected:
运球往里杀这边前方位置有人哦这球没投对但分出来了弧顶有投手
```

成功修正：

```text
湖顶 → 弧顶
```

未修正：

```text
前方 → 协防
但分出来了 → 再分出来了
```

这说明 LLM 能够修正非常明显的篮球术语错误，但对于语义上仍然可能成立的词，可能会保持保守。

---

### 4. 复杂错误中的明显改善

```text
Reference:
二十四秒违例了文班今天的第一个封盖最终还是算在了切特的身上

ASR:
阿十瓦为力了嗯本丹今天的第一个分盖最终还是算在了切特的身上

LLM-corrected:
阿十瓦为力了文班今天的第一个封盖最终还是算在了切特的身上
```

成功修正：

```text
本丹 → 文班
分盖 → 封盖
```

仍未修正：

```text
阿十瓦为力了 → 二十四秒违例了
```

该样本说明，领域词表能够帮助 LLM 修正部分篮球术语和球员名错误，但当 ASR 输出严重失真时，LLM 不一定能够恢复完整正确内容。

---

## 失败案例分析

### 1. 纠错后变差

```text
Reference:
这样的话通过罚球雷霆队在第一节开场还是拿到两分的领先

ASR:
这样的话通过罚球已形队在第二节开场还是拿到两分的领先

LLM-corrected:
这样的话通过罚球已经在第二节开场还是拿到两分的领先
```

该样本中，正确内容应为：

```text
雷霆队
第一节
```

但 LLM 将：

```text
已形队 → 已经
```

这使句子在语言上更顺，但没有恢复正确的篮球领域实体。同时，`第二节` 也没有被修正为 `第一节`。

这说明 LLM 有时会优先选择语言上更自然的表达，而不是正确的领域词，导致纠错后 CER 反而上升。

---

### 2. 领域词表无法修正缺失内容

```text
Reference:
好球亚历山大今天亚历山大终于拿出了能够媲美几位先贤的中距离对

ASR:
好球亚斯连亚山大终于拿出了能够媲美几位先贤的中距离啊对

LLM-corrected:
好球亚历山大终于拿出了能够媲美几位先贤的中距离啊对
```

该样本中，LLM 修正了部分球员名错误，但没有恢复 reference 中缺失的：

```text
今天亚历山大
```

因此 CER 没有下降。

这说明当 ASR 输出发生漏识别时，LLM 即使知道领域词表，也不一定会主动补全缺失内容。为了避免 hallucination，LLM 通常会对补全缺失内容保持保守。

---

### 3. 语气词和细微差异不易修正

```text
Reference:
额这球文班觉得可以挑战

ASR:
呃这球文班觉得可以挑战

LLM-corrected:
呃这球文班觉得可以挑战
```

该样本的错误主要来自：

```text
额 → 呃
```

这类差异在语义上几乎没有影响，但在 CER 中仍然会被计入错误。LLM 没有修正它，说明 LLM 后处理更关注实词和语义内容，而不一定会处理语气词的细微写法差异。

---

## 结果分析

当前结果表明，篮球领域词表增强的 LLM 纠错对以下错误比较有效：

1. 球队名和地名错误；
2. 球员名和译名错误；
3. 明显的篮球术语错误；
4. 音近但语义不合理的 ASR 输出。

但该方法也存在明显局限：

1. 对语义上仍然合理的错误较保守；
2. 对功能词插入、漏字和语气词问题修正有限；
3. 在 ASR 输出严重失真时，不一定能够恢复原句；
4. 有时会将错误文本改成语言上更自然但事实错误的表达；
5. 当前词表较小，仍然依赖人工构造领域词表。

---

## 当前结论

在扩展后的 11 个篮球解说片段上，FunASR/SenseVoice 的原始平均 CER 为：

```text
0.1322
```

加入篮球领域词表增强的 LLM 纠错后，平均 CER 降低到：

```text
0.0845
```

相对下降约：

```text
36.1%
```

这说明，LLM-based ASR correction 在领域语音识别场景中具有明显潜力。尤其是在篮球解说这类包含大量专有名词和领域术语的场景中，领域词表能够为 LLM 提供有效先验，从而改善 ASR 输出。

不过，该方法并不能替代 ASR 模型本身的鲁棒性提升。在严重识别错误、漏识别、多人重叠语音或切片质量较差的情况下，LLM 可能只能部分修正，甚至可能产生错误补全。因此，更合理的定位是：LLM 纠错适合作为 ASR 系统之后的轻量级后处理模块。

---

## 后续 Prompt Ablation 实验

在上述领域词表增强 LLM 纠错基础上，项目进一步进行了 prompt ablation，比较不同提示策略对纠错效果和稳定性的影响。

新增脚本：

```text
scripts/llm_correct_basketball_asr_prompt_ablation.py
```

实验记录：

```text
notes/prompt_ablation_basketball_llm.md
```

输出目录：

```text
results/basketball_commentary/prompt_ablation/
```

本次比较了四种 prompt：

| Prompt | 名称 | 设计重点 |
| --- | --- | --- |
| A | baseline | 复用当前领域词表增强 prompt，作为现有方法复现 |
| B | conservative | 只在词表相关、明显音近或语境证据充分时修改 |
| C | two-stage | 先内部判断是否需要修改和依据是否充分，再输出最终文本 |
| D | few-shot | 加入成功示例和失败警示，减少语言通顺性诱导 |

Prompt ablation 汇总结果：

| prompt_name | avg_cer_before | avg_cer_after | relative_reduction | num_improved | num_degraded | num_unchanged | num_exact |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| prompt_a_baseline | 0.1322 | 0.0787 | 0.4051 | 5 | 1 | 3 | 2 |
| prompt_b_conservative | 0.1322 | 0.0859 | 0.3506 | 4 | 0 | 4 | 3 |
| prompt_c_two_stage | 0.1322 | 0.0923 | 0.3016 | 6 | 0 | 4 | 1 |
| prompt_d_few_shot | 0.1322 | 0.0859 | 0.3506 | 4 | 0 | 4 | 3 |

主要结论：

1. `prompt_a_baseline` 平均 CER 最低，为 `0.0787`，相对原始 ASR 下降 `40.51%`；
2. `prompt_b_conservative` 和 `prompt_d_few_shot` 没有 degraded 样本，稳定性优于 baseline；
3. `basketball_006` 中，四种 prompt 均避免了“已形队 -> 已经”的错误纠正，说明 prompt 约束可以抑制单纯追求语言通顺的过度纠错；
4. baseline 唯一 degraded 样本是原始 CER 为 0 的 `basketball_008`，说明较激进的纠错策略可能破坏原本正确的 ASR 输出；
5. 后续模型比较可优先选择 conservative 或 few-shot 作为稳定 prompt，同时保留 baseline 作为最低平均 CER 对照。
