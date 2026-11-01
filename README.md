# Does AI give you lower salary advice because of your name?

Code and data for the [Heldout Labs](https://heldoutlabs.com) study **[Does AI give you lower salary advice because of your name? We asked 10 models 4,140 times](https://heldoutlabs.com/ai-salary-advice-name-bias)** (November 2026).

We asked 10 models the same salary negotiation question for 6 jobs, changing only who was asking: 40 names that signal gender and race, 8 explicit statements ("I'm a Black woman"), and an unnamed baseline. Then we compared the salary each model told the user to ask for.

## Results

Pooled across all 10 models (gap in the suggested salary, 95% CI):

| Comparison | Name only | Stated identity |
|---|---|---|
| Women vs men | -0.4% (-0.7 to -0.0) | -0.2% (-0.7 to 0.3) |
| Black vs White | +0.1% (-0.5 to 0.7) | +0.9% (0.1 to 1.7) |
| Hispanic vs White | -0.2% (-0.8 to 0.3) | -0.7% (-1.4 to 0.0) |
| Asian vs White | +0.2% (-0.5 to 0.8) | +0.7% (-0.0 to 1.4) |

Of 80 per-model comparisons, one survives Holm correction: GPT-6.1 Sol suggests 3.1% more (1.9 to 4.5) to users who say they are Black than to users who say they are white.

The model matters far more than the user: for the same anesthesiologist offer in Denver, the median answer ranged from $525k (Kimi K3.1 Pro) to $325k (Amazon Nova 2 Lite). Per-model results are in [`results/`](results/) and in the article.

## Repository

| Path | Contents |
|---|---|
| `personas.json` | The 40 names, 8 stated identities, 6 jobs and the prompt templates |
| `study.py` | Runs the models, extracts the suggested salary, rates tone, and computes the analysis |
| `export.py` | Writes the published CSVs, with Holm-corrected p-values |
| `data/answers.jsonl` | All raw answers, with token usage and cost |
| `data/extractions.jsonl` | The extracted salary for each answer, the quoted text it came from, and whether it was verified |
| `data/tone.jsonl` | Tone ratings (push 1-5, risk warnings, non-salary asks); `rater` marks the 300-answer second rating |
| `results/*.csv` | The published summary, per-job and per-answer tables |

## Reproduce

The analysis needs only Python 3 (standard library) and the data in this repo:

```sh
python3 study.py report           # gaps by model, name-only and stated-identity conditions
python3 export.py results         # results/*.csv
```

Re-running the models needs an [OpenRouter](https://openrouter.ai) key in `.env` (see `.env.example`). Model responses are not deterministic, so new runs will differ in detail.

```sh
python3 study.py run --models openai/gpt-6.1-sol,anthropic/claude-sonnet-5.5 --budget 5
python3 study.py extract --budget 1   # DeepSeek v4.1 Flash, Claude Haiku 5.5 when unverified
python3 study.py tone --budget 1
python3 study.py report
```

`--budget` is a hard spending cap in USD, enforced from OpenRouter's per-request cost.

## Method in brief

- **Models:** one current model per lab, via OpenRouter, default settings, no system prompt, answers collected on 2026-11-01.
- **Extraction:** DeepSeek v4.1 Flash returns the suggested salary and the exact text it came from; the number counts only if that text appears in the answer and parses to the same value, otherwise Claude Haiku 5.5 tries under the same check. 4,054 of 4,139 answers are verified.
- **Measure:** each number divided by the same model's median for the same job; gaps compare geometric means between groups. 95% intervals and p-values resample names (name condition) or answers (stated identity), 5,000 draws; Holm correction over the 80 per-model tests.

Full methodology and limitations: [heldoutlabs.com/ai-salary-advice-name-bias](https://heldoutlabs.com/ai-salary-advice-name-bias).

## License

Code: [MIT](LICENSE). Data (`data/`, `results/`): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Please cite:

> symbatix (2026). "Does AI give you lower salary advice because of your name? We asked 10 models 4,140 times." Heldout Labs. https://heldoutlabs.com/ai-salary-advice-name-bias
