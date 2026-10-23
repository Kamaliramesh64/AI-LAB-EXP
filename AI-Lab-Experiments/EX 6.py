# Two-room vacuum cleaner agent
rooms = {"A": "Dirty", "B": "Dirty"}
location = "A"

while "Dirty" in rooms.values():
    print(f"Location: {location}, Status: {rooms[location]}")
    if rooms[location] == "Dirty":
        rooms[location] = "Clean"
        print(f"Action: Clean room {location}")
    else:
        location = "B" if location == "A" else "A"
        print(f"Action: Move to room {location}")

print("All rooms are clean.")
print(rooms)
