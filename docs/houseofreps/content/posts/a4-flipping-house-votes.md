+++
title = "Flipping House votes with apportionment data"
date = 2024-01-13T13:06:44-08:00
draft = false
+++

How changing the method for seat apportionment in the House would reshape voting.

![](https://storage.googleapis.com/oke-website/2023_houseofreps3/p1.webp)

*Source: author.*

## Background

Representation is a contentious subject. The U.S. Congress tries to balance the representation of each state across it’s two chambers: the Senate, where each state gets equal representation, and the House of Representatives, where each state gets a voice proportional to its population.

But that’s where things get harder. Based on the last census there are `331.9MM` people in the U.S., of which `11.823%` reside in California. Unfortunately, `11.823%` of the `435` total seats in the House assigns `51.43` representatives to California. What should do with the extra `0.43` of a person?

No matter which [algorithm](https://www.census.gov/topics/public-sector/congressional-apportionment/about/computing.html) is used to resolve this, clearly some states will end up underrepresented, and some overrepresented. In recent articles, we examined the impacts of the algorithm used to assign members to the US House of Representatives ("apportionment"). In particular, we found that:

* Delaware has been the most consistently underrepresented state over the past 60 years. It’s ranking in the state populations has created a population ranking trap that has consistently delivered fewer representatives than the fair value.

* If `25` people had moved from Minnesota to the rest of the U.S. in 2020, the state would have lost a representative in the 2020–2030 apportionments. Similarly, if `84` people had moved to New York from the rest of the U.S., the state would have gained a seat.

You can read more about this work here:

* [Sorry, Delaware, America’s most underrepresented state](https://www.oliver-ernst.com/house-of-reps/posts/a1-delaware-underrepresented/) - Congratulations for losing the state population lottery, 70 years and counting.

* [The impact of 25 people on Congressional voting](https://www.oliver-ernst.com/house-of-reps/posts/a2-impact-25-people/) - This is the story of how Minnesota was just 25 people away from losing a representative.

This story is about voting. If changing the seat assignment algorithm changes the number of seats assigned to each state, then similarly the votes in the US House must be affected. And if the vote was already close to the minimum number required for a bill to pass, then possibly even, the outcome of one or more rollcalls would have changed. Let’s dive deeper.

## Voting data

Voting data for both the House and the Senate can be found on [https://voteview.com/](https://voteview.com/). From their website:

> Voteview allows users to view every congressional roll call vote in American history on a map of the United States and on a liberal-conservative ideological map including information about the ideological positions of voting Senators and Representatives. The original Voteview of DOS was developed by Keith T. Poole and Howard Rosenthal at Carnegie-Mellon University between 1989 and 1992. Poole and Rosenthal developed Voteview for Windows in 1993 at Princeton University and that work was continued by Boris Shor. The legacy version of the website is available at legacy.voteview.com.

You can access the actual voting data here: [https://voteview.com/data](https://voteview.com/data).

The three data types we are interested in for this project are:

* The votes data, which lists for every congress/chamber/rollnumber the vote of every member. Each member is described by a `icpsr` number, and their vote by a `castcode` . The cast code is one of: (0 — Not a member of the chamber when this vote was taken), (1 — Yea), (2 — Paired Yea), (3 — Announced Yea), (4 — Announced Nay), (5 — Paired Nay), (6 — Nay), (7,8 — Present), (9 — Not Voting). For the purpose of this analysis, we can focus on just (1 — Yea) and (6 — Nay) votes.

    ![](https://storage.googleapis.com/oke-website/2023_houseofreps3/p2.webp)

* We also need to know the state which every member belongs to — that is, to map the icpsr number to a state. This can be done with the members ideology data.

    ![](https://storage.googleapis.com/oke-website/2023_houseofreps3/p3.webp)

* The roll call data, which describes for every congress/chamber/rollnumber the outcome of the vote, as well as some possible metadata. We mainly use this for the metadata about the roll number, since the actual voting data is already contained in the votes CSV file.

    ![](https://storage.googleapis.com/oke-website/2023_houseofreps3/p4.webp)

With the data in hand, we can proceed to investigate how the apportionment algorithm affects actual votes.

## Changing votes

With this data in hand, we can examine each rollcall, for which we measure the number of Yea/Nay votes using 2 methods:

1. The actual number of Yea/Nay votes ( `actual(Yea)` and `actual(Nay)`), and

2. The number of Yea/Nay votes if fractional voting had been used to assign the house seats instead of the current priority method (`fractional(Yea)` and `fractional(Nay)`). This re-weights the votes of each state’s representatives to reflect the state’s actual population (it’s percentage of the total US population).

From this, the difference between the actual and fractional votes is:
```
max(|actual(Yea)-fractional(Yea)|, |actual(Nay)-fractional(Nay)|)
```

![](https://storage.googleapis.com/oke-website/2023_houseofreps3/p5.webp)

*Difference between actual and fractional votes across rollcalls. Each point is a rollcall vote for a different congress (x-axis). On the y-axis is shown how the number of Yea/Nay votes would change if the apportionment method were changed to fractional voting. In most congresses, the average rollcall flips by 0.5 votes, but some rollcalls switch by as much as 2 votes more or fewer Yea/Nay votes.*

In the plot, each point is a rollcall vote for a different congress (x-axis). On the y-axis is shown how the number of Yea/Nay votes would change if the apportionment method were changed to fractional voting. In most congresses, the average rollcall flips by 0.5 votes, but some rollcalls switch by over 2 more or fewer Yea/Nay votes.

2 votes might not sound like a lot, but at the current US population of 331.9MM people, each vote represents 760k citizens. Therefore a swing in the Yea/Nay count by 2 votes represents the voices of 1.5MM citizens — more than the entire state of Hawaii.

## Flipped decisions

Not only do votes change, but if the pass/fail was already near the threshold, there’s a chance that the *outcome* of the vote could flip — i.e. flipping from pass to fail or vice versa. Let’s look at some examples:

### Congress 118 (2023–2025) rollnumber 17: Election of the speaker (McCarthy)

* Actual result: **FAIL** (Yea: 216, Nay: 216)
* Result after switching the fractional voting: **PASS** (Yea: 216.9008, Nay: 215.1039).

Indeed: under fractional voting, McCarthy would have passed his election as speaker of the house in 2023. This article is not an endorsement one way or the other, but it’s fascinating to see the impact of this algorithm.

### Congress 117 (2021–2023) rollnumber 155: Making emergency supplemental appropriations for the fiscal year ending September 30, 2021, and for other purposes (HR3237)

* Actual result: **PASSED** (Yea: 213, Nay: 212)
* Result after switching to fractional voting: **FAIL** (Yea: 212.7383, Nay: 212.8086)

From [congress.gov](https://www.congress.gov/bill/117th-congress/house-bill/3237):

> This bill provides FY2021 supplemental appropriations for federal agencies to respond to the events at the U.S. Capitol Complex on January 6, 2021, and assist Afghan refugees.

### Congress 106 (1999–2001) rollnumber 102: Authorizing the President of the United States to Conduct Military Air Operations and Missile Strikes Against the Federal Republic of Yugoslavia (Serbia and Montenegro) (SCONRES21)

* Actual result: **FAIL** (Yea: 213, Nay: 213)
* Result after switching to fractional voting: **PASSED** (Yea: 213.8699, Nay: 211.8879)

Here, "authorization" is a bit misleading, as this was a [concurrent resolution](https://www.govtrack.us/congress/bills/106/sconres21):

> A concurrent resolution is often used for matters that affect the rules of Congress or to express the sentiment of Congress. It must be agreed to by both the House and Senate in identical form but is not signed by the President and does not carry the force of law.

Still, it’s meaningful that by the sentiment of congress actually flips if you take exact state populations into account.

## Closing thoughts

In this article we looked at how the U.S. House seat apportionment algorithm affects rollcall votes. We used data from [https://voteview.com/](https://voteview.com/) to show that the algorithm can swing as many as 2 votes in the US, representing the voices of 1.5MM citizens. This is particularly relevant in closely divided congresses, where the 2 votes can flip the decision of a rollcall vote such as the election of Kevin McCarthy as speaker. This is not an endorsement, but it is a fascinating result that shows how important the small details of our democratic system are.

You can view the code for this analysis on GitHub here:

* [GitHub - smrfeld/house-of-reps: Python package to model apportionment in house of representatives](https://github.com/smrfeld/house-of-reps)

You can read more about this work here:

* [Sorry, Delaware, America’s most underrepresented state](https://www.oliver-ernst.com/house-of-reps/posts/a1-delaware-underrepresented/) - Congratulations for losing the state population lottery, 70 years and counting.

* [The impact of 25 people on Congressional voting](https://www.oliver-ernst.com/house-of-reps/posts/a2-impact-25-people/) - This is the story of how Minnesota was just 25 people away from losing a representative.
