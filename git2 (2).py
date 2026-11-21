import os
import shutil
import argparse

def create_directory(path):
    try:
        os.makedirs(path, exist_ok=True)
        print(f"Directory created or already exists: {path}")
    except Exception as e:
        print(f"Error creating directory: {e}")

def move_to_new_directory(source, destination):
    if not os.path.exists(source):
        print(f"Error: Source directory does not exist: {source}")
        return

    create_directory(destination)
    
    try:
        for item in os.listdir(source):
            s = os.path.join(source, item)
            d = os.path.join(destination, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
        print(f"Project copied to new directory: {destination}")
    except Exception as e:
        print(f"Error moving project: {e}")

def main():
    parser = argparse.ArgumentParser(description="Create a new directory or copy a project to a new directory.")
    parser.add_argument("action", choices=["create", "copy"], help="Action to perform: 'create' to create a new directory, 'copy' to copy a project to a new directory")
    parser.add_argument("path", help="Path to create or source path for copying")
    parser.add_argument("--destination", help="Destination path for copying (required for 'copy' action)")
    
    args = parser.parse_args()
    
    if args.action == "create":
        create_directory(args.path)
    elif args.action == "copy":
        if not args.destination:
            parser.error("The --destination argument is required for the 'copy' action")
        move_to_new_directory(args.path, args.destination)

if __name__ == "__main__":
    main()