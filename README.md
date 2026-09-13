---
license: other
license_name: compilingthings-benchmark-evaluation-licence-v1.0
license_link: LICENSE

pretty_name: CompilingThings MQL5 Compile Benchmark

language:
- en

task_categories:
- text-generation

tags:
- mql5
- algorithmic-trading
- expert-advisor
- code-generation
- benchmark

size_categories:
- n<1K

configs:
- config_name: prompts
  default: true
  data_files:
  - split: test
    path: prompts.jsonl
- config_name: per_item_results
  data_files:
  - split: test
    path: per_item_results.jsonl
- config_name: holdout_ea300_results
  data_files:
  - split: test
    path: holdout_ea300_results.jsonl
- config_name: holdout_nonea200_results
  data_files:
  - split: test
    path: holdout_nonea200_results.jsonl
- config_name: bridge_q8_184_results
  data_files:
  - split: test
    path: bridge_q8_184_results.jsonl
---

# CompilingThings Compile Benchmark for MQL5®

This release evaluates compile success of generated MQL5 on two private held-out sets. The first is 300 Expert Advisor prompts, run on four arms: the base model, two tuned local models and one frontier API model. The second is 200 non-EA prompts (include files, custom indicators, scripts and services, 50 each), run on the three local arms, plus a stability re-run of one of them. The holdout results are attested, not fully verifiable: every row is published as hashes and verdicts, the prompts are not. The 184 public prompts of version 1.0.0 remain in the release, with their published results unchanged.

MQL5® and MetaTrader 5® are registered trademarks of MetaQuotes Ltd. CompilingThings is an independent project. No affiliation, sponsorship, certification, endorsement, or approval by MetaQuotes Ltd. is claimed.

Release identifier: `CompilingThings/compile-benchmark-v1.1.0`. This version replaces the card of `v1.0.0` in place; the 1.0.0 files and figures are carried forward, not re-run.

## Result

A pass requires zero compiler errors and a produced EX5 artifact. A generation cut off at the 8,192-token ceiling counts as a fail. Every local arm run for v1.1 was served at Q8_0 quantisation; see "Serving configuration" and "Q8_0 against the 1.0.0 bf16 arm".

### 300 Expert Advisor prompts, private holdout

| Arm | Compile success | Result | Truncated | Infrastructure failures |
|---|---:|---:|---:|---:|
| Base Qwen2.5-Coder-14B-Instruct | 0.33% | 1/300 | 3 | 0 |
| Tuned 14B, 83k corpus (the 1.0.0 tuned model) | 93.67% | 281/300 | 0 | 0 |
| Tuned 14B, 220k corpus | 94.00% | 282/300 | 0 | 0 |
| gpt-5.6-sol | 95.33% | 286/300 | 4 | 3 |

The frontier arm's seven excluded rows are its own: four generations hit the token ceiling and three API calls returned HTTP 500. Excluding those seven rows gives 286/293 = 97.61%; the all-300 headline stays 286/300 = 95.33%.

The two tuned models are flat against each other on EA prompts: they disagree on 35 of 300 items, 18 in favour of the 220k model and 17 in favour of the 83k model, McNemar p = 1.0.

Against gpt-5.6-sol the 220k model is 1.33 points behind over all 300 (p = 0.57) and 3.41 points behind when the frontier arm's seven excluded rows are dropped from both sides (293 pairs, Newcombe 95% CI −6.86 to −0.24 pp, McNemar p = 0.0525). Both denominators are reported because dropping the frontier failures moves the comparison from −1.33 to −3.41 points. These results do not establish equivalence.

### 200 non-EA prompts, private holdout, 50 per class

| Arm | Compile success, all 200 | Excluding own truncations | Truncated |
|---|---:|---:|---:|
| Base Qwen2.5-Coder-14B-Instruct | 28.0% (56/200) | 30.1% (56/186) | 14 |
| Tuned 14B, 83k corpus | 67.5% (135/200) | 72.2% (135/187) | 13 |
| Tuned 14B, 220k corpus | 84.0% (168/200) | 89.4% (168/188) | 12 |

