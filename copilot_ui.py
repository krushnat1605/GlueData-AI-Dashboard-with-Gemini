import streamlit as st


def render_copilot_ui(router):
    st.subheader("🤖 AWS Glue AI Copilot Chatbot")

    if router.df is not None and not router.df.empty:
        try:
            router.con.register("glue_jobs", router.df)
        except Exception:
            pass
    user_query = st.chat_input("Ask any question about your job logs")

    if user_query:
        st.chat_message("user").write(user_query)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing dataset will give you answer shortly"):
                response = router.answer(user_query)

            st.markdown("### 💡 AI Insights")
            st.info(response["user_msg"])

            st.markdown("### 📊 Metrics & Data Results for your query ")
            st.dataframe(response["df"], use_container_width=True)

            if response.get("sql"):
                with st.expander("🛠 Inspect Executed SQL"):
                    st.code(response["sql"], language="sql")