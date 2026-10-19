from festival import load_festival

festival = load_festival()

print("VENUE:", festival["venues"][0])
print("ARTIST:", festival["artists"][0])

seen = set()
for performance in festival["performances"]:
    if performance["kind"] not in seen:
        seen.add(performance["kind"])
        print("PERFORMANCE:", performance)