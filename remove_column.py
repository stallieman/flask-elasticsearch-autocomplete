import pandas as pd

# Load the CSV file
file_path = '/Users/marcostalman/Projecten/flask-elasticsearch-autocomplete/IMDB_Movies_Dataset.csv'
df = pd.read_csv(file_path)

# Drop the first column
df = df.drop(df.columns[0], axis=1)

# Save the modified CSV back to a file
df.to_csv(file_path, index=False)