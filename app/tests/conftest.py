from app.db import NotedDB
import pytest

results_table = []

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    
    if report.when == 'call':
        results_table.append({
            "name": item.name,
            "status": "PASS" if report.passed else "FAIL",
            "duration": f"{report.duration:.2f}s"
        })

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Prints the user-friendly report after all tests finish."""
    terminalreporter.section("TECHLABS AI ENGINEER - EVALUATION REPORT")
    
    header = f"{'Test Scenario':<40} | {'Status':<10} | {'Duration':<10}"
    terminalreporter.write_line(header)
    terminalreporter.write_line("-" * len(header))
    
    passed_count = 0
    for res in results_table:
        color = "green" if res["status"] == "PASS" else "red"
        if res["status"] == "PASS": passed_count += 1
        
        terminalreporter.write_line(
            f"{res['name']:<40} | ", black=True, bold=True
        )
        terminalreporter.write(f"{res['status']:<10}", **{color: True})
        terminalreporter.write_line(f" | {res['duration']:<10}")

    total = len(results_table)
    terminalreporter.write_line("-" * len(header))
    if total > 0:
        terminalreporter.write_line(f"FINAL SCORE: {passed_count}/{total} ({(passed_count/total)*100:.1f}%)")
    
@pytest.fixture(autouse=True)
def reset_singleton():
    """Ensure each test starts with a clean NotedDB singleton instance."""
    NotedDB._instance = None
    yield
    if NotedDB._instance:
        NotedDB._instance.close_connection()
    NotedDB._instance = None