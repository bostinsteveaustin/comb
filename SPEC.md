# Comb 0.1

A plain-text format for recording where a product's design and build stand.

**Status:** draft for review. Expect it to change.

## 1. What Comb is

Comb is a small set of YAML files that live in a repository beside the code. They record, for each idea in a product:

- what the idea is for
- where its requirements, designs, data, tests and constraints live
- whether those agree with each other, and with neighbouring ideas
- which questions are open, and who decided what

Comb points to artefacts. It never copies them. Requirements stay in your requirement documents, tests stay in your test files, and code stays in code.

Comb is not a specification language, a test framework or a diagram format. It does not say how the files get written, whether by hand or by a tool, and it does not say how they should be drawn.

## 2. Files

```
comb/
  comb.yaml            the project and its rules
  cells/<id>.yaml      one file per idea
  journeys/<id>.yaml   one file per route a person takes
```

Every file starts with `comb: "0.1"`. An `id` is lower-case words joined by hyphens, unique in the project, and matches the file name.

Avoid `on`, `off`, `yes` and `no` as field names or bare values. Many YAML readers turn them into true and false.

## 3. Pointers

A pointer says where a real artefact lives.

```yaml
{ path: docs/prd/borrowing.md, at: 3f9c2ab, anchor: BOR-04, kind: document }
```

| Field | Required | Meaning |
|---|---|---|
| `path` | yes | File path in the repository |
| `at` | yes | The commit the pointer was true at |
| `repo` | no | Another repository. Omit for this one. |
| `lines` | no | A line or range, such as `12` or `4-9` |
| `anchor` | no | A heading, requirement ID or function name |
| `kind` | no | `document`, `scenario`, `design`, `code`, `test`, `schema`, `config`, `measure`, `other` |

`at` is required so that a pointer can go stale in a way a tool can see. If the file has changed since that commit, the pointer needs looking at again.

For something outside a repository, use `{ url: ..., seen: 2026-11-12 }`.

## 4. Cells

A cell is one idea: a feature, a rule, a mechanism. It has a centre, a stage, five faces and a list of questions.

```yaml
comb: "0.1"
id: late-fees
name: Late fees
parent: loanshelf
stage: specified

core:
  problem: A late tool costs the next member their weekend.
  for: The library, and members who return on time.
  excludes:
    - Charging for wear and tear

faces:
  function:        { condition: unchecked, points_to: [...] }
  design:          { condition: unchecked, points_to: [...] }
  data:            { condition: empty }
  testing:         { condition: unchecked, points_to: [...] }
  non_functionals: { condition: open, question: q2 }

questions: [...]
```

**`core`** is why the idea exists. `problem` and `for` are required. `excludes` says what the idea deliberately leaves out. `source` can point to the document it came from.

**`parent`** is the project id or the id of a larger cell.

**`stage`** is one of `concept`, `specified`, `building`, `built`, `retired`.

**`faces`** are fixed. Every cell has all five, even if a face is `empty`:

| Face | What it points to |
|---|---|
| `function` | Requirements, rules, and the code that carries them out |
| `design` | Screens, flows and wording |
| `data` | Schemas, records and storage |
| `testing` | Scenarios and tests |
| `non_functionals` | Limits, security, privacy, performance |

The list of questions (section 7) is the sixth face.

The faces are fixed so that a missing one shows. A cell at stage `specified` or later with an empty `function` or `testing` face draws a warning.

## 5. Conditions

Every face, seam and border has a condition. The list is fixed, and each condition needs evidence.

| Condition | Meaning | It must carry |
|---|---|---|
| `unexamined` | Nobody has looked | Nothing |
| `empty` | Nothing exists here (faces only) | Nothing, and no `points_to` |
| `unchecked` | Something exists, and nobody has verified it | `points_to` |
| `agrees` | The sources match, and a test shows it | `evidence`: at least one pointer of kind `test` |
| `disputed` | Two sources say different things | `statements`: at least two, each with a pointer |
| `open` | It turns on a question nobody has answered | `question`: the id of a question in this cell |
| `settled` | A person has decided | `decision`: the id of a decision in this cell |
| `unreachable` | It exists, and nothing can get to it | `reason` |

`unexamined` and `agrees` are deliberately far apart. Silence is not agreement.

A statement is one plain sentence and a pointer:

