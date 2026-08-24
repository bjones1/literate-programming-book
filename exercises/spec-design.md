Spec design: eliminate unanswered questions
===========================================

Quoting the previous [handout](spec-quality/handout.md):

> "The model's job is to produce something plausible. Your job is to make sure
> only one thing is plausible."

A series of [tests](spec-quality/warmup_truncate.py) ask some of these
questions. Your spec must answer them:

1. What is a character? (A byte, a
   [code point](https://en.wikipedia.org/wiki/Code_point#In_Unicode), a
   [grapheme](https://en.wikipedia.org/wiki/Grapheme)?)
2. How should whitespace be handled? Should whitespace be removed from the
   beginning of the string? From the end?
3. Should we add an ellipsis in the middle of a word?
4. What is an ellipsis? (A Unicode character, or three periods)?
5. Do we add an ellipsis to < 100 characters?
6. What is the length of the resulting string after truncation? 100 characters,
   101 characters, etc.

Read the tests to look for more questions; not all are listed here. Then ask:
what else is unspecified? Ensure your spec answers all these questions.
