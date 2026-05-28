# 篮球解说 LLM 纠错 Prompt Ablation 实验

## 1. 实验目标

本实验用于比较不同 prompt 策略对篮球解说 ASR 后处理纠错效果的影响。输入为同一批 SenseVoice/FunASR 篮球解说 ASR 输出，LLM 只接收 `hypothesis` 和篮球领域词表，不接收人工标注 `reference`。`reference` 仅用于事后计算 CER。

核心问题：

1. baseline 领域词表增强 prompt 能否复现已有改善；
2. conservative / two-stage prompt 是否能减少过度纠错；
3. few-shot prompt 是否能通过正例和失败警示提升实体、术语纠错能力；
4. 典型失败样本 `basketball_006` 是否减少了“已形队 -> 已经”这类语言通顺但领域错误的修改。

## 2. 四种 Prompt 设计

| Prompt | 名称 | 设计思路 | 预期作用 |
| --- | --- | --- | --- |
| A | baseline | 复用当前 `llm_correct_basketball_asr.py` 的领域词表增强思路，要求修正明显 ASR 错误，只输出文本。 | 作为现有方法复现基线。 |
| B | conservative | 更强调“有充分依据才修改”，要求 ASR 与词表高度相关、明显音近或语境高度匹配，不为了通顺改写。 | 减少过度纠错和 degraded samples。 |
| C | two-stage | 在 prompt 中要求模型先内部判断是否需要修改、是否有足够依据，再输出最终文本。CSV 中只记录最终纠正文本。 | 减少不必要修改，提高稳定性。 |
| D | few-shot | 加入成功示例：`山东密奥 -> 圣安东尼奥`、`七决 -> 西决`、`哈滕 -> 哈腾`、`湖顶 -> 弧顶`；加入失败警示：不要把“已形队”改成“已经”。 | 强化领域实体/术语纠错，同时提醒模型避免语言流畅性诱导。 |

## 3. 运行命令

先设置 DeepSeek API 环境变量：

```powershell
$env:LLM_API_KEY="your_api_key"
$env:LLM_BASE_URL="https://api.deepseek.com"
$env:LLM_MODEL="deepseek-chat"
```

然后在项目根目录运行：

```powershell
cd D:\Github_repo\Speech-Project

python scripts\llm_correct_basketball_asr_prompt_ablation.py `
  --input results/basketball_commentary/asr_results_basketball_commentary_all.csv `
  --lexicon data/basketball_commentary/manifests/basketball_lexicon.txt `
  --output-dir results/basketball_commentary/prompt_ablation
