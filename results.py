import pandas as pd

df = pd.read_json("resultados.json")

df.T.to_excel("resultados.xlsx")
