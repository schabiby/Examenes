import streamlit as st
import pandas as pd
import base64
from config import DATA_FILE, DEFAULT_COURSES, DEFAULT_NUM_MODULES
from data_manager import (
    load_data, save_data,
    create_group, delete_group, update_group_modules,
    add_student_to_group, remove_student_from_group,
    get_student_data, get_courses, get_module_names,
    compute_total, count_entered,
    get_group_summary
)
from pdf_generator import generate_pdf_report
from averages import compute_score_out_of_10, build_full_dataframe_with_averages, separate_data_from_full_df

st.set_page_config(page_title="Student Marks Manager", layout="wide")

# ---- Sidebar toggle ----
if 'show_sidebar' not in st.session_state:
    st.session_state.show_sidebar = True

hide_sidebar_css = """
<style>
[data-testid="stSidebar"] {
    display: none !important;
}
</style>
"""

col_title, col_toggle = st.columns([6, 1])
with col_title:
    st.title("📚 Student Marks Manager")
with col_toggle:
    if st.button("☰" if st.session_state.show_sidebar else "☰", help="Toggle sidebar"):
        st.session_state.show_sidebar = not st.session_state.show_sidebar
        st.rerun()

if not st.session_state.show_sidebar:
    st.markdown(hide_sidebar_css, unsafe_allow_html=True)

# ---- Load data ----
data = load_data()
groups = data["groups"]

if 'groups' not in st.session_state:
    st.session_state.groups = groups

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("👥 Create Group")
    with st.form(key="create_group_form"):
        group_name = st.text_input("Group name")
        num_modules = st.number_input("Number of modules", min_value=1, max_value=30, value=DEFAULT_NUM_MODULES, step=1)
        courses_input = st.text_input("Course names (comma separated)", value=", ".join(DEFAULT_COURSES))
        submit_group = st.form_submit_button("➕ Create Group", use_container_width=True)
        if submit_group:
            if group_name.strip() and courses_input.strip():
                courses = [c.strip() for c in courses_input.split(",") if c.strip()]
                if not courses:
                    st.error("Please enter at least one course.")
                else:
                    if create_group(st.session_state.groups, group_name.strip(), courses, int(num_modules)):
                        save_data({"groups": st.session_state.groups})
                        st.success(f"✅ Group '{group_name}' created with {len(courses)} courses and {num_modules} modules.")
                    else:
                        st.error("Group already exists.")
            else:
                st.warning("Please fill in all fields.")

    st.divider()

    if st.session_state.groups:
        group_names = list(st.session_state.groups.keys())
        selected_group = st.selectbox("Select a Group", group_names, key="group_selector")
        if selected_group:
            current_mods = st.session_state.groups[selected_group]["num_modules"]
            new_mod_count = st.number_input("Number of modules", min_value=1, max_value=30, value=current_mods, step=1, key="edit_modules")
            if new_mod_count != current_mods:
                if st.button("📝 Update Modules", use_container_width=True):
                    if update_group_modules(st.session_state.groups, selected_group, int(new_mod_count)):
                        save_data({"groups": st.session_state.groups})
                        st.success(f"Modules updated to {new_mod_count}")
                        st.rerun()
                    else:
                        st.error("Failed to update.")

        with st.form(key="delete_group_form"):
            delete_btn = st.form_submit_button("🗑️ Delete Group", type="secondary", use_container_width=True)
            if delete_btn and selected_group:
                if delete_group(st.session_state.groups, selected_group):
                    save_data({"groups": st.session_state.groups})
                    st.success(f"🗑️ Group '{selected_group}' deleted!")
                    st.rerun()
    else:
        selected_group = None
        st.info("No groups yet.")

    st.divider()
    total_students = sum(len(g.get("students", {})) for g in st.session_state.groups.values())
    st.metric("👥 Total Students", total_students)

# ---------- MAIN AREA ----------
if not selected_group:
    st.info("👈 Please create or select a group from the sidebar to start.")
    st.stop()

group_data = st.session_state.groups[selected_group]
courses = group_data["courses"]
module_names = get_module_names(st.session_state.groups, selected_group)
members = list(group_data["students"].keys())

col_left, col_right = st.columns([1, 2], gap="medium")

