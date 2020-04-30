import argparse
import json
import os

import requests


class GitHubAPI(requests.Session):
    def __init__(self, token):
        super().__init__()
        self.base_url = "https://api.github.com"

        # GitHub API requires User-Agent:
        # https://developer.github.com/v3/#user-agent-required
        self.headers = {
            "Authorization": f"token {token}",
            "User-Agent": "",
        }

    def get(self, end_point, **kwargs):
        return super().get(self.base_url + end_point, **kwargs)

    def post(self, end_point, **kwargs):
        return super().post(self.base_url + end_point, **kwargs)


def parse_args():
    parser = argparse.ArgumentParser(description="Kernel Profiler")
    parser.add_argument(
        "-p",
        "--path",
        required=True,
        help="Path to a file you want to create a link for",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    GITHUB_API_TOKEN = os.environ.get("GITHUB_API_TOKEN")
    USER_NAME = os.environ.get("CIRCLE_PROJECT_USERNAME")
    REPO_NAME = os.environ.get("CIRCLE_PROJECT_REPONAME")
    BUILD_NUM = os.environ.get("CIRCLE_BUILD_NUM")
    SHA = os.environ.get("CIRCLE_SHA1")

    api = GitHubAPI(GITHUB_API_TOKEN)

    r = api.get(f"/repos/{USER_NAME}/{REPO_NAME}")
    REPO_ID = r.json()["id"]

    target_url = f"https://{BUILD_NUM}-{REPO_ID}-gh.circle-artifacts.com/0/{args.path}"

    params = {
        "state": "success",
        "target_url": target_url,
        "description": "Open the output HTML",
        "context": "ci/circleci: create_example_link",
    }

    # Create a link to the output HTML as a commit status
    end_point = f"/repos/{USER_NAME}/{REPO_NAME}/statuses/{SHA}"
    r = api.post(end_point, data=json.dumps(params))

    assert r.status_code == 201


if __name__ == "__main__":
    main()
