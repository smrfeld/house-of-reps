# Correct and clean datasets from census.gov

We are interested in population data from the census and the number of representatives assigned to each state.

The bulk of this data is contained in [historical.csv](data_src/historical.csv). This is historical data that can be downloaded from `census.gov` on [this page](https://www.census.gov/data/tables/time-series/dec/density-data-text.html), specifically at [this link](https://www2.census.gov/programs-surveys/decennial/2020/data/apportionment/apportionment.csv). It contains data for 1910 - 2020 in 10 year intervals for the population and the number of house representatives assigned.

Unfortunately, this data is **incomplete** because it does not include the populations for each state of residents that are overseas, dominantly in the armed forces. This was first included in determining each states number of representatives in 1970, when, during the Vietnam war, c.a. 1.5 million service members were stationed abroad.

- For 1970, [apportionment_pop_1970.csv](data_src/apportionment_pop_1970.csv) was manually created from the data listed in the included 1970 report for the house: [ApportionmentInformation-1970Census.pdf](data_src/ApportionmentInformation-1970Census.pdf).
- For 1980, the number of overseas residents was **not** included in determining the number of representatives. The argument for this is laid out in [ApportionmentInformation-1980Census.pdf](data_src/ApportionmentInformation-1980Census.pdf).
- For 1990, 2000, 2010 and 2020, the actual populations used including residents stationed overseas are contained in the tables:
    * [apportionment_pop_1990.csv](data_src/apportionment_pop_1990.csv)
    * [apportionment_pop_2000.csv](data_src/apportionment_pop_2000.csv)
    * [apportionment_pop_2010.csv](data_src/apportionment_pop_2010.csv)
    * [apportionment_pop_2020.csv](data_src/apportionment_pop_2020.csv)
    
    The Excel tables from which this data came can be downloaded from [this](https://www.census.gov/programs-surveys/decennial-census/data/tables.html) `census.gov` site.

The script `correct_data.py` complies this information into a single table [apportionment.csv](data_out/apportionment.csv) in the `data_out` directory.