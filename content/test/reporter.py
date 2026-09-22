import json
from pathlib import Path
from expectance_impls import Result

class GateInspector:
    def __init__(self, import_checker, test_instances, reports_dir: Path) -> None:
        self.import_checker = import_checker
        self.test_instances = test_instances
        self.reports_dir = reports_dir

    def evaluate_and_report(self) -> bool:
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        print("\n" + "=" * 60)
        print(" SHIP GATE EVALUATION REPORT")
        print("=" * 60)

        import_passed = self._evaluate_import_checker()

        all_passed = import_passed
        total_assertions = 0
        failed_assertions = 0

        for instance in self.test_instances:
            cls_name = instance.__class__.__name__
            report_file = self.reports_dir / f"{cls_name.lower()}.json"

            results_dicts = [
                res.to_dict() if isinstance(res, Result) else res
                for res in instance.results
            ]

            payload = {
                "test_class": cls_name,
                "fixture_used": instance.TEMPLATE_FIXTURE_NAME,
                "sandbox_dir": str(instance.sandbox_dir),
                "results": results_dicts,
            }

            report_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            instance_passed = True
            print(f"\n[SUITE] {cls_name}")

            for res in results_dicts:
                total_assertions += 1
                passed = res.get("passed", False)
                assertion = res.get("assertion", "")
                details = res.get("details", "")

                status = "PASS" if passed else "FAIL"

                if not passed:
                    instance_passed = False
                    all_passed = False
                    failed_assertions += 1

                print(f"  - [{status}] {assertion}")
                if not passed and details:
                    print(f"      Details: {details}")

            suite_status = "PASSED" if instance_passed else "FAILED"
            print(f"  Summary: {suite_status}")

        print("\n" + "-" * 60)
        print(
            f"TOTAL: {total_assertions} assertions | "
            f"PASSED: {total_assertions - failed_assertions} | "
            f"FAILED: {failed_assertions}"
        )
        print("=" * 60 + "\n")

        return all_passed

    def _evaluate_import_checker(self) -> bool:
        from dataclasses import asdict

        import_report_path = self.reports_dir / "import_verification.json"

        reports_dicts = [asdict(rep) for rep in self.import_checker.reports]

        # Write report JSON file
        import_report_path.write_text(
            json.dumps(reports_dicts, indent=2), encoding="utf-8"
        )

        total_violations = sum(
            len(rep.forbidden_import_statements)
            + len(rep.dangling_imports)
            + len(rep.undeclared_imports)
            for rep in self.import_checker.reports
        )

        print(f"\n[SUITE] ImportVerifier")
        if total_violations == 0:
            print(
                f"  - [PASS] Static import analysis ({len(self.import_checker.reports)} files clean)"
            )
            print("  Summary: PASSED")
            return True
        else:
            print(
                f"  - [FAIL] Static import analysis ({total_violations} violations found)"
            )
            for rep in self.import_checker.reports:
                categories = [
                    ("forbidden_imports", rep.forbidden_import_statements),
                    ("dangling_imports", rep.dangling_imports),
                    ("undeclared_imports", rep.undeclared_imports),
                ]
                for cat_name, violations in categories:
                    for v in violations:
                        print(f"      [{rep.rel_path}] {cat_name}: {v}")
            print("  Summary: FAILED")
            return False