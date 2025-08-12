import streamlit as st
import requests
import json
import pandas as pd
from typing import Optional

# FastAPI server URL
API_BASE_URL = "http://localhost:8000"

# Configure Streamlit page
st.set_page_config(
    page_title="Patient Management System",
    page_icon="🏥",
    layout="wide"
)

def make_request(endpoint: str, method: str = "GET", data: Optional[dict] = None):
    """Helper function to make API requests"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        
        return response
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to API server. Please make sure the FastAPI server is running on http://localhost:8000")
        return None
    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
        return None

def main():
    st.title("🏥 Patient Management System")
    st.markdown("---")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["🏠 Home", "👁️ View All Patients", "🔍 Search Patient", "➕ Add Patient", "✏️ Update Patient", "🗑️ Delete Patient", "📊 Sort Patients"]
    )
    
    if page == "🏠 Home":
        show_home_page()
    elif page == "👁️ View All Patients":
        show_all_patients()
    elif page == "🔍 Search Patient":
        search_patient()
    elif page == "➕ Add Patient":
        add_patient()
    elif page == "✏️ Update Patient":
        update_patient()
    elif page == "🗑️ Delete Patient":
        delete_patient()
    elif page == "📊 Sort Patients":
        sort_patients()

def show_home_page():
    st.header("Welcome to Patient Management System")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 System Features")
        st.write("""
        - **View All Patients**: Browse complete patient database
        - **Search Patient**: Find specific patient by ID
        - **Add Patient**: Register new patients with BMI calculation
        - **Update Patient**: Modify existing patient information
        - **Delete Patient**: Remove patient records
        - **Sort Patients**: Sort patients by age, height, or weight
        """)
    
    with col2:
        st.subheader("📊 System Status")
        # Check API status
        response = make_request("/")
        if response and response.status_code == 200:
            st.success("✅ API Server is running")
            
            # Get patient count
            patients_response = make_request("/view")
            if patients_response and patients_response.status_code == 200:
                patient_count = len(patients_response.json())
                st.info(f"📋 Total Patients: {patient_count}")
        else:
            st.error("❌ API Server is not responding")

def show_all_patients():
    st.header("👁️ View All Patients")
    
    response = make_request("/view")
    if response and response.status_code == 200:
        patients_data = response.json()
        
        if not patients_data:
            st.warning("No patients found in the database.")
            return
        
        # Convert to DataFrame for better display
        df_data = []
        for patient_id, patient_info in patients_data.items():
            row = {"ID": patient_id}
            row.update(patient_info)
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Patients", len(df))
        with col2:
            avg_age = df['age'].mean()
            st.metric("Average Age", f"{avg_age:.1f}")
        with col3:
            avg_bmi = df['bmi'].mean()
            st.metric("Average BMI", f"{avg_bmi:.1f}")
        with col4:
            male_count = len(df[df['gender'] == 'male'])
            st.metric("Male Patients", male_count)
        
        st.markdown("---")
        st.subheader("Patient Records")
        st.dataframe(df, use_container_width=True)

def search_patient():
    st.header("🔍 Search Patient")
    
    patient_id = st.text_input("Enter Patient ID:", placeholder="e.g., P001")
    
    if st.button("Search Patient"):
        if patient_id:
            response = make_request(f"/patient/{patient_id}")
            if response and response.status_code == 200:
                patient_data = response.json()
                
                st.success(f"✅ Patient {patient_id} found!")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Personal Information")
                    st.write(f"**Name:** {patient_data['name']}")
                    st.write(f"**Age:** {patient_data['age']} years")
                    st.write(f"**Gender:** {patient_data['gender'].title()}")
                    st.write(f"**City:** {patient_data['city']}")
                
                with col2:
                    st.subheader("Health Information")
                    st.write(f"**Height:** {patient_data['height']} m")
                    st.write(f"**Weight:** {patient_data['weight']} kg")
                    st.write(f"**BMI:** {patient_data['bmi']}")
                    
                    # BMI verdict with color coding
                    verdict = patient_data['verdict']
                    if verdict == "Normal":
                        st.success(f"**Status:** {verdict}")
                    elif verdict in ["Underweight", "Overweight"]:
                        st.warning(f"**Status:** {verdict}")
                    else:  # Obese
                        st.error(f"**Status:** {verdict}")
                        
            elif response and response.status_code == 404:
                st.error("❌ Patient ID not found!")
            else:
                st.error("❌ Error occurred while searching for patient.")
        else:
            st.warning("Please enter a Patient ID.")

def add_patient():
    st.header("➕ Add New Patient")
    
    with st.form("add_patient_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            patient_id = st.text_input("Patient ID*", placeholder="e.g., P010")
            name = st.text_input("Full Name*", placeholder="e.g., John Doe")
            age = st.number_input("Age*", min_value=1, max_value=120, value=25)
            city = st.text_input("City*", placeholder="e.g., Mumbai")
        
        with col2:
            gender = st.selectbox("Gender*", ["male", "female", "others"])
            height = st.number_input("Height (meters)*", min_value=0.1, max_value=3.0, value=1.70, step=0.01)
            weight = st.number_input("Weight (kg)*", min_value=1.0, max_value=500.0, value=70.0, step=0.1)
        
        submitted = st.form_submit_button("Add Patient", type="primary")
        
        if submitted:
            if all([patient_id, name, city]):
                patient_data = {
                    "id": patient_id,
                    "name": name,
                    "city": city,
                    "age": age,
                    "gender": gender,
                    "height": height,
                    "weight": weight
                }
                
                response = make_request("/patient", method="POST", data=patient_data)
                if response and response.status_code == 200:
                    st.success("✅ Patient added successfully!")
                elif response and response.status_code == 400:
                    st.error("❌ Patient ID already exists!")
                else:
                    st.error("❌ Error occurred while adding patient.")
            else:
                st.error("❌ Please fill all required fields marked with *")

def update_patient():
    st.header("✏️ Update Patient")
    
    patient_id = st.text_input("Enter Patient ID to update:", placeholder="e.g., P001")
    
    if patient_id:
        # First, get existing patient data
        response = make_request(f"/patient/{patient_id}")
        if response and response.status_code == 200:
            existing_data = response.json()
            
            st.success(f"✅ Patient {patient_id} found!")
            st.subheader("Update Information (leave blank to keep current value)")
            
            with st.form("update_patient_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    name = st.text_input("Full Name", placeholder=f"Current: {existing_data['name']}")
                    age = st.number_input("Age", min_value=1, max_value=120, value=None, placeholder=f"Current: {existing_data['age']}")
                    city = st.text_input("City", placeholder=f"Current: {existing_data['city']}")
                
                with col2:
                    gender = st.selectbox("Gender", ["", "male", "female"], index=0)
                    height = st.number_input("Height (meters)", min_value=0.1, max_value=3.0, value=None, placeholder=f"Current: {existing_data['height']}")
                    weight = st.number_input("Weight (kg)", min_value=1.0, max_value=500.0, value=None, placeholder=f"Current: {existing_data['weight']}")
                
                submitted = st.form_submit_button("Update Patient", type="primary")
                
                if submitted:
                    update_data = {}
                    if name: update_data["name"] = name
                    if age: update_data["age"] = age
                    if city: update_data["city"] = city
                    if gender: update_data["gender"] = gender
                    if height: update_data["height"] = height
                    if weight: update_data["weight"] = weight
                    
                    if update_data:
                        response = make_request(f"/patient_edit/{patient_id}", method="PUT", data=update_data)
                        if response and response.status_code == 200:
                            st.success("✅ Patient updated successfully!")
                        else:
                            st.error("❌ Error occurred while updating patient.")
                    else:
                        st.warning("No changes made.")
        elif response and response.status_code == 404:
            st.error("❌ Patient ID not found!")

def delete_patient():
    st.header("🗑️ Delete Patient")
    
    patient_id = st.text_input("Enter Patient ID to delete:", placeholder="e.g., P001")
    
    if patient_id:
        # Show patient info before deletion
        response = make_request(f"/patient/{patient_id}")
        if response and response.status_code == 200:
            patient_data = response.json()
            
            st.warning(f"⚠️ Patient {patient_id} found!")
            st.write(f"**Name:** {patient_data['name']}")
            st.write(f"**Age:** {patient_data['age']} years")
            st.write(f"**City:** {patient_data['city']}")
            
            st.error("🚨 This action cannot be undone!")
            
            if st.button("🗑️ Confirm Delete", type="primary"):
                response = make_request(f"/patient_delete/{patient_id}", method="DELETE")
                if response and response.status_code == 200:
                    st.success("✅ Patient deleted successfully!")
                else:
                    st.error("❌ Error occurred while deleting patient.")
        elif response and response.status_code == 404:
            st.error("❌ Patient ID not found!")

def sort_patients():
    st.header("📊 Sort Patients")
    
    col1, col2 = st.columns(2)
    
    with col1:
        sort_field = st.selectbox("Sort by:", ["age", "height", "weight"])
    
    with col2:
        sort_order = st.selectbox("Order:", ["asc", "desc"])
    
    if st.button("Sort Patients"):
        response = make_request(f"/sort?sort_by={sort_field}&order={sort_order}")
        if response and response.status_code == 200:
            sorted_data = response.json()
            
            if sorted_data:
                st.success(f"✅ Patients sorted by {sort_field} in {sort_order}ending order")
                
                # Convert to DataFrame
                df = pd.DataFrame(sorted_data)
                
                # Highlight the sorting column
                st.subheader(f"Sorted by {sort_field.title()} ({sort_order.upper()})")
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("No patients found to sort.")
        else:
            st.error("❌ Error occurred while sorting patients.")

if __name__ == "__main__":
    main()