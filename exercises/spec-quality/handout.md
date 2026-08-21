In-Class Exercise: What Your Prompt Didn't Say
==============================================

You will write two prompts today. The first will produce clean, working,
confident code that fails most of its acceptance tests. The second will not.
Nothing about the model will change in between.

Setup
-----

Everything runs in the browser at
[https://pythononline.net](https://pythononline.net). There is nothing to
install on your laptop, and no Python version to argue with.

1. **Make a free account.** Click *Sign In*, then *Register*. A guest session
   runs code but has no cloud storage, and packages are stored per project on
   that storage — so without an account you cannot install pytest, and your
   files disappear when the tab closes.

2. **Make a project.** Click the project name in the top left to open the
   dashboard, go to *Projects*, click *+*, and name it `spec-quality`.

3. **Load the starter files.** Right-click the empty space in the **EXPLORER**
   panel, choose *Import Project*, and upload the bundle your instructor gave
   you. You should end up with this handout, `model.py`, `run_tests.py`, a
   `warmup/` folder, and a `submission/` folder at the root of the project.

4. **Install two packages.** Open the **PACKAGES** panel in the left sidebar and
   stay on the *User* tab. Type `pytest` in the search box, and click *Install*
   on the result. Do the same for `tzdata`.

   * `pytest` runs the acceptance suite.
   * `tzdata` is the timezone database. Python Online runs a deliberately
     minimal container, so `ZoneInfo("America/Chicago")` fails without it, and
     Part 2 fails for reasons that have nothing to do with your prompt.

   Packages install into this project's hidden `.pypackages` folder, which means
   you install them **once per project**, not once per file, and a package
   installed here cannot affect any other project you own.

5. **Check it.** Click the `run_tests.py` tab, then click the green **Run**
   button (or press `Ctrl + Enter`). It should tell you there is no
   `solution.py` yet. That is the correct answer for now — it means pytest and
   tzdata are both working.

   Two things about Run that will otherwise cost you five minutes: it executes
   the last Python file you had **selected**, so click into the file you mean
   before clicking Run; and every script is killed at 60 seconds, which is
   roughly sixty times longer than this suite needs.

Ground rules for both parts
---------------------------

1. Send the prompt **exactly** as specified. Do not add helpful detail.
2. Do not ask the model follow-up questions.
3. Do not edit the code it gives you.

You are measuring a prompt, not producing a program. Improving the code by hand
destroys the measurement.

Part 1: what is truncation?
---------------------------

Send this to an LLM, and nothing else:

```
Write a Python function that truncates a string to 100 characters
and adds an ellipsis.
```

Open [my\_truncate.py](my_truncate.py), select everything below the comment
header, and paste the answer over it. Then click the
[warmup\_truncate.py](warmup_truncate.py) tab and click **Run**.

Report your **fingerprint** when asked.

That sentence felt complete when you wrote it. The runner will show you the
eight decisions it left open, and your classmates' fingerprints will show you
that the model made those decisions differently for each of you. Write down
which of the eight answers you actually intended. Most people find they had an
opinion about two or three and had never considered the rest.

> "The model's job is to produce something plausible. Your job is to make sure only one thing is plausible."

The failure taxonomy
--------------------

Use these names in your write-up. They transfer directly to real work.

| Name                     | What it is                                            | Example from today                                             |
| ------------------------ | ----------------------------------------------------- | -------------------------------------------------------------- |
| **Ambiguity**            | Your words have more than one valid reading           | Does the ellipsis count toward the 100?                        |
| **Omission**             | You gave no reading at all, so the model invented one | The sixty-minute grace window                                  |
| **Implicit context**     | Obvious to you, invisible to the model                | Whose Saturday is it — yours, the server's, or the merchant's? |
| **Interface contract**   | Types, errors, nulls, return shapes                   | A bool cannot express a partial cancellation                   |
| **Boundaries**           | Exactly-at-the-limit, empty, already-done             | Re-cancelling a cancelled order                                |
| **Downstream consumers** | Who reads your output and what they need              | The UI localizes reason codes                                  |
| **Non-functional**       | Scale, latency, concurrency, cost                     | Retries from a flaky mobile client                             |

The one to internalize is **omission**. Ambiguity at least leaves a trace you
can spot when you reread your own prompt. Omission leaves nothing: the model
produces a confident answer to a question you never asked, and the output looks
exactly as good as a correct one. The only way to catch it is to have decided,
in advance, what correct means.
