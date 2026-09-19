from ship_gate import BaseFixtureTest, COMMAND, INFOSOURCE
from app.presentation import ActionResult
from ports_adapters.ports import IOControl, PathTokens
from app.constants import RepoContract


class EmptyRepoTests(BaseFixtureTest):
    TEMPLATE_FIXTURE_NAME = "empty_repo"

    def abort_keys_decline_init(self) -> list[dict]:
        return [
            {
                "before": COMMAND.START_APP,
                "sequence": [key],
                "expected": {
                    "source": INFOSOURCE.PROGRAM_EXIT_MSG,
                    "value": ActionResult.MSG_DECLINED_INIT,
                },
            }
            for key in IOControl.ABORT_KEYS
        ]

    def clankerize_repo_contract(self) -> dict:
        clean_paths = [
            p.removeprefix(f"{PathTokens.PUD}/")
            for p in RepoContract.get_all_target_paths()
        ]
        return {
            "before": COMMAND.START_APP,
            "sequence": ["yes", IOControl.ACCEPT_KEY],
            "expected": {
                "source": INFOSOURCE.DISK,
                "value": clean_paths,
            },
        }

    def navigate_ui_and_copy_prompts(self) -> list[dict]:
        return [
            {
                "sequence": ["1"],  # select domain
                "expected": {
                    "source": INFOSOURCE.TERMINAL_WRITE,
                    "value": "Domain <..> on key <..> selected",
                },
            },
            {
                "sequence": ["q"],  # select prompt 'q'
                "expected": {
                    "source": INFOSOURCE.TO_CLIPBOARD_CONTENT,
                    "value": "Copied <..> lines (<..> chars) to clipboard",
                },
            },
            {
                "sequence": ["w"],  # select prompt 'w'
                "expected": {
                    "source": INFOSOURCE.TO_CLIPBOARD_CONTENT,
                    "value": "Copied <..> lines (<..> chars) to clipboard",
                },
                "after": COMMAND.TERMINATE_APP,
            },
        ]