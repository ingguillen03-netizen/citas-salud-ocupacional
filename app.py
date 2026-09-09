import streamlit as st
from supabase import create_client

# Asegúrate de que esta sea la URL de tu proyecto actual y tu clave 'anon public'
SUPABASE_URL = "https://efqckksjhldyxmokmcfd.supabase.co"
SUPABASE_KEY = "TU_ANON_KEY_AQUI"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Citas Médicas", page_icon="🩺")
st.title("🩺 Reserva de Citas")
st.subheader("Salud Ocupacional")

clave = st.text_input("Clave de Empleado:")
fecha_sel = st.date_input("Selecciona la fecha:")

try:
    # Consulta de horarios
    respuesta = supabase.table("horarios_disponibles")\
        .select("hora")\
        .eq("fecha", str(fecha_sel))\
        .eq("disponible", True)\
        .execute()

    horas_libres = [item["hora"] for item in respuesta.data] if respuesta.data else []

    if not horas_libres:
        st.warning("⚠️ No hay horarios disponibles para esta fecha. Selecciona otro día.")
    else:
        hora_sel = st.selectbox("Horarios Disponibles:", horas_libres)
        motivo = st.selectbox("Motivo de consulta:", [
            "Examen Periódico", 
            "Consulta General", 
            "Evaluación Ergonómica", 
            "Valoración de Egreso"
        ])
        
        if st.button("Confirmar Cita"):
            if not clave.strip():
                st.error("Por favor ingresa tu clave de empleado.")
            else:
                nueva_cita = {
                    "clave": clave,
                    "fecha": str(fecha_sel),
                    "hora": hora_sel,
                    "motivo": motivo,
                    "estado": "Pendiente"
                }
                supabase.table("citas").insert(nueva_cita).execute()
                
                supabase.table("horarios_disponibles")\
                    .update({"disponible": False})\
                    .eq("fecha", str(fecha_sel))\
                    .eq("hora", hora_sel)\
                    .execute()
                    
                st.success("¡Cita agendada con éxito!")
                st.rerun()

except Exception as e:
    st.error(f"❌ Diagnóstico del error: {e}")
