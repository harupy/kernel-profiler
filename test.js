// API doc: https://octokit.github.io/rest.js/v16

const { owner, repo } = context.repo;
const issue_number = context.issue.number;
const pull_number = context.issue.number;

// Get a pull request that triggered this action.
const pr = (
  await github.pulls.get({
    owner,
    repo,
    pull_number,
  })
).data;

// Get labels that are available in this repository.
const getName = ({ name }) => name;
const allLabels = (
  await github.issues.listLabelsForRepo({
    owner,
    repo,
  })
).data.map(getName);

const isAvailable = name => allLabels.includes(name);

// Get labels attached to the pull request.
const currentLabels = (
  await github.issues.listLabelsOnIssue({
    owner,
    repo,
    issue_number,
  })
).data.map(getName);

const isAttached = name => currentLabels.includes(name);

// Find labels in the pull request description.
const findLabels = (regex, s, labels = []) => {
  const res = regex.exec(s);

  if (res) {
    const checked = res[1].trim() === "x";
    const name = res[2].trim();

    return findLabels(regex, s, [{ name, checked }, ...labels]);
  }

  return labels;
};

const regex = /- \[([ x]*)\] (.+)/gm;
const labels = findLabels(regex, pr.body).filter(({ name }) => isAvailable(name));

// Remove unchecked labels.
// NOTE: This doesn't raise an error even if the label doesn't exist.
labels
  .filter(({ name, checked }) => !checked && isAttached(name))
  .forEach(async ({ name }) => {
    await github.issues.removeLabel({
      owner,
      repo,
      issue_number,
      name,
    });
  });

// Add checked tasks
await github.issues.addLabels({
  owner,
  repo,
  issue_number,
  labels: labels.filter(({ name, checked }) => checked && !isAttached(name)).map(getName),
});
