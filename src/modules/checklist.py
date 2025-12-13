import streamlit as st
from datetime import datetime
from uuid import uuid4


class ChecklistView:
    @staticmethod
    def _init_state():
        if "checklist_new_topic_name" not in st.session_state:
            st.session_state.checklist_new_topic_name = ""
        if "checklist_error" not in st.session_state:
            st.session_state.checklist_error = ""
        if "checklist_rename_topic_id" not in st.session_state:
            st.session_state.checklist_rename_topic_id = None
        if "checklist_rename_topic_text" not in st.session_state:
            st.session_state.checklist_rename_topic_text = ""

    @staticmethod
    def _require_db():
        if not st.session_state.get("db_connected", False):
            st.warning("Para usar o check-list com persistência, configure DATABASE_URL (Postgres/Neon) no Streamlit Cloud.")
            st.stop()
        if "db_manager" not in st.session_state:
            st.warning("DB manager não inicializado.")
            st.stop()
        return st.session_state.db_manager

    @staticmethod
    def _add_topic():
        pm = ChecklistView._require_db()
        name = (st.session_state.get("checklist_new_topic_name") or "").strip()
        if not name:
            st.session_state.checklist_error = "Digite o nome do tópico."
            return
        topic_id = f"ct_{uuid4().hex}"
        ok = pm.create_checklist_topic(topic_id, name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        if not ok:
            st.session_state.checklist_error = "Não foi possível criar o tópico."
            return
        st.session_state.checklist_new_topic_name = ""
        st.session_state.checklist_error = ""

    @staticmethod
    def _start_rename_topic(topic_id: str, current_name: str):
        st.session_state.checklist_rename_topic_id = topic_id
        st.session_state.checklist_rename_topic_text = current_name

    @staticmethod
    def _cancel_rename_topic():
        st.session_state.checklist_rename_topic_id = None
        st.session_state.checklist_rename_topic_text = ""

    @staticmethod
    def _save_rename_topic():
        pm = ChecklistView._require_db()
        topic_id = st.session_state.get("checklist_rename_topic_id")
        new_name = (st.session_state.get("checklist_rename_topic_text") or "").strip()
        if not topic_id:
            return
        if not new_name:
            st.session_state.checklist_error = "Digite o novo nome do tópico."
            return
        ok = pm.rename_checklist_topic(topic_id, new_name)
        if not ok:
            st.session_state.checklist_error = "Não foi possível renomear o tópico."
            return
        st.session_state.checklist_error = ""
        ChecklistView._cancel_rename_topic()

    @staticmethod
    def _add_task(topic_id: str, input_key: str):
        pm = ChecklistView._require_db()
        text = (st.session_state.get(input_key) or "").strip()
        if not text:
            st.session_state.checklist_error = "Digite a tarefa do tópico."
            return
        task_id = f"ctk_{uuid4().hex}"
        ok = pm.create_checklist_task(task_id, topic_id, text, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        if not ok:
            st.session_state.checklist_error = "Não foi possível criar a tarefa."
            return
        st.session_state[input_key] = ""
        st.session_state.checklist_error = ""

    @staticmethod
    def _toggle_task_done(task_id: str, checkbox_key: str):
        pm = ChecklistView._require_db()
        done = bool(st.session_state.get(checkbox_key))
        pm.set_checklist_task_done(task_id, done)

    @staticmethod
    def _delete_task(task_id: str):
        pm = ChecklistView._require_db()
        pm.delete_checklist_task(task_id)

    @staticmethod
    def render():
        """Checklist por Tópico -> Tarefas, persistido no Postgres (Neon)."""
        ChecklistView._init_state()

        pm = ChecklistView._require_db()

        st.subheader("✅ Check-list")

        st.caption("Tópicos e tarefas são salvos no PostgreSQL (Neon).")

        if st.session_state.get("checklist_error"):
            st.warning(st.session_state.checklist_error)

        col1, col2 = st.columns([4, 1])
        with col1:
            st.text_input("Tópico", key="checklist_new_topic_name")
        with col2:
            st.button("Adicionar", key="checklist_add_topic", on_click=ChecklistView._add_topic)

        st.markdown("---")

        topics = pm.load_checklist_topics()
        if not topics:
            st.info("Nenhum tópico cadastrado ainda.")
            return

        for topic in topics:
            topic_id = topic["id"]
            topic_name = topic.get("nome", "")

            header_cols = st.columns([0.72, 0.28])
            with header_cols[0]:
                st.markdown(f"**Tópico:** {topic_name}")
            with header_cols[1]:
                if st.session_state.get("checklist_rename_topic_id") == topic_id:
                    st.button("Cancelar", key=f"ct_cancel_{topic_id}", on_click=ChecklistView._cancel_rename_topic)
                else:
                    st.button(
                        "Renomear",
                        key=f"ct_rename_{topic_id}",
                        on_click=ChecklistView._start_rename_topic,
                        args=(topic_id, topic_name),
                    )

            if st.session_state.get("checklist_rename_topic_id") == topic_id:
                rename_cols = st.columns([0.75, 0.25])
                with rename_cols[0]:
                    st.text_input("Novo nome", key="checklist_rename_topic_text")
                with rename_cols[1]:
                    st.button("Salvar", key=f"ct_save_{topic_id}", on_click=ChecklistView._save_rename_topic)

            # Adicionar tarefa ao tópico
            task_input_key = f"checklist_new_task_{topic_id}"
            if task_input_key not in st.session_state:
                st.session_state[task_input_key] = ""

            add_cols = st.columns([0.8, 0.2])
            with add_cols[0]:
                st.text_input("Tarefa", key=task_input_key)
            with add_cols[1]:
                st.button(
                    "Adicionar",
                    key=f"ct_add_task_{topic_id}",
                    on_click=ChecklistView._add_task,
                    args=(topic_id, task_input_key),
                )

            tasks = pm.load_checklist_tasks(topic_id)
            if not tasks:
                st.info("- Nenhuma tarefa neste tópico.")
                st.markdown("---")
                continue

            for task in tasks:
                task_id = task["id"]
                task_text = task.get("texto", "")
                done = bool(task.get("concluida"))

                row = st.columns([0.78, 0.22])
                checkbox_key = f"ctk_done_{task_id}"

                with row[0]:
                    st.checkbox(
                        task_text,
                        key=checkbox_key,
                        value=done,
                        on_change=ChecklistView._toggle_task_done,
                        args=(task_id, checkbox_key),
                    )

                with row[1]:
                    current_done = bool(st.session_state.get(checkbox_key, done))
                    if current_done:
                        st.button(
                            "Deletar do banco",
                            key=f"ctk_delete_{task_id}",
                            on_click=ChecklistView._delete_task,
                            args=(task_id,),
                        )

            st.markdown("---")
