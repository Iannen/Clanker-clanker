from results import Outcome, MethodResult, RunResult, AtomicTestResult, SandboxOperationsResult, SandboxOperationsResult, FileAnalysisResults, AssertSuiteResult, ContainerResult, ExpectanceResult, FileReport

class ConsoleReportVisitor:
    def visit_run_result(self, node: RunResult) -> str:
        display_name = node.name.removeprefix("Run<").removesuffix(">")

        lines = [
            "============================================================",
            f"Test results - {display_name}",
            "============================================================",
        ]

        for fa in node.file_analysis_results:
            lines.append(fa.accept(self))

        total = passed = failed = undefined = 0
        for suite in node.assert_suite_results:
            for test in suite.all_atomic_tests:
                total += 1
                if test.outcome == Outcome.PASS:
                    passed += 1
                elif test.outcome == Outcome.FAIL:
                    failed += 1
                else:
                    undefined += 1
            lines.append(suite.accept(self))

        lines.append("\n------------------------------------------------------------")
        lines.append(
            f"TOTAL: {total} tests | PASS: {passed} | "
            f"FAIL: {failed} | UNDEFINED: {undefined}"
        )
        lines.append("============================================================")
        return "\n".join(lines)

    def visit_file_analysis_results(self, node: FileAnalysisResults) -> str:
        icon = self._icon(node.outcome)
        if node.is_clean:
            return (
                f"{icon} Import Checker - {node.total_files_checked} files clean\n"
                "    Report: import_checker.json"
            )
        lines = [f"{icon} Import Checker"]
        for r in node.reports:
            if not r.is_clean:
                lines.append(r.accept(self))
        lines.append("    Report: import_checker.json")
        return "\n".join(lines)

    def visit_file_report(self, node: FileReport) -> str:
        icon = self._icon(node.outcome)
        lines = [f"    {icon} {node.rel_path}"]
        for err in (
            node.forbidden_import_statements
            + node.dangling_imports
            + node.undeclared_imports
        ):
            lines.append(f"        * {err}")
        return "\n".join(lines)

    def visit_assert_suite_result(self, node: AssertSuiteResult) -> str:
        icon = self._icon(node.outcome)
        lines = [f"\n{icon} {node.suite_name}"]
        for m in node.method_results:
            lines.append(m.accept(self))
        lines.append(f"    Report: {node.report_filename}")
        return "\n".join(lines)

    def visit_method_result(self, node: MethodResult) -> str:
        icon = self._icon(node.outcome)
        lines = [f"    {icon} {node.method_name}"]
        for container in node.container_results:
            lines.append(container.accept(self))
        return "\n".join(lines)

    def visit_container_result(self, node: ContainerResult) -> str:
        lines = [node.test_result.accept(self)]
        if node.preop_result is not None:
            lines.append(node.preop_result.accept(self))
        if node.postop_result is not None:
            lines.append(node.postop_result.accept(self))
        return "\n".join(lines)

    def visit_atomic_test_result(self, node: AtomicTestResult) -> str:
        icon = self._icon(node.outcome)
        header = (
            f"        {icon} Test #{node.test_number} - {node.name} - "
            f"{node.passed_expectances}/{node.total_expectances} expectances"
        )
        if node.outcome == Outcome.PASS:
            return header

        detail_lines = [header]
        for exp in node.expectance_results:
            detail_lines.append(exp.accept(self))
        return "\n".join(detail_lines)

    def visit_expectance_result(self, node: ExpectanceResult) -> str:
        icon = self._icon(node.outcome)
        line = f"            {icon} {node.assertion}"
        if node.details:
            line += f" — {node.details}"
        return line

    def visit_sandbox_operations_result(self, node: SandboxOperationsResult) -> str:
        icon = self._icon(node.outcome)
        lines = [f"            {icon} Sandbox operations"]
        for op, detail, outcome in node.operations:
            status = self._icon(outcome)
            lines.append(f"                {status} {op}: {detail}")
        if node.disk_state:
            lines.append("                disk state:")
            for entry in node.disk_state:
                lines.append(f"                    {entry}")
        return "\n".join(lines)

    @staticmethod
    def _icon(outcome: Outcome) -> str:
        return {
            Outcome.PASS: "✅",
            Outcome.FAIL: "❌",
            Outcome.UNDEFINED: "💀",
            Outcome.INIT: "?",
        }.get(outcome, "?")