The first column is the headline: a truncated generation is a fail. The second column drops each arm's own truncated rows from its own denominator. gpt-5.6-sol was not run on this set.

Per class, all 200 counted:

| Class | Base | 83k | 220k |
|---|---:|---:|---:|
| Include file | 20/50 | 38/50 | 31/50 |
| Custom indicator | 0/50 | 49/50 | 50/50 |
| Script | 13/50 | 19/50 | 39/50 |
| Service | 23/50 | 29/50 | 48/50 |

Each cell is 50 items and is indicative, not conclusive. The 220k model is 20 items ahead of the 83k model on scripts and 19 ahead on services, and 7 behind on include files (31/50 vs 38/50; McNemar p = 0.14 over the 50 include-file pairs, p = 0.39 over the 38 pairs left when truncations are dropped, both intervals spanning zero). Those four figures are differences between the class totals in the table, not counts of items that changed verdict: item by item, 24 scripts moved to the 220k model and 4 the other way, 19 services and none the other way, 5 include files and 12 the other way, and 1 indicator and none the other way, which is where the 49 and the 16 in the paired-movement table below come from. Eleven of the 220k model's twelve truncations are include files. Whether the truncations cause the include-file loss is not tested by this release; the 83k model truncated eight include files and still scored higher on that class.

Over the whole set the 220k model is 16.5 points ahead of the 83k model (all 200, 49 items gained against 16 lost, Newcombe 95% CI +8.85 to +23.96 pp, McNemar p = 5.1e-5) and 17.0 points ahead with truncations dropped (182 pairs, CI +9.35 to +24.60 pp, p = 3.3e-5). This is the only set in the benchmark where the two tuned models separate.

The 8,192-token ceiling was chosen so that no arm would be truncated. On the two EA sets it achieved that for the tuned arms. On the non-EA set it did not: 14, 13 and 12 rows were cut off. Truncation counts are reported per arm and per class in the result files and are never folded into a compile-failure category.

### 184 public prompts, version 1.0.0 result, unchanged

| Arm | Compile success | Result |
|---|---:|---:|
| Base Qwen2.5-Coder-14B-Instruct | 1.09% | 2/184 |
| Fine-tuned Qwen2.5-Coder-14B-Instruct (83k corpus, bf16) | 92.39% | 170/184 |
| gpt-5.6-sol | 97.28% | 179/184 |

These are the 1.0.0 figures under the 1.0.0 serving configuration (bf16 transformers). They are not re-headlined here. The 184 prompts have been public since 1.0.0 and should be treated as a public benchmark, not as an uncontaminated set; the two holdouts above exist for that reason. The 1.0.0 card's description of these arms is carried in "The 1.0.0 arms" below.

### Stability check: the 220k arm re-run on the 200 non-EA prompts

The 220k arm was run a second time on the same 200 prompts under the same configuration. The rule was fixed before the second run started: the first run is the headline regardless of outcome, both runs publish, and neither is averaged or selected.

| | First run (headline) | Second run |
|---|---:|---:|
| Compile success, all 200 | 168/200 | 169/200 |
| Truncated | 12 | 11 |
| Per class | 31 · 50 · 39 · 48 | 31 · 50 · 40 · 48 |

By the rows' own compile verdicts, two of 200 items flipped, one in each direction, so both runs carry 169 true verdicts. The one-item difference in the table comes from the pre-registered rule (the protocol is identified under `protocol` in `publication_metadata.json` by filename and SHA-256; it is retained in the evidence package and not distributed in this release): the item that compiled despite truncation in the first run is scored as a fail there, and in the second run it did not compile.

The generated source was byte-identical on 164 of 200 items; the 36 that differed were 20 include files, 13 scripts, 2 services and 1 indicator.

