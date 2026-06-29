# averages.py
import pandas as pd

def compute_course_averages(student_data, courses, module_names):
    avgs = {}
    for course in courses:
        marks = [student_data[course].get(mod) for mod in module_names if student_data[course].get(mod) is not None]
        avgs[course] = sum(marks) / len(marks) if marks else None
    return avgs

def compute_module_averages(student_data, courses, module_names):
    avgs = {}
    for mod in module_names:
        marks = [student_data[course].get(mod) for course in courses if student_data[course].get(mod) is not None]
        avgs[mod] = sum(marks) / len(marks) if marks else None
    return avgs

def compute_score_out_of_10(student_data, courses, module_names):
    course_avgs = compute_course_averages(student_data, courses, module_names)
    valid = [avg for avg in course_avgs.values() if avg is not None]
    if not valid:
        return 0.0
    return sum(valid) / len(valid)

def build_full_dataframe_with_averages(student_data, courses, module_names):
    """Build a DataFrame with modules as rows, courses as columns,
       plus an extra column 'Module Avg' and an extra row 'Course Avg'.
    """
    data = {course: [] for course in courses}
    for mod in module_names:
        for course in courses:
            mark = student_data.get(course, {}).get(mod)
            data[course].append(mark if mark is not None else None)
    df = pd.DataFrame(data, index=module_names)
    
    course_avgs = compute_course_averages(student_data, courses, module_names)
    module_avgs = compute_module_averages(student_data, courses, module_names)
    
    # Add Module Avg column
    df["Module Avg"] = [module_avgs.get(mod, None) for mod in module_names]
    
    # Add Course Avg row
    course_avg_row = {course: course_avgs.get(course, None) for course in courses}
    all_marks = [m for mod in module_names for course in courses if (m := df.loc[mod, course]) is not None]
    course_avg_row["Module Avg"] = sum(all_marks)/len(all_marks) if all_marks else None
    df.loc["Course Avg"] = course_avg_row
    return df

def separate_data_from_full_df(full_df, courses, module_names):
    """Extract only the editable marks (exclude averages row/col)."""
    student_data = {course: {} for course in courses}
    for mod in module_names:
        if mod in full_df.index:
            for course in courses:
                val = full_df.loc[mod, course]
                if pd.isna(val):
                    student_data[course][mod] = None
                else:
                    student_data[course][mod] = float(val)
    return student_data