```

脚本会生成以下文件：

```text
results/basketball_commentary/prompt_ablation/prompt_a_baseline.csv
results/basketball_commentary/prompt_ablation/prompt_b_conservative.csv
results/basketball_commentary/prompt_ablation/prompt_c_two_stage.csv
results/basketball_commentary/prompt_ablation/prompt_d_few_shot.csv
results/basketball_commentary/prompt_ablation/prompt_ablation_summary.csv
```

## 4. Summary 表格

本次实验已于 2026-05-28 运行完成，结果来自：

```text
results/basketball_commentary/prompt_ablation/prompt_ablation_summary.csv
```

| prompt_name | num_samples | avg_cer_before | avg_cer_after | relative_reduction | num_improved | num_degraded | num_unchanged | num_exact | num_api_error | output_file |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| prompt_a_baseline | 11 | 0.1322 | 0.0787 | 0.4051 | 5 | 1 | 3 | 2 | 0 | results/basketball_commentary/prompt_ablation/prompt_a_baseline.csv |
| prompt_b_conservative | 11 | 0.1322 | 0.0859 | 0.3506 | 4 | 0 | 4 | 3 | 0 | results/basketball_commentary/prompt_ablation/prompt_b_conservative.csv |
| prompt_c_two_stage | 11 | 0.1322 | 0.0923 | 0.3016 | 6 | 0 | 4 | 1 | 0 | results/basketball_commentary/prompt_ablation/prompt_c_two_stage.csv |
| prompt_d_few_shot | 11 | 0.1322 | 0.0859 | 0.3506 | 4 | 0 | 4 | 3 | 0 | results/basketball_commentary/prompt_ablation/prompt_d_few_shot.csv |

从平均 CER 看，`prompt_a_baseline` 最低，达到 0.0787，相对下降 40.51%。从稳定性看，`prompt_b_conservative`、`prompt_c_two_stage` 和 `prompt_d_few_shot` 都没有 degraded 样本，其中 conservative 和 few-shot 在无 degraded 的同时保持 0.0859 的平均 CER，稳定性更好。

## 5. 状态字段解释

明细 CSV 中每条样本包含 `status`：

| status | 含义 |
| --- | --- |
| improved | `cer_after < cer_before`，LLM 纠错降低了 CER。 |
| degraded | `cer_after > cer_before`，LLM 纠错后 CER 变差。 |
| unchanged | `cer_after == cer_before`，纠错前后 CER 无变化。 |
| exact | `cer_after == 0`，纠错后与 reference 完全一致。 |
| api_error | 当前样本 API 调用失败；脚本保留原 hypothesis 作为 corrected_hypothesis，并继续处理后续样本。 |

其中：

```text
delta_cer = cer_after - cer_before
relative_reduction = (avg_cer_before - avg_cer_after) / avg_cer_before
```

## 6. 典型样本分析

### basketball_001

原始错误集中在球队/地名和比赛阶段：

```text
山东密奥 -> 圣安东尼奥
七决 -> 西决
```

该样本用于观察四种 prompt 是否都能恢复高置信度领域实体。baseline 和 few-shot 预期较容易完全修正；conservative 和 two-stage 如果判断音近与词表证据充分，也应能修正。

实际结果：

| Prompt | corrected_hypothesis | CER after | status |
| --- | --- | ---: | --- |
| A baseline | 首先还是主队圣安东尼奥马刺跳到球权来吧西决的第四场来了嗯 | 0.0000 | exact |
| B conservative | 首先还是主队圣安东尼奥马刺跳到球权来吧西决的第四场来了嗯 | 0.0000 | exact |
| C two-stage | 首先还是主队圣安东尼奥马刺跳到球权吧西决的第四场来了嗯 | 0.0357 | improved |
| D few-shot | 首先还是主队圣安东尼奥马刺跳到球权来吧西决的第四场来了嗯 | 0.0000 | exact |

除 two-stage 删除了“来”导致未完全匹配外，其余三种 prompt 均完全修正该样本。

### basketball_002

原始错误集中在球员名：

```text
哈滕 -> 哈腾
卡瑟尔 -> 卡斯尔
```

该样本用于观察 prompt 是否能稳定利用球员名词表。few-shot 中包含 `哈滕 -> 哈腾` 示例，预期对该样本有帮助。

实际结果：

| Prompt | corrected_hypothesis | CER after | status |
| --- | --- | ---: | --- |
| A baseline | 对位上哈腾去对文班卡森去防卡斯尔 | 0.0000 | exact |
| B conservative | 对位上哈腾去对文班卡森去防卡斯尔 | 0.0000 | exact |
| C two-stage | 对位上哈腾去对文班卡森恩去防卡斯尔 | 0.0625 | improved |
| D few-shot | 对位上哈腾去对文班，卡森去防卡斯尔 | 0.0000 | exact |

baseline、conservative 和 few-shot 都能完全修正球员名；two-stage 修正了 `哈滕` 和 `卡瑟尔`，但保留了 `卡森恩` 中多余的“恩”。

### basketball_003

原始错误包含篮球术语和语义上仍可能成立的普通词：

```text
湖顶 -> 弧顶
前方 -> 协防
```

`湖顶 -> 弧顶` 是较明显的音近术语错误；`前方 -> 协防` 虽符合词表，但上下文证据稍弱。该样本可观察 conservative / two-stage 是否只修正高置信错误，还是能进一步恢复领域术语。

实际结果中，四种 prompt 都修正了：

```text
湖顶 -> 弧顶
```

但都没有修正：

```text
前方 -> 协防
但分出来了 -> 再分出来了
```

因此四种 prompt 在该样本上均为 `cer_after = 0.1034`，状态为 improved。这说明词表和 prompt 对明显音近术语有效，但对语义上仍可成立的普通词替换仍偏保守。

### basketball_006

Reference:

```text
这样的话通过罚球雷霆队在第一节开场还是拿到两分的领先
```

ASR:

```text
这样的话通过罚球已形队在第二节开场还是拿到两分的领先
```

已有 baseline 类 prompt 的失败表现是将：

```text
已形队 -> 已经
```

这会让句子更通顺，但没有恢复正确篮球实体 `雷霆队`，同时也没有修正 `第二节 -> 第一节`，导致 CER 变差。

本 ablation 中重点观察：

1. conservative 是否保持 `已形队` 不变，避免变差；
2. two-stage 是否因为依据不足而拒绝“已形队 -> 已经”；
3. few-shot 是否受失败警示约束，不再输出“已经”；
4. 是否有 prompt 能在不读取 reference 的情况下，根据词表和上下文恢复 `雷霆队`。

实际结果：

| Prompt | corrected_hypothesis | CER before | CER after | status |
| --- | --- | ---: | ---: | --- |
| A baseline | 这样的话通过罚球雷霆队在第二节开场还是拿到两分的领先 | 0.1154 | 0.0385 | improved |
| B conservative | 这样的话通过罚球已形队在第二节开场还是拿到两分的领先 | 0.1154 | 0.1154 | unchanged |
| C two-stage | 这样的话通过罚球雷霆队在第二节开场还是拿到两分的领先 | 0.1154 | 0.0385 | improved |
| D few-shot | 这样的话通过罚球主队在第二节开场还是拿到两分的领先 | 0.1154 | 0.1154 | unchanged |

这次实验中没有任何 prompt 将“已形队”改成“已经”，说明 conservative、two-stage 和 few-shot 的约束都在一定程度上抑制了语言流畅性诱导。baseline 和 two-stage 进一步将“已形队”恢复为 `雷霆队`，但都没有修正 `第二节 -> 第一节`。conservative 保持原文，避免了变差；few-shot 改成 `主队`，虽然不是正确实体，但 CER 与原始 ASR 持平。

### basketball_008

该样本原始 ASR 的 CER 已经是 0：

```text
Reference:
一个赌博式的传球没有能够塞过去