Both runs used the same recorded settings; this release does not isolate the cause of the differences. An output hash in this release is provenance of the observed run where a source was produced, not a promise that a re-generation reproduces it. Both runs' rows are published.

## Q8_0 against the 1.0.0 bf16 arm

Every local arm run for v1.1 was served as a Q8_0 GGUF through llama.cpp. The 1.0.0 tuned arm was served at bf16 through transformers. To connect the two, the 83k model was re-run at Q8_0 on the 184 public prompts.

| 83k model, 184 public prompts | Result |
|---|---:|
| Q8_0, llama.cpp (this release) | 175/184 |
| bf16, transformers (1.0.0) | 170/184 |

Six items passed under Q8_0 and failed under bf16; one the other way. That is a 5-item gap, Newcombe 95% CI −0.26 to +6.28 pp, McNemar p = 0.125, not significant at n = 184. The two runs also differ in serving backend, so the difference is not attributable to quantisation alone. The bf16 arm is the 1.0.0 tuned arm as published, identified by the weight hashes under `models.tuned.merged_weights` and `model_identities.tuned_83k` in `publication_metadata.json`; this release did not re-verify those weights. The 1.0.0 figures stand as published; the Q8_0 re-run of the 184 is published as a bridge row set, not as a replacement.

The base arm was also re-run at Q8_0 on the 184 (2/184 with 2 truncated, the same two passing items as 1.0.0, which truncated none), and the 220k arm was run on them (169/184, 0 truncated). Those rows ship in the bridge file for completeness. The 184-item set is public, so none of these is a holdout figure.

## Run the benchmark

The 184 public prompts are in `prompts.jsonl`. Render each prompt with the Expert Advisor system prompt and the template in `serving_template.json`, generate MQL5, compile it, and record the verdict using the schema in `per_item_results.jsonl`. Every published run of the 184 used the Expert Advisor system prompt for all 184 items, including the six whose specification header declares another type; a reproduction that follows that rule reproduces the published request hashes.

The system prompt for the 184 public prompts and for the 300 EA holdout:

```text
You are an expert MQL5 programmer. Write the complete MQL5 Expert Advisor code that implements the given specification exactly.
```

The serving template:

```text
<|system|>{system_prompt}<|end|>\n<|user|>{prompt}<|end|>\n<|assistant|>
```

`\n` is a real newline. The `template` field in `serving_template.json` holds actual newline characters, so a JSON parser returns the correct string without further unescaping.

The 200 non-EA holdout items use the same sentence with the unit noun replaced, by the class of the set they were drawn into, never by the specification header. The four strings are published in `serving_template.json` and are, verbatim:

```text
You are an expert MQL5 programmer. Write the complete MQL5 include file code that implements the given specification exactly.
You are an expert MQL5 programmer. Write the complete MQL5 custom indicator code that implements the given specification exactly.
You are an expert MQL5 programmer. Write the complete MQL5 script code that implements the given specification exactly.
You are an expert MQL5 programmer. Write the complete MQL5 service code that implements the given specification exactly.
```

The holdout prompts are not published. A reader can evaluate any model on the 184 public prompts under the published contract. The holdout results are attested by per-item hashes, not independently reproducible; see "What is public and what is not".

`verify_public_release.py` ships in this release and checks release hashes, item pairing, row counts, contingency tables, and headline result counts. It needs Python 3.9+ and nothing else. Run it from the release directory:

```text
python verify_public_release.py --public .
```

## Scoring contract

Two verdicts are computed for every item that reached compilation and published side by side. On the three frontier rows where generation failed before compilation (the API returned HTTP 500), both verdicts are null.

- `verdict_headline` — true when the compile log reports zero errors and the .ex5 artifact was produced.
- `verdict_strict` — true when the compile log reports zero errors and zero warnings and the .ex5 artifact was produced.

