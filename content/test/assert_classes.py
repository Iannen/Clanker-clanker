from abc import ABC, abstractmethod
from typing import Callable, Self, Union

from core.engine_deps import IOControl
from core import RepoContract, WorkspaceAlreadyInitialized, ActionResult
from adapters.terminal.scripted_terminal_adapter import TestSequenceEnded

class Sandbox(ABC):
    @abstractmethod
    def create_dirs(self, *paths: str) -> Self: ...

    @abstractmethod
    def create_file(self, path: str, content: str = "") -> Self: ...

    @abstractmethod
    def edit_file(self, path: str, old: str, new: str) -> Self:...

    @abstractmethod
    def rm(self, *paths: str) -> Self: ...


class Execution(ABC):
    @abstractmethod
    def expect_exit_msg(self, expected_msg: str) -> Self: ...

    @abstractmethod
    def expect_disk_has(self, expected_paths: list[str] | set[str]) -> Self: ...

    @abstractmethod
    def expect_ui_contains(self, template: str) -> Self: ...

    @abstractmethod
    def where(self, field: str, predicate: Callable[[str], bool]) -> Self: ...

    @abstractmethod
    def expect_prompt_contains(self, expected_prompt: str) -> Self: ...

    @abstractmethod
    def expect_prompt_min_lines(self, count: int) -> Self: ...

class ActionsFactory(ABC):
    @abstractmethod
    def create_test(self, sequence: list[str], name: str = "") -> "TestContainer": ...


class EmptyRepoTests:
    TEMPLATE_FIXTURE_NAME = "empty_repo"

    def assert_end_of_sequence_terminates_properly(self, actions: ActionsFactory) -> list["TestContainer"]:
        return [
            actions.create_test([]) \
                .expect.expect_exit_msg(TestSequenceEnded.__name__)
        ]

    def assert_abort_keys_decline_init(self, actions: ActionsFactory) -> list["TestContainer"]:
        return [
            actions.create_test([key]) \
                .expect.expect_exit_msg(ActionResult.MSG_DECLINED_INIT)
            for key in IOControl.ABORT_KEYS
        ]

    def assert_clankerize_repo_contract(self, actions: ActionsFactory) -> list["TestContainer"]:
        return [
            actions.create_test(["yes", IOControl.ACCEPT_KEY]) \
                .expect.expect_ui_contains(ActionResult.BOOTSTRAP_SUCCESS) \
                .expect.expect_disk_has(RepoContract.get_all_target_paths()),
        ]

    def navigate_ui_and_copy_prompts(self, actions: ActionsFactory) -> list["TestContainer"]:
        ats = []
        prefix = ["1"]
        ats.append(
            actions.create_test(list(prefix)) \
                .expect.expect_ui_contains("Domain 'manifest-analysis' on key '1' selected")
        )
        for c in "as":
            prefix.append(c)
            ats.append(
                actions.create_test(list(prefix)) \
                    .expect.expect_ui_contains(ActionResult.COPIED_TO_CLIPBOARD) \
                    .expect.where("lines", lambda l: int(l) > 100) \
                    .expect.where("chars", lambda c: int(c) > 3000) \
                    .expect.expect_prompt_min_lines(50)
            )
        for c in "df":
            prefix.append(c)
            ats.append(
                actions.create_test(list(prefix)) \
                    .expect.expect_ui_contains(ActionResult.UNBOUND_KEY) \
                    .expect.where("key", lambda k, target=c: str(k) == target)
            )
        return ats


class CorruptRepoTests:
    TEMPLATE_FIXTURE_NAME = "empty_repo"

    def assert_clankerize_fail(self, actions: ActionsFactory) -> list["TestContainer"]:
        all_targets = list(RepoContract.get_all_target_paths())
        dir_targets = list(RepoContract.DIRS_TO_CREATE)
        file_targets = [dst for _, dst in RepoContract.MAPPINGS]

        items = [
            actions.create_test(["yes", IOControl.ACCEPT_KEY]) \
                .expect.expect_ui_contains(ActionResult.BOOTSTRAP_SUCCESS) \
                .postop.rm(*all_targets)
        ]

        for dir_path in dir_targets:
            items.append(
                actions.create_test(["yes", IOControl.ACCEPT_KEY]) \
                    .preop.create_dirs(dir_path) \
                    .expect.expect_exit_msg(WorkspaceAlreadyInitialized.__name__) \
                    .postop.rm(dir_path)
            )

        for file_path in file_targets:
            items.append(
                actions.create_test(["yes", IOControl.ACCEPT_KEY]) \
                    .preop.create_file(file_path, content="blocking content") \
                    .expect.expect_exit_msg(WorkspaceAlreadyInitialized.__name__) \
                    .postop.rm(file_path)
            )
        return items