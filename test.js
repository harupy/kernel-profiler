const owner = "harupy";
const repo = "kernel-profiler";
const issue_number = context.issue.number;
const pull_number = context.issue.number;

// Get a pull request that trigger this action.
const pr = await github.pulls.get({
  owner,
  repo,
  pull_number,
});

// Find labels from the pull request description.
const isChecked = x => x.trim() === "x";

const findLabels = (regex, s, labels = []) => {
  const res = regex.exec(s);

  if (res) {
    const checked = isChecked(res[1]);
    const label = res[2];

    return findLabels(regex, s, [{ label, checked }, ...labels]);
  }

  return labels;
};

const allLabels = await github.issues.listLabelsForRepo({
  owner,
  repo,
});

const regex = /- \[([ x]*)\] (.+)/gm;
const labels = findLabels(regex, pr.data.body).map(({ label }) => allLabels.includes(label));

// Delete unchecked labels
labels
  .filter(({ checked }) => !checked)
  .forEach(async ({ label }) => {
    await github.issues.deleteLabel({
      owner,
      repo,
      label,
    });
  });

// Add check labels.
await github.issues.addLabels({
  owner,
  repo,
  issue_number: context.issue.number,
  labels: labels.filter(({ checked }) => checked),
});
