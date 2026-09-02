#!/usr/bin/env python3
"""Verify the public release, and ship with the package.

Needs Python 3.9 or later and nothing else - no third-party packages. Invoke it with
whichever launcher your system has: `py`, `python3` or `python`.

Most checks here are ones a third party can run on the published files. Checks 1 and 2
are not: they need the evaluation pool, the frozen manifest and the id-to-name mapping,
none of which is distributed, and they report SKIPPED without them. Hashes are computed
with the semantics the harness used - sha256 over the UTF-8 encoding of the string, no
normalisation - so a mismatch is a real finding rather than an encoding artefact.

Checks:
  1  authority file hashes to the source_sha256 the frozen manifest recorded
  2  every published prompt is byte-identical to the evaluated prompt
  3  both published hashes recompute from the published prompt for every row, under
     each arm's rendering rule (local template for base/tuned; system+user for frontier)
  4  each item maps to exactly three result rows: one base, one tuned, one frontier
  5  the public rows reproduce every published table: 2/184, 170/184, 179/184, the
     base-vs-tuned contingency table and the tuned-vs-frontier paired table
  6  substituting into the published template reproduces prompt_sha256 for every
     local-arm row
  7  every SHA-256 quoted in the card is one the release stands behind
  8  every checksum-manifest entry recomputes from the shipped files
  D  diagnostic: do the sealed spec_sha256 / prompt_sha256 reproduce from the prompt?

Checks 1 and 2 need the evaluation pool, the frozen manifest and the id-to-name mapping.
None of those is distributed, so for a public reader they report SKIPPED and the run
continues. Checks 3 through 8 need nothing but the published files.

Check 6 is not redundant with check 3. Check 3 renders the prompt with this file's own
format_local_prompt; check 6 renders it the way a reader does, by substituting into the
template published in serving_template.json. They agree only if the published template is
correct - and it once was not.

Exit 0 all checks pass, 2 a check failed, 3 an input was missing or unreadable.

Usage:
    python3 verify_public_release.py --public .

With the undistributed inputs to hand, checks 1 and 2 also run:
    python3 verify_public_release.py --public <dir> --private <dir> \
        --authority <pool.jsonl> --manifest <frozen manifest.json>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

MANIFEST_NAME = "SHA256SUMS.txt"

SYSTEM_PROMPT = (
    "You are an expert MQL5 programmer. Write the complete MQL5 "
    "Expert Advisor code that implements the given specification exactly."
)

EXPECTED = {"n": 184, "base": 2, "tuned": 170, "a": 1, "b": 1, "c": 169, "d": 13}
# The frontier arm and its pairing against the tuned arm, added 2026-09-02.
EXPECTED_FRONTIER = {"n": 184, "frontier": 179,
                     "both_pass": 168, "tuned_only": 2,
                     "frontier_only": 11, "both_fail": 3}


def format_api_prompt(system: str, spec: str) -> str:
    """Canonical rendering of the frontier arm's system+user pair. The vendor API
    takes the two as separate fields; the frontier rows' prompt_sha256 hashes this
    single-string rendering of them."""
    return f"{system}\n\n{spec}"


def sha256_text(text: str) -> str:
    """Byte-for-byte the harness's hash rule: sha256 over the UTF-8 encoding."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{lineno}: {exc}")


