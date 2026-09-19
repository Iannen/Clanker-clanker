from ship_gate import BaseFixtureTest
from app.presentation import ActionResult
from ports_adapters.ports import IOControl, PathTokens
from app.constants import RepoContract


class EmptyRepoTests(BaseFixtureTest):
    TEMPLATE_FIXTURE_NAME = "empty_repo"

    def assert_abort_keys_decline_init(self) -> list[dict]:
        return [
            {
                "input_sequence": [abort_key],
                "expected": {
                    "exit_code": 0,
                    "exit_msg": ActionResult.MSG_DECLINED_INIT
                }
            }
            for abort_key in IOControl.ABORT_KEYS
        ]

    def assert_clankerize_repo_contract(self) -> dict:
        clean_paths = [
            p.removeprefix(f"{PathTokens.PUD}/")
            for p in RepoContract.get_all_target_paths()
        ]
        return {
            "input_sequence": ["yes", IOControl.ACCEPT_KEY, IOControl.ABORT_KEYS[0]],
            "expected": {
                "fs_paths_exist": clean_paths
            },
        }