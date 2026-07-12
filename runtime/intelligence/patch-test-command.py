from pathlib import Path

p = Path.home() / "AIFT/runtime/intelligence/test-runner.py"

s = p.read_text()

s = s.replace(
    '"npm run typecheck"',
    '"npm run check"'
)

p.write_text(s)

print("Updated TypeScript test command")
