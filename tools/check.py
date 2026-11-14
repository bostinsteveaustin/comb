#!/usr/bin/env python3
"""Check a folder of Comb files.

    python3 tools/check.py examples/loanshelf/comb

Reads comb.yaml, cells/*.yaml and journeys/*.yaml. Reports errors (the files
break the format) and warnings (the files are valid but something is worth a
look). Exits 1 if there are errors.

It checks structure, references and the evidence each condition needs. It does
not open the artefacts that pointers name, and it does not judge whether two
statements really disagree. That is for people and for other tools.

Needs: pyyaml, jsonschema.
"""
import datetime
import json
import sys
from collections import Counter
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema" / "comb.schema.json"

# Which faces a cell is expected to have something in, by stage.
EXPECTED_FACES = {
    "concept": [],
    "specified": ["function", "testing"],
    "building": ["function", "testing"],
    "built": ["function", "testing"],
    "retired": [],
}


def plain(value):
    """YAML reads an unquoted 2026-09-10 as a date. The format wants text."""
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()[:10]
    if isinstance(value, dict):
        return {key: plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [plain(item) for item in value]
    return value


def load(path):
    with open(path, encoding="utf-8") as handle:
        return plain(yaml.safe_load(handle))


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, where, message):
        self.errors.append(f"{where}: {message}")

    def warn(self, where, message):
        self.warnings.append(f"{where}: {message}")


def validator_for(schema, definition):
    return Draft202012Validator({"$ref": f"#/$defs/{definition}", "$defs": schema["$defs"]})


def check_schema(report, validator, data, where):
    ok = True
    for problem in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
        ok = False
        at = "/".join(str(part) for part in problem.absolute_path) or "(top)"
        report.error(where, f"{at}: {problem.message}")
    return ok


def check_mark(report, where, mark, cell, is_face=False):
    """The evidence each condition needs."""
    condition = mark["condition"]
    statements = mark.get("statements", [])
    question_ids = {q["id"] for q in cell.get("questions", [])}
    decision_ids = {d["id"] for d in cell.get("decisions", [])}

    if condition == "empty" and not is_face:
        report.error(where, "only a face can be 'empty'")
    if condition == "not_applicable":
        if not is_face:
            report.error(where, "only a face can be 'not_applicable'")
        if not mark.get("reason"):
            report.error(where, "'not_applicable' needs a reason")
        if mark.get("points_to"):
            report.error(where, "'not_applicable' but it points to something")
    if condition == "empty" and mark.get("points_to"):
        report.error(where, "'empty' but it points to something")
    if condition == "disputed" and len(statements) < 2:
        report.error(where, "'disputed' needs at least two statements, each with a pointer")
    if condition == "agrees":
        tests = [p for p in mark.get("evidence", []) if p.get("kind") == "test"]
        if not tests:
            report.error(where, "'agrees' needs evidence: a pointer of kind 'test'")
    if condition == "open":
        if "question" not in mark:
            report.error(where, "'open' needs the id of a question")
        elif mark["question"] not in question_ids:
            report.error(where, f"question '{mark['question']}' is not in this cell")
    if condition == "settled":
        if "decision" not in mark:
            report.error(where, "'settled' needs the id of a decision")
        elif mark["decision"] not in decision_ids:
            report.error(where, f"decision '{mark['decision']}' is not in this cell")
    if condition == "unreachable" and not mark.get("reason"):
        report.error(where, "'unreachable' needs a reason")
    if condition == "settled" and mark.get("proposed_by") and not mark.get("confirmed_by"):
        report.error(where, "'settled' cannot be a proposal: a person decides")
    if condition == "unchecked" and is_face and not mark.get("points_to"):
        report.warn(where, "'unchecked' but it points to nothing")
    if condition == "agrees" and where.endswith("face:testing") and not mark.get("points_to"):
        report.warn(where, "'agrees' on the testing face, but it points to no scenarios for the tests to agree with")
    if condition == "settled" and mark.get("decision") in cell.get("_unconfirmed_decisions", ()):
        report.error(where, f"'settled' rests on decision '{mark['decision']}', which a person has not confirmed")


def pointers_in(value):
    """Every pointer anywhere inside a file."""
    if isinstance(value, dict):
        if "path" in value and "at" in value:
            yield value
        for item in value.values():
            yield from pointers_in(item)
    elif isinstance(value, list):
        for item in value:
            yield from pointers_in(item)


