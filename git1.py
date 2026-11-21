import os
import shutil
import argparse

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Directory created: {path}")
    else:
        print(f"Directory already exists: {path}")

def move_to_new_directory(source, destination):
    if not os.path.exists(source):
        print(f"Source directory does not exist: {source}")
        return

    create_directory(destination)
    
    for item in os.listdir(source):
        s = os.path.join(source, item)
        d = os.path.join(destination, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)
    
    print(f"Project moved to new directory: {destination}")

def main():
    parser = argparse.ArgumentParser(description="Create a new directory or move a project to a new directory.")
    parser.add_argument("action", choices=["create", "move"], help="Action to perform: 'create' to create a new directory, 'move' to move a project to a new directory")
    parser.add_argument("path", help="Path to create or source path for moving")
    parser.add_argument("--destination", help="Destination path for moving (required for 'move' action)")
    
    args = parser.parse_args()
    
    if args.action == "create":
        create_directory(args.path)
    elif args.action == "move":
        if not args.destination:
            parser.error("The --destination argument is required for the 'move' action")
        move_to_new_directory(args.path, args.destination)

if __name__ == "__main__":
    main()