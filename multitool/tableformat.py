# tableformat.py


class TableFormatter:
    def headings(self, headers):
        '''Output the table headings'''
        raise NotImplementedError()

    def row(self, rowdata):
        '''Output single row of table data'''
        raise NotImplementedError()


class TextTableFormatter(TableFormatter):
    '''Output data in plain-text format'''
    def headings(self, headers):
        s = ''
        for h in headers:
            s = s + (f'{h:>10s}')
        s = s + '\n'
        s = s + (('-'*10 + ' ')*len(headers))
        return s

    def row(self, rowdata):
        s = ''
        for d in rowdata:
            s = s + (f'{d:>10s}')
        return s


class CSVTableFormatter(TableFormatter):
    '''Output data in CSV format.'''
    def headings(self, headers):
        s = ','.join(headers)
        return s

    def row(self, rowdata):
        s = ','.join(rowdata)
        return s


class HTMLTableFormatter(TableFormatter):
    '''Output data in HTML format.'''
    def headings(self, headers):
        s = '<tr>'
        for h in headers:
            s = s + f'<th>{h}</th>'
        s = s + ('</tr>')
        return s

    def row(self, rowdata):
        s = '<tr>'
        for d in rowdata:
            s = s + f'<td>{d}</td>'
        s = s + '</tr>'
        return s


class MDTableFormatter(TableFormatter):
    '''Output data in GH Markdown format'''
    def headings(self, headers):
        s = ''
        for x, h in enumerate(headers):
            if (x == 0):
                s = s + f'{h} '
            else:
                s = s + f'| {h} '
        s = s + '\n'
        for i, h in enumerate(headers):
            if (i == 0):
                s = s + '-'*len(h) + ' '
            else:
                s = s + '| ' + '-'*len(h) + ' '
        return s

    def row(self, rowdata):
        s = ''
        for x, row in enumerate(rowdata):
            if (x == 0):
                s = s + f'{row} '
            else:
                s = s + f'| {row} '
        return s


def create_formatter(name):
    '''Create formatter object in specified format'''
    if name == 'txt':
        return TextTableFormatter()
    elif name == 'csv':
        return CSVTableFormatter()
    elif name == 'html':
        return HTMLTableFormatter()
    elif name == 'md':
        return MDTableFormatter()
    else:
        raise FormatError(f'Unknown table format {name}')


def print_table(data, headers, formatter):
    '''Generic table formatting function using formatters'''
    s = str(formatter.headings(headers))
    for obj in data:
        rowdata = [str(getattr(obj, name)) for name in headers]
        s = s + str(formatter.row(rowdata))
    return s


class FormatError(Exception):
    pass
