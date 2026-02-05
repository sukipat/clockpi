import os

def find_missing_minutes(folder_path):
    expected = set()

    # Generate all expected HH_MM.json filenames
    for hour in range(24):
        for minute in range(60):
            expected.add(f"{hour:02d}_{minute:02d}.json")

    # Get actual .json files in the folder
    actual = {
        f for f in os.listdir(folder_path)
        if f.endswith(".json")
    }

    # Find missing files
    missing = sorted(expected - actual)

    return missing


if __name__ == "__main__":
    folder = "/Users/suki/Developer/clockpi/times"  # <-- change this
    missing_files = find_missing_minutes(folder)

    if not missing_files:
        print("✅ No missing minutes — all files present.")
    else:
        print(f"❌ Missing {len(missing_files)} minute(s):")
        for f in missing_files:
            print(f)