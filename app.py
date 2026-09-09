import streamlit as st
from supabase import create_client

SUPABASE_URL = "https://efqckksjhldyxmokmcfd.supabase.co/rest/v1/Citas"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVmcWNra3NqaGxkeXhtb2ttY2ZkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg5MzM0NjYsImV4cCI6MjEwNDUwOTQ2Nn0._q0FRMevxqLmAiYUb9wBzDLIzyqXQblhuIhn6FCXvxU"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Citas Médicas", page_icon="🩺")
st.title("🩺 Gestor de Citas")
st.subheader("Salud Ocupacional")

with st.form("form_cita", clear_on_submit=True):
    clave = st.text_input("Clave o Número de Empleado:")
    fecha = st.date_input("Fecha preferida:")
    hora = st.time_input("Hora preferida:")
    motivo = st.selectbox("Motivo:", [
        "Examen Periódico", 
        "Consulta General", 
        "Evaluación Ergonómica", 
        "Valoración de Egreso"
    ])
    submit = st.form_submit_button("Agendar Cita")

if submit:
    if not clave.strip():
        st.error("Por favor ingresa tu clave.")
    else:
        nueva_cita = {
            "clave": clave,
            "fecha": str(fecha),
            "hora": str(hora),
            "motivo": motivo,
            "estado": "Pendiente"
        }
        supabase.table("citas").insert(nueva_cita).execute()
        st.success("¡Cita agendada correctamente!")
