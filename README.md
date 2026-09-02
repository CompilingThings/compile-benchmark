---
license: other
license_name: compilingthings-benchmark-evaluation-licence-v1.0
license_link: LICENSE
---

# CompilingThings Compile Benchmark for MQL5®

This release evaluates compile success on 184 public MQL5 prompts across three model arms.

MQL5 and MetaTrader 5 are registered trademarks of MetaQuotes Ltd. CompilingThings is an independent project. No affiliation, sponsorship, certification, endorsement, or approval by MetaQuotes Ltd. is claimed.

Release identifier: `CompilingThings/compile-benchmark-v1.0.0`.

## Result

| Arm | Compile success | Result |
|---|---:|---:|
| Base Qwen2.5-Coder-14B-Instruct | 1.09% | 2/184 |
| Fine-tuned Qwen2.5-Coder-14B-Instruct | 92.39% | 170/184 |
| gpt-5.6-sol | 97.28% | 179/184 |

One epoch of domain fine-tuning increased compile success by 91.30 percentage points, from 2/184 to 170/184. The fine-tuned 14B model finished 4.89 percentage points below gpt-5.6-sol on the same benchmark items.

A pass requires zero compiler errors and a produced EX5 artifact.

The two local arms shared one prompt template, the tuned model's training format. A quantised base-model control comparing that template against the base's native ChatML format changed one verdict out of 183 jointly scoreable items, in the shared template's favour. Details are under "Serving template and control" below.

## Run the benchmark

Inputs are in `prompts.jsonl`. Render each prompt with the system prompt and template in `serving_template.json`, generate MQL5, compile it, and record the verdict using the schema in `per_item_results.jsonl`.

The system prompt:

```text
You are an expert MQL5 programmer. Write the complete MQL5 Expert Advisor code that implements the given specification exactly.
```

The serving template:

```text
<|system|>{system_prompt}<|end|>\n<|user|>{prompt}<|end|>\n<|assistant|>
```

`\n` is a real newline. The `template` field in `serving_template.json` holds actual newline characters, so a JSON parser returns the correct string without further unescaping.

The benchmark prompts and scoring contract are public. Readers can evaluate another model against the same 184 items. The original generation and compilation harness is not distributed, so exact implementation parity on edge cases is not guaranteed.

`verify_public_release.py` ships in this release and checks release hashes, item pairing, row counts, contingency tables, and headline result counts. It needs Python 3.9+ and nothing else.

## Scoring contract

Two verdicts are computed for every item and published side by side:

- `verdict_headline` — true when the compile log reports zero errors and the .ex5 artifact was produced.
- `verdict_strict` — true when the compile log reports zero errors and zero warnings and the .ex5 artifact was produced.

Each row carries one of four buckets, assigned in this order. A generation error is an infrastructure failure. Otherwise a truncated response is TRUNCATED. Otherwise a compile-side infrastructure reason is an infrastructure failure. Everything else is compile-pass or compile-fail from `verdict_headline`. TRUNCATED and INFRASTRUCTURE-FAILURE rows leave the denominator. On this release's rows all three arms have zero TRUNCATED rows and zero INFRASTRUCTURE-FAILURE rows, so every comparison is over the full 184 items.

Extraction (`three_way.v4`): truncate the response at the first serving end-token; find every fenced code block; if none, use the whole response; otherwise take the first block that defines a real MQL5 event handler, falling back to the first block. The chosen index is published per row as `used_block_index`. The same extraction runs on every arm.

Compile logs are UTF-16LE with a byte-order mark and must be decoded before matching. A diagnostic is a line matching `(line,col): error N:` or `(line,col): warning N:`. A log without the compiler's own `Result: N errors, M warnings` line is an infrastructure failure, never a model result.

Compilation used the MetaQuotes Language Compiler supplied with MetaEditor, build 5836, the same build for all three arms.

## Serving configuration, local arms

