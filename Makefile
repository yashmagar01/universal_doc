# Templix task interface (canonical). recipes delegate to scripts/*.ps1 so that
# make and PowerShell always run the same checks (owner condition 4).
# make is not installed on this machine; use scripts/*.ps1 directly (see README).
.PHONY: setup dev check e2e fixtures lint typecheck unit parity

setup:
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/setup.ps1

dev:
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev.ps1

check:
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1

e2e:
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/e2e.ps1

fixtures:
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/fixtures.ps1
