import openpyxl
from pathlib import Path

class ActivitySpreadsheet(object):
    def __init__(self, path):
        self.path = path

    def parse(self):
        xlsx_file = Path('ActivityData', self.path)
        wb_obj = openpyxl.load_workbook(xlsx_file)
        sheet = wb_obj.active

        col_names = []
        for column in sheet.iter_cols(1, sheet.max_column):
            col_names.append(column[0].value)

        print(col_names)

        for row in sheet.iter_rows(max_row=6):
            for cell in row:
                print(cell.value, end=" ")
            print()


ass = ActivitySpreadsheet('/Users/ckdake/Documents/exerciselog.xlsx')
ass.parse()