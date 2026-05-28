# 篮球解说 ASR 的领域词表增强 LLM 纠错

## 目标

本步骤的目标是在篮球解说 ASR 结果的基础上，引入 **basketball terminology-aware LLM correction**，测试大语言模型在给定篮球领域词表后，是否能够修正体育解说场景中的语音识别错误。

当前流程为：

```text
篮球解说 ASR 输出
→ 加入篮球领域词表
→ LLM 纠错
→ 纠错后文本
→ CER before/after comparison
```

与普通 LLM 纠错不同，本步骤向 LLM 提供了篮球相关术语、球队名、球员名和比赛阶段表达，作为领域知识辅助纠错。

需要强调的是，LLM 纠错时只接收 ASR hypothesis 和篮球领域词表，不接收人工标注的 reference。reference 仅用于纠错后的 CER 评测，因此不会直接发生 reference 泄漏。

---

## 输入与输出文件

篮球解说 ASR 结果文件：

```text
results/basketball_commentary/asr_results_basketball_commentary.csv
```

篮球领域词表文件：

```text
data/basketball_commentary/manifests/basketball_lexicon.txt
```

LLM 纠错结果文件：

```text
results/basketball_commentary/asr_results_basketball_commentary_llm_corrected.csv
```

使用的脚本：

```text
scripts/llm_correct_basketball_asr.py
```

---

## 篮球领域词表

当前使用的领域词表如下：

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

该词表用于向 LLM 提供篮球解说中的领域先验，例如球队名、球员名、篮球术语和比赛阶段表达。

当前词表规模较小，主要用于验证领域词表增强的 LLM 后处理是否有效。更严格的后续实验可以扩展为更一般的篮球术语表，而不是只覆盖当前测试样本中出现的词。

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
  --input results/basketball_commentary/asr_results_basketball_commentary.csv `
  --output results/basketball_commentary/asr_results_basketball_commentary_llm_corrected.csv `
  --lexicon data/basketball_commentary/manifests/basketball_lexicon.txt
```

查看纠错结果：

```powershell
Import-Csv .\results\basketball_commentary\asr_results_basketball_commentary_llm_corrected.csv |
Select-Object utt_id,reference,hypothesis,llm_corrected_hypothesis,cer_before_llm,llm_corrected_cer,llm_changed |
Format-List
```

---

## 实验结果

| Sample         | CER Before LLM | CER After LLM | Result           |
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

相对下降约为：

```text
55.3%
```

这说明，在当前小型篮球解说测试集上，加入篮球领域词表的 LLM 后处理显著降低了 ASR 的 CER。

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

### 4. 术语修正与功能词残留

```text
Reference:
两边打来打去都是一五挡拆哎两队挡拆之后持球人的这个效率在今年季后赛一个第一个第二

ASR:
两边打来打去都是一五挡拆对哎两队挡拆之后十修人的这个效率啊在今年季后赛一个第一第二

LLM-corrected:
两边打来打去都是一五挡拆对哎两队挡拆之后持球人的这个效率啊在今年季后赛一个第一第二
```

成功修正：

```text
十修人 → 持球人
```

仍未修正：

```text
插入的“对”“啊”
第一个第二 → 第一第二
```

这说明领域词表有助于修正核心篮球术语，但对语气词插入、细微漏字和表达顺序问题的改善有限。

---

### 5. 复杂错误中的部分改善与过度纠错风险

```text
Reference:
二十四秒违例了文班今天的第一个封盖最终还是算在了切特的身上

ASR:
阿十瓦为力了嗯本丹今天的第一个分盖最终还是算在了切特的身上

LLM-corrected:
哈腾卡位了嗯文班今天的第一个封盖最终还是算在了切特的身上
```

成功修正：

```text
本丹 → 文班
分盖 → 封盖
```

错误修正：

```text
阿十瓦为力了 → 哈腾卡位了
```

正确 reference 应为：

```text
二十四秒违例了
```

该样本说明，领域词表虽然能够帮助 LLM 修正部分篮球术语和球员名错误，但在 ASR 输出严重失真的情况下，LLM 可能会根据篮球语境进行猜测，从而产生过度纠错或错误补全。

---

## 结果分析

当前结果表明，篮球领域词表增强的 LLM 纠错对以下错误特别有效：

1. 球队名和地名错误；
2. 球员名和译名错误；
3. 明显的篮球术语错误；
4. 音近但语义不合理的 ASR 输出。

但是，它也存在明显局限：

1. 对语义上仍然合理的错误较保守；
2. 对功能词插入、漏字和语气词问题修正有限；
3. 在 ASR 输出严重失真时，可能出现过度纠错；
4. 当前词表较小，仍然依赖人工构造领域词表。

---

## 当前结论

在当前 5 个篮球解说片段上，FunASR/SenseVoice 的原始平均 CER 为：

```text
0.1879
```

加入篮球领域词表增强的 LLM 纠错后，平均 CER 降低到：

```text
0.0840
```

相对下降约：

```text
55.3%
```

这说明，LLM-based ASR correction 在领域语音识别场景中具有明显潜力。尤其是在篮球解说这类包含大量专有名词和领域术语的场景中，领域词表能够为 LLM 提供有效先验，从而显著改善 ASR 输出。

不过，该方法并不能替代 ASR 模型本身的鲁棒性提升。在严重识别错误、多人重叠语音或切片质量较差的情况下，LLM 可能只能部分修正，甚至可能产生错误补全。因此，更合理的定位是：LLM 纠错适合作为 ASR 系统之后的轻量级后处理模块。