with col_left:
    st.subheader(f"📋 Students in '{selected_group}'")
    st.caption(f"Courses: {', '.join(courses)} | Modules: {len(module_names)}")

    with st.form(key="add_new_student_form"):
        new_student_name = st.text_input("Student name")
        add_new_submit = st.form_submit_button("➕ Add New Student", use_container_width=True)
        if add_new_submit:
            if new_student_name.strip():
                sid = new_student_name.strip()
                if sid in group_data["students"]:
                    st.warning(f"Student '{sid}' already exists in this group.")
                else:
                    if add_student_to_group(st.session_state.groups, selected_group, sid):
                        save_data({"groups": st.session_state.groups})
                        st.success(f"✅ Student '{sid}' added to group!")
                    else:
                        st.error("Failed to add student.")
            else:
                st.warning("Enter a name.")

    st.divider()
    st.caption("Students are unique per group.")
    st.divider()

    if not members:
        st.info("No students in this group yet.")
        selected_student = None
    else:
        st.write("**Click a student to view/edit marks:**")
        with st.container(height=300):
            for sid in members:
                if st.button(sid, key=f"btn_{sid}", use_container_width=True):
                    st.session_state.selected_student = sid
                    st.rerun()

        if 'selected_student' in st.session_state and st.session_state.selected_student in members:
            selected_student = st.session_state.selected_student
        else:
            selected_student = members[0] if members else None
            if selected_student:
                st.session_state.selected_student = selected_student

        if selected_student:
            if st.button(f"🗑️ Remove '{selected_student}' from group", type="secondary", use_container_width=True):
                if remove_student_from_group(st.session_state.groups, selected_group, selected_student):
                    save_data({"groups": st.session_state.groups})
                    st.success(f"🗑️ Student '{selected_student}' removed!")
                    if 'selected_student' in st.session_state:
                        del st.session_state.selected_student
                    st.rerun()

with col_right:
    if not members:
        st.info("This group has no members. Add students from the left panel.")
    elif selected_student:
        student_data = get_student_data(st.session_state.groups, selected_group, selected_student)
        if student_data is None:
            st.error("Student data not found.")
        else:
            st.subheader(f"✏️ Marks for {selected_student}")
            entered = count_entered(student_data)
            total_cells = len(courses) * len(module_names)
            progress = entered / total_cells if total_cells > 0 else 0
            score = compute_score_out_of_10(student_data, courses, module_names)

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("📊 Score (out of 10)", f"{score:.2f}")
            with c2:
                st.metric("✅ Marks Entered", f"{entered} / {total_cells}")
            with c3:
                st.metric("📈 Progress", f"{progress:.0%}")
                st.progress(progress)

            # Build full DataFrame with averages
            full_df = build_full_dataframe_with_averages(student_data, courses, module_names)

            # Use data_editor without disabled – allow editing all cells
            edited_df = st.data_editor(
                full_df,
                column_config={
                    course: st.column_config.NumberColumn(
                        course,
                        min_value=0,
                        max_value=10,
                        step=0.5,
                        format="%.1f",
                        help="Enter mark between 0 and 10 (e.g., 8.5)"
                    ) for course in courses
                },
                use_container_width=True,
                height=400,
                key="marks_editor"
            )

            # Check if any editable cell changed (only the module x courses part)
            # Ignore changes to "Module Avg" column or "Course Avg" row
            editable_old = full_df.loc[module_names, courses]
            editable_new = edited_df.loc[module_names, courses]
            if not editable_new.equals(editable_old):
                # Update student data from the edited DataFrame
                new_student_data = separate_data_from_full_df(edited_df, courses, module_names)
                st.session_state.groups[selected_group]["students"][selected_student] = new_student_data
                save_data({"groups": st.session_state.groups})
                st.toast("✅ Marks saved successfully!", icon="✔️")
                st.rerun()

            if st.button(f"🗑️ Delete '{selected_student}' permanently", type="secondary"):
                if selected_student in st.session_state.groups[selected_group]["students"]:
                    del st.session_state.groups[selected_group]["students"][selected_student]
                    save_data({"groups": st.session_state.groups})
                    st.success(f"🗑️ Student '{selected_student}' deleted!")
                    if 'selected_student' in st.session_state:
                        del st.session_state.selected_student
                    st.rerun()
    else:
        st.subheader(f"📊 Group Summary – '{selected_group}'")
        summary_df = get_group_summary(st.session_state.groups, selected_group)
        if not summary_df.empty:
            st.dataframe(
                summary_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Student": "Student",
                    **{f"{c} Total": st.column_config.NumberColumn(f"{c} Total", format="%.2f") for c in courses},
                    "Grand Total": st.column_config.NumberColumn("Grand Total", format="%.2f")
                }
            )
        else:
            st.warning("No data available.")
        if st.button("📥 Download PDF Report", type="primary"):
            with st.spinner("Generating PDF..."):
                pdf_bytes = generate_pdf_report(st.session_state.groups, selected_group)
                if pdf_bytes:
                    b64 = base64.b64encode(pdf_bytes).decode()
                    href = f'<a href="data:application/pdf;base64,{b64}" download="{selected_group}_report.pdf">Click here to download PDF</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    st.success("✅ PDF generated!")
                else:
                    st.error("Failed to generate PDF.")