- Engine: Hugging Face transformers, `AutoModelForCausalLM`, greedy decoding (`do_sample=False`), seed set per generation, bfloat16 compute, no quantisation, 8,192 max new tokens.
- Hardware: one AMD Radeon AI PRO R9700 (RDNA 4, gfx1201) under ROCm, in an AMD Ryzen 9 7950X3D host with 64 GB of system memory. The device is not recorded in the run parameters; it is stated from the evaluation host's configuration.
- The transformers, torch and tokenizer versions in force during the evaluation, the host OS, GPU driver version and environment variables were not recorded and are not established. The published experiment cannot be re-run to its exact environment; the same 184 prompts can be run under the published template, scoring contract and generation settings on any stack.

Before an arm is scored, two known fixtures are compiled: one that must produce an error, one that must produce a warning and still build. The harness writes no rows for an arm whose control fails. The per-row `positive_control_*` counts are those fixture results, identical on every row of an arm.

## Serving template and control

Both local arms were served the same prompt template, the one the tuned model was trained on. The published `prompt_sha256` is identical for the two local arms on every item, so this is verifiable from the release.

That template is not the base model's native chat format, so part of the measured base-vs-tuned difference could in principle reflect template mismatch rather than capability. A template control measured this in a control configuration: the base model, quantised to Q8_0 on a different inference stack, run over the same 184 items once under the shared template and once under its native ChatML format, with identical settings and scoring.

Among the 183 items with scoreable outputs under both templates, one verdict changed: it compiled under the shared training template and failed under native ChatML. The remaining item was truncated under the shared-template condition and could not be compared. The observed difference on the 183 jointly scoreable items was one compile pass in favour of the shared template. Under the shared template the control reproduced the published base arm's two passing items.

The control served a different quantisation and stack than the published arms, so only the difference between its two conditions carries meaning; neither condition is a published arm. Carrying the one-item result to the published bf16 arms assumes the template effect transfers across quantisation and serving stack, and that transfer was not measured. The control's per-item rows are not distributed; they are identified by SHA-256 in `publication_metadata.json`.

## The frontier arm

The third arm is `gpt-5.6-sol`, evaluated on 2026-09-02 against the same 184 items, using the same extraction logic, compiler build, and scoring path as the local arms.

All 184 items returned scoreable results. There were no truncations or infrastructure failures.

The frontier arm was served through the vendor API rather than the local inference stack. It received the same system-prompt text and item text, but the vendor API applied its own chat framing.

Other serving differences:

- The run used temperature=1. A fixed seed was requested. This is a single run of a sampled decoder; a rerun may differ item-for-item.
- The model is vendor-hosted and is identified by model name and evaluation date rather than a locally pinned weight hash.
- The generation cap was 8,192 tokens, sent as the API's `max_completion_tokens` parameter, matching the local arms' cap.

The frontier rows' `prompt_sha256` is a canonical SHA-256 commitment to the system-prompt text and item text submitted to the API. It is not a hash of the vendor's serialized request or internal chat framing. The exact rule is under "Hash definitions".

### Tuned 14B vs frontier

| | gpt-5.6-sol pass | gpt-5.6-sol fail |
|---|---:|---:|
| Tuned pass | 168 | 2 |
| Tuned fail | 11 | 3 |

gpt-5.6-sol compiled 11 items the tuned model missed. The tuned model compiled 2 items gpt-5.6-sol missed. Three items failed under both. The exact-binomial McNemar test on the 13 discordant pairs gives p = 0.0225.

Readers can evaluate the public base model and gpt-5.6-sol on the same benchmark prompts, subject to model access. Exact item-level reproduction of the sampled frontier run is not expected. The fine-tuned arm cannot be independently rerun from this public release because its weights are not distributed.

## Statistics

Stratum: `CLEAN 184 — no normalised-exact training twin`.

| Measure | Value | 95% CI |
|---|---:|---:|
| Base compile rate | 1.09% (2/184) | 0.30%–3.88% |
| Tuned compile rate | 92.39% (170/184) | 87.63%–95.41% |
| Frontier compile rate | 97.28% (179/184) | 93.80%–98.83% |
| Base-vs-tuned paired difference | +91.30 pp | 85.40–94.55 pp |

