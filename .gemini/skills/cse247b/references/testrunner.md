Test Runner
name: testrunner
Objective: Create a smarter test runner (Python, Verilog, etc.). Given a list of tests, it prioritizes tests to run based on past failures, but also checks the code diff (git diff) and uses an LLM to hint which tests are likely to fail, then runs those tests first.
Description: The setup should have a "read-only" visualization to see the results (e.g., https://github.com/Kyzune/Auto-Report or https://github.com/dorny/test-reporter).
It should integrate with HAgent, but ideally it should be stand-alone.
