# Changelog

Files declare the first two numbers, `comb: "0.1"`. The third number marks additions that keep existing files valid.

## 0.1.1 (12 November 2026)

- Any mark (a face, seam or border) can carry `proposed_by` and `confirmed_by`. A mark with only `proposed_by` is a proposal.
- The checker counts unconfirmed proposals and rejects a `settled` mark that is only a proposal.
- The Loanshelf example shows one confirmed mark and one proposal.
- Licence stated as Apache 2.0, with a NOTICE file naming the copyright holder.
- The schema's `$id` points at this repository.

## 0.1.0 (12 November 2026)

- First draft: project, cell and journey files; five faces plus questions; eight conditions with the evidence each needs; seams, borders, decisions and rules.
- JSON Schema, a checker, and the Loanshelf worked example.
