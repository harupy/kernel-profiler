import os


def main():
    # GITHUB_API_TOKEN = os.environ.get("GITHUB_API_TOKEN")
    CIRCLE_PROJECT_REPONAME = os.environ.get("CIRCLE_PROJECT_REPONAME")
    CIRCLE_PROJECT_USERNAME = os.environ.get("CIRCLE_PROJECT_USERNAME")
    CIRCLE_BUILD_NUM = os.environ.get("CIRCLE_BUILD_NUM")
    CIRCLE_SHA1 = os.environ.get("CIRCLE_SHA1")

    print(CIRCLE_PROJECT_REPONAME)
    print(CIRCLE_PROJECT_USERNAME)
    print(CIRCLE_BUILD_NUM)
    print(CIRCLE_SHA1)


if __name__ == "__main__":
    main()