Each row carries one of four buckets, assigned in this order. A generation error is an infrastructure failure. Otherwise a truncated response is TRUNCATED. Otherwise a compile-side infrastructure reason is an infrastructure failure. Everything else is compile-pass or compile-fail from `verdict_headline`.

A TRUNCATED or INFRASTRUCTURE-FAILURE row counts as a fail in the headline figure and is dropped from the denominator in the second figure printed beside it. One row in the release compiled despite being truncated (a 220k include-file generation in the first non-EA run); the pre-registered rule scores it as a fail, which is why that arm shows 168 passes where 169 rows carry a true verdict. Both numbers are in the result files.

Extraction (`three_way.v4`): truncate the response at the first serving end-token; find every fenced code block; if none, use the whole response; otherwise take the first block that defines a real MQL5 event handler, falling back to the first block. The chosen index is published per row as `used_block_index` in `per_item_results.jsonl` and `bridge_q8_184_results.jsonl`. It is null where `n_fenced_blocks` is 0, which is every tuned-arm row in those two files: the tuned models answer with bare code, so the whole response was used and there was no block to index. The holdout row files do not carry it, so holdout extraction choices are not row-auditable from this release. The same extraction runs on every arm.

Compile logs are UTF-16LE with a byte-order mark and must be decoded before matching. A diagnostic is a line matching `(line,col): error N:` or `(line,col): warning N:`. A log without the compiler's own `Result: N errors, M warnings` line is an infrastructure failure, never a model result.

MQL5 outputs were compiled using the MetaQuotes Language Compiler through MetaEditor, build 5836, the same build for every arm in this release and in 1.0.0. Include-file items are compiled through a minimal caller that includes them, since an include file alone produces no EX5.

The harness, the extractor and the scorer are not distributed, and neither is the compiler. The rules above describe what they do at the level published here; details below that level are not published, so an independent implementation may score individual items differently. Before an arm is scored, two known fixtures are compiled: one that must produce an error, one that must produce a warning and still build. The harness writes no rows for an arm whose control fails. The 1.0.0 rows and the bridge rows carry the control's error and warning counts, which attest that the control ran; the holdout row files do not carry them. The fixture inputs and the control's compiler output were not retained, so the control itself cannot be audited from this release, and no known-answer validation record for the extractor is retained either.

## Serving configuration

Local arms, this release:

- Engine: llama.cpp `llama-server` build 10441 (commit `0177dcc73`, Clang 20.1.8, Windows x86_64), Q8_0 GGUF, Vulkan backend, 8 parallel slots, 69,632-token context, all layers offloaded (`-ngl 999`), 8 concurrent requests per arm. Launch line, verbatim: `llama-server.exe -m <gguf> -np 8 -c 69632 -ngl 999 --device Vulkan0 --host 127.0.0.1 --port 8088`.
- Host: Windows 11 Pro 10.0.26200, AMD graphics driver 32.0.31036.15 (2026-08-12). No environment variables were set for the server. Python-side library versions were not recorded and are a gap.
- Decoding: temperature 0.0, top-k 1 and seed 42 sent with every request, 8,192 max new tokens. The harness records what it sent; whether the server applied every setting as sent is not independently verified by this release.
- Hardware: one AMD Radeon AI PRO R9700 in an AMD Ryzen 9 7950X3D host with 64 GB of system memory. The device is not recorded in the run parameters; it is stated from the evaluation host's configuration.

The frontier arm, `gpt-5.6-sol`, was evaluated on the 300 EA holdout on 2026-09-11 through the vendor API, one request at a time. That is a statement about concurrency and not about HTTP attempts: one item was in flight at a time. The harness set no retry policy and no client-side timeout for this arm, so any transport retry behind a single request was whatever the vendor's Python client library did by default, and that library's version was not recorded. The three rows that returned HTTP 500 are items whose request failed after whatever the client attempted. The request asked for temperature 1.0 and seed 42 and sent the same 8,192-token cap as `max_completion_tokens`; whether the service applied those settings is not recorded. The system-prompt text and the item text were sent as separate system and user fields; the local arms received them rendered into one serving template. The local arms were run with greedy settings requested, at concurrency 8. The frontier result is a single run of a sampled decoder identified by model name and evaluation date, and a rerun may differ item for item. The two serving and decoding configurations differ, and the head-to-head is a comparison across those configurations, not a configuration-matched one.

