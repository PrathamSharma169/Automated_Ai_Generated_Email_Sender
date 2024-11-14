import pandas as pd
data = {
    'Name': ['Yugal','Yash'],
    'location' : ['Indore','Bhopal'],
    'email' : ['yugal_sample@gmail.com','Yash_sample@gmail.com'] # these are fake id
}
df=pd.DataFrame(data)
df.to_csv('sample.csv')