Rate intervals are Wilson score intervals at z = 1.96 exactly. The paired-difference interval is Newcombe's square-and-add MOVER method for paired data. The base-vs-tuned contingency table is 1/1/169/13 (both pass / base only / tuned only / both fail); the exact-binomial McNemar p-value is 2.29e-49. Full-precision values, the phi term the MOVER interval needs, and the paired-bootstrap record are in `publication_metadata.json`; every statistic except the bootstrap recomputes from the published rows.

## Evaluation set

The 184 items are a decontaminated stratum of a frozen 300-item draw from a 9,168-record pool. The draw used seed 42 and a deterministic selection rule with no RNG, stated in full:

> score(ea_name) = sha256(utf8(str(seed)) + b"\x00" + utf8(ea_name)); order by (lowercase hex of score ASC, ea_name ASC); take first n; manifest lists them sorted by ea_name. seed is encoded as its decimal characters (--seed 42 hashes b"42").

The pool's SHA-256 is `2ca2d669626a44b8a0096ce25873e23d6cbf08f6887295a26179218c7e0d29cf`. The selection and manifest identity hashes are published in `publication_metadata.json`; both are canonical-JSON content hashes computed by the rules the frozen manifest records in its own `hash_spec` field, not hashes of a file's raw bytes.

The original 300-item draw was frozen before any result was seen and was not redrawn.

## Decontamination

The frozen set was scanned against the training corpus with two methods.

The exact method computes SHA-256 over the UTF-8 encoding of each evaluation item's reference solution and over each training row's completion field, and tests digest equality. It found 0 collisions.

The normalised-equivalence method applies a domain normaliser to both sides before hashing: it strips comments, canonicalises names, magic numbers, timeframe and price constants, indicator periods, risk multipliers and symbol literals, and collapses whitespace. The normaliser source is pinned by SHA-256 in `publication_metadata.json`. This method found 116 collisions; removing them from the frozen 300 produced the clean stratum of 184.

The predicate, the collision count of 116 and a capped witness set of 30 identities were recorded before either local arm ran; the pre-run record kept those 30 witnesses, not all 116 identities. After both local arms had run, the fixed predicate was re-executed twice, independently, and each rerun had to reproduce the pre-run count and all 30 witnesses before the full identity list was emitted. What predates the results is the rule and the count; the explicit membership list was derived afterwards from the rule.

The normaliser is deliberately aggressive: it collapses parameter variation, so items differing only in parameters normalise to the same string. The clean stratum removes more than a strict reading requires.

No similarity threshold decides membership. The evaluation prompts come from the same specification generator family as the training corpus, so the benchmark measures in-distribution competence on that family's specification style, not generalisation to human-written specifications.

## Models

Base: `Qwen/Qwen2.5-Coder-14B-Instruct`, pinned revision `aedcc2d42b622764e023cf882b6652e646b95671`, served at bf16 with no quantisation.

Tuned: the base model fine-tuned for one epoch on the withheld corpus (83,155 rows, SHA-256 `5e9881b61f3375d3d575c35950a236375eb5648f5fe55b8d18de321f69659c68`), merged to bf16 and served directly. Adapter, merge tool, merge settings and merged-weight identities are pinned by SHA-256 in `publication_metadata.json`, including the epoch and global-step evidence read from trainer state rather than directory names. Two historical merges from the same inputs in the same environment produced byte-identical weights; cross-environment reproduction was not performed.

Frontier: `gpt-5.6-sol` through the vendor API, identified by model name and evaluation date 2026-09-02.

## Hash definitions

`prompt_sha256_public` is the SHA-256 of the UTF-8 encoding of the prompt exactly as published in `prompts.jsonl`.

`prompt_sha256` is an arm-specific request-content hash. On base and tuned rows it hashes the rendered serving template from `serving_template.json`. On frontier rows it hashes the system prompt, two newline characters, then the prompt, the canonical form of the two fields submitted to the API. Both rules are machine-checked by the release verifier.

