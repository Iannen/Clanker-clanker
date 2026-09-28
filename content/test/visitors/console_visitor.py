class ConsoleReportVisitor:
    def visit_run_result(self, node) -> str:
        display_name = node.name.removeprefix("Run<").removesuffix(">")

        lines = [
            "============================================================",
            f"Test results - {display_name}",
            "============================================================",
        ]

        for fa in node.file_analysis_results:
            lines.append(fa.accept(self))

        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        crashed_tests = 0

        for suite in node.assert_suite_results:
            total_tests += suite.total_tests
            passed_tests += suite.passed_tests
            failed_tests += suite.failed_tests
            crashed_tests += suite.crashed_tests
            lines.append(suite.accept(self))

        lines.append("\n------------------------------------------------------------")
        lines.append(
            f"TOTAL: {total_tests} tests | PASSED: {passed_tests} | "
            f"FAILED: {failed_tests} | CRASHED: {crashed_tests}"
        )
        lines.append("============================================================")

        return "\n".join(lines)

    def visit_file_analysis_results(self, node) -> str:
        if node.is_clean:
            lines = [
                f"✅ Import Checker - {node.total_files_checked} files clean",
                "    Report: import_checker.json",
            ]
        else:
            lines = ["❌ Import Checker"]
            for r in node.reports:
                if not r.is_clean:
                    lines.extend(r.accept(self))
            lines.append("    Report: import_checker.json")
        return "\n".join(lines)

    def visit_file_report(self, node) -> list[str]:
        lines = [f"    ❌ {node.rel_path}"]
        for err in (
            node.forbidden_import_statements
            + node.dangling_imports
            + node.undeclared_imports
        ):
            lines.append(f"        * {err}")
        return lines

    def visit_assert_suite_result(self, node) -> str:
        class_icon = "✅" if node.passed else "❌"
        lines = [f"\n{class_icon} {node.suite_name}"]
        for m in node.method_results:
            lines.append(m.accept(self))
        lines.append(f"    Report: {node.report_filename}")
        return "\n".join(lines)

    def visit_method_result(self, node) -> str:
        method_icon = "✅" if node.passed else "❌"
        lines = [f"    {method_icon} {node.method_name}"]
        for test in node.atomic_tests:
            lines.append(test.accept(self))
        return "\n".join(lines)

    def visit_atomic_test_result(self, node) -> str:
        if node.crashed:
            return f"        💀 Test #{node.test_number} - Application terminated unexpectedly"
        test_icon = "✅" if node.passed else "❌"
        return (
            f"        {test_icon} Test #{node.test_number} - "
            f"{node.passed_expectances}/{node.total_expectances} expectances"
        )

    def visit_container_result(self, node):
        pass

    def visit_expectance_result(self, node):
        pass

    def visit_sandbox_operations_result(self, node):
        pass