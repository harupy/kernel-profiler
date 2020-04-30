import json
import os
from pprint import pprint

import requests


class GitHubAPI(requests.Session):
    def __init__(self, token):
        super().__init__()
        self.base_url = "https://api.github.com"

        # GitHub API requires User-Agent: https://developer.github.com/v3/#user-agent-required
        self.headers = {
            "Authorization": f"token {token}",
            "User-Agent": "",
        }

    def get(self, end_point, **kwargs):
        return super().get(self.base_url + end_point, **kwargs)

    def post(self, end_point, **kwargs):
        return super().post(self.base_url + end_point, **kwargs)


def main():
    GITHUB_API_TOKEN = os.environ.get("GITHUB_API_TOKEN")
    USER_NAME = os.environ.get("CIRCLE_PROJECT_USERNAME")
    REPO_NAME = os.environ.get("CIRCLE_PROJECT_REPONAME")
    BUILD_NUM = os.environ.get("CIRCLE_BUILD_NUM")
    SHA = os.environ.get("CIRCLE_SHA1")

    api = GitHubAPI(GITHUB_API_TOKEN)

    r = api.get(f"/repos/{USER_NAME}/{REPO_NAME}")
    REPO_ID = r.json()["id"]

    path = "0/output/m5-forecasting-accuracy.html"
    target_url = f"https://{BUILD_NUM}-{REPO_ID}-gh.circle-artifacts.com/{path}"

    params = {
        "state": "success",
        "target_url": target_url,
        "description": "Open the output HTML",
        "context": "ci/circleci: build_doc",
    }

    # Create a link to the output HTML as a commit status
    end_point = f"/repos/{USER_NAME}/{REPO_NAME}/statuses/{SHA}"
    r = requests.post(end_point, data=json.dumps(params))
    pprint(r.json())


if __name__ == "__main__":
    main()
