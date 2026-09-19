from typing import Any

import yaml


ANSI_LIGHT_BLUE = "\033[94m"
ANSI_RESET = "\033[0m"


def log_yaml(logger: Any, header: str, data: Any) -> None:
    separator = "#" * 80
    yaml_content = yaml.safe_dump(
        data,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
    ).rstrip()
    logger.info(f"\n{ANSI_LIGHT_BLUE}{separator}\n{header}\n{yaml_content}\n{separator}{ANSI_RESET}")