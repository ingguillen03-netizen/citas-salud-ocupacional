import streamlit as st
from supabase import create_client
from datetime import datetime, date

SUPABASE_URL = "https://efqckksjhldyxmokmcfd.supabase.co"
# ⚠️ REEMPLAZA ESTA CLAVE CON TU SUPABASE ANON KEY ⚠️
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVmcWNra3NqaGxkeXhtb2ttY2ZkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg5MzM0NjYsImV4cCI6MjEwNDUwOTQ2Nn0._q0FRMevxqLmAiYUb9wBzDLIzyqXQblhuIhn6FCXvxU"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Salud Ocupacional & Telemedicina", page_icon="🩺", layout="centered")

st.title("🩺 Portal de Salud Ocupacional & Telemedicina")
st.caption("Atención Médica en Planta y Cobertura a Sucursales / Regiones")

tab1, tab2 = st.tabs(["📅 Agendar Cita", "🔍 Consultar Mis Citas"])

# -------------------------------------------------------------
# PESTAÑA 1: AGENDAR CITA
# -------------------------------------------------------------
with tab1:
    st.subheader("Reserva de Consulta Médica")
    
    col_nom, col_clav = st.columns([2, 1])
    with col_nom:
        nombre = st.text_input("Nombre Completo del Trabajador:*", placeholder="Ej. Juan Carlos Pérez López")
    with col_clav:
        clave = st.text_input("Clave / ID Empleado (opcional):", placeholder="Ej. EMP-1024")
    
    col_mod, col_suc = st.columns([1, 1])
    with col_mod:
        modalidad = st.selectbox(
            "Modalidad de Atención:*",
            ["Presencial (Planta Principal)", "A Distancia / Telemedicina (Sucursales/Regiones)"]
        )
    with col_suc:
        sucursal = st.text_input("Sucursal / Región / Área:*", placeholder="Ej. Planta Central, Sucursal Norte...")

    fecha_sel = st.date_input("Selecciona la fecha para tu cita:", min_value=date.today())

    try:
        # Obtener horarios libres en Supabase
        respuesta = supabase.table("horarios_disponibles")\
            .select("hora")\
            .eq("fecha", str(fecha_sel))\
            .eq("disponible", True)\
            .execute()

        horas_libres = sorted([item["hora"] for item in respuesta.data]) if respuesta.data else []

        if not horas_libres:
            st.warning("⚠️ No hay horarios disponibles habilitados para esta fecha. Intenta seleccionando otro día.")
        else:
            hora_sel = st.selectbox("Horarios Disponibles:", horas_libres)
            
            st.divider()
            
            tipo_atencion = st.radio(
                "Selecciona el Tipo / Origen de la Atención Médica:",
                [
                    "Enfermedad General (Consulta Aguda)",
                    "Riesgo de Trabajo (Seguimiento de Accidente / Trámites ST)",
                    "Control de Maternidad / Prenatal",
                    "Control Crónico-Degenerativo (Diabetes, Hipertensión, Obesidad)"
                ]
            )

            col1, col2 = st.columns(2)
            with col1:
                tiempo_sintomas = st.selectbox("Tiempo con síntoma:", ["Hoy empezó", "1 a 3 días", "Más de una semana", "N/A - Seguimiento"])
            with col2:
                urgencia = st.select_slider("Nivel de malestar:", options=["Bajo", "Leve", "Moderado", "Alto"])

            observaciones = st.text_area("Notas / Sintomatología adicional (opcional):", placeholder="Ej. Solicitud de valoración a distancia por malestar articular...")

            if "Telemedicina" in modalidad:
                st.info("ℹ️ **Atención Virtual:** Al confirmarse tu cita, se generará un enlace de videollamada (Google Meet / Zoom) que podrás ver en la pestaña 'Consultar Mis Citas'.")

            if st.button("Confirmar Solicitud de Cita", type="primary", use_container_width=True):
                if not nombre.strip():
                    st.error("Por favor ingresa tu Nombre Completo para poder agendar.")
                else:
                    nueva_cita = {
                        "nombre": nombre,
                        "clave": clave if clave.strip() else "S/N",
                        "modalidad": modalidad,
                        "sucursal": sucursal if sucursal.strip() else "Planta Principal",
                        "fecha": str(fecha_sel),
                        "hora": hora_sel,
                        "motivo": tipo_atencion,
                        "es_laboral": tipo_atencion,
                        "tiempo_sintomas": tiempo_sintomas,
                        "urgencia": urgencia,
                        "observaciones": observaciones,
                        "estado": "Pendiente",
                        "link_reunion": ""
                    }
                    
                    # 1. Insertar la cita
                    supabase.table("citas").insert(nueva_cita).execute()
                    
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
                        * **Empleado:** {nombre} `({clave if clave.strip() else 'Sin N°'})`
                        * **Ubicación / Modalidad:** {modalidad} | *{sucursal}*
                        * **Fecha solicitada:** {fecha_sel} a las {hora_sel} hrs.
                        * **Tipo de atención:** {tipo_atencion}
                        * **Estado actual:** 🟡 *Pendiente de aprobación por el área médica*
                        
                        *Guarda tu nombre o clave para consultar el estatus o enlace de videollamada en la pestaña 'Consultar Mis Citas'.*
                        """)

    except Exception as e:
        st.error(f"Error de conexión: {e}")

# -------------------------------------------------------------
# PESTAÑA 2: CONSULTAR Y REAGENDAR CITAS
# -------------------------------------------------------------
with tab2:
    st.subheader("Consultar Estatus de Solicitudes y Enlaces Virtuales")
    busqueda = st.text_input("Ingresa tu Nombre Completo o Clave de Empleado para consultar:", key="buscar_empleado")
    
    if st.button("Buscar Citas", use_container_width=True):
        if not busqueda.strip():
            st.warning("Por favor escribe tu nombre o clave para buscar.")
        else:
            try:
                # Búsqueda flexible por nombre o clave
                res = supabase.table("citas")\
                    .select("*")\
                    .or_(f"clave.ilike.%{busqueda}%,nombre.ilike.%{busqueda}%")\
                    .order("id", desc=True)\
                    .execute()
                
                citas_user = res.data
                
                if not citas_user:
                    st.info("No se encontraron citas asociadas a esa búsqueda.")
                else:
                    ahora = datetime.now()
                    
                    for cita in citas_user:
                        nom_disp = cita.get('nombre') or 'Empleado'
                        with st.expander(f"Cita #{cita['id']} - {nom_disp} | {cita['fecha']} ({cita['hora']})", expanded=True):
                            
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
                            st.write(f"**Empleado:** {nom_disp} (Clave: `{cita.get('clave', 'S/N')}`)")
                            st.write(f"**Modalidad / Ubicación:** {cita.get('modalidad', 'Presencial')} | *{cita.get('sucursal', 'N/A')}*")
                            st.write(f"**Tipo de Atención:** {cita.get('es_laboral', cita.get('motivo'))}")
                            
                            if cita.get('observaciones'):
                                st.caption(f"Notas: {cita['observaciones']}")

                            # Si la cita es Virtual / Telemedicina y ya tiene link asignado por el médico
                            link_meet = cita.get('link_reunion')
                            if link_meet and link_meet.strip():
                                st.success("📹 **Enlace de Videollamada Disponible:**")
                                st.link_button("💻 Entrar a la Cita Virtual (Google Meet / Zoom)", link_meet)
                            elif "Telemedicina" in str(cita.get('modalidad')) and cita['estado'] == 'Confirmada':
                                st.info("ℹ️ Cita confirmada. El enlace de videollamada será publicado por el médico momentos antes de la consulta.")

                            # Si venció la cita, opción de reagendar
                            if vencida:
                                st.warning("⚠️ Esta cita no fue procesada a tiempo antes del horario solicitado.")
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
                                        supabase.table("citas").update({
                                            "fecha": str(nueva_fecha),
                                            "hora": nueva_hora,
                                            "estado": "Pendiente"
                                        }).eq("id", cita['id']).execute()
                                        
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