ASR:
一个赌博式的传球没有能够塞 过去
```

baseline 将其改成：

```text
一个赌博式传球没有能够塞过去
```

删除了“的”，导致 `cer_after = 0.0667`，状态为 degraded。conservative、two-stage 和 few-shot 都保持 exact，没有破坏原本正确的样本。这是 conservative/few-shot 更稳定的主要证据之一。

## 7. 初步结论记录位

| 问题 | 结论 |
| --- | --- |
| 哪种 prompt 平均 CER 最低？ | `prompt_a_baseline` 最低，avg CER after = 0.0787，相对下降 40.51%。 |
| 哪种 prompt 最稳定？ | `prompt_b_conservative` 和 `prompt_d_few_shot` 更稳定：二者均无 degraded，avg CER after = 0.0859，且 exact 样本数为 3。 |
| 是否减少 degraded samples？ | 是。baseline 有 1 条 degraded；conservative、two-stage、few-shot 均为 0 条 degraded。 |
| `basketball_006` 是否减少错误纠正？ | 是。四种 prompt 都没有再把“已形队”改成“已经”。baseline 和 two-stage 改为 `雷霆队` 并降低 CER；conservative 保持原文；few-shot 改为 `主队` 但 CER 持平。 |

综合结论：

1. 如果追求最低平均 CER，当前最佳是 `prompt_a_baseline`；
2. 如果追求更稳健、避免破坏原本正确样本，`prompt_b_conservative` 和 `prompt_d_few_shot` 更合适；
3. `prompt_c_two_stage` 没有 degraded，且 improved 样本最多，但 exact 样本较少，说明它倾向于做小幅修正，却不一定能完全恢复原句；
4. prompt ablation 证明了更严格的提示可以减少 degraded samples，但可能牺牲一部分纠错幅度；
5. 后续 model comparison 可以优先选用 conservative 或 few-shot 作为“稳定 prompt”，同时保留 baseline 作为“最低平均 CER prompt”对照。