## Statistics

Rate intervals are Wilson score intervals without continuity correction, and paired differences use Newcombe's square-and-add method with the exact-binomial McNemar test on discordant pairs. Two z values are in force, one per release: every interval computed for this release uses z = 1.959963984540054, the two-sided 95% normal quantile at full precision, while the intervals carried forward from 1.0.0 were computed with the rounded z = 1.96 and are republished exactly as 1.0.0 published them. `publication_metadata.json` records both under `interval_conventions`. Every arm ran the same prompts, so no comparison in this release treats two arms as independent samples. Full-precision values, contingency tables and the paired-bootstrap record are in `publication_metadata.json`. Every statistic in the tables above recomputes from the published row files. Two metadata blocks do not: the 183-item precision check, which needs the identity of the one excluded item (not published), and the 19-item replay on the public set, whose rows are not in the release. The bootstrap is recorded, not recomputable.

Per-set paired movement between the two tuned models, 220k against 83k:

| Set | Pairs | 220k gains | 220k loses | Difference | p |
|---|---:|---:|---:|---:|---:|
| 184 public (both at Q8_0) | 184 | 6 | 12 | −3.26 pp | 0.24 |
| 300 EA holdout | 300 | 18 | 17 | +0.33 pp | 1.0 |
| 200 non-EA holdout | 200 | 49 | 16 | +16.50 pp | 5.1e-5 |

On EA prompts the two models move items in both directions in roughly equal numbers. On non-EA prompts the movement strongly favours the 220k model: 49 items moved its way, 16 the other. The three sets are different populations and their rates are not comparable with each other.

## Evaluation sets

The 184 public prompts are unchanged from 1.0.0. All 184 were run under the Expert Advisor instruction, in 1.0.0 and in the bridge; six of them declare another type in their specification header (item_009, item_089 and item_102 script; item_093 and item_134 indicator; item_167 include) and were run under that same instruction regardless; `publication_metadata.json` lists them under `public_set_184_composition`. They are a decontaminated stratum of a frozen 300-item draw, selection rule and hashes as published there and carried in `publication_metadata.json`.

The 300 EA holdout was drawn from a private pool of 1,000 EA items held out of training. The items with a normalised-exact match to the 220k corpus were removed (352 of 1,000), leaving 648. The first 300 in the pool's frozen order were taken. The manifest's identity hash is published; the prompts and item names are not. This pool was scanned against the 220k corpus only; no scan of it against the 83k corpus exists, so the 83k arm's holdout figures carry no decontamination evidence of their own.

The 200 non-EA holdout was drawn from a private pool of 600 withheld non-EA items, 150 per class, the 21 items with a normalised-exact match to the 220k corpus were removed before the draw (20 scripts, 1 service), then the first 50 of each class in the pool's own order were taken. Manifest identity hashes are published; prompts and names are not. The same scan scope applies: this pool was checked against the 220k corpus, not the 83k corpus. One specification appears in both the 184 public set (run under the Expert Advisor instruction) and this set (run under the indicator instruction); it is identified by hash in the metadata, and the overlap is one item of 200.

Both holdouts were frozen before any arm ran and were not redrawn. The stability re-run above used the same 200 items.

## Decontamination

Every evaluation set was scanned against the 220k corpus, and the 184 public items also keep their 1.0.0 scan against the 83k corpus. No holdout was scanned against the 83k corpus. The two methods are those published in 1.0.0: exact SHA-256 equality of the reference solution against every training row, and equality after a domain normaliser that strips comments and canonicalises names, magic numbers, timeframe and price constants, indicator periods, risk multipliers and symbol literals. No similarity threshold decides membership.

