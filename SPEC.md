# Comb 0.2

A plain-text format for recording where a product's design and build stand.

**Version:** 0.2.0, 14 November 2026. A draft for review; expect it to change.

Files declare `comb: "0.2"`. A 0.1 file is still valid and means what it meant; section 13 says what 0.2 added and how to move. Changes are listed in [CHANGELOG.md](CHANGELOG.md).

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

Every file starts with `comb: "0.2"`, and every file in a comb declares the same version. An `id` is lower-case words joined by hyphens, unique in the project, and matches the file name.

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

### Other repositories

A product often spans more than one repository. The comb lives in one of them, and a pointer without `repo` means that one. `comb.yaml` lists the others, so that a pointer's `repo` is a name the project has declared and not a string someone typed.

```yaml
repositories:
  - name: loanshelf/notices
    url: https://example.org/loanshelf/notices
    holds: The wording of every email and text the library sends.
```

`name` is required and is the value a pointer's `repo` uses. `url` and `holds` are optional.

Once `repositories` is present, a pointer that names a repository not in the list is an error. If it is absent and a pointer names another repository, the checker warns.

## 4. Cells

A cell is one idea: a feature, a rule, a mechanism. It has a centre, a stage, five faces and a list of questions.

```yaml
comb: "0.2"
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
| `empty` | Nothing exists here, and something could (faces only) | Nothing, and no `points_to` |
| `not_applicable` | Nothing exists here, and nothing should (faces only) | `reason`, and no `points_to` |
| `unchecked` | Something exists, and nobody has verified it | `points_to` |
| `agrees` | The sources match, and a test shows it | `evidence`: at least one pointer of kind `test` |
| `disputed` | Two sources say different things | `statements`: at least two, each with a pointer |
| `open` | It turns on a question nobody has answered | `question`: the id of a question in this cell |
| `settled` | A person has decided | `decision`: the id of a decision in this cell |
| `unreachable` | It exists, and nothing can get to it | `reason` |

`unexamined` and `agrees` are deliberately far apart. Silence is not agreement.

`empty` and `not_applicable` are apart for the same reason. `empty` is a gap that may need filling, and on some faces it draws a warning. `not_applicable` is a judgement that the face has nothing to hold, such as the data face of an idea that stores nothing, and it must say why. It can be proposed by a tool and confirmed by a person like any other mark.

### What `agrees` claims

`agrees` is the strongest thing a mark can say, so it is worth being exact about what it says.

- It is a claim about a moment. The `at` of each evidence pointer is the commit the test was seen to pass at. If the test or what it tests has changed since, the mark needs looking at again.
- A test existing is not agreement. A face that points to tests nobody has run against its sources is `unchecked`.

On each face:

| Face | `agrees` means |
|---|---|
| `function` | The code does what the requirements say, and the evidence is a test of that behaviour |
| `design` | What people see matches the design, and the evidence is a test that looks at it |
| `data` | What is stored matches the schema and the rules about it, and the evidence is a test of that |
| `testing` | Every scenario the face points to has a test, and those tests pass. The evidence is those tests, and `points_to` names the scenarios |
| `non_functionals` | The limit is met, and the evidence is a test that measures it |

The testing face is the one that is easy to get wrong, because its evidence and its subject are both tests. It does not mean "tests exist" or "the tests pass". It means the tests cover what the scenarios say should be tested. A testing face marked `agrees` that points to no scenarios draws a warning: there is nothing for the tests to agree with.

A statement is one plain sentence and a pointer:

```yaml
statements:
  - says: A loan lasts 7 days.
    pointer: { path: docs/prd/borrowing.md, at: 3f9c2ab, anchor: BOR-04, kind: document }
  - says: The due date is set 14 days after collection.
    pointer: { path: src/loans/due-date.ts, at: 8d41e07, lines: "12", kind: code }
```

### Proposed and confirmed

Any mark can say who put it there and who has checked it.

```yaml
condition: disputed
proposed_by: onboarding-agent
confirmed_by: Product owner
statements: [...]
```

A mark with `proposed_by` and no `confirmed_by` is a proposal. It is a claim for a person to look at, not yet a finding. A tool that fills in many cells at once should mark everything it writes this way.

`settled` can never be a proposal, because only a person decides.

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

### Decisions made before the comb

Most products have decisions that were made long before anyone wrote a comb: in meeting minutes, decision records, or a paragraph of a requirements document. They belong in the comb, and a tool reading the repository can find them. A tool still cannot make a decision, so it records one it found as a proposal.

```yaml
decisions:
  - id: d1
    about: cell
    decided: Members collect tools in person. The library does not deliver.
    by: Library committee
    date: 2026-06-03
    reason: Volunteers cannot cover deliveries.
    source: { path: docs/minutes/2026-06.md, at: 3f9c2ab, anchor: Item 4, kind: document }
    proposed_by: onboarding-agent
```

`source` points to where the decision was first recorded. `by`, `date` and `reason` are taken from that record, not from the tool.

`proposed_by` names whoever copied the decision in. A decision with `proposed_by` must have a `source`. Until a person adds `confirmed_by`, it is a claim that this decision was made and is recorded correctly, and nothing may rest on it: a mark or a question cannot be `settled` by an unconfirmed decision.

A decision a person writes directly into the comb needs none of these three fields.

## 9. Journeys

A journey is the route one kind of person takes, in order. Each step names the cell it passes through.

```yaml
comb: "0.2"
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
comb: "0.2"
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

## 13. Moving from 0.1

Change the first line of every file to `comb: "0.2"`. Nothing else is required: every valid 0.1 file is a valid 0.2 file with the same meaning.

What 0.2 added, all of it optional:

| Addition | Section |
|---|---|
| `repositories` in `comb.yaml` | 3 |
| The condition `not_applicable` | 5 |
| A stated meaning for `agrees` on each face | 5 |
| `source`, `proposed_by` and `confirmed_by` on a decision | 8 |

A file that declares `0.1` may not use the additions, and the files of one comb may not mix versions. A tool that reads only 0.1 should refuse a 0.2 file and say so; it should not guess.

Worth a look when you move:

- Any face marked `empty` that is really "nothing should be here". Change it to `not_applicable` with a reason, and the warning goes.
- Any testing face marked `agrees`. Check it against section 5.

## 14. Questions for reviewers

1. Are these the right five faces, plus questions? What would you add or drop?
2. Is `settled` enough for a known failure, or does that need a condition of its own?
3. Should a border live in one of its two cells, or in a file of its own?
4. Should decisions live in the cell, or in one log for the whole project?
5. Could you write your own scenario area in this format without help? Where did it fight you?
6. Is anything here that your existing files already say better?
7. Is `not_applicable` worth a condition of its own, or would `empty` with a `reason` do?
8. Should a decision copied in by a tool sit with the others, as here, or in a list of its own until a person confirms it?
9. Does the meaning of `agrees` on the testing face match how you would use it?
