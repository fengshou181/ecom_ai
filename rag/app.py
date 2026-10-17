# -*- coding: utf-8 -*-
"""电商数据 RAG 问答 - Streamlit 聊天界面"""
import streamlit as st
from sql_chain import ask

st.set_page_config(page_title="电商数据智能问答", page_icon="🛒", layout="wide")
st.title("🛒 电商数据智能问答")
st.caption("基于 Ollama qwen2.5 + Chroma + Apache Doris 的本地 Text-to-SQL RAG")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sql"):
            with st.expander("查看生成的 SQL"):
                st.code(msg["sql"], language="sql")
        if msg.get("df") is not None and len(msg["df"]):
            st.dataframe(msg["df"], use_container_width=True)

if question := st.chat_input("例如: olist 每月 GMV 趋势 / 淘宝 PV 到购买转化率"):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("思考中（本地模型生成可能需要 10-60 秒）..."):
            r = ask(question)
        if r["error"]:
            st.error(r["error"])
            st.session_state.messages.append({"role": "assistant", "content": f"出错了: {r['error']}"})
        else:
            st.markdown(r["answer"])
            with st.expander("查看生成的 SQL"):
                st.code(r["sql"], language="sql")
            if r["dataframe"] is not None and len(r["dataframe"]):
                st.dataframe(r["dataframe"], use_container_width=True)
            st.session_state.messages.append(
                {"role": "assistant", "content": r["answer"], "sql": r["sql"], "df": r["dataframe"]}
            )
