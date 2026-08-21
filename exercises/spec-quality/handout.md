In-Class Exercise: What Your Prompt Didn't Say
==============================================

You will write two prompts today. The first will produce clean, working,
confident code that fails most of its acceptance tests. The second will not.
Nothing about the model will change in between.

Setup
-----

Everything runs in the browser at <https://pythononline.net>. There is nothing
to install on your laptop, and no Python version to argue with.

**1. Make a free account.** Click *Sign In*, then *Register*. A guest session
runs code but has no cloud storage, and packages are stored per project on that
storage — so without an account you cannot install pytest, and your files
disappear when the tab closes.

**2. Make a project.** Click the project name in the top left to open the
dashboard, go to *Projects*, click *+*, and name it `spec-quality`.

**3. Load the starter files.** Right-click the empty space in the **EXPLORER**
panel, choose *Import Project*, and upload the bundle your instructor gave you.
You should end up with this handout, `model.py`, `run_tests.py`, a `warmup/`
folder, and a `submission/` folder at the root of the project.

**4. Install two packages.** Open the **PACKAGES** panel in the left sidebar
and stay on the *User* tab. Type `pytest` in the search box, and click
*Install* on the result. Do the same for `tzdata`.

- `pytest` runs the acceptance suite.
- `tzdata` is the timezone database. Python Online runs a deliberately minimal
  container, so `ZoneInfo("America/Chicago")` fails without it, and Part 2
  fails for reasons that have nothing to do with your prompt.

Packages install into this project's hidden `.pypackages` folder, which means
you install them **once per project**, not once per file, and a package
installed here cannot affect any other project you own.

**5. Check it.** Click the `run_tests.py` tab, then click the green **Run**
button (or press `Ctrl + Enter`). It should tell you there is no `solution.py`
yet. That is the correct answer for now — it means pytest and tzdata are both
working.

Two things about Run that will otherwise cost you five minutes: it executes the
last Python file you had **selected**, so click into the file you mean before
clicking Run; and every script is killed at 60 seconds, which is roughly sixty
times longer than this suite needs.

Ground rules for both parts
----------------------------

1. Send the prompt **exactly** as specified. Do not add helpful detail.
2. Do not ask the model follow-up questions.
3. Do not edit the code it gives you.

You are measuring a prompt, not producing a program. Improving the code by hand
destroys the measurement.

Part 1: The warm-up (8 minutes)
--------------------------------

Send this to an LLM, and nothing else:

```
Write a Python function that truncates a string to 100 characters
and adds an ellipsis.
```

Open [warmup/my_truncate.py](warmup/my_truncate.py), select everything below
the comment header, and paste the answer over it. Then click the
[warmup/warmup_truncate.py](warmup/warmup_truncate.py) tab and click **Run**.

Report your **fingerprint** when asked.

That sentence felt complete when you wrote it. The runner will show you the
eight decisions it left open, and your classmates' fingerprints will show you
that the model made those decisions differently for each of you. Write down
which of the eight answers you actually intended. Most people find they had an
opinion about two or three and had never considered the rest.

Part 2, Round 1: The invented policy (12 minutes)
--------------------------------------------------

Attach [model.py](model.py) to a new chat, and send exactly this:

```
We're building an e-commerce backend. Here is our order model.
Write a function that determines whether a customer can cancel an order.
```

Your instructor will now release the acceptance suite. Import it the same way
you imported the starter files — right-click in the Explorer, *Import Project*
— and you will get `harness.py` and `test_cancellation.py` alongside what you
already have. Then create a file called `solution.py`, paste the LLM's code
into it, click the `run_tests.py` tab, and click **Run**.

`test_cancellation.py` is the answer key, and reading it before your prompt is
written is reading the answer key. Don't open it yet.

Record your score. Then set `VERBOSE = True` at the top of `run_tests.py`, run
it again to read the failures, and — before the policy is released — answer two
questions in writing:

- For each failure, is this something the model got *wrong*, or something you
  never *said*?
- Where did the model's answer come from, if not from your prompt?

Save a copy of the code as `submission/round1_solution.py`.

Part 2, Round 2: Write the specification (20 minutes)
-------------------------------------------------------

Import the last drop, which brings `CANCELLATION_POLICY.md`, `contract.py`, and
the rubric you will be graded against. The policy document is what the business
actually meant all along. Notice that it is prose, not a
specification: it is full of justification, hedging, and implication, and it is
your job to turn it into something a model can implement without guessing.

Open a **new chat** — do not continue the old one, and do not paste the old
code in. Write a prompt that specifies the work. Then replace the contents of
`solution.py` with the result and run `run_tests.py` again.

The graded artifact is your prompt. See [rubric.md](rubric.md). Save it as
`submission/round2_prompt.md`, along with `submission/round2_solution.py` and
your two scores. When you are done, right-click in the Explorer and choose
*Export Project* to get a zip of everything to hand in.

A caution worth taking seriously: the fastest way to pass these tests is to
paste the tests into the prompt. That is cheating in the same way that reading
the answer key is cheating, and more importantly it does not work in your job,
where the tests do not exist until someone specifies the behavior. Specify the
behavior.

The failure taxonomy
--------------------

Use these names in your write-up. They transfer directly to real work.

| Name | What it is | Example from today |
| --- | --- | --- |
| **Ambiguity** | Your words have more than one valid reading | Does the ellipsis count toward the 100? |
| **Omission** | You gave no reading at all, so the model invented one | The sixty-minute grace window |
| **Implicit context** | Obvious to you, invisible to the model | Whose Saturday is it — yours, the server's, or the merchant's? |
| **Interface contract** | Types, errors, nulls, return shapes | A bool cannot express a partial cancellation |
| **Boundaries** | Exactly-at-the-limit, empty, already-done | Re-cancelling a cancelled order |
| **Downstream consumers** | Who reads your output and what they need | The UI localizes reason codes |
| **Non-functional** | Scale, latency, concurrency, cost | Retries from a flaky mobile client |

The one to internalize is **omission**. Ambiguity at least leaves a trace you
can spot when you reread your own prompt. Omission leaves nothing: the model
produces a confident answer to a question you never asked, and the output looks
exactly as good as a correct one. The only way to catch it is to have decided,
in advance, what correct means.
