import fitler

amc = fitler.ActivityFileCollection('./export*/activities/*')
amc.process()
print(amc.to_json())
