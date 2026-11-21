
import os
import subprocess
import argparse

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    return output.decode('utf-8'), error.decode('utf-8')

def init_git_repo(path):
    os.chdir(path)
    output, error = run_command("git init")
    if error:
        print(f"Error initializing repository: {error}")
    else:
        print(f"Git repository initialized in {path}")

def move_to_git_repo(source, destination):
    if not os.path.exists(destination):
        os.makedirs(destination)
   
    for item in os.listdir(source):
        s = os.path.join(source, item)
        d = os.path.join(destination, item)
        if os.path.isdir(s):
            if not os.path.exists(d):
                os.makedirs(d)
            move_to_git_repo(s, d)
        else:
            if not os.path.exists(d) or os.stat(s).st_mtime - os.stat(d).st_mtime > 1:
                open(d, 'wb').write(open(s, 'rb').read())
   
    init_git_repo(destination)
    print(f"Project moved to new Git repository in {destination}")

def main():
    parser = argparse.ArgumentParser(description="Create a Git repository or move a project to a new Git repository.")
    parser.add_argument("action", choices=["init", "move"], help="Action to perform: 'init' to initialize a new repo, 'move' to move a project to a new repo")
    parser.add_argument("path", help="Path to initialize or source path for moving")
    parser.add_argument("--destination", help="Destination path for moving (required for 'move' action)")
   
    args = parser.parse_args()
   
    if args.action == "init":
        init_git_repo(args.path)
    elif args.action == "move":
        if not args.destination:
            parser.error("The --destination argument is required for the 'move' action")
        move_to_git_repo(args.path, args.destination)

if __name__ == "__main__":
    main() 
