import fitler

amc = ActivityFileCollection('./export*/activities/*')
amc.process()
print(amc.to_json())
