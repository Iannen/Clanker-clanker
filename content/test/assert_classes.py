from ship_gate import BaseFixtureTest
from app.exceptions import ProgramExit
from app.presentation import ActionResult
from tui.tui_service import IOControl
from app.constants import RepoContract


class EmptyRepoTests(BaseFixtureTest):
    TEMPLATE_FIXTURE_NAME = "empty_repo"

    def assert_escape_exits(self) -> dict:
        # could probably get into some for each action here? *future-problem*
        return {
            "input_sequence": [IOControl.ABORT_KEYS[0]],
            "expected": {
                "exit_code": 0,
                "exit_msg": ProgramExit.MSG_DECLINED_INIT
            }
        }

    def assert_ctrl_c_exits(self) -> dict:
        return {
            "input_sequence": [IOControl.ABORT_KEYS[1]],
            "expected": {
                "exit_code": 0,
                "exit_msg": ProgramExit.MSG_DECLINED_INIT
            }
        }

    def assert_clankerize_repo_contract(self) -> dict:
        contract_paths = [
            getattr(RepoContract, attr)
            for attr in dir(RepoContract)
            if not attr.startswith("_") and isinstance(getattr(RepoContract, attr), str)
        ]
        return {
            "input_sequence": ["yes", IOControl.ACCEPT_KEY],
            "expected": {
                "fs_paths_exist": contract_paths
            },
        }