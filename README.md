# House of representatives apportionments

`houseofreps` implements apportionment methods for assigning seats in the US House of Representatives.

**Disclaimer: This product uses the Census Bureau Data API but is not endorsed or certified by the Census Bureau. See [Terms of Service](https://www.census.gov/data/developers/about/terms-of-service.html).**

Years supported:
```
1960, 1970, 1980, 1990, 2000, 2010, 2020
```

## Data source

The data source is from [https://www.census.gov](https://www.census.gov) and is completely described in the [data](data) folder.

## Installation

Local installation: clone the repo, then:
```
pip install -r requirements.txt
pip install -e .
```

## Tests

Tests are implemented for `pytest`. In the `tests` folder run:
```
pytest
```