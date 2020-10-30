import glob

path = './export*/activities/*'

gen = glob.iglob(path)

for file in gen:
    print(file)