Every scan carries three known-positive fixtures and one falsifying twin, and all passed: a verbatim duplicate was caught by both methods, a cosmetic variant and a line-ending variant by the normalised method only, and the twin by neither. Twelve fixture records are retained in the evidence package and are not distributed: four for the 2026-08-19 scan, four for the 2026-09-10 scan that covered the public 184 and the 1,000-item EA pool together, and four for the 2026-09-11 scan of the 600-item non-EA pool. All twelve are named with their SHA-256 in `publication_metadata.json` under `decontamination.known_answer_validation` and `decontamination.known_answer_validation_scope`, and the two later scans also carried their known positives and their twin through the full corpus pass rather than a fixture sample alone. The two pool scans behind the third and fourth rows of the table below are named and hashed there as well, under `decontamination.holdout_pool_scans`; that is where the 352, the 21 and the split of the 21 into 20 scripts and 1 service are recorded.

Both methods are scored on the reference-solution side. The specification text was scanned as well, and only its exact result is scored, at zero collisions: the specifications are entirely comment lines, the normaliser strips comments first, so every specification normalises to the empty string and a normalised-exact count on that side would measure the instrument, not the corpus. The retained scan records that result as escalated rather than scored, and which side the stop conditions bind on is left unsettled.

| Set | Corpus | Exact | Normalised-exact | Action |
|---|---|---:|---:|---|
| 184 public | 83k (83,155 rows) | 0 | 116 of 300 | removed, leaving 184 (1.0.0) |
| 184 public | 220k (215,541 rows) | 0 | 1 of 184 | reported; nothing removed |
| 1,000 EA pool | 220k | 0 | 352 of 1,000 | removed before the 300 draw |
| 600 non-EA pool | 220k | 0 | 21 of 600 | removed before the 200 draw |

The 184-item scan against the 83k corpus cannot be re-run today; the corpus file it read no longer exists, and its hash was established by that run. It was re-run once, on 2026-08-31, from an archived copy at the same hash, and agreed; that copy is also gone. The metadata records that event under `reproduction_gate`. The one 184-item collision against the 220k corpus is reported, not removed, so the 220k arm's 169/184 bridge figure includes one item with a normalised twin in its corpus.

A descriptive similarity curve was also computed for each scan by a candidate-based matcher whose figures are lower bounds; it is retained with the evidence and is not part of this release. Contamination in this release means an exact or normalised-exact collision, and those counts are in the table above.

The evaluation prompts come from the same specification generator family as the training corpus, so the benchmark measures in-distribution competence on that family's specification style, not generalisation to human-written specifications.

## Models

Base: `Qwen/Qwen2.5-Coder-14B-Instruct`, pinned revision `aedcc2d42b622764e023cf882b6652e646b95671`, quantised to Q8_0 for this release.

Tuned, 83k: the 1.0.0 fine-tuned model (one epoch on 83,155 rows, corpus SHA-256 `5e9881b61f3375d3d575c35950a236375eb5648f5fe55b8d18de321f69659c68`), merged and quantised to Q8_0.

Tuned, 220k: the same base fine-tuned for one epoch on a 215,541-row corpus, SHA-256 `3c2f57db5986eaac49f7ae5ed6732e1ae702b339b1354bf3d94e33c7b611e023`, merged and quantised to Q8_0. Adapter, merge and GGUF identities are pinned by SHA-256 in `publication_metadata.json`. For the 220k model the one-epoch figure comes from the training plan; no trainer-state epoch or global step was read for it, and the metadata says so. For the 83k model the epoch and global step were read from trainer state. Two historical merges of the 83k model from the same inputs in the same environment produced byte-identical weights. Cross-environment reproduction was not performed for either tuned model. A row-content hash manifest ships as `corpus_row_hashes.json`: 219,867 row hashes, no contents, no names. The 215,541-row corpus the model was trained on is the subset of those rows that passed a maximum-length rule; the 4,326 other hashes are the rows that rule dropped. The threshold is not published and this release did not check the subset row by row, so the check a counterparty holding the corpus can make is that every row they hold hashes to a member of the manifest. No one else can verify it.