# What 0.2 added. A file that declares 0.1 may use none of it.
def uses_0_2(data):
    found = []
    if isinstance(data, dict):
        if data.get("repositories"):
            found.append("repositories")
        for face in (data.get("faces") or {}).values():
            if isinstance(face, dict) and face.get("condition") == "not_applicable":
                found.append("not_applicable")
        for decision in data.get("decisions") or []:
            if isinstance(decision, dict):
                found += [key for key in ("source", "proposed_by", "confirmed_by") if key in decision]
    return sorted(set(found))


def check_version(report, data, where, versions):
    version = data.get("comb")
    versions[version] = versions.get(version, 0) + 1
    if version == "0.1":
        for feature in uses_0_2(data):
            report.error(where, f"'{feature}' was added in 0.2, and this file declares 0.1")


def check_repos(report, data, where, declared):
    """A pointer to another repository should name one the project declares."""
    named = sorted({p["repo"] for p in pointers_in(data) if "repo" in p})
    for repo in named:
        if declared is None:
            if data.get("comb") != "0.1":
                report.warn(where, f"points into '{repo}', and comb.yaml declares no repositories")
        elif repo not in declared:
            report.error(where, f"points into '{repo}', which comb.yaml does not declare")


def check_cell(report, cell, where, known_ids, project_id):
    # A decision copied in by a tool is a proposal until a person confirms it.
    cell["_unconfirmed_decisions"] = {
        d["id"] for d in cell.get("decisions", []) if d.get("proposed_by") and not d.get("confirmed_by")
    }

    if cell["parent"] not in known_ids and cell["parent"] != project_id:
        report.error(where, f"parent '{cell['parent']}' is not the project or a cell")
    if cell["parent"] == cell["id"]:
        report.error(where, "a cell cannot be its own parent")

    for name, face in cell["faces"].items():
        check_mark(report, f"{where} face:{name}", face, cell, is_face=True)
    for name in EXPECTED_FACES[cell["stage"]]:
        if cell["faces"][name]["condition"] == "empty":
            report.warn(where, f"face '{name}' is empty on a cell at stage '{cell['stage']}'")

    for seam in cell.get("seams", []):
        check_mark(report, f"{where} seam:{'/'.join(seam['between'])}", seam, cell)

    for border in cell.get("borders", []):
        label = f"{where} border:{border['with']}"
        if border["with"] not in known_ids:
            report.error(label, "no such cell")
        if border["with"] == cell["id"]:
            report.error(label, "a cell cannot border itself")
        check_mark(report, label, border, cell)

    decision_ids = [d["id"] for d in cell.get("decisions", [])]
    for repeated in [i for i, n in Counter(decision_ids).items() if n > 1]:
        report.error(where, f"decision id '{repeated}' is used twice")
    question_ids = [q["id"] for q in cell["questions"]]
    for repeated in [i for i, n in Counter(question_ids).items() if n > 1]:
        report.error(where, f"question id '{repeated}' is used twice")

    for question in cell["questions"]:
        label = f"{where} question:{question['id']}"
        if question["condition"] == "settled":
            if "decision" not in question:
                report.error(label, "'settled' needs the id of a decision")
            elif question["decision"] not in decision_ids:
                report.error(label, f"decision '{question['decision']}' is not in this cell")
            elif question["decision"] in cell["_unconfirmed_decisions"]:
                report.error(label, f"'settled' rests on decision '{question['decision']}', which a person has not confirmed")
        if question["condition"] in ("open", "reopened") and "watched_by" not in question:
            report.warn(label, "nothing is watching this question")

    for decision in cell.get("decisions", []):
        label = f"{where} decision:{decision['id']}"
        about = decision["about"]
        if about.startswith("question:") and about.split(":", 1)[1] not in question_ids:
            report.error(label, f"it is about '{about}', which is not in this cell")
        if about.startswith("border:") and about.split(":", 1)[1] not in known_ids:
            report.error(label, f"it is about '{about}', which is not a cell")
        if decision.get("proposed_by") and not decision.get("source"):
            report.error(label, "a decision copied in by a tool needs a source: where it was first recorded")
        if not decision.get("proof"):
            report.warn(label, "no proof yet: no test holds this decision in place")


