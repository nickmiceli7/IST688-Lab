import streamlit as st

lab1 = st.Page('Lab/Lab1.py', title='Lab1')
lab2 = st.Page('Lab/Lab2.py', title='Lab2')
lab3 = st.Page('Lab/Lab3.py', title='Lab3')
lab4 = st.Page('Lab/Lab4.py', title='Lab4')
lab5 = st.Page('Lab/Lab5.py', title='Lab5', default=True)

pg = st.navigation([lab1, lab2, lab3, lab4, lab5])
pg.run()