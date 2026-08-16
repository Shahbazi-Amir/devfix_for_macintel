#!/usr/bin/env python3
from pathlib import Path

p = Path("tests/test_devfix_tunnel.sh")
text = p.read_text()
old = "grep -q -- '-u \"#$uid\"' \"$GUARDIAN\" || fail \"guardian marker path I/O does not drop to target UID\""
new = "grep -q 'user_exec .* /usr/bin/tee' \"$GUARDIAN\" || fail \"guardian marker writes are not user-scoped\""
if text.count(old) != 1:
    raise SystemExit(f"expected one static privilege assertion, found {text.count(old)}")
p.write_text(text.replace(old, new, 1))

rem = Path("docs/tunnel/remediations")
rem.mkdir(parents=True, exist_ok=True)
(rem / "005_TEST_STATIC_PATTERN_SC2016.md").write_text(
    "# Remediation 005 — TEST_STATIC_PATTERN_SC2016\n\n"
    "V4 product patching completed, but the new static security assertion itself triggered ShellCheck `SC2016` because it contained a literal shell variable name inside single quotes. The assertion was kept and rewritten to verify the `user_exec -> /usr/bin/tee` privilege-drop path without embedding a literal `$uid` expression. Product security logic and test coverage were not weakened.\n"
)