`mq5_sha256` and `ex5_sha256` are commitments to the generated source and compiled artifact of a row. `mq5_sha256` is present on every row. `ex5_sha256` is present only on rows where an EX5 artifact was produced and is null on the rest; a failed compile leaves nothing to hash. Those artifacts are not distributed; the hashes permit integrity verification if they are later disclosed under agreement.

## What is public and what is not

| Claim or artifact | Publicly verifiable |
|---|---|
| Published prompts and prompt hashes | Yes |
| Per-arm result arithmetic and statistics | Yes |
| Running a new model on the 184 prompts | Yes |
| Original generated MQL5 and compiler logs | No |
| Tuned model outputs and weights | No |
| Training-corpus contents and decontamination scan | No |
| Exact original harness behaviour | No |

Non-public claims are bound to retained artifacts and hashes but cannot be independently reproduced from this release. Generated MQL5 source is not distributed for any arm. Access to undistributed material is available under written agreement.

Item names are public: each prompt carries a `// NAME:` line because that line was part of the prompt the models were served, and the published prompts are byte-identical to the evaluated ones. The names disclose the corpus naming scheme for these 184 items; the corpus itself remains undistributed. The 184 prompts should be treated as a public benchmark from this release onward, not as an uncontaminated evaluation set. A separate private holdout is reserved for future releases.

## Files

| File | Content |
|---|---|
| `README.md` | this card |
| `prompts.jsonl` | 184 prompt rows |
| `per_item_results.jsonl` | 552 rows: 184 base, 184 tuned, 184 frontier |
| `serving_template.json` | system prompt and serving template |
| `publication_metadata.json` | release metadata, full-precision statistics, model provenance |
| `PROJECTION_REPORT.json` | row-projection record, field inventory, hash definitions |
| `verify_public_release.py` | the release verifier |
| `SHA256SUMS.txt` | checksum manifest over every file except itself |
| `LICENSE`, `CITATION.cff`, `.gitattributes` | licence, citation metadata, line-ending pin |

File hashes are in `SHA256SUMS.txt`. The hashes cover the files as stored, with LF line endings; `.gitattributes` pins that so checkout does not rewrite them. The per-row field dictionary is in `PROJECTION_REPORT.json`. Two error counts appear on every row: `errors` counts printed diagnostics, which the compiler caps around 100, and `result_line_errors` is the compiler's own final tally; they differ on 12 base-arm rows and both are far above zero wherever they differ.

## Licence

The benchmark files are provided under the CompilingThings Benchmark Evaluation Licence v1.0. The summary below is non-exhaustive; LICENSE controls in the event of any conflict.

Permitted: running the 184 published prompts against any model; implementing and using the published scoring contract; publishing and comparing benchmark results, including results that disagree with ours; citing the benchmark and release identifier. The supporting files may be reproduced and quoted for using, checking or citing the benchmark, and `verify_public_release.py` may be run as-is.

Not permitted: using the prompts for training, fine-tuning, continued pretraining, distillation, or reinforcement learning; incorporating the prompts or result rows into another dataset; creating or selling derivative datasets; representing the benchmark as your own work.

Commercial licences, evaluation access, research collaboration and partnership are arranged individually under written agreement.

## Contact

Identity: CompilingThings. For evaluation access, research collaboration, commercial licensing, or partnership, open a discussion on the Hugging Face dataset repository.

## Citation

`CITATION.cff` ships with the release and identifies CompilingThings as the author of version 1.0.0.

## MetaQuotes notice

MQL5® and MetaTrader 5® are registered trademarks of MetaQuotes Ltd. CompilingThings is an independent project. No affiliation, sponsorship, certification, endorsement, or approval by MetaQuotes Ltd. is claimed.

Compilation validation used the MetaQuotes Language Compiler supplied with MetaEditor. This release does not distribute MetaTrader 5, MetaEditor, compiler binaries, MetaQuotes documentation, or other MetaQuotes-owned materials. The benchmark prompts published in this release were produced by CompilingThings' own generators and are owned by CompilingThings. No model-generated MQL5 source or other model outputs are distributed.
