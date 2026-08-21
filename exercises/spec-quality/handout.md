In-Class Exercise: What Your Prompt Didn't Say
==============================================

You will write one sentence today. It will produce clean, working, confident
code — and a program that differs from your neighbor's in eight ways. Same
sentence, same model, different program.

Setup
-----

Everything runs in the browser at
[https://pythononline.net](https://pythononline.net). There is nothing to
install on your laptop, and no Python version to argue with.

1. **Make a free account.** Click *Sign In*, then *Register*. A guest session
   runs code but has no cloud storage, so your files disappear when the tab
   closes.

2. **Make a project.** Click the project name in the top left to open the
   dashboard, go to *Projects*, click *+*, and name it `spec-quality`.

3. **Load the starter files.** Right-click the empty space in the **EXPLORER**
   panel, choose *Import Project*, and upload the bundle your instructor gave
   you. You should end up with this handout, `my_truncate.py`, and
   `warmup_truncate.py` at the root of the project. Nothing else is needed —
   the runner uses only the standard library, so there are no packages to
   install.

4. **Check it.** Click the `warmup_truncate.py` tab, then click the green
   **Run** button (or press `Ctrl + Enter`). Every one of the eight probes
   should report `RAISED NotImplementedError`. That is the correct answer for
   now — it means the runner found `my_truncate.py` and is calling it.

   Two things about Run that will otherwise cost you five minutes: it executes
   the last Python file you had **selected**, so click into the file you mean
   before clicking Run; and every script is killed at 60 seconds, which is
   roughly sixty times longer than this runner needs.

Ground rules
------------

1. Send the prompt **exactly** as specified. Do not add helpful detail.
2. Do not ask the model follow-up questions.
3. Do not edit the code it gives you.

You are measuring a prompt, not producing a program. Improving the code by hand
destroys the measurement.

What is truncation?
-------------------

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

| Name                     | What it is                                            | Example                                                        |
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
