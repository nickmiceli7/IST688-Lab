import streamlit as st

lab1 = st.Page('Lab1.py', title='Lab1')
lab2 = st.Page('Lab2.py', title='Lab2')

pg = st.navigation([lab1, lab2])
pg.run()