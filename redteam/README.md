# Scoring audit

`audit.py` implements each candidate from the future scientist's visible
inputs. Each named directory has a `run.sh` that installs its candidate,
runs visible train scoring, then launches the original hidden test shell
script **with no arguments in a separate process**. No evaluator code,
Python packages, import hooks, or surviving processes are changed. Input
archives, checkpoint artifacts, and score files are restored after every
trial. The hidden test's score JSON and subprocess exit codes are retained
in the candidate directory.

The reference implementation is available in improve mode. Its outputs are
reused for inexpensive trials that change only artifacts or scoring
dependencies. The label and seed replay shortcuts obtain their answers from
`data/`, which is available in both modes.

Run the full bundle in the provided container as a scheduled CPU job:

```sh
python -u redteam/audit.py all
```

An individual trial can be run with `bash redteam/<name>/run.sh`. Runtime
backup state is in the ignored `_state/` folder; it is not a candidate input.
`summary.json` uses population standard deviations across the finite complete
audit attempts to illustrate the rank formula. Future ranking depends on its
own attempt population; raw per-experiment results are authoritative.

`python3 redteam/verify.py` checks saved evidence and regenerates the rank
normalization sensitivity record without running a model. `verification.json`
records these checks and file restoration. `job_record.json`, `job_stdout.log`,
and `job_stderr.log` preserve the completed CPU job record after restoring the
temporary job files outside this directory.

All `shortcut_*` candidates are shortcut tests, including attempts that fail.
`shortcut_bruteforce` is an honest alternative the test may not distinguish
from its much more elaborate reference. It is labeled a shortcut throughout
to make any tie explicit.
