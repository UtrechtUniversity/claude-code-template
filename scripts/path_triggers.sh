#!/usr/bin/env bash
#
# path_triggers.sh — emit shell-eval'able env vars naming the slow tests
# that must run on a PR despite -m "not slow" or the e2e smoke filter,
# given the diff between BASE and HEAD.
#
# Two reasons a slow test gets pulled into a PR run:
#
#   1. CHANGED.  The test file itself was added or modified in the PR.
#      A new or edited test must run regardless of its marker — that's
#      how the author finds out it works.  Applies to both backend and
#      e2e suites.
#
#   2. PATH-TRIGGERED.  The PR touches a source path mapped to slow
#      tests covering that path.  Catches the case where you change
#      a hot source file and break an integration test before the
#      nightly catches it next morning.  Update both the map AND
#      CLAUDE.md's "Slow tier — path triggers" table when adding
#      triggers.
#
# Usage:
#   eval "$(scripts/path_triggers.sh "$BASE_SHA")"
#
# After eval, three vars are set (any may be empty):
#
#   PT_BACKEND_FORCE_FILES   space-separated list of backend test files
#                            (paths relative to backend/) to run unfiltered
#                            — i.e. without -m "not slow"
#
#   PT_BACKEND_TESTMON_BYPASS  "1" if the diff touches non-Python data
#                            dependencies that pytest-testmon cannot
#                            see through (currently: anything under
#                            backend/tests/fixtures/).  When set, the
#                            ci.yml backend-test step drops --testmon
#                            for every batch — testmon hashes Python
#                            source blocks, so a JSON / CSV fixture
#                            change would slip past it.  Empty otherwise.
#
#   PT_E2E_FORCE_FILES       space-separated list of frontend e2e spec
#                            paths (relative to frontend/) to run on PR
#                            in addition to the smoke set.

set -eu
# pipefail intentionally NOT set — empty `grep` exits non-zero, which
# is normal here: an empty diff is a valid input.

BASE="${1:?usage: path_triggers.sh <BASE_SHA>}"
changed=$(git diff --name-only "$BASE"...HEAD || true)

# --- 1. Changed test files (always run, marker-independent) ---------------
# Exclude deletions: a removed test file can't be run, and forwarding it
# to pytest / playwright would error with "file or directory not found".

extant=$(git diff --name-only --diff-filter=d "$BASE"...HEAD || true)
backend_changed=$(echo "$extant" | grep -E '^backend/tests/.+\.py$' | sed 's|^backend/||' || true)
e2e_changed=$(echo "$extant"     | grep -E '^frontend/tests/e2e/.+\.spec\.ts$' | sed 's|^frontend/||' || true)

# --- 2. Path-triggered backend test files ---------------------------------
#
# Example: a change to backend/src/app/main.py or the routes/ directory
# is enough motivation to run the full API test file, even if testmon
# thinks no covered block changed.  Mirrors CLAUDE.md "Slow tier —
# path triggers".

extra_backend=""
if echo "$changed" | grep -qE '^backend/src/app/(main\.py|routes/)'; then
  extra_backend="$extra_backend tests/test_items.py tests/test_items_integration.py"
fi

# Fixture data dependencies (JSON, CSV, seed payloads) are loaded at
# test runtime but their content is invisible to testmon — the plugin
# hashes Python source blocks, not data files.  When the diff touches
# anything under backend/tests/fixtures/, disable the testmon filter
# for the whole backend-test job so fixture-driven tests re-run
# unconditionally.  No fixtures yet — extend as your project grows.
backend_testmon_bypass=""
if echo "$changed" | grep -qE '^backend/tests/fixtures/'; then
  backend_testmon_bypass="1"
fi

# --- 3. Path-triggered e2e specs ------------------------------------------
#
# The PR e2e fast tier runs the smoke set (smoke.spec.ts).  Specs below
# are nightly-by-default and pulled onto PR only when the mapped source
# area changes.  Keep this map in lock-step with CLAUDE.md.

extra_e2e=""
if echo "$changed" | grep -qE '^backend/src/app/routes/'; then
  extra_e2e="$extra_e2e tests/e2e/items-flow.spec.ts"
fi

# --- Combine + dedupe + emit ----------------------------------------------

dedupe() {
  tr -s '[:space:]' '\n' | awk 'NF && !seen[$0]++' | tr '\n' ' ' | sed 's/ $//'
}
all_backend=$(echo "$backend_changed $extra_backend" | dedupe)
all_e2e=$(echo "$e2e_changed $extra_e2e"             | dedupe)

printf 'PT_BACKEND_FORCE_FILES=%q\n'    "$all_backend"
printf 'PT_BACKEND_TESTMON_BYPASS=%q\n' "$backend_testmon_bypass"
printf 'PT_E2E_FORCE_FILES=%q\n'        "$all_e2e"
