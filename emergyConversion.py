
def joules_to_calories(joules):
    return joules * 0.239006

def calories_to_joules(calories):
    return calories * 4.184

def joules_to_kilowatt_hours(joules):
    return joules / 3600000

def kilowatt_hours_to_joules(kwh):
    return kwh * 3600000

def main():
    print("Energy Conversion Calculator")
    print("1. Joules to Calories")
    print("2. Calories to Joules")
    print("3. Joules to Kilowatt-hours")
    print("4. Kilowatt-hours to Joules")

    choice = int(input("Enter your choice (1-4): "))
    value = float(input("Enter the value to convert: "))

    if choice == 1:
        result = joules_to_calories(value)
        print(f"{value} Joules = {result:.2f} Calories")
    elif choice == 2:
        result = calories_to_joules(value)
        print(f"{value} Calories = {result:.2f} Joules")
    elif choice == 3:
        result = joules_to_kilowatt_hours(value)
        print(f"{value} Joules = {result:.6f} Kilowatt-hours")
    elif choice == 4:
        result = kilowatt_hours_to_joules(value)
        print(f"{value} Kilowatt-hours = {result:.2f} Joules")
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main() 
