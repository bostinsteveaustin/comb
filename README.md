# Comb

A plain-text format for recording where a product's design and build stand.

**Status:** version 0.1, a draft for review.

## Why

Software is now built faster than anyone can check it against what was intended. Requirements, designs, tests and code each say something about an idea, and they drift apart quietly. The people who own the intent often cannot read the code to find out.

Comb gives each idea one small file. The file points to where the idea's requirements, designs, data and tests live, records whether they agree, and keeps the open questions and the decisions made about them. Because it is plain text in the repository, people and coding agents can both read it, and git keeps the history.

## What is in a Comb folder

| File | Holds |
|---|---|
| `comb.yaml` | The project and the rules that apply everywhere |
| `cells/<id>.yaml` | One idea: its purpose, five faces, questions, seams, borders and decisions |
| `journeys/<id>.yaml` | The route one kind of person takes, step by step |

The full format is in [SPEC.md](SPEC.md). The schema is in [schema/comb.schema.json](schema/comb.schema.json).

## Try it

```
pip install pyyaml jsonschema
python3 tools/check.py examples/loanshelf/comb
```

The example is Loanshelf, an invented tool-lending library with five cells and one journey. It passes with five warnings, and each warning is deliberate. One mark is shown as proposed by a tool and not yet confirmed by a person. The warnings:

- an open question that nothing is watching
- a decision with no test holding it in place
- two built cells with no tests
- a journey step that no cell holds

## What Comb does not do

- It does not replace requirement documents, scenario files, tests or code. It points to them.
- It does not say how the files are produced.
- It does not say how they should be drawn.
- The checker confirms the files are well formed. It does not decide whether two statements really disagree.

## Feedback

This is an early draft and the questions at the end of [SPEC.md](SPEC.md) are real ones. The most useful test is to write one area of a project you know in this format and note where it fought you.

## Licence

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
