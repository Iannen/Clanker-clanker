from base_classes import (
    AtomicTest,
    BaseFixtureTest,
    DiskState,
    ExitMsg,
    PromptRender,
    UIRender,
)
from app.presentation import ActionResult
from ports_adapters.ports import IOControl, PathTokens
from app.constants import RepoContract

class EmptyRepoTests(BaseFixtureTest):
    TEMPLATE_FIXTURE_NAME = "empty_repo"

    def assert_abort_keys_decline_init(self) -> list[AtomicTest]:
        return [
            AtomicTest(
                sequence=[key],
                expected=ExitMsg(ActionResult.MSG_DECLINED_INIT),
            )
            for key in IOControl.ABORT_KEYS
        ]

    def _assert_clankerize_repo_contract(self) -> AtomicTest:
        return AtomicTest(
            sequence=["yes", IOControl.ACCEPT_KEY],
            expected=DiskState(RepoContract.get_all_target_paths()),
        )

    def _navigate_ui_and_copy_prompts(self) -> list[AtomicTest]:
        return [
            AtomicTest(
                sequence=["1"],
                expected=UIRender(
                    "Domain 'manifest-analysis' on key '1' selected"
                ),
            ),
        ]