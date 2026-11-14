# Changelog

Files declare the first two numbers, such as `comb: "0.2"`. The third number marks additions that keep existing files valid.

The second number changes when a file can hold something an older reader would not understand, even if every older file stays valid.

## 0.2.0 (14 November 2026), draft

Four gaps found by writing a comb for a real product. Every 0.1 file is still valid and means what it meant.

- `comb.yaml` can list the other `repositories` a pointer may name. Once listed, a pointer to an undeclared repository is an error.
- A new condition, `not_applicable`, for a face that has nothing to hold and should not. It needs a `reason`. `empty` now means a gap.
- The specification says what `agrees` claims on each face. On the testing face it means the tests cover the scenarios the face points to, not that tests exist.
- A decision made before the comb can be copied in with `source`, `proposed_by` and `confirmed_by`. Nothing can be `settled` by one until a person confirms it.
- The checker reads 0.1 and 0.2, refuses a 0.1 file that uses a 0.2 addition, and refuses a comb whose files mix versions.
- The Loanshelf example is written to 0.2 and shows each addition.

## 0.1.1 (12 November 2026)

- Any mark (a face, seam or border) can carry `proposed_by` and `confirmed_by`. A mark with only `proposed_by` is a proposal.
- The checker counts unconfirmed proposals and rejects a `settled` mark that is only a proposal.
- The Loanshelf example shows one confirmed mark and one proposal.
- Licence stated as Apache 2.0, with a NOTICE file naming the copyright holder.
- The schema's `$id` points at this repository.

## 0.1.0 (12 November 2026)

- First draft: project, cell and journey files; five faces plus questions; eight conditions with the evidence each needs; seams, borders, decisions and rules.
- JSON Schema, a checker, and the Loanshelf worked example.
