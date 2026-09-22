import json
from pathlib import Path
from base_classes import TestSuiteResult
from import_checker import ImportReports


class GateInspector:
    def __init__(
        self,
        import_reports: ImportReports,
        test_results: list[TestSuiteResult],
        reports_dir: Path,
    ) -> None:
        self.import_reports = import_reports
        self.test_results = test_results
        self.reports_dir = reports_dir

    def evaluate_and_report(self) -> bool:
        print("\n============================================================")
        print(" SHIP GATE EVALUATION REPORT")
        print("============================================================")

        import_pass = self._report_import_verification()
        tests_pass = self._report_fixture_tests()

        all_assertions = []
        for suite in self.test_results:
            all_assertions.extend(suite.results)

        total_count = len(all_assertions)
        passed_count = sum(1 for r in all_assertions if r.passed)
        failed_count = total_count - passed_count

        print("\n------------------------------------------------------------")
        print(
            f"TOTAL: {total_count} assertions | PASSED: {passed_count} | FAILED: {failed_count}"
        )
        print("============================================================\n")

        self._write_json_reports()

        return import_pass and tests_pass

    def _report_import_verification(self) -> bool:
        print("\n[SUITE] ImportPolicySuite")
        if self.import_reports.is_clean:
            print(
                f"  - [PASS] Static import analysis ({self.import_reports.total_files_checked} files clean)"
            )
            print("  Summary: PASSED")
            return True

        for report in self.import_reports.reports:
            if not report.is_clean:
                print(f"  - [FAIL] {report.rel_path}")
                for err in (
                    report.forbidden_import_statements
                    + report.dangling_imports
                    + report.undeclared_imports
                ):
                    print(f"      * {err}")
        print("  Summary: FAILED")
        return False

    def _report_fixture_tests(self) -> bool:
        all_passed = True
        for suite in self.test_results:
            print(f"\n[SUITE] {suite.suite_name}")
            suite_passed = suite.passed

            for res in suite.results:
                status = "PASS" if res.passed else "FAIL"
                print(f"  - [{status}] {res.assertion}")
                if not res.passed:
                    if res.details:
                        print(f"      Details: {res.details}")

            if not suite_passed:
                all_passed = False

            summary = "PASSED" if suite_passed else "FAILED"
            print(f"  Summary: {summary}")

        return all_passed

    def _write_json_reports(self) -> None:
        import_data = [
            {
                "rel_path": r.rel_path,
                "forbidden_import_statements": r.forbidden_import_statements,
                "dangling_imports": r.dangling_imports,
                "undeclared_imports": r.undeclared_imports,
            }
            for r in self.import_reports.reports
        ]
        with open(
            self.reports_dir / "import_verification.json",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(import_data, f, indent=2)

        test_data = []
        for suite in self.test_results:
            suite_results = [r.to_dict() for r in suite.results]
            test_data.append(
                {"suite": suite.suite_name, "results": suite_results}
            )

        with open(
            self.reports_dir / "latest_run.json", "w", encoding="utf-8"
        ) as f:
            json.dump(test_data, f, indent=2)