def format_local_prompt(spec: str) -> str:
    """The serving template, rendered exactly as the harness rendered it."""
    return (
        f"<|system|>{SYSTEM_PROMPT}<|end|>\n"
        f"<|user|>{spec}<|end|>\n"
        f"<|assistant|>"
    )


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    # Only --public is required. The authority pool, the frozen manifest and the id-to-name
    # mapping are not distributed, so a public reader has none of them; requiring any of
    # them made the script exit before check 3 and the release was not runnable by anyone
    # outside. Checks 3, 4 and 5 need nothing but the published files, and they are the
    # checks that matter to a reader: the hashes recompute, the pairing is one-to-one, and
    # the headline falls out of the rows.
    ap.add_argument("--public", type=Path, required=True)
    ap.add_argument("--private", type=Path,
                    help="holds item_id_mapping.jsonl; not distributed, so check 2 skips")
    ap.add_argument("--authority", type=Path,
                    help="the evaluation pool; not distributed, so check 1 skips")
    ap.add_argument("--manifest", type=Path,
                    help="the frozen manifest; not distributed, so check 1 skips")
    ap.add_argument("--sealed-rows", type=Path,
                    help="the sealed base-arm results file (not distributed), "
                         "for the reproduction diagnostic")
    args = ap.parse_args(argv)

    failures: list[str] = []
    notes: list[str] = []

    # ---- check 1 -----------------------------------------------------------------
    # Runs only when the pool and the frozen manifest are both to hand. Neither ships, so
    # for a public reader this reports SKIPPED and the run continues.
    have_authority = args.authority is not None and args.authority.is_file()
    have_manifest = args.manifest is not None and args.manifest.is_file()
    authority: dict[str, str] = {}

    if have_authority and have_manifest:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        actual = sha256_file(args.authority)
        if actual == manifest["source_sha256"]:
            print(f"  [1] authority sha256 matches the frozen manifest  {actual[:16]}...")
        else:
            failures.append(
                f"[1] authority sha256 {actual} != manifest source_sha256 "
                f"{manifest['source_sha256']}"
            )
        # The authority is the only source of prompt text. Published prompts are checked
        # against it rather than the other way round.
        for rec in read_jsonl(args.authority):
            name = rec.get("ea_name")
            if name is not None:
                authority[name] = rec["prompt"]
    else:
        print("  [1] SKIPPED - needs the evaluation pool and the frozen manifest, "
              "neither of which is distributed")

    # Checks 3-8 verify the PUBLIC release, so they read the public prompts file
    # unconditionally. An earlier version fell back between the two, which meant a
    # present --private copy silently substituted for the release copy and the
    # verifier could pass a public file that no longer matched its results.
    public_prompts = args.public / "prompts.jsonl"
    if not public_prompts.is_file():
        print(f"MISSING: prompts.jsonl in {args.public}")
        return 3

    published = list(read_jsonl(public_prompts))

    # ---- check 2 -----------------------------------------------------------------
    # Needs the id-to-name mapping, which is not distributed. A public reader gets a
    # clear SKIPPED rather than a crash; internally the mapping is present and it runs.
    id_to_name: dict[str, str] = {}
    mapping_path = args.private / "item_id_mapping.jsonl" if args.private else None
    if mapping_path is not None and mapping_path.is_file():
        id_to_name = {r["item_id"]: r["ea_name"] for r in read_jsonl(mapping_path)}

    if not id_to_name or not authority:
        print("  [2] SKIPPED - needs the evaluation pool and the id-to-name mapping, "
              "neither of which is distributed")
    else:
        mismatched = [
            r["item_id"] for r in published
            if authority.get(id_to_name.get(r["item_id"], "")) != r["prompt"]
        ]
        if mismatched:
            failures.append(
                f"[2] {len(mismatched)} published prompt(s) differ from the evaluated "
                f"prompt"
            )
        else:
            print(f"  [2] all {len(published)} published prompts are byte-identical to "
                  f"the evaluated prompt")

    # ---- check 3 -----------------------------------------------------------------
    # The check any reader can run with nothing but the published files.
    public_hash = {r["item_id"]: sha256_text(r["prompt"]) for r in published}
    results_path = args.public / "per_item_results.jsonl"
    if not results_path.is_file():
        # The docstring's exit-3 contract for missing inputs, honoured here too —
        # without this a missing results file was an uncaught traceback.
        print(f"MISSING: per_item_results.jsonl in {args.public}")
        return 3
    rows = list(read_jsonl(results_path))
    prompt_by_id = {p["item_id"]: p["prompt"] for p in published}
    # The published prompt_sha256 per item for the LOCAL arms, for check 6 to compare a
    # reader-built template render to. Frontier rows hash a different rendering (the
    # API's system+user pair) and are checked under that rule in check 3.
    by_id_hash = {r["item_id"]: r.get("prompt_sha256") for r in rows
                  if r.get("arm") != "frontier"}

    hash_bad = [
        r["item_id"] for r in rows
        if public_hash.get(r["item_id"]) != r.get("prompt_sha256_public")
    ]
    tmpl_bad_rows = []
    for r in rows:
        if r["item_id"] not in prompt_by_id:
            continue
        prompt = prompt_by_id[r["item_id"]]
        want = (format_api_prompt(SYSTEM_PROMPT, prompt)
                if r.get("arm") == "frontier" else format_local_prompt(prompt))
        if sha256_text(want) != r.get("prompt_sha256"):
            tmpl_bad_rows.append(r["item_id"])
    if hash_bad:
        failures.append(f"[3] prompt_sha256_public does not recompute for "
                        f"{len(set(hash_bad))} item(s)")
    elif tmpl_bad_rows:
        failures.append(f"[3] prompt_sha256 does not recompute from the published "
                        f"serving template for {len(set(tmpl_bad_rows))} item(s)")
    else:
        print(f"  [3] both published hashes recompute from the published prompt for all "
              f"{len(public_hash)} items ({len(rows)} rows)")

    # ---- check 4 -----------------------------------------------------------------
    by_item: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_item[r["item_id"]].append(r)
    bad = {
        i: sorted(x["arm"] for x in v)
        for i, v in by_item.items()
        if sorted(x["arm"] for x in v) != ["base", "frontier", "tuned"]
    }
    if bad:
        failures.append(f"[4] {len(bad)} item(s) do not map to exactly one base, one "
                        f"tuned and one frontier row: {list(bad.items())[:3]}")
    else:
        print(f"  [4] all {len(by_item)} items map to exactly one base, one tuned and "
              f"one frontier row")

    # ---- check 5 -----------------------------------------------------------------
    # The headline is a claim about verdict_headline, so it is measured on that field.
    # The two verdict fields can and do diverge - warnings fail strict but not headline,
    # and some frontier rows show exactly that - so the divergence is counted and printed
    # below rather than assumed away, and the tables are measured on verdict_headline
    # only. An earlier version read verdict_strict and got away with it only while the
    # two happened to agree.
    disagree = [
        i for i, v in by_item.items()
        if any(x["verdict_headline"] != x["verdict_strict"] for x in v)
    ]
    if disagree:
        notes.append(f"[5] NOTE: verdict_headline and verdict_strict disagree on "
                     f"{len(disagree)} item-arm row(s); the headline below is measured on "
                     f"verdict_headline")
    else:
        notes.append(f"[5] verdict_headline and verdict_strict agree on all "
                     f"{len(rows)} rows")

    a = b = c = d = 0
    fp = f_both_pass = f_tuned_only = f_frontier_only = f_both_fail = 0
    for v in by_item.values():
        base = next(x for x in v if x["arm"] == "base")["verdict_headline"]
        tuned = next(x for x in v if x["arm"] == "tuned")["verdict_headline"]
        frontier = next(x for x in v if x["arm"] == "frontier")["verdict_headline"]
        if base and tuned:
            a += 1
        elif base and not tuned:
            b += 1
        elif tuned:
            c += 1
        else:
            d += 1
        if frontier:
            fp += 1
        if tuned and frontier:
            f_both_pass += 1
        elif tuned:
            f_tuned_only += 1
        elif frontier:
            f_frontier_only += 1
        else:
            f_both_fail += 1
    got = {"n": len(by_item), "base": a + b, "tuned": a + c,
           "a": a, "b": b, "c": c, "d": d}
    got_frontier = {"n": len(by_item), "frontier": fp,
                    "both_pass": f_both_pass, "tuned_only": f_tuned_only,
                    "frontier_only": f_frontier_only, "both_fail": f_both_fail}
    if got == EXPECTED and got_frontier == EXPECTED_FRONTIER:
        print(f"  [5] headline reproduces from the public rows: base {got['base']}/"
              f"{got['n']}, tuned {got['tuned']}/{got['n']}, frontier "
              f"{fp}/{got['n']}, a={a} b={b} c={c} d={d}; tuned-vs-frontier "
              f"{f_both_pass}/{f_tuned_only}/{f_frontier_only}/{f_both_fail}")
    else:
        failures.append(f"[5] headline does not reproduce. expected {EXPECTED} + "
                        f"{EXPECTED_FRONTIER}, got {got} + {got_frontier}")
    # ---- check 6 -----------------------------------------------------------------
    # The reader's path, and the reason this check exists. Checks 3 renders the prompt
    # with format_local_prompt, a function compiled into this script. A reader has no such
    # function: they parse serving_template.json, substitute the two placeholders, and
    # hash. Those are different routes to the same string only if the published template
    # is right. It once was not - the template field held the two-character sequence
    # backslash-n where a newline belonged, so every reader-side hash disagreed while
    # check 3 passed. A check that shares the harness's own definition cannot see that.
    template_path = args.public / "serving_template.json"
    if not template_path.is_file():
        failures.append("[6] serving_template.json is missing from the public release")
    else:
        tmpl = json.loads(template_path.read_text(encoding="utf-8"))
        sys_prompt = tmpl["system_prompt"]
        if sha256_text(sys_prompt) != tmpl["system_prompt_sha256"]:
            failures.append("[6] the published system prompt does not match its own "
                            "published hash")
        rendered_bad = [
            r["item_id"] for r in published
            if sha256_text(
                tmpl["template"].replace("{system_prompt}", sys_prompt)
                                .replace("{prompt}", r["prompt"])
            ) != by_id_hash.get(r["item_id"])
        ]
        if rendered_bad:
            failures.append(
                f"[6] substituting into the published template does not reproduce "
                f"prompt_sha256 for {len(set(rendered_bad))} item(s). A reader following "
                f"serving_template.json cannot reproduce our hashes."
            )
        else:
            print(f"  [6] substituting into the published template reproduces "
                  f"prompt_sha256 for all {len(published)} items")


    # ---- check 7 -----------------------------------------------------------------
    # Every 64-hex string in README.md must be a hash the release actually stands behind.
    # The card quotes file hashes in prose and in a table, and those are hand-carried from
    # the metadata when the card is written - so they go stale the moment any file is
    # regenerated. That happened: the card published a serving_template.json hash from an
    # earlier build while the manifest, the metadata and the projection report all agreed
    # on a different one. Nothing caught it, because nothing was comparing the two.
    readme = args.public / "README.md"
    manifest_file = args.public / MANIFEST_NAME
    if readme.is_file() and manifest_file.is_file():
        known: set[str] = set()
        for line in manifest_file.read_text(encoding="utf-8").splitlines():
            digest = line.split("  ")[0].strip()
            if len(digest) == 64:
                known.add(digest)
        # Hashes the release legitimately quotes that are not file hashes: model weights,
        # the corpus, the adapter, the evaluation pool, the normaliser source. Those live
        # in publication_metadata.json, so that file is the second authority.
        # serving_template.json is a third authority: it carries the system-prompt hash
        # and the worked example, which are legitimately quoted in the card and appear in
        # neither the manifest nor the metadata.
        authorities = "".join(
            (args.public / n).read_text(encoding="utf-8")
            for n in ("publication_metadata.json", "serving_template.json",
                      "PROJECTION_REPORT.json")
            if (args.public / n).is_file()
        )
        stale = sorted({
            h for h in re.findall(r"\b[0-9a-f]{64}\b", readme.read_text(encoding="utf-8"))
            if h not in known and h not in authorities
        })
        if stale:
            failures.append(
                f"[7] README.md quotes {len(stale)} sha256 value(s) that appear in none "
                f"of {MANIFEST_NAME}, publication_metadata.json, serving_template.json "
                f"or PROJECTION_REPORT.json, so the card disagrees with the release: "
                f"{stale[:3]}"
            )
        else:
            print("  [7] every sha256 quoted in the card is one the release stands behind")
    else:
        # A copy missing the card or the manifest must not verify. Without this branch
        # the check was silently skipped and a damaged copy printed ALL CHECKS PASSED.
        absent = [n for n, f in (("README.md", readme), (MANIFEST_NAME, manifest_file))
                  if not f.is_file()]
        failures.append(f"[7] cannot run: missing {', '.join(absent)}")

    # ---- check 8 -----------------------------------------------------------------
    # Recompute the manifest. Check 7 reads SHA256SUMS.txt to learn which hashes the
    # release stands behind, but never hashes a file - so a modified LICENSE or
    # CITATION.cff passed the verifier untouched while the card said the verifier checks
    # the release package. Third parties do not all have sha256sum, and telling them to
    # run a tool this script could run itself is not verification.
    if manifest_file.is_file():
        listed: dict[str, str] = {}
        for line in manifest_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            digest, _, name = line.partition("  ")
            if len(digest.strip()) == 64 and name.strip():
                listed[name.strip()] = digest.strip()

        bad, missing = [], []
        for name, want in sorted(listed.items()):
            f = args.public / name
            if not f.is_file():
                missing.append(name)
            elif sha256_file(f) != want:
                bad.append(name)

        present = {p.name for p in args.public.iterdir() if p.is_file()}
        unlisted = sorted(present - set(listed) - {MANIFEST_NAME})

        if bad or missing:
            failures.append(
                f"[8] manifest reconciliation FAILED: {len(bad)} file(s) do not match "
                f"their recorded hash {bad[:3]}, {len(missing)} listed file(s) absent "
                f"{missing[:3]}"
            )
        elif unlisted:
            failures.append(
                f"[8] {len(unlisted)} file(s) in the release are not listed in "
                f"{MANIFEST_NAME}: {unlisted[:5]}"
            )
        else:
            print(f"  [8] all {len(listed)} manifest entries recompute, and the only "
                  f"unlisted file is {MANIFEST_NAME}, which cannot list itself")
    else:
        # Same rule as check 7: a copy with no manifest is unverifiable, not verified.
        failures.append(f"[8] cannot run: {MANIFEST_NAME} is missing")

    # ---- diagnostic --------------------------------------------------------------
    if args.sealed_rows and args.sealed_rows.is_file():
        sealed = {r["ea_name"]: r for r in read_jsonl(args.sealed_rows)}
        spec_ok = spec_bad = tmpl_ok = tmpl_bad = 0
        example = None
        for r in published:
            s = sealed.get(id_to_name.get(r["item_id"], ""))
            if not s:
                continue
            if sha256_text(r["prompt"]) == s.get("spec_sha256"):
                spec_ok += 1
            else:
                spec_bad += 1
                if example is None:
                    # Published rows carry item_id only; the name comes from the
                    # private mapping already resolved above.
                    example = (r["item_id"], id_to_name.get(r["item_id"], "?"),
                               sha256_text(r["prompt"]), s.get("spec_sha256"))
            if sha256_text(format_local_prompt(r["prompt"])) == s.get("prompt_sha256"):
                tmpl_ok += 1
            else:
                tmpl_bad += 1
        notes.append(
            f"[D] sealed spec_sha256 reproduces for {spec_ok}/{spec_ok + spec_bad} items; "
            f"sealed prompt_sha256 reproduces under the local serving template for "
            f"{tmpl_ok}/{tmpl_ok + tmpl_bad}"
        )
        if example:
            notes.append(f"[D] first divergence: {example[0]} ({example[1]})\n"
                         f"      sha256(published prompt) = {example[2]}\n"
                         f"      sealed spec_sha256       = {example[3]}")
        # A known-answer check on the hashing itself, so a zero above cannot be blamed
        # on this script's encoding.
        want = "820208ddccc935fe44222db63416e192f605183e1b77c8e833de0d8aa94c6377"
        got_sp = sha256_text(SYSTEM_PROMPT)
        notes.append(f"[D] instrument check: sha256(SYSTEM_PROMPT) "
                     f"{'MATCHES' if got_sp == want else 'DIFFERS FROM'} the sealed "
                     f"system_prompt_sha256")
        if got_sp != want:
            failures.append("[D] this script's hashing does not reproduce a known answer; "
                            "every hash result above is untrustworthy")

    for n in notes:
        print(n)

    if failures:
        print("\n=== FAILED ===")
        for f in failures:
            print(f"  {f}")
        return 2
    print("\n=== ALL CHECKS PASSED ===")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
