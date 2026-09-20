from base_classes import BaseFixtureTest

from expectance_impls import (
    shadow_of,
    DiskStateImpl,
    ExitMsgImpl,
    PromptRenderImpl,
    StderrContainsImpl,
    UIRenderImpl,
    AtomicTest,
    Result
)

from app.presentation import ActionResult
from app.exceptions import TestSequenceEnded
from ports_adapters.ports import IOControl, PathTokens
from app.constants import RepoContract

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

class EmptyRepoTests(BaseFixtureTest):
    TEMPLATE_FIXTURE_NAME = "empty_repo"

    def assert_abort_keys_decline_init(self) -> list[AtomicTest]:
        return [
            AtomicTest(
                sequence=[key],
                expects=ExitMsg.contains(ActionResult.MSG_DECLINED_INIT),
                reset_sequence=True,
            )
            for key in IOControl.ABORT_KEYS
        ]

    def assert_end_of_sequence_terminates_properly(self) -> list[AtomicTest]:
        return AtomicTest(sequence=[],expects=ExitMsg.contains(TestSequenceEnded.__name__))

    def assert_clankerize_repo_contract(self) -> AtomicTest:
        return AtomicTest(
            sequence=["yes", IOControl.ACCEPT_KEY],
            expects=[
                DiskState.has(RepoContract.get_all_target_paths()),
                UIRender.contains(ActionResult.BOOTSTRAP_SUCCESS)
            ],
        )

    def navigate_ui_and_copy_prompts(self) -> list[AtomicTest]:
        return [
            AtomicTest(
                sequence=["1"],
                expects=UIRender.contains("Domain 'manifest-analysis' on key '1' selected"),
            ),
            AtomicTest(
                sequence=["a"],
                expects=[
                    UIRender.contains(ActionResult.COPIED_TO_CLIPBOARD)
                        .where("lines", lambda l: int(l) > 150)
                        .where("chars", lambda c: int(c) > 100)
                ],
            )
        ]