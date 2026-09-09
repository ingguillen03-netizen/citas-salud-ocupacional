import streamlit as st
from supabase import create_client

SUPABASE_URL = "https://efqckksjhldyxmokmcfd.supabase.co"
SUPABASE_KEY = "TU_ANON_KEY_AQUI"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Salud Ocupacional - Citas", page_icon="🩺")
st.title("🩺 Reserva de Cita Médica")
st.caption("Módulo de Atención a Trabajadores")

clave = st.text_input("Clave de Empleado:", placeholder="Ej. EMP-1024")
fecha_sel = st.date_input("Selecciona la fecha:")

try:
    # Buscar horarios libres habilitados por el médico
    respuesta = supabase.table("horarios_disponibles")\
        .select("hora")\
        .eq("fecha", str(fecha_sel))\
        .eq("disponible", True)\
        .execute()

    horas_libres = [item["hora"] for item in respuesta.data] if respuesta.data else []

    if not horas_libres:
        st.warning("⚠️ No hay horarios disponibles habilitados para esta fecha.")
    else:
        hora_sel = st.selectbox("Horario disponible:", horas_libres)
        
        st.divider()
        st.subheader("Datos de la Consulta")
        
        motivo = st.selectbox("Motivo principal:", [
            "Consulta General / Malestar",
            "Examen Médico Periódico",
            "Evaluación de Ergonómica",
            "Valoración por Incapacidad",
            "Examen de Ingreso / Egreso"
        ])

        es_laboral = st.radio(
            "¿La molestia está relacionada con tu trabajo o un accidente laboral?",
            ["No / Enfermedad común", "Sí / Trabajo en planta", "Incidente de trayecto"]
        )

        col1, col2 = st.columns(2)
        with col1:
            tiempo_sintomas = st.selectbox("Tiempo con el síntoma:", ["Hoy empezó", "1 a 3 días", "Más de una semana", "N/A"])
        with col2:
            urgencia = st.select_slider("Nivel de malestar:", options=["Bajo", "Leve", "Moderado", "Alto"])

        observaciones = st.text_area("Describe brevemente tu molestia o motivo (opcional):", placeholder="Ej. Dolor lumbar al levantar carga...")

        if st.button("Agendar Cita", type="primary"):
            if not clave.strip():
                st.error("Por favor ingresa tu clave de empleado.")
            else:
                nueva_cita = {
                    "clave": clave,
                    "fecha": str(fecha_sel),
                    "hora": hora_sel,
                    "motivo": motivo,
                    "es_laboral": es_laboral,
                    "tiempo_sintomas": tiempo_sintomas,
                    "urgencia": urgencia,
                    "observaciones": observaciones,
                    "estado": "Pendiente"
                }
                
                # 1. Registrar cita
                supabase.table("citas").insert(nueva_cita).execute()
                
                # 2. Bloquear horario reservado
                supabase.table("horarios_disponibles")\
                    .update({"disponible": False})\
                    .eq("fecha", str(fecha_sel))\
                    .eq("hora", hora_sel)\
                    .execute()
                    
                st.success("¡Cita agendada exitosamente!")
                st.rerun()

except Exception as e:
    st.error(f"Error de conexión: {e}")