```yaml
statements:
  - says: A loan lasts 7 days.
    pointer: { path: docs/prd/borrowing.md, at: 3f9c2ab, anchor: BOR-04, kind: document }
  - says: The due date is set 14 days after collection.
    pointer: { path: src/loans/due-date.ts, at: 8d41e07, lines: "12", kind: code }
```

## 6. Seams and borders

A **seam** is where two faces of the same cell meet. Use it when they disagree with each other.

```yaml
seams:
  - between: [function, design]
    condition: disputed
    statements: [...]
```

A **border** is where two cells meet. Use it when two ideas depend on each other or conflict.

```yaml
borders:
  - with: loan-period
    condition: disputed
    statements: [...]
```

A border is written once, in either of the two cell files.

## 7. Questions

Questions are permanent. A question changes condition; it is never deleted.

```yaml
questions:
  - id: q1
    text: Should late fees exist at all?
    condition: settled
    raised_by: Product owner
    raised_on: 2026-09-02
    decision: d1
    watched_by:
      measure: Share of loans returned late, by month
      reopen_when: Above 20% for two months running
```

`condition` is `open`, `parked`, `settled` or `reopened`. A settled question names its decision.

`watched_by` ties a question to a measure. `reopen_when` says what reading of that measure should bring the question back. An open question with nothing watching it draws a warning.

## 8. Decisions

A decision records that a person settled something.

```yaml
decisions:
  - id: d1
    about: question:q1
    decided: Keep fees for the pilot.
    by: Product owner
    date: 2026-09-10
    reason: Two other tool libraries reported that returns slipped after dropping fees.
    reopens_if: Late returns go above 20% for two months running.
    proof:
      - { path: tests/fees/pilot.test.ts, at: 9a1c3d2, kind: test }
```

`about` is one of `face:<name>`, `seam:<face>/<face>`, `border:<cell id>`, `question:<id>` or `cell`.

`by` is a person. Tools and agents may propose a decision. They do not make one.

`proof` points to the scenarios and tests that hold the decision in place. A decision with no proof draws a warning: it has been made, and nothing yet stops the build drifting away from it.

Decisions are added, not edited. To change your mind, add a new decision.

## 9. Journeys

A journey is the route one kind of person takes, in order. Each step names the cell it passes through.

```yaml
comb: "0.1"
id: member-borrows-a-tool
name: A member borrows a tool and returns it late
actor: Member
steps:
  - does: Reserves a drill for the weekend.
    cell: borrowing
    reach: reached
  - does: Gets a reminder the day before it is due.
    cell: reminders
    reach: unreachable
    reason: The reminder job is not scheduled, so no reminder is ever sent.
  - does: Gets a receipt for the fee.
    reach: unknown
```

`reach` is `reached`, `unreachable` or `unknown`. An unreachable step needs a `reason`.

A step with no `cell` is allowed. It means the journey needs something no cell holds, and it draws a warning. A cell that no journey passes through also draws a warning.

## 10. Rules

`comb.yaml` names the project and the rules that apply to every cell.

```yaml
comb: "0.1"
id: loanshelf
name: Loanshelf
rules:
  - id: R2
    text: There is one loan period, and every message and fee follows it.
    check: Is a number of days written anywhere else?
```

A `check` is a question to ask of any change.

## 11. If you already mark scenarios

Teams that mark each scenario as passing, failing or needing a decision already hold most of this. The suggested mapping:

| Your marker | In Comb |
|---|---|
| Passes | `agrees`, with the test as `evidence` |
| Fails | `disputed`: one statement from the scenario, one from the test result or the code |
| Needs a decision | `open`, with a question |
| Known failure, accepted for now | `settled`, keeping both `statements`, with a decision whose `reopens_if` says when it will be fixed |

## 12. The checker

```
python3 tools/check.py examples/loanshelf/comb
```

It checks that files follow the format, that every reference lands, and that each condition carries its evidence. It needs `pyyaml` and `jsonschema`.

It does not open the artefacts that pointers name, check that a commit exists, or judge whether two statements really disagree.

## 13. Questions for reviewers

1. Are these the right five faces, plus questions? What would you add or drop?
2. Is `settled` enough for a known failure, or does that need a condition of its own?
3. Should a border live in one of its two cells, or in a file of its own?
4. Should decisions live in the cell, or in one log for the whole project?
5. Could you write your own scenario area in this format without help? Where did it fight you?
6. Is anything here that your existing files already say better?
