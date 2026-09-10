import streamlit as st
from supabase import create_client
from datetime import datetime, date

SUPABASE_URL = "https://efqckksjhldyxmokmcfd.supabase.co"
SUPABASE_KEY = "TU_ANON_KEY_AQUI"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Salud Ocupacional - Citas", page_icon="🩺", layout="centered")

st.title("🩺 Portal de Salud Ocupacional")
st.caption("Atención Médica y Vigilancia de la Salud")

tab1, tab2 = st.tabs(["📅 Agendar Cita", "🔍 Consultar Mis Citas"])

# -------------------------------------------------------------
# PESTAÑA 1: AGENDAR CITA
# -------------------------------------------------------------
with tab1:
    st.subheader("Reserva de Consulta Médica")
    
    clave = st.text_input("Clave de Empleado:", placeholder="Ej. EMP-1024")
    fecha_sel = st.date_input("Selecciona la fecha:", min_value=date.today())

    try:
        # Obtener horarios libres en Supabase
        respuesta = supabase.table("horarios_disponibles")\
            .select("hora")\
            .eq("fecha", str(fecha_sel))\
            .eq("disponible", True)\
            .execute()

        horas_libres = sorted([item["hora"] for item in respuesta.data]) if respuesta.data else []

        if not horas_libres:
            st.warning("⚠️ No hay horarios disponibles para esta fecha. Intenta seleccionando otro día.")
        else:
            hora_sel = st.selectbox("Horarios Disponibles:", horas_libres)
            
            st.divider()
            motivo = st.selectbox("Motivo principal:", [
                "Consulta General / Malestar",
                "Examen Médico Periódico",
                "Evaluación Ergonómica",
                "Valoración por Incapacidad",
                "Examen de Ingreso / Egreso"
            ])

            es_laboral = st.radio(
                "¿Relacionado con trabajo o accidente laboral?",
                ["No / Enfermedad común", "Sí / Trabajo en planta", "Incidente de trayecto"]
            )

            col1, col2 = st.columns(2)
            with col1:
                tiempo_sintomas = st.selectbox("Tiempo con síntoma:", ["Hoy empezó", "1 a 3 días", "Más de una semana", "N/A"])
            with col2:
                urgencia = st.select_slider("Nivel de malestar:", options=["Bajo", "Leve", "Moderado", "Alto"])

            observaciones = st.text_area("Notas / Sintomatología adicional (opcional):", placeholder="Ej. Dolor articular al realizar cargas...")

            if st.button("Confirmar Solicitud de Cita", type="primary", use_container_width=True):
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
                    
                    # 1. Insertar la cita
                    res_ins = supabase.table("citas").insert(nueva_cita).execute()
                    
                    # 2. Bloquear horario
                    supabase.table("horarios_disponibles")\
                        .update({"disponible": False})\
                        .eq("fecha", str(fecha_sel))\
                        .eq("hora", hora_sel)\
                        .execute()
                    
                    st.balloons()
                    st.success("✅ ¡Solicitud registrada exitosamente!")
                    
                    # Mostrar Tarjeta / Ticket de Confirmación
                    with st.container():
                        st.info(f"""
                        ### 📄 Resumen de Solicitud
                        * **Empleado:** `{clave}`
                        * **Fecha solicitada:** {fecha_sel} a las {hora_sel} hrs.
                        * **Motivo:** {motivo}
                        * **Estado actual:** 🟡 *Pendiente de aprobación por el área médica*
                        
                        *Puedes revisar la evolución de tu solicitud en la pestaña 'Consultar Mis Citas'.*
                        """)

    except Exception as e:
        st.error(f"Error de conexión: {e}")

# -------------------------------------------------------------
# PESTAÑA 2: CONSULTAR Y REAGENDAR CITAS
# -------------------------------------------------------------
with tab2:
    st.subheader("Consultar Estatus de Solicitudes")
    clave_busqueda = st.text_input("Ingresa tu Clave de Empleado para consultar:", key="buscar_clave")
    
    if st.button("Buscar Citas", use_container_width=True):
        if not clave_busqueda.strip():
            st.warning("Por favor escribe tu clave para buscar.")
        else:
            try:
                citas_user = supabase.table("citas")\
                    .select("*")\
                    .eq("clave", clave_busqueda)\
                    .order("id", desc=True)\
                    .execute().data
                
                if not citas_user:
                    st.info("No se encontraron citas asociadas a esta clave.")
                else:
                    ahora = datetime.now()
                    
                    for cita in citas_user:
                        with st.expander(f"Cita #{cita['id']} - {cita['fecha']} ({cita['hora']})", expanded=True):
                            
                            # Determinar si la cita ya venció
                            dt_cita = datetime.strptime(f"{cita['fecha']} {cita['hora']}", "%Y-%m-%d %H:%M:%S")
                            vencida = (dt_cita < ahora) and (cita['estado'] == 'Pendiente')
                            
                            if vencida:
                                estado_fmt = "⌛ VENCIDA / NO ATENDIDA A TIEMPO"
                            elif cita['estado'] == 'Pendiente':
                                estado_fmt = "🟡 PENDIENTE DE APROBACIÓN"
                            elif cita['estado'] == 'Confirmada':
                                estado_fmt = "🟢 CONFIRMADA Y PROGRAMADA"
                            else:
                                estado_fmt = f"🔴 {cita['estado'].upper()}"

                            st.markdown(f"**Estatus:** {estado_fmt}")
                            st.write(f"**Motivo:** {cita['motivo']} | **Relación laboral:** {cita['es_laboral']}")
                            if cita.get('observaciones'):
                                st.caption(f"Notas: {cita['observaciones']}")

                            # Si venció o requiere reagendar
                            if vencida:
                                st.warning("⚠️ Esta cita no fue procesada a tiempo por el equipo médico antes del horario solicitado.")
                                st.subheader("🔄 Reagendar Cita")
                                nueva_fecha = st.date_input("Nueva fecha:", key=f"f_{cita['id']}", min_value=date.today())
                                
                                res_h = supabase.table("horarios_disponibles")\
                                    .select("hora")\
                                    .eq("fecha", str(nueva_fecha))\
                                    .eq("disponible", True)\
                                    .execute()
                                
                                nuevas_horas = sorted([h["hora"] for h in res_h.data]) if res_h.data else []
                                
                                if nuevas_horas:
                                    nueva_hora = st.selectbox("Selecciona un nuevo horario libre:", nuevas_horas, key=f"h_{cita['id']}")
                                    if st.button("Confirmar Reagendamiento", key=f"btn_reag_{cita['id']}"):
                                        # Actualizar fecha y hora en la cita
                                        supabase.table("citas").update({
                                            "fecha": str(nueva_fecha),
                                            "hora": nueva_hora,
                                            "estado": "Pendiente"
                                        }).eq("id", cita['id']).execute()
                                        
                                        # Bloquear la nueva hora
                                        supabase.table("horarios_disponibles").update({"disponible": False})\
                                            .eq("fecha", str(nueva_fecha))\
                                            .eq("hora", nueva_hora)\
                                            .execute()
                                        
                                        st.success("¡Cita reagendada correctamente!")
                                        st.rerun()
                                else:
                                    st.info("Sin horarios disponibles para esa nueva fecha.")

            except Exception as e:
                st.error(f"Error al consultar: {e}")
