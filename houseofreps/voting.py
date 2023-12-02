from .state import St

from dataclasses import dataclass
from mashumaro import DataClassDictMixin
from typing import Dict

@dataclass
class Members(DataClassDictMixin):
    icpsr_to_state: Dict[int, St]

def load_members_from_csv(fname: str) -> Members:

    import pandas as pd

    # Load csv
    df = pd.read_csv(fname)

    # Column icpsr to state_abbrev
    icpsr_to_state_str = dict(zip(df.icpsr, df.state_abbrev))

    # Convert to icpsr to St
    st_values = set([ s.value for s in St ])
    icpsr_to_state = {
        icpsr: St(state_abbrev) 
        for icpsr, state_abbrev in icpsr_to_state_str.items()
        if state_abbrev in st_values
        }

    return Members(icpsr_to_state=icpsr_to_state)