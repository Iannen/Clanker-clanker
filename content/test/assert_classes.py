from base_classes import BaseFixtureTest

from expectance_impls import (
    ShadowBase,
    DiskStateImpl,
    ExitMsgImpl,
    PromptRenderImpl,
    StderrContainsImpl,
    UIRenderImpl,
    AtomicTest
)

from app.presentation import ActionResult
from app.exceptions import TestSequenceEnded
from ports_adapters.ports import IOControl, PathTokens
from app.constants import RepoContract

class ExitMsg(ShadowBase):
    IMPL_CLASS = ExitMsgImpl

    def to_result(self, run_state: dict, sandbox_dir: Path) -> Result:
        return self._impl.to_result(run_state, sandbox_dir)

class StderrContains(ShadowBase):
    IMPL_CLASS = StderrContainsImpl

    def to_result(self, run_state: dict, sandbox_dir: Path) -> Result:
        return self._impl.to_result(run_state, sandbox_dir)

class DiskState(ShadowBase):
    IMPL_CLASS = DiskStateImpl

    def to_result(self, run_state: dict, sandbox_dir: Path) -> Result:
        return self._impl.to_result(run_state, sandbox_dir)

class PromptRender(ShadowBase):
    IMPL_CLASS = PromptRenderImpl

    def to_result(self, run_state: dict, sandbox_dir: Path) -> Result:
        return self._impl.to_result(run_state, sandbox_dir)

class UIRender(ShadowBase):
    IMPL_CLASS = UIRenderImpl  
    def where(self, field: str, predicate: callable) -> "UIRender":
        self._impl.where(field, predicate)
        return self

    def to_result(self, run_state: dict, sandbox_dir: Path) -> Result:
        return self._impl.to_result(run_state, sandbox_dir)

class EmptyRepoTests(BaseFixtureTest):
    TEMPLATE_FIXTURE_NAME = "empty_repo"

    def assert_abort_keys_decline_init(self) -> list[AtomicTest]:
        return [
            AtomicTest(
                sequence=[key],
                expects=ExitMsg(ActionResult.MSG_DECLINED_INIT),
                reset_sequence=True,
            )
            for key in IOControl.ABORT_KEYS
        ]

    def assert_end_of_sequence_terminates_properly(self) -> list[AtomicTest]:
        return AtomicTest(sequence=[],expects=ExitMsg(TestSequenceEnded.__name__))

    def assert_clankerize_repo_contract(self) -> AtomicTest:
        return AtomicTest(
            sequence=["yes", IOControl.ACCEPT_KEY],
            expects=[
                DiskState(RepoContract.get_all_target_paths()),
                UIRender(ActionResult.BOOTSTRAP_SUCCESS)
            ],
        )

    def navigate_ui_and_copy_prompts(self) -> list[AtomicTest]:
        return [
            AtomicTest(
                sequence=["1"],
                expects=UIRender("Domain 'manifest-analysis' on key '1' selected"),
            ),
            AtomicTest(
                sequence=["a"],
                expects=UIRender(ActionResult.COPIED_TO_CLIPBOARD)
                    .where("lines", lambda l: int(l) > 150)
                    .where("chars", lambda c: int(c) > 100),)
        ]