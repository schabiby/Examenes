import json
import os
import pandas as pd
from config import DATA_FILE, DEFAULT_COURSES, DEFAULT_NUM_MODULES

# ---------- LOAD / SAVE ----------
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                if "groups" not in data:
                    data["groups"] = {}
                # Migrate old format (list of students) to new dict
                for gname, gval in list(data["groups"].items()):
                    if not isinstance(gval, dict):
                        if isinstance(gval, list):
                            new_group = {
                                "courses": DEFAULT_COURSES[:],
                                "num_modules": DEFAULT_NUM_MODULES,
                                "students": {}
                            }
                            for sid in gval:
                                new_group["students"][sid] = {}
                                for course in DEFAULT_COURSES:
                                    new_group["students"][sid][course] = {}
                                    for mod in [f"Module {i}" for i in range(1, DEFAULT_NUM_MODULES + 1)]:
                                        new_group["students"][sid][course][mod] = None
                            data["groups"][gname] = new_group
                        else:
                            del data["groups"][gname]
                return data
        except Exception:
            return {"groups": {}}
    return {"groups": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ---------- GROUP OPERATIONS ----------
def create_group(groups, group_name, courses, num_modules):
    if group_name in groups:
        return False
    groups[group_name] = {
        "courses": [c.strip() for c in courses if c.strip()],
        "num_modules": num_modules,
        "students": {}
    }
    return True

def delete_group(groups, group_name):
    if group_name in groups:
        del groups[group_name]
        return True
    return False

def update_group_modules(groups, group_name, new_num_modules):
    """Change the number of modules for a group.
       If increasing, add empty modules for all students.
       If decreasing, drop the extra modules (marks lost)."""
    if group_name not in groups:
        return False
    old_num = groups[group_name]["num_modules"]
    if new_num_modules == old_num:
        return True
    groups[group_name]["num_modules"] = new_num_modules
    # Adjust each student's data
    old_mods = [f"Module {i}" for i in range(1, old_num + 1)]
    new_mods = [f"Module {i}" for i in range(1, new_num_modules + 1)]
    for sid, sdata in groups[group_name]["students"].items():
        for course in groups[group_name]["courses"]:
            # Keep old marks for modules that still exist
            if new_num_modules > old_num:
                # Add new modules with None
                for mod in new_mods:
                    if mod not in sdata[course]:
                        sdata[course][mod] = None
            else:
                # Remove modules that are beyond new count
                for mod in old_mods:
                    if mod not in new_mods:
                        if mod in sdata[course]:
                            del sdata[course][mod]
    return True

def get_courses(groups, group_name):
    return groups.get(group_name, {}).get("courses", [])

def get_num_modules(groups, group_name):
    return groups.get(group_name, {}).get("num_modules", DEFAULT_NUM_MODULES)

def get_module_names(groups, group_name):
    num = get_num_modules(groups, group_name)
    return [f"Module {i}" for i in range(1, num + 1)]

def add_student_to_group(groups, group_name, student_id):
    if group_name not in groups:
        return False
    if student_id in groups[group_name]["students"]:
        return False
    courses = get_courses(groups, group_name)
    modules = get_module_names(groups, group_name)
    student_data = {}
    for course in courses:
        student_data[course] = {}
        for mod in modules:
            student_data[course][mod] = None
    groups[group_name]["students"][student_id] = student_data
    return True

def remove_student_from_group(groups, group_name, student_id):
    if group_name not in groups:
        return False
    if student_id not in groups[group_name]["students"]:
        return False
    del groups[group_name]["students"][student_id]
    return True

# ---------- STUDENT DATA OPERATIONS ----------
def get_student_data(groups, group_name, student_id):
    return groups.get(group_name, {}).get("students", {}).get(student_id)

def compute_total(student_data):
    total = 0.0
    for course, mods in student_data.items():
        for mod, mark in mods.items():
            if mark is not None:
                total += mark
    return total

def compute_course_total(student_data, course):
    total = 0.0
    for mod, mark in student_data.get(course, {}).items():
        if mark is not None:
            total += mark
    return total

def count_entered(student_data):
    count = 0
    for course, mods in student_data.items():
        for mark in mods.values():
            if mark is not None:
                count += 1
    return count

def student_data_to_df(student_data, courses, module_names):
    """Build DataFrame with modules as rows, courses as columns."""
    data = {course: [] for course in courses}
    for mod in module_names:
        for course in courses:
            mark = student_data.get(course, {}).get(mod)
            data[course].append(mark if mark is not None else None)
    df = pd.DataFrame(data, index=module_names)
    return df

def df_to_student_data(df, student_data, courses, module_names):
    """Update student_data from edited DataFrame."""
    for course in courses:
        for mod in module_names:
            student_data[course][mod] = None
    for mod in module_names:
        for course in courses:
            val = df.loc[mod, course]
            if pd.isna(val):
                student_data[course][mod] = None
            else:
                student_data[course][mod] = float(val)
    return student_data

def get_group_summary(groups, group_name):
    if group_name not in groups:
        return pd.DataFrame()
    group = groups[group_name]
    courses = group["courses"]
    rows = []
    for sid, data in group["students"].items():
        row = {"Student": sid}
        for course in courses:
            row[f"{course} Total"] = compute_course_total(data, course)
        row["Grand Total"] = compute_total(data)
        rows.append(row)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)

def get_group_details(groups, group_name):
    if group_name not in groups:
        return {}
    group = groups[group_name]
    courses = group["courses"]
    module_names = get_module_names(groups, group_name)
    details = {}
    for sid, data in group["students"].items():
        details[sid] = student_data_to_df(data, courses, module_names)
    return details