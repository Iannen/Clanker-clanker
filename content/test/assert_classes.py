from base_classes import (
    AtomicTest,
    BaseFixtureTest,
    DiskState,
    ExitMsg,
    PromptRender,
    UIRender,
    StderrContains,
    Regex
)
from app.presentation import ActionResult
from app.exceptions import TestSequenceEnded
from ports_adapters.ports import IOControl, PathTokens
from app.constants import RepoContract

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
                expects=UIRender(
                    Regex(
                        r"Copied (?P<lines>\d+) lines \((?P<chars>\d+) chars\) to clipboard",
                        validator=lambda m: int(m.group("lines")) > 0 and int(m.group("chars")) > 0
                    )
                ),
            )
        ]