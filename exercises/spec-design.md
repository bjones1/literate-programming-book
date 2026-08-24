Spec design: eliminate unanswered questions
===========================================

Quoting the previous [handout](spec-quality/handout.md):

> "The model's job is to produce something plausible. Your job is to make sure
> only one thing is plausible."

A series of [probes](spec-quality/warmup_truncate.py) asks some of these
questions. Your spec must answer them:

1. What is a character? (A byte, a
   [code point](https://en.wikipedia.org/wiki/Code_point#In_Unicode), a
   [grapheme](https://en.wikipedia.org/wiki/Grapheme)?)
2. How should whitespace be handled? Should whitespace be removed from the
   beginning of the string? From the end?
3. What is an ellipsis? (A single Unicode character, or three periods?)
4. Should we add an ellipsis in the middle of a word?
5. Do strings shorter than 100 characters get an ellipsis?
6. What is the length of the resulting string after truncation? 100 characters,
   101 characters, or 103 characters when three periods are appended to a
   full-length result?

Read the probes to look for more questions; not all are listed here. Then ask:
what else is unspecified? Ensure your spec answers all these questions. Review
it with an LLM until two consecutive reviews surface nothing you consider a real
gap.

Another way to sharpen a specification is to write the tests first: each test
forces a decision the prose left open. Ask questions of yourself: what valid but
unexpected input could produce an incorrect output?

An essential part of writing a spec is learning: becoming an expert in a
particular area, then creatively applying this knowledge to crafting a
thoughtful specification, along with associated tests, which make the spec more
concrete. For this problem, you need to truly understand the difference between
a byte, a code point, and a grapheme; you need to know what an ellipsis is
(including its representation as a Unicode code point), what qualifies as
whitespace even in an international context, how to write unit tests in Python,
etc.

For this example, use [pytest](https://docs.pytest.org/en/stable/). Place your
tests in a new file called `test_truncate.py`, which must be located in the same
directory as `my_truncate.py`. To run your tests, upload the `test_truncate.py`
you created along with `run_tests.py` to
[https://pythononline.net](https://pythononline.net). Click on `run_tests.py` in
this web IDE, then click the green Run button.
