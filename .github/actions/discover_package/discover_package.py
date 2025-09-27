import os
import sys
import logging
from package_info import VersionInfo

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

logger = logging.getLogger(__name__)


def main():
    info = VersionInfo.get_latest()
    logger.info("collected current version info: %s", info)

    gh_out = os.getenv("GITHUB_OUTPUT")
    if not gh_out:
        logger.error("GITHUB_OUTPUT not set; are we running outside GitHub Actions?")
        sys.exit(1)

    data = info.to_dict()
    with open(gh_out, "a") as f:
        for k, v in data.items():
            print(f'{k}={v}', file=f)
            logger.debug(f'exported: {k}={v}')


if __name__ == "__main__":
    main()
