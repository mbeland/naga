# fileparse.py
#
# Exercise 3.3
import csv
import logging
log = logging.getLogger(__name__)


def parse_csv(data, select=None, types=None, has_headers=True,
              delimiter=None, silence_errors=False):
    '''
    Parse a CSV data set into a list of records
        Provide data set (req)
        Columns to include as select= (def. None)
        Types conversion for data fields (def. None)
        has_headers (def. True)
        specify delimiter (def. None, defaults to comma)
    '''
    if select and not has_headers:
        raise RuntimeError("Select argument requires column headers")
    if delimiter:
        rows = csv.reader(data, delimiter=delimiter)
    else:
        rows = csv.reader(data)

    # read the data headers
    if has_headers:
        headers = next(rows)

    records = []
    # If a column selector was given, find indices of the specified
    # columns. Also narrow the set of headers used for resulting
    # dictionaries
    if select:
        indices = [headers.index(colname) for colname in select]
        headers = select
    else:
        indices = []

    for x, row in enumerate(rows, start=1):
        try:
            if not row:     # Skip rows with no data
                continue
            # Filter the row if specific columns were selected
            if indices:
                row = [row[index] for index in indices]

            # If types are specified, convert data elements accordingly
            if types:
                row = [func(val) for func, val in zip(types, row)]

            # Make a dictionary
            if has_headers:
                records.append(dict(zip(headers, row)))
            else:
                records.append(row)
        except ValueError as e:
            if not silence_errors:
                log.warning(f'Row {x}: Couldn\'t convert {row}')
                log.debug(f'Row {x}: Reason {e}')
            continue
    return(records)