Frontier: `gpt-5.6-sol` through the vendor API, identified by model name and evaluation date (2026-09-02 on the 184; 2026-09-11 on the 300).

Model weights are not distributed in any version of this release.

## The 1.0.0 arms

The 1.0.0 local arms were served through Hugging Face transformers at bf16 with greedy decoding, on the same hardware. The two local arms shared one prompt template, the tuned model's training format; a quantised base-model control comparing that template against the base's native ChatML format changed one verdict out of 183 jointly scoreable items, in the shared template's favour. The 1.0.0 frontier arm ran on 2026-09-02 with temperature 1. The 1.0.0 base-vs-tuned contingency table is 1/1/169/13 (both pass / base only / tuned only / both fail), McNemar p = 2.29e-49; tuned-vs-frontier is 168/2/11/3, p = 0.0225. Those figures and their intervals are unchanged in `publication_metadata.json`.

## Hash definitions

`prompt_sha256_public` is the SHA-256 of the UTF-8 encoding of the prompt exactly as published in `prompts.jsonl`. Holdout rows carry `item_sha256`, the SHA-256 of the UTF-8 specification text, as their only item identity; the text itself is not published.

`prompt_sha256` is an arm-specific request-content hash. On local rows it hashes the rendered serving template. On frontier rows it hashes the system prompt, two newline characters, then the prompt. The verifier recomputes both rules on the 184 public rows of `per_item_results.jsonl`. On the holdout and bridge files it checks row counts, arm identities, headline and truncation counts and item pairing. On the two holdout files it cannot recompute a prompt hash because the holdout prompts are not published. On the bridge file the prompts are the 184 public prompts, so each row's `prompt_sha256` equals the local-arm value on the matching 1.0.0 row and can be checked by that equality; the verifier does not recompute it there.

`mq5_sha256` and `ex5_sha256` are commitments to the generated source and compiled artifact of a row. `mq5_sha256` is present on every row; on the seven frontier rows where no source was extracted (three API failures and four ceiling truncations) it holds the SHA-256 of zero bytes, `e3b0c442…`, and commits to nothing. `ex5_sha256` is present only on rows where an EX5 artifact was produced and is null on the rest. Those artifacts are not distributed; the hashes permit integrity verification if they are later disclosed under agreement.

## What is public and what is not

| Claim or artifact | Publicly verifiable |
|---|---|
| The 184 published prompts and their hashes | Yes |
| Per-arm result arithmetic and statistics, every set | Yes |
| Running a new model on the 184 prompts | Yes |
| Holdout prompts, item names, and running a model on them | No |
| Original generated MQL5 and compiler logs | No |
| Tuned model outputs and weights | No |
| Training-corpus contents and decontamination scans | No |
| Exact original harness behaviour | No |

The holdout results are attested, not fully verifiable. Every holdout row is published as item hash, arm, verdicts, bucket, error and warning counts, truncation flag and output hashes. The arithmetic can be checked. Rows with a generated source are bound to the retained source and compiler output by hash; the seven frontier rows with no extracted source are bound only to their item and request identity and to the recorded failure. No third party can regenerate any of them from this release. Access to undistributed material is available under written agreement.

## Files

