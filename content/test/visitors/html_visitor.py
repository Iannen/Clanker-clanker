from results import Outcome, RunResult, FileAnalysisResults, FileReport, AssertSuiteResult, MethodResult, ContainerResult, AtomicTestResult, ExpectanceResult, SandboxOperationsResult
import html


class HtmlReportVisitor:
    def visit_run_result(self, node: RunResult) -> str:
        display_name = html.escape(node.name.removeprefix("Run<").removesuffix(">"))
        status_badge = self._badge(node.outcome)

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

        suite_html_blocks = [suite.accept(self) for suite in node.assert_suite_results]
        file_analysis_html = "".join(
            fa.accept(self) for fa in node.file_analysis_results
        )
        total_import_violations = sum(
            fa.total_violations for fa in node.file_analysis_results
        )
        suites_content = "".join(suite_html_blocks)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Test Run Report - {display_name}</title>
  <style>
    :root {{
      --bg-primary: #0f172a;
      --bg-card: #1e293b;
      --bg-subtle: #334155;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --accent-pass: #22c55e;
      --accent-fail: #ef4444;
      --accent-undefined: #a855f7;
      --accent-warn: #f59e0b;
      --border-color: #334155;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background-color: var(--bg-primary);
      color: var(--text-main);
      padding: 1.5rem;
      line-height: 1.5;
    }}
    .container {{ max-width: 1000px; margin: 0 auto; }}
    .header-card {{
      background: var(--bg-card);
      border-radius: 12px;
      padding: 1.5rem;
      border: 1px solid var(--border-color);
      margin-bottom: 1.5rem;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }}
    .header-title-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
    }}
    .run-title {{ font-size: 1.5rem; font-weight: 700; font-family: monospace; }}
    .badge {{
      padding: 0.35rem 0.85rem;
      border-radius: 9999px;
      font-weight: 700;
      font-size: 0.875rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .badge-pass {{ background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid var(--accent-pass); }}
    .badge-fail {{ background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid var(--accent-fail); }}
    .badge-undefined {{ background: rgba(168, 85, 247, 0.2); color: #e9d5ff; border: 1px solid var(--accent-undefined); }}
    .stats-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
      gap: 1rem;
    }}
    .stat-box {{
      background: rgba(15, 23, 42, 0.6);
      padding: 0.75rem 1rem;
      border-radius: 8px;
      border: 1px solid var(--border-color);
      text-align: center;
    }}
    .stat-val {{ font-size: 1.5rem; font-weight: 800; }}
    .stat-lbl {{ font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; margin-top: 0.2rem; }}
    .filter-bar {{ display: flex; gap: 0.5rem; margin-bottom: 1.5rem; }}
    .filter-btn {{
      background: var(--bg-card);
      color: var(--text-muted);
      border: 1px solid var(--border-color);
      padding: 0.4rem 0.9rem;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.875rem;
      transition: all 0.2s;
    }}
    .filter-btn:hover, .filter-btn.active {{
      color: var(--text-main);
      border-color: #64748b;
      background: var(--bg-subtle);
    }}
    .section-card {{
      background: var(--bg-card);
      border-radius: 10px;
      border: 1px solid var(--border-color);
      margin-bottom: 1.25rem;
      overflow: hidden;
    }}
    .section-header {{
      padding: 1rem 1.25rem;
      background: rgba(255,255,255,0.02);
      display: flex;
      justify-content: space-between;
      align-items: center;
      cursor: pointer;
      user-select: none;
    }}
    .section-header:hover {{ background: rgba(255,255,255,0.04); }}
    .section-title {{ font-weight: 600; font-size: 1.1rem; display: flex; align-items: center; gap: 0.5rem; }}
    .content-block {{ padding: 1.25rem; border-top: 1px solid var(--border-color); }}
    .test-card {{
      background: #0f172a;
      border: 1px solid var(--border-color);
      border-radius: 6px;
      margin-bottom: 0.75rem;
    }}
    .test-header {{
      padding: 0.75rem 1rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.925rem;
      cursor: pointer;
    }}
    .test-details {{
      padding: 1rem;
      border-top: 1px solid var(--border-color);
      background: rgba(0,0,0,0.2);
      font-size: 0.875rem;
    }}
    .exp-list {{ margin-top: 0.5rem; list-style: none; }}
    .exp-item {{
      padding: 0.4rem 0.6rem;
      border-radius: 4px;
      margin-bottom: 0.3rem;
      font-family: monospace;
      font-size: 0.825rem;
      display: flex;
      justify-content: space-between;
    }}
    .exp-pass {{ background: rgba(34, 197, 94, 0.1); color: #86efac; }}
    .exp-fail {{ background: rgba(239, 68, 68, 0.15); color: #fca5a5; }}
    .exp-undefined {{ background: rgba(168, 85, 247, 0.15); color: #e9d5ff; }}
    .undefined-box {{
      background: rgba(168, 85, 247, 0.15);
      border: 1px solid var(--accent-undefined);
      color: #e9d5ff;
      padding: 0.75rem;
      border-radius: 6px;
      font-family: monospace;
      margin-top: 0.5rem;
    }}
    .frame-box {{
      background: #020617;
      padding: 0.5rem;
      border-radius: 4px;
      font-family: monospace;
      color: #94a3b8;
      font-size: 0.8rem;
      margin-top: 0.5rem;
    }}
    .hidden {{ display: none !important; }}
  </style>
</head>
<body>
<div class="container">
  <div class="header-card">
    <div class="header-title-row">
      <div>
        <div style="font-size: 0.8rem; color: var(--text-muted);">TEST RUN REPORT</div>
        <div class="run-title">{display_name}</div>
      </div>
      {status_badge}
    </div>
    <div class="stats-grid">
      <div class="stat-box">
        <div class="stat-val">{total}</div>
        <div class="stat-lbl">Total Tests</div>
      </div>
      <div class="stat-box" style="color: var(--accent-pass);">
        <div class="stat-val">{passed}</div>
        <div class="stat-lbl">Pass</div>
      </div>
      <div class="stat-box" style="color: var(--accent-fail);">
        <div class="stat-val">{failed}</div>
        <div class="stat-lbl">Fail</div>
      </div>
      <div class="stat-box" style="color: var(--accent-undefined);">
        <div class="stat-val">{undefined}</div>
        <div class="stat-lbl">Undefined</div>
      </div>
      <div class="stat-box" style="color: var(--accent-warn);">
        <div class="stat-val">{total_import_violations}</div>
        <div class="stat-lbl">Import Errs</div>
      </div>
    </div>
  </div>

  <div class="filter-bar">
    <button class="filter-btn active" onclick="filterAll(event)">All Results</button>
    <button class="filter-btn" onclick="filterNonPass(event)">Fail &amp; Undefined Only</button>
  </div>

  {file_analysis_html}
  {suites_content}
</div>

<script>
  function toggleSection(id) {{
    const el = document.getElementById(id);
    if (el) el.classList.toggle('hidden');
  }}

  function filterNonPass(e) {{
    document.querySelectorAll('.pass-suite').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
    e.target.classList.add('active');
  }}

  function filterAll(e) {{
    document.querySelectorAll('.suite-card').forEach(el => el.classList.remove('hidden'));
    document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
    e.target.classList.add('active');
  }}
</script>
</body>
</html>"""

    def visit_file_analysis_results(self, node: FileAnalysisResults) -> str:
        icon = self._icon(node.outcome)
        status_label = f"{node.total_files_checked} files inspected"
        reports_html = "".join(r.accept(self) for r in node.reports)

        return f"""
  <div class="section-card">
    <div class="section-header" onclick="toggleSection('import-body')">
      <div class="section-title">
        <span>{icon} Import Checker</span>
      </div>
      <span style="font-size: 0.85rem; color: var(--text-muted);">{status_label}</span>
    </div>
    <div id="import-body" class="content-block">
      {reports_html}
    </div>
  </div>"""

    def visit_file_report(self, node: FileReport) -> str:
        rel_path = html.escape(node.rel_path)
        if node.outcome == Outcome.PASS:
            return (
                f'<div style="font-size: 0.9rem; margin-bottom: 0.4rem;">'
                f'<span style="color: var(--accent-pass);">✅ {rel_path}</span></div>'
            )

        errors = (
            node.forbidden_import_statements
            + node.dangling_imports
            + node.undeclared_imports
        )
        err_items = "".join(f"<li>• {html.escape(err)}</li>" for err in errors)
        return f"""
      <div style="margin-bottom: 0.5rem; font-size: 0.9rem;">
        <span style="color: var(--accent-fail);">❌ {rel_path}</span>
        <ul style="margin-left: 1.5rem; font-family: monospace; font-size: 0.825rem; color: var(--text-muted);">
          {err_items}
        </ul>
      </div>"""

    def visit_assert_suite_result(self, node: AssertSuiteResult) -> str:
        suite_id = f"suite-{abs(hash(node.suite_name))}"
        icon = self._icon(node.outcome)
        suite_class = "pass-suite" if node.outcome == Outcome.PASS else "fail-suite"
        methods_html = "".join(m.accept(self) for m in node.method_results)

        return f"""
  <div class="section-card suite-card {suite_class}">
    <div class="section-header" onclick="toggleSection('{suite_id}')">
      <div class="section-title">
        <span>{icon} {html.escape(node.suite_name)}</span>
      </div>
      <span style="font-size: 0.85rem; color: var(--text-muted);">Report: {html.escape(node.report_filename)}</span>
    </div>
    <div id="{suite_id}" class="content-block">
      {methods_html}
    </div>
  </div>"""

    def visit_method_result(self, node: MethodResult) -> str:
        icon = self._icon(node.outcome)
        containers_html = "".join(c.accept(self) for c in node.container_results)

        return f"""
      <div style="margin-bottom: 0.5rem; font-weight: 600; color: #cbd5e1;">
        {icon} {html.escape(node.method_name)}
      </div>
      {containers_html}"""

    def visit_container_result(self, node: ContainerResult) -> str:
        parts = [node.test_result.accept(self)]
        if node.preop_result is not None:
            parts.append(
                '<strong style="margin-top: 0.75rem; display: block;">Pre-Sandbox Operations:</strong>'
                + node.preop_result.accept(self)
            )
        if node.postop_result is not None:
            parts.append(
                '<strong style="margin-top: 0.75rem; display: block;">Post-Sandbox Operations:</strong>'
                + node.postop_result.accept(self)
            )
        return "".join(parts)

    def visit_atomic_test_result(self, node: AtomicTestResult) -> str:
        test_id = f"test-{node.test_number}-{abs(hash(node.name))}"
        icon = self._icon(node.outcome)

        if node.outcome == Outcome.UNDEFINED:
            status_span = (
                '<span style="color: var(--accent-undefined); font-size: 0.8rem;">UNDEFINED</span>'
            )
            details_body = (
                '<div class="undefined-box">💀 Outcome UNDEFINED '
                '(test setup error or application terminated unexpectedly)</div>'
            )
        else:
            color = (
                "var(--text-muted)"
                if node.outcome == Outcome.PASS
                else "var(--accent-fail)"
            )
            status_span = (
                f'<span style="color: {color}; font-size: 0.8rem;">'
                f'{node.passed_expectances}/{node.total_expectances} expectances</span>'
            )
            exp_items = "".join(e.accept(self) for e in node.expectance_results)
            details_body = (
                f'<strong>Expectances:</strong><div class="exp-list">{exp_items}</div>'
            )

        frames_html = ""
        if node.frames:
            frame_lines = []
            for f in node.frames:
                cmd = html.escape(str(getattr(f, "cmd", getattr(f, "command", f))))
                exit_code = getattr(f, "exit_code", 0)
                frame_lines.append(f"$ {cmd} [exit code: {exit_code}]")
            frames_str = "<br>".join(frame_lines)
            frames_html = (
                '<strong style="margin-top: 0.75rem; display: block;">Execution Frames:</strong>'
                f'<div class="frame-box">{frames_str}</div>'
            )

        is_hidden = "hidden" if node.outcome == Outcome.PASS else ""

        return f"""
      <div class="test-card">
        <div class="test-header" onclick="toggleSection('{test_id}')">
          <span>{icon} Test #{node.test_number} - {html.escape(node.name)}</span>
          {status_span}
        </div>
        <div id="{test_id}" class="test-details {is_hidden}">
          {details_body}
          {frames_html}
        </div>
      </div>"""

    def visit_expectance_result(self, node: ExpectanceResult) -> str:
        css_cls = {
            Outcome.PASS: "exp-pass",
            Outcome.FAIL: "exp-fail",
            Outcome.UNDEFINED: "exp-undefined",
        }.get(node.outcome, "exp-fail")
        status_txt = html.escape(node.outcome.name)
        assertion = html.escape(node.assertion)
        details_html = (
            f'<div style="font-family: monospace; font-size: 0.8rem; color: #fca5a5; margin-top: 0.25rem;">'
            f'Details: {html.escape(node.details)}</div>'
            if node.details
            else ""
        )

        return f"""
          <div class="exp-item {css_cls}">
            <span>{assertion}</span>
            <span>{status_txt}</span>
          </div>
          {details_html}"""

    def visit_sandbox_operations_result(self, node: SandboxOperationsResult) -> str:
        op_lines = []
        for op_type, desc, outcome in node.operations:
            icon = self._icon(outcome)
            status = html.escape(outcome.name)
            op_lines.append(
                f"{icon} {html.escape(op_type)}: {html.escape(desc)} ({status})"
            )
        if node.disk_state:
            op_lines.append("disk state:")
            for entry in node.disk_state:
                op_lines.append(f"  {html.escape(entry)}")
        ops_str = "<br>".join(op_lines)
        return f'<div class="frame-box">{ops_str}</div>'

    @staticmethod
    def _icon(outcome: Outcome) -> str:
        return {
            Outcome.PASS: "✅",
            Outcome.FAIL: "❌",
            Outcome.UNDEFINED: "💀",
            Outcome.INIT: "?",
        }.get(outcome, "?")

    @staticmethod
    def _badge(outcome: Outcome) -> str:
        mapping = {
            Outcome.PASS: ('badge-pass', 'PASS'),
            Outcome.FAIL: ('badge-fail', 'FAIL'),
            Outcome.UNDEFINED: ('badge-undefined', 'UNDEFINED'),
        }
        css, label = mapping.get(outcome, ('badge-fail', outcome.name if hasattr(outcome, 'name') else str(outcome)))
        return f'<span class="badge {css}">{label}</span>'