def main(folder):
    root = Path(folder)
    report = Report()
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    project_file = root / "comb.yaml"
    if not project_file.exists():
        print(f"No comb.yaml in {root}")
        return 1
    project = load(project_file)
    if not check_schema(report, validator_for(schema, "project"), project, "comb.yaml"):
        project_id = None
    else:
        project_id = project["id"]
    versions = {}
    declared = None
    if isinstance(project, dict):
        check_version(report, project, "comb.yaml", versions)
        if project_id and "repositories" in project:
            declared = {r["name"] for r in project["repositories"]}
            for repeated in [n for n, c in Counter(r["name"] for r in project["repositories"]).items() if c > 1]:
                report.error("comb.yaml", f"repository '{repeated}' is declared twice")
        check_repos(report, project, "comb.yaml", declared)

    cells = {}
    set_aside = set()  # ids of cell files that broke the format; kept so other files do not report them missing
    cell_validator = validator_for(schema, "cell")
    for path in sorted((root / "cells").glob("*.yaml")):
        where = f"cells/{path.name}"
        cell = load(path)
        if not check_schema(report, cell_validator, cell, where):
            report.error(where, "fix the lines above first; the other checks were skipped for this file")
            set_aside.add(cell.get("id") if isinstance(cell, dict) and isinstance(cell.get("id"), str) else path.stem)
            continue
        check_version(report, cell, where, versions)
        check_repos(report, cell, where, declared)
        if cell["id"] != path.stem:
            report.error(where, f"id '{cell['id']}' does not match the file name")
        if cell["id"] in cells:
            report.error(where, f"id '{cell['id']}' is used twice")
        if cell["id"] == project_id:
            report.error(where, "a cell cannot share the project's id")
        cells[cell["id"]] = (cell, where)

    for cell, where in cells.values():
        check_cell(report, cell, where, set(cells) | set_aside, project_id)

    # A border is declared once, in either of the two cells.
    seen = {}
    for cell, where in cells.values():
        for border in cell.get("borders", []):
            pair = tuple(sorted((cell["id"], border["with"])))
            if pair in seen:
                report.error(where, f"border with '{border['with']}' is already declared in {seen[pair]}")
            seen[pair] = where

    journeys = {}
    journey_validator = validator_for(schema, "journey")
    for path in sorted((root / "journeys").glob("*.yaml")):
        where = f"journeys/{path.name}"
        journey = load(path)
        if not check_schema(report, journey_validator, journey, where):
            continue
        check_version(report, journey, where, versions)
        if journey["id"] != path.stem:
            report.error(where, f"id '{journey['id']}' does not match the file name")
        journeys[journey["id"]] = journey
        for number, step in enumerate(journey["steps"], start=1):
            label = f"{where} step {number}"
            if "cell" not in step:
                report.warn(label, "no cell: nothing on the map holds this step")
            elif step["cell"] not in cells and step["cell"] not in set_aside:
                report.error(label, f"no such cell '{step['cell']}'")
            if step["reach"] == "unreachable" and not step.get("reason"):
                report.error(label, "'unreachable' needs a reason")

    if len(versions) > 1:
        mix = ", ".join(f"{count} at {version}" for version, count in sorted(versions.items()))
        report.error("comb.yaml", f"the files declare different versions ({mix}); a comb is written to one")

    on_a_journey = {s.get("cell") for j in journeys.values() for s in j["steps"]}
    for cell_id, (cell, where) in cells.items():
        if journeys and cell_id not in on_a_journey and cell["stage"] != "retired":
            report.warn(where, "no journey passes through this cell")

    tally = Counter()
    proposals = 0
    proposed_decisions = 0
    for cell, _ in cells.values():
        proposed_decisions += len(cell.get("_unconfirmed_decisions", ()))
        marks = list(cell["faces"].values()) + cell.get("seams", []) + cell.get("borders", [])
        for mark in marks:
            tally[mark["condition"]] += 1
            if mark.get("proposed_by") and not mark.get("confirmed_by"):
                proposals += 1

    print(f"{project.get('name', root.name)}: {len(cells)} cells, {len(journeys)} journeys")
    if tally:
        print("Conditions on faces, seams and borders:")
        for condition, count in sorted(tally.items(), key=lambda item: (-item[1], item[0])):
            print(f"  {condition:<16}{count}")
    if proposals:
        print(f"Proposed and not yet confirmed by a person: {proposals}")
    if proposed_decisions:
        print(f"Earlier decisions copied in and not yet confirmed by a person: {proposed_decisions}")
    if report.errors:
        print(f"\n{len(report.errors)} errors")
        for line in report.errors:
            print(f"  error    {line}")
    if report.warnings:
        print(f"\n{len(report.warnings)} warnings")
        for line in report.warnings:
            print(f"  warning  {line}")
    if not report.errors and not report.warnings:
        print("\nNo errors, no warnings.")
    return 1 if report.errors else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