| File | Content |
|---|---|
| `README.md` | this card |
| `prompts.jsonl` | 184 public prompt rows (1.0.0) |
| `per_item_results.jsonl` | 552 rows: 184 base, 184 tuned, 184 frontier (1.0.0, bf16) |
| `holdout_ea300_results.jsonl` | 1,200 hash-keyed rows: base, 83k, 220k, frontier on the 300 EA holdout |
| `holdout_nonea200_results.jsonl` | 800 hash-keyed rows: base, 83k, 220k and the 220k re-run on the 200 non-EA holdout |
| `bridge_q8_184_results.jsonl` | 552 rows: base, 83k and 220k at Q8_0 on the 184 public prompts |
| `serving_template.json` | system prompts (EA and the four non-EA classes) and serving template |
| `publication_metadata.json` | release metadata, full-precision statistics, model and manifest identities |
| `corpus_row_hashes.json` | 219,867 row-content hashes of the 220k corpus, no contents |
| `PROJECTION_REPORT.json` | row-projection record, field inventory, hash definitions |
| `verify_public_release.py` | the release verifier |
| `SHA256SUMS.txt` | checksum manifest over every file except itself |
| `LICENSE`, `CITATION.cff`, `.gitattributes` | licence, citation metadata, line-ending pin |

File hashes are in `SHA256SUMS.txt`. The hashes cover the files as stored, with LF line endings; `.gitattributes` pins that so checkout does not rewrite them. The per-row field dictionary is in `PROJECTION_REPORT.json`.

## Limitations

- Compilation is a low bar. It is a necessary, not a sufficient, condition for useful code. Nothing in this release measures whether any generated artifact is correct, useful, or safe to run.
- A single language, with no claim of transfer.
- The prompts are generator-produced, not harvested from human-written production code, and come from the same generator family as the training corpus. This measures in-distribution competence; it is not a test of generalisation to human-written specifications.
- The frontier arm is a moving target; its snapshot dates bound the comparison.
- The 8,192-token ceiling truncated rows on the non-EA set. Whether an item the model would have finished past that ceiling should count against it is a judgement this release makes one way (it counts as a fail).
- The holdout sets are private, so their results are attested by hash rather than reproducible.
- Each non-EA class cell is 50 items.
- Token counts for the training corpora are not published; row counts and corpus hashes are.
- The harness, extractor and scorer are not distributed. An independent implementation of the scoring contract may score individual items differently.
- Merge determinism rests on two historical merges of the 83k model, not on a fresh remerge.

## Licence

The benchmark files are provided under the CompilingThings Benchmark Evaluation Licence v1.0. The summary below is non-exhaustive; LICENSE controls in the event of any conflict.

Permitted: running the 184 published prompts against any model; checking, citing and comparing the published result rows and the corpus row-hash manifest, including the holdout row files; implementing and using the published scoring contract; publishing and comparing benchmark results, including results that disagree with ours; citing the benchmark and release identifier. The supporting files may be reproduced and quoted for using, checking or citing the benchmark, and `verify_public_release.py` may be run as-is.

Not permitted: using the prompts for training, fine-tuning, continued pretraining, distillation, or reinforcement learning; incorporating the prompts or result rows into another dataset; creating or selling derivative datasets; representing the benchmark as your own work.

Commercial licences, evaluation access, research collaboration and partnership are arranged individually under written agreement.

## Contact

Identity: CompilingThings. For evaluation access, research collaboration, commercial licensing, or partnership, open a discussion on the Hugging Face dataset repository.

## Citation

`CITATION.cff` ships with the release and identifies CompilingThings as the author of version 1.1.0.

## MetaQuotes notice

MQL5® and MetaTrader 5® are registered trademarks of MetaQuotes Ltd. CompilingThings is an independent project. No affiliation, sponsorship, certification, endorsement, or approval by MetaQuotes Ltd. is claimed.

MQL5 outputs were compiled using the MetaQuotes Language Compiler through MetaEditor. This release does not distribute MetaTrader 5, MetaEditor, compiler binaries, MetaQuotes documentation, or other MetaQuotes-owned materials. The benchmark prompts published in this release were produced by CompilingThings' own generators and are owned by CompilingThings. No model-generated MQL5 source or other model outputs are distributed.
