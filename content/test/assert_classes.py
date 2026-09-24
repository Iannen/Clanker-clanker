from base_classes import BaseFixtureTest
from expectance_impls import (
    shadow_of,
    DiskStateImpl,
    ExitMsgImpl,
    PromptRenderImpl,
    StderrContainsImpl,
    UIRenderImpl,
    AtomicTest,
    SandboxOperations,
    Result
)

from core.engine_deps import IOControl
from core import RepoContract, TestSequenceEnded, WorkspaceAlreadyInitialized, ActionResult
from adapters.terminal.scripted_terminal_adapter import ScriptedTerminalAdapter


@shadow_of(ExitMsgImpl)
class ExitMsg:
    def contains(self, expected_msg: str) -> "ExitMsg": pass
    def to_result(self, run_state: dict) -> Result: pass

@shadow_of(StderrContainsImpl)
class StderrContains:
    def contains(self, expected_text: str) -> "StderrContains": pass
    def to_result(self, run_state: dict) -> Result: pass

@shadow_of(DiskStateImpl)
class DiskState:
    def has(self, expected_paths: list[str] | set[str]) -> "DiskState": pass
    def to_result(self, run_state: dict) -> Result: pass

@shadow_of(PromptRenderImpl)
class PromptRender:
    def contains(self, expected_prompt: str) -> "PromptRender": pass
    def to_result(self, run_state: dict) -> Result: pass

@shadow_of(UIRenderImpl)
class UIRender:
    def contains(self, template: str) -> "UIRender": pass
    def where(self, field: str, predicate: callable) -> "UIRender": pass
    def to_result(self, run_state: dict) -> Result: pass

END_APP = ScriptedTerminalAdapter.END_APP_EVENT

class EmptyRepoTests(BaseFixtureTest):
    TEMPLATE_FIXTURE_NAME = "empty_repo"

    def assert_end_of_sequence_terminates_properly(self) -> list[AtomicTest]:
        return AtomicTest(
            sequence=[],
            expects=StderrContains.contains(TestSequenceEnded.__name__),
            )

    def assert_abort_keys_decline_init(self) -> list[AtomicTest]:
        return [
            AtomicTest(
                sequence=[key],
                expects=ExitMsg.contains(ActionResult.MSG_DECLINED_INIT),
            )
            for key in IOControl.ABORT_KEYS
        ]

    def assert_clankerize_repo_contract(self) -> list[AtomicTest]:
        return [
            AtomicTest(
                sequence=["yes", IOControl.ACCEPT_KEY],
                expects = [
                    UIRender.contains(ActionResult.BOOTSTRAP_SUCCESS),
                    DiskState.has(RepoContract.get_all_target_paths())
                ],  
            ),
        ]

    def navigate_ui_and_copy_prompts(self) -> list[AtomicTest]:
        ats = []
        prefix = ["1"]
        ats.append(AtomicTest(
                sequence=list(prefix),
                expects=UIRender.contains("Domain 'manifest-analysis' on key '1' selected"),
            ))
        for c in "as":
            prefix.append(c)
            ats.append(
                AtomicTest(
                    sequence=list(prefix),
                    expects=[
                        UIRender.contains(ActionResult.COPIED_TO_CLIPBOARD)
                            .where("lines", lambda l: int(l) > 100)
                            .where("chars", lambda c: int(c) > 3000),
                        PromptRender.min_lines(50),
                    ]    
                )
            )
        for c in "df":
            prefix.append(c)
            ats.append(
                AtomicTest(
                    sequence=list(prefix),
                    expects = UIRender.contains(ActionResult.UNBOUND_KEY)
                        .where("key", lambda k, target=c: str(k) == target)
                )
            )
        return ats


class CorruptRepoTests(BaseFixtureTest):
    TEMPLATE_FIXTURE_NAME = "empty_repo"

    def assert_clankerize_fail(self) -> list[AtomicTest | SandboxOperations]:
        all_targets = list(RepoContract.get_all_target_paths())
        dir_targets = list(RepoContract.DIRS_TO_CREATE)
        file_targets = [dst for _, dst in RepoContract.MAPPINGS]

        actions: list[AtomicTest | SandboxOperations] = [
            AtomicTest(
                sequence=["yes", IOControl.ACCEPT_KEY],
                expects=UIRender.contains(ActionResult.BOOTSTRAP_SUCCESS),
            ),
            SandboxOperations().rm(*all_targets),
        ]

        for dir_path in dir_targets:
            actions.extend([
                SandboxOperations().create_dirs(dir_path),
                AtomicTest(
                    sequence=["yes", IOControl.ACCEPT_KEY],
                    expects=StderrContains.contains(WorkspaceAlreadyInitialized.__name__),
                ),
                SandboxOperations().rm(dir_path),
            ])

        for file_path in file_targets:
            actions.extend([
                SandboxOperations().create_file(file_path, content="blocking content"),
                AtomicTest(
                    sequence=["yes", IOControl.ACCEPT_KEY],
                    expects=StderrContains.contains(WorkspaceAlreadyInitialized.__name__),
                ),
                SandboxOperations().rm(file_path),
            ])

        return actions