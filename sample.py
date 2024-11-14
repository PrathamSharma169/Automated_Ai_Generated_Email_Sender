import pandas as pd
data = {
    'Name': ['Yugal','Raju'],
    'location' : ['Indore','Khargon'],
    'email' : ['yugal1107@gmail.com','yuvraj7000raju@gmail.com']
}
df=pd.DataFrame(data)
df.to_csv('sample.csv')