from base_classes import BaseFixtureTest
from expectance_impls import AtomicTest, SandboxOperations

from core.engine_deps import IOControl
from core import RepoContract, TestSequenceEnded, WorkspaceAlreadyInitialized, ActionResult


class EmptyRepoTests(BaseFixtureTest):
    TEMPLATE_FIXTURE_NAME = "empty_repo"

    def assert_end_of_sequence_terminates_properly(self) -> list[AtomicTest]:
        return AtomicTest(sequence=[]).expect_exit_msg(TestSequenceEnded.__name__)

    def assert_abort_keys_decline_init(self) -> list[AtomicTest]:
        return [
            AtomicTest(sequence=[key]).expect_exit_msg(ActionResult.MSG_DECLINED_INIT)
            for key in IOControl.ABORT_KEYS
        ]

    def assert_clankerize_repo_contract(self) -> list[AtomicTest]:
        return [
            AtomicTest(sequence=["yes", IOControl.ACCEPT_KEY])
                .expect_ui_contains(ActionResult.BOOTSTRAP_SUCCESS)
                .expect_disk_has(RepoContract.get_all_target_paths()),
        ]

    def navigate_ui_and_copy_prompts(self) -> list[AtomicTest]:
        ats = []
        prefix = ["1"]
        ats.append(
            AtomicTest(sequence=list(prefix))
                .expect_ui_contains("Domain 'manifest-analysis' on key '1' selected")
        )
        for c in "as":
            prefix.append(c)
            ats.append(
                AtomicTest(sequence=list(prefix))
                    .expect_ui_contains(ActionResult.COPIED_TO_CLIPBOARD)
                    .where("lines", lambda l: int(l) > 100)
                    .where("chars", lambda c: int(c) > 3000)
                    .expect_prompt_min_lines(50)
            )
        for c in "df":
            prefix.append(c)
            ats.append(
                AtomicTest(sequence=list(prefix))
                    .expect_ui_contains(ActionResult.UNBOUND_KEY)
                    .where("key", lambda k, target=c: str(k) == target)
            )
        return ats


class CorruptRepoTests(BaseFixtureTest):
    TEMPLATE_FIXTURE_NAME = "empty_repo"

    def assert_clankerize_fail(self) -> list[AtomicTest | SandboxOperations]:
        all_targets = list(RepoContract.get_all_target_paths())
        dir_targets = list(RepoContract.DIRS_TO_CREATE)
        file_targets = [dst for _, dst in RepoContract.MAPPINGS]

        actions: list[AtomicTest | SandboxOperations] = [
            AtomicTest(sequence=["yes", IOControl.ACCEPT_KEY])
                .expect_ui_contains(ActionResult.BOOTSTRAP_SUCCESS),
            SandboxOperations().rm(*all_targets),
        ]

        for dir_path in dir_targets:
            actions.extend([
                SandboxOperations().create_dirs(dir_path),
                AtomicTest(sequence=["yes", IOControl.ACCEPT_KEY])
                    .expect_exit_msg(WorkspaceAlreadyInitialized.__name__),
                SandboxOperations().rm(dir_path),
            ])

        for file_path in file_targets:
            actions.extend([
                SandboxOperations().create_file(file_path, content="blocking content"),
                AtomicTest(sequence=["yes", IOControl.ACCEPT_KEY])
                    .expect_exit_msg(WorkspaceAlreadyInitialized.__name__),
                SandboxOperations().rm(file_path),
            ])
        return actions