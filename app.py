import streamlit as st
import pandas as pd
import sqlite3
import datetime

# --- Database Functions ---
def init_db():
    with sqlite3.connect('project_mapping.db') as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                category TEXT NOT NULL,
                pic TEXT NOT NULL,
                status TEXT NOT NULL,
                date_start TEXT NOT NULL,
                date_end TEXT NOT NULL
            )
        ''')
        conn.commit()

@st.cache_resource
def get_connection():
    return sqlite3.connect('project_mapping.db', check_same_thread=False)

def get_all_projects():
    try:
        with get_connection() as conn:
            df = pd.read_sql("SELECT * FROM projects", conn)
        return df
    except Exception as e:
        st.error(f"Error fetching projects: {e}")
        return pd.DataFrame()

def add_project(project_name, category, pic, status, date_start, date_end):
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("INSERT INTO projects (project_name, category, pic, status, date_start, date_end) VALUES (?, ?, ?, ?, ?, ?)",
                      (project_name, category, pic, status, date_start.strftime('%Y-%m-%d'), date_end.strftime('%Y-%m-%d')))
            conn.commit()
            st.success("Project added successfully!")
    except sqlite3.Error as e:
        st.error(f"Error adding project: {e}")

def update_project(id, project_name, category, pic, status, date_start, date_end):
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("UPDATE projects SET project_name=?, category=?, pic=?, status=?, date_start=?, date_end=? WHERE id=?",
                      (project_name, category, pic, status, date_start.strftime('%Y-%m-%d'), date_end.strftime('%Y-%m-%d'), id))
            conn.commit()
            st.success("Project updated successfully!")
    except sqlite3.Error as e:
        st.error(f"Error updating project: {e}")

def delete_project(id):
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM projects WHERE id=?", (id,))
            conn.commit()
            st.success("Project deleted successfully!")
    except sqlite3.Error as e:
        st.error(f"Error deleting project: {e}")

# --- Streamlit App ---
init_db()
st.image("cistech.png", width=250)

st.title("Dashboard Mapping Project")

tab1, tab2, tab3, tab4 = st.tabs(["View Projects", "Add Project", "Edit Project", "Delete Project"])

with tab1:
    st.subheader("Project List")
    df = get_all_projects()
    if not df.empty:
        display_df = df.rename(columns={
            'project_name': 'Project',
            'category': 'Category',
            'pic': 'PIC',
            'status': 'Status',
            'date_start': 'Start Date',
            'date_end': 'End Date'
        }).reset_index(drop=True)  # Reset index here

        # Display the DataFrame starting from index 1
        display_df.index += 1  # Start index from 1
        st.dataframe(display_df.drop('id', axis=1), use_container_width=True)
    else:
        st.info("No projects found in the database.")

with tab2:
    st.subheader("Add New Project")
    with st.form("add_project_form"):
        category = st.selectbox("Category", ["Project", "Service"])
        new_project = st.text_input("Project Name")
        new_pic = st.text_input("PIC")
        new_status = st.selectbox("Status", ["Not Started", "Waiting BA", "Not Report", "In Progress", "On Hold", "Completed"])
        st.write("Project Duration")
        today = datetime.date.today()
        date_range = st.date_input(
            "Select start and end date",
            value=(today, today + datetime.timedelta(days=30)),
            min_value=today - datetime.timedelta(days=365),
            max_value=today + datetime.timedelta(days=365),
        )

        submit_button = st.form_submit_button("Add Project")
        if submit_button:
            if new_project and new_pic:
                if isinstance(date_range, tuple) and len(date_range) == 2:
                    date_start, date_end = date_range
                    add_project(new_project, category, new_pic, new_status, date_start, date_end)
                else:
                    st.error("Please select both start and end dates.")
            else:
                st.error("Project Name and PIC are required!")

with tab3:
    st.subheader("Edit Project")
    df = get_all_projects()
    if not df.empty:
        project_options = df[['id', 'project_name']].copy()
        project_to_edit = st.selectbox("Select Project to Edit",
                                        options=project_options['id'].tolist(),
                                        format_func=lambda x: project_options[project_options['id'] == x]['project_name'].iloc[0])

        selected_project = df[df['id'] == project_to_edit].iloc[0]
        with st.form("edit_project_form"):
            edit_category = st.selectbox("Category", ["Project", "Service"], index=["Project", "Service"].index(selected_project['category']) if selected_project['category'] in ["Project", "Service"] else 0)
            edit_project = st.text_input("Project Name", selected_project['project_name'])
            edit_pic = st.text_input("PIC", selected_project['pic'])
            edit_status = st.selectbox("Status", ["Not Started", "Waiting BA", "Not Report", "In Progress", "On Hold", "Completed"], index=["Not Started", "Waiting BA", "Not Report", "In Progress", "On Hold", "Completed"].index(selected_project['status']) if selected_project['status'] in ["Not Started", "Waiting BA", "Not Report", "In Progress", "On Hold", "Completed"] else 0)
            st.write("Project Duration")
            start_date = datetime.datetime.strptime(selected_project['date_start'], '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(selected_project['date_end'], '%Y-%m-%d').date()
            date_range = st.date_input(
                "Select start and end date",
                value=(start_date, end_date),
                min_value=datetime.date.today() - datetime.timedelta(days=365),
                max_value=datetime.date.today() + datetime.timedelta(days=365),
            )

            update_button = st.form_submit_button("Update Project")
            if update_button:
                if edit_project and edit_pic:
                    if isinstance(date_range, tuple) and len(date_range) == 2:
                        edit_date_start, edit_date_end = date_range
                        update_project(project_to_edit, edit_project, edit_category, edit_pic, edit_status, edit_date_start, edit_date_end)
                    else:
                        st.error("Please select both start and end dates.")
                else:
                    st.error("Project Name and PIC are required!")

with tab4:
    st.subheader("Delete Project")
    df = get_all_projects()
    if not df.empty:
        project_to_delete = st.selectbox("Select Project to Delete", df['id'].tolist(), format_func=lambda x: df[df['id'] == x]['project_name'].iloc[0])
        if st.button("Delete Project"):
            delete_project(project_to_delete)
    else:
        st.info("No projects found to delete.")
