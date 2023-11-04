import pandas as pd
import os
from houseofreps import St

# Read historical data
dir_src = "data_src"
df = pd.read_csv(os.path.join(dir_src,"historical.csv"))

# Discard 1950 and earlier - problems with these assignments using priority method
df = df[df["Year"] > 1950]

# Fix stupid comma numbers
df["Resident Population"] = df["Resident Population"].apply(lambda x: int(x.replace(',','')))

# Drop regions not related to states
state_names = [x.name for x in St]
def contains(name):
    return name in state_names
df = df[df['Name'].apply(contains)]

# Add column for overseas population included
df.insert(4, "Overseas population included", 0)
df.insert(5, "Population used for apportionment", 0)

# Read data for population with overseas included
pop_with_overseas = {}
for year in ['1970','1990','2000','2010','2020']:
    pop_with_overseas[year] = {}

    df_app = pd.read_csv(os.path.join(dir_src,"apportionment_pop_%s.csv" % year))
    for idx,row in df_app.iterrows():
        state = row[0]
        st = St.from_name(state)

        pwo = row[1]
        if year == '1970' or year == '1990' or year == '2010' or year == '2020':
            pwo = int(pwo.replace(',',''))
        elif year == '2000':
            pwo = int(pwo.replace(' ',''))

        pop_with_overseas[year][st] = pwo

# Add to dataframe
for idx, row in df.iterrows():
    state = row[0]
    st = St.from_name(state)

    year = row[2]
    pop_res = row[3]

    df.loc[idx, "Population used for apportionment"] = pop_res # type: ignore
    if str(year) in pop_with_overseas and st in pop_with_overseas[str(year)]:
        df.loc[idx, "Overseas population included"] = pop_with_overseas[str(year)][st] - pop_res # type: ignore
        if pop_with_overseas[str(year)][st] != 0:
            df.loc[idx, "Population used for apportionment"] = pop_with_overseas[str(year)][st] # type: ignore

# Write
if not os.path.isdir("data_out"):
    os.makedirs("data_out")

fname = "data_out/apportionment.csv"
df.to_csv(fname)

print("Successfully compiled data sources and wrote output to: %s." % fname)