class JsonSerializerVisitor:
    def visit_run_result(self, node) -> dict:
        return {
            "name": node.name,
            "passed": node.passed,
            "file_analysis_results": [
                fa.accept(self) for fa in node.file_analysis_results
            ],
            "assert_suite_results": [
                suite.accept(self) for suite in node.assert_suite_results
            ],
        }

    def visit_file_analysis_results(self, node) -> list[dict]:
        return [r.accept(self) for r in node.reports]

    def visit_file_report(self, node) -> dict:
        return {
            "rel_path": node.rel_path,
            "forbidden_import_statements": node.forbidden_import_statements,
            "dangling_imports": node.dangling_imports,
            "undeclared_imports": node.undeclared_imports,
        }

    def visit_assert_suite_result(self, node) -> dict:
        return {
            "suite_name": node.suite_name,
            "report_filename": node.report_filename,
            "passed": node.passed,
            "methods": [m.accept(self) for m in node.method_results],
        }

    def visit_method_result(self, node) -> dict:
        return {
            "method_name": node.method_name,
            "passed": node.passed,
            "container_results": [c.accept(self) for c in node.container_results],
        }

    def visit_container_result(self, node) -> dict:
        return {
            "test_result": node.test_result.accept(self),
            "preop_result": node.preop_result.accept(self) if node.preop_result else None,
            "postop_result": node.postop_result.accept(self) if node.postop_result else None,
            "passed": node.passed,
        }

    def visit_atomic_test_result(self, node) -> dict:
        return {
            "test_number": node.test_number,
            "name": node.name,
            "passed": node.passed,
            "crashed": node.crashed,
            "crash_message": node.crash_message,
            "expectances": [r.accept(self) for r in node.expectance_results],
            "frames": [frame.__dict__ for frame in node.frames],
        }

    def visit_expectance_result(self, node) -> dict:
        res = {
            "assertion": node.assertion,
            "passed": node.passed,
        }
        if node.details:
            res["details"] = node.details
        return res

    def visit_sandbox_operations_result(self, node) -> dict:
        return {
            "type": "sandbox_operations",
            "passed": node.passed,
            "operations": [
                {
                    "operation": op_type,
                    "description": desc,
                    "passed": passed,
                }
                for op_type, desc, passed in node.operations
            ],
            "disk_state": node.disk_state,
        }