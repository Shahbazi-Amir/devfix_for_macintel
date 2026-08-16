# Remediation 005 — TEST_STATIC_PATTERN_SC2016

V4 product patching completed, but the new static security assertion itself triggered ShellCheck `SC2016` because it contained a literal shell variable name inside single quotes. The assertion was kept and rewritten to verify the `user_exec -> /usr/bin/tee` privilege-drop path without embedding a literal `$uid` expression. Product security logic and test coverage were not weakened.
