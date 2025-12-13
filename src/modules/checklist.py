import streamlit as st
from uuid import uuid4


class ChecklistView:
    @staticmethod
    def _init_state():
        if "checklist_items" not in st.session_state:
            st.session_state.checklist_items = []

    @staticmethod
    def render():
        """Checklist simples em memória (session_state), sem persistência."""
        ChecklistView._init_state()

        st.subheader("✅ Check-list")

        col1, col2 = st.columns([4, 1])
        with col1:
            topic = st.text_input("Nome do tópico", key="checklist_new_topic")
        with col2:
            if st.button("Adicionar", key="checklist_add"):
                text = (topic or "").strip()
                if not text:
                    st.warning("Digite o nome do tópico.")
                else:
                    st.session_state.checklist_items.append(
                        {"id": uuid4().hex, "text": text, "done": False}
                    )
                    st.session_state.checklist_new_topic = ""
                    st.rerun()

        st.markdown("---")

        items = st.session_state.checklist_items
        if not items:
            st.info("Nenhum tópico no check-list ainda.")
            return

        for item in list(items):
            item_id = item["id"]
            cols = st.columns([0.12, 0.68, 0.20])

            with cols[0]:
                done = st.checkbox("", value=bool(item.get("done")), key=f"check_{item_id}")
                item["done"] = done

            with cols[1]:
                label = item.get("text", "")
                if item.get("done"):
                    st.markdown(f"~~{label}~~")
                else:
                    st.write(label)

            with cols[2]:
                if item.get("done"):
                    if st.button("Excluir", key=f"check_delete_{item_id}"):
                        st.session_state.checklist_items = [
                            x for x in st.session_state.checklist_items if x.get("id") != item_id
                        ]
                        st.rerun()
