from festival import load_festival
from modeles import Festival

f = Festival.from_data(load_festival())
print(f)
print(len(f.programme(day=f.days[1])))