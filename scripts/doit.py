import fitler

sac = fitler.SpreadsheetActivityCollection(path='data/exerciselog.xlsx')
sac.initialize()
print("Spreadsheet rows parsed: ", len(sac.activities))
