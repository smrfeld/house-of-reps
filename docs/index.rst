.. houseofreps documentation master file, created by
   sphinx-quickstart on Sat Nov  4 14:04:37 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to houseofreps's documentation!
=======================================

`houseofreps` is a Python package for working with the apportionment of seats to the U.S. House of Representatives.

**Disclaimer:**
This product uses the Census Bureau Data API but is not endorsed or certified by the Census Bureau. See `Terms of Service <https://www.census.gov/data/developers/about/terms-of-service.html>`_.

Years supported:
----------------

- 1960
- 1970
- 1980
- 1990
- 2000
- 2010
- 2020

A detailed explanation of the current house seat apportionment algorithm can be found `here <https://www.census.gov/topics/public-sector/congressional-apportionment/about/computing.html>`_.

Data source
-----------

The data source is from `https://www.census.gov <https://www.census.gov>`_ and is completely described in the `data` folder.

Installation
------------

Local installation: clone the repo from the GitHub page `https://github.com/smrfeld/house-of-reps <https://github.com/smrfeld/house-of-reps>`_, then::

    pip install -r requirements.txt
    pip install -e .

Tests
-----

Tests are implemented for `pytest`. In the `tests` folder run::

    pytest

Discussion
----------

It's fascinating to understand how seats in the US House of Representatives are assigned. Before this project, I had never thought about this problem:

- The US Senate consists of two senators for every US state - this is straightforward.
- The US House of Representatives has members assigned based on the state's population. This leads to an immediate problem: the fraction of people residing in each state doesn't lead to an integer assignment of seats!

What can we do?

- Fractional voting - assign each state a fractional vote. With modern technology, this actually seems like the more reasonable approach. However, this is not how the US House of Representatives is currently assigned.
- An algorithm that assigns members to each state. For every state, a choice must be made - is the number of seats rounded up or rounded down? Either way, some state has to pay the price and receive fewer seats.

A detailed explanation of the current house seat apportionment algorithm can be found `here <https://www.census.gov/topics/public-sector/congressional-apportionment/about/computing.html>`_. Every 10 years, the number of seats is assigned based on the latest census data (most recently: 2020).

For completeness, the description of the algorithm is copied here from `https://www.census.gov/topics/public-sector/congressional-apportionment/about/computing.html <https://www.census.gov/topics/public-sector/congressional-apportionment/about/computing.html>`_, with some comments:

The method assigns seats in the House of Representatives according to a "priority" value. The priority value is determined by multiplying the population of a state by a "multiplier."

Let P represent a state's total population. **This already raises questions, particularly regarding overseas service members, who were excluded from the population counts in 1980 following the Vietnam war.**

All states start by receiving 1 seat. A state cannot receive less than one seat.

Next, let n represent the number of seats a state would have if it gained a seat (because all states automatically received one seat the next seat gained is "seat two," and the next "seat three," and the next "seat four," and so on.)

Now define the **multiplier**::

    1/sqrt(n*(n-1))

[which is called the reciprocal of the geometric mean].

Thus the formula for calculating the multiplier for the second seat is::

    1 / sqrt(2(2-1)) ~ 1/1.414213562 ~ 0.70710678

and the third seat is::

    1 / sqrt(3(3-1)) ~ 1/2.449489743 ~ 0.40824829

Once the "multipliers" have been calculated, the next step is to multiply this figure by the population total for each of the 50 states (**the District of Columbia is not included in these calculations**). The resulting numbers are the priority values.

Once you've calculated priority values for the total number of potential seats for each state, the next step is to rank and assign seat numbers to the resulting priority values starting with seat 51, until all 435 seats have been assigned (remember, each state automatically received one seat). Next, tally the number of seats for each state to arrive at the total number of seats in the House of Representatives apportioned to each state.


Contents
========

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules.rst


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
