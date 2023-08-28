import os
import json

if __name__ == "__main__":
    with open("all-roles.json", "r") as file:
        contents = json.load(file)
        roles = contents["Roles"]
        for role in roles:
            