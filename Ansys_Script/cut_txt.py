import pandas

df = pandas.read_csv('surfaces.txt', delimiter=',')


with open('surfaces_param.csv', 'w', newline='') as csvfile:
    for i in df.columns:
        a = i.replace("db.models['ACP Model'].element_sets['", "")
        b = a.replace("']", "")
        csvfile.write('%s' %b)
        csvfile.write('\n')
