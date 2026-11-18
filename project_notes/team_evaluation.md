<h1 id="cc-NgJX8yVtOQ">Team evaluation project example</h1>

Here's an example of a team evaluation and report; the report includes formulas
used to calculate teaming scores. It's based on
[https://github.com/bjones1/team\_evaluations/tree/master/\_sources/current](https://github.com/bjones1/team_evaluations/tree/master/_sources/current) and
[https://github.com/bjones1/BookServer/blob/lp/bookserver/internal/team.py](https://github.com/bjones1/BookServer/blob/lp/bookserver/internal/team.py).

Team evaluation 1
-----------------

Team: (team name)

### Role

In the following questions, briefly describe your role in all aspects of
(project/course name) and in preparing content for the (assignment name).

(Textbox here for student response)

### Group dynamics

Discuss the reliability and participation of your group members. Has anyone
missed a meeting, shown up late, left early, or missed any internal deadlines?
If so, please be specific.

(Textbox here for student response)

### Contributions

Evaluate each team member's contribution to the (assignment name) by
distributing 100 total possible points as you think they should be allocated
based on each member's input. Please note that you are not rating each member on
a scale of 0 to 100; rather, you are distributing a total of 100 points across
all team members other than yourself (e.g., if everyone has contributed equally
on a four-person team, you should give your three team members each a 33.3; if
everyone has contributed equally on a five-person team, you should give your
four team members each a 25). This rating does not count toward individual
grades; rather, it is an opportunity to reveal any problems that might exist
within your group.

(one numeric entry box for each team member, except the student completing this
form. After these, display a sum of the ratings; if the sum isn't 100, warning
that the sum should be 100.)

REQUIRED: If the allocated points above are not equally distributed, you must
provide an explanation for your ratings.

(Textbox here for student response)

Team evaluation 1 report
------------------------

(Put a table of contents, with a link to each team's report)

### Team: (team name)

#### Role

(Create a table with the name of each team member, followed by their response)

(Repeat this same format for the group dynamics heading)

### Contributions

(Create a table showing team member names as headings for both rows (evaluators)
and columns (evaluatees), followed by the ratings. Each row displays the
normalized ratings for that teammate; columns contains the ratings chosen by the
corresponding teammate. In addition, display the average rating for each
evaluated teammate and a delta.

For each evaluator $i$, normalize their ratings to ensure they sum to 1:
$\textrm{normalized\_rating}_i = \frac{1}{n}\sum_{j=1}^n{\textrm{rating}_j}$,
where $n$ = number of teammates.

$\textrm{delta} = \frac{\textrm{actual\_rating} - \textrm{expected\_rating}}{\textrm{expected\_rating}} \cdot 100$,
where $\textrm{expected\_rating} = \frac{1}{n - 1}$. )
