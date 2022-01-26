## Algorithm

We have a function that assigns seats to every state. Let the number of seats assigned to state `i` be `s_i`, where `i = 0,1,...,49`.

Let the population of each state be `n_i`. Then we have some way of assigning seats to all the states:
```
s = f(n)
```
where `s,n` are vectors and `f` is the function that involves priorities. Note that `f` is not differentiable due to the max operation when finding the highest priority.

Each state seat has some probability of being democrat vs. republican. Let the probability of being republican be `pr_i` and democrat be `pd_i`. Note that there are also unaffiliated (independents) `pu_i`, so that `pr_i + pd_i + pu_i = 1`.

The number of democratic/republican/unaffiliated votes of state `i` is then
```
vd_i = pd_i * s_i
vr_i = pr_i * s_i
vu_i = pu_i * s_i
```

For each issue `j`, a republican vote has some probability `qr+_j` of voting for the issue, `qr-_j` against the issue, and `qr0_j` abstaining. Here `qr+_j + qr-_j + qr0_j = 1`. We make the assumption that the probability of voting for/against an issue is independent of the state the candidate is from - this is certainly not quite correct, but makes it easier to evaluate the probabilities since many states have only one representative. The number of pro-votes by democrats/republicans/unaffiliated in state `i` for issue `j` is then:
```
vd+_ij = qd+_j * vd_i = qd+_j * pd_i * s_i
vr+_ij = qr+_j * vr_i = qr+_j * pr_i * s_i
vu+_ij = qu+_j * vu_i = qu+_j * pu_i * s_i
```

The total number of pro votes is:
```
v+_ij = vd+_ij + vr+_ij + vu+_ij = (qd+_j * pd_i + qr+_j * pr_i + qu+_j * pu_i) * s_i
```

These equations pass a sanity check: if we use some data to get the probabilities `p` and `q`, then at the correct distribution of representatives `s`, we will reproduce the correct votes.

We want a simple majority to pass a bill, i.e. `v+_ij >= 218` by shifting as few people as possible. Let the original population distribution be `r` (similar to `s`, but `s` is the shifted version). Then the constrained optimization problem is:
```
min_s |s - r|_1 
s.t. v+_ij >= 218 
and |s_i| > 0
```
where `|x|_1` denotes the `L1` norm. Here `v+_ij` is an implicit function of `s`. The last constraint ensures that there are people in every state.

We can reduce the search space a bit here - since we don't want `s` and `r` to differ significantly, we can instead let the population of each state change by only `+-ds_max` where ds is some small number, e.g. `ds_max = 0.1` million. Then:
```
min_s |s - r|_1 
s.t. v+_ij >= 218
and |s_i| > 0 
and |s_i - r_i| <= ds_max
```
This further constrains the search space. If we limit ourselves to `ds_max <= min(r)`, then this takes care of the second constraint:
```
min_s |s - r|_1 
s.t. v+_ij >= 218
and |s_i - r_i| <= ds_max
```
It's better to work with the displacement vector directly, since then the second constraint is a constraint on the controls (rather than the state), which is easier:
```
min_s | ds |_1
s.t. v+_ij >= 218
and |ds_i| <= ds_max
```

We need one final constraint: the displacement vector should sum to zero - people should not disappear! This can be enforced by letting the first element be the negative sum of the others
```
ds_0 = - sum_{i=1,...} ds_i
```
Note that `ds_0` still must satisfy the `ds_max` condition.