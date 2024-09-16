import streamlit as st
import pandas as pd
import gdown
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import plotly.graph_objects as go
import openai
import requests
import os
import sys
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import altair as alt
import json
import vegafusion
from PIL import Image

load_dotenv()

st.set_page_config(layout="wide")

# Define the relative file paths
relative_file_path = 'backend/data/unique_document_ids.csv'
grouped_file_path = 'backend/data/grouped_data.csv'

# Load the CSV file to get the sales data
def load_sales_data():
    # Existing code to load sales data
    pass

def display_chart_image():
    # Existing code to display an image
    pass

# Initialize session state
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

# Load the sales data
df_sales = load_sales_data()

def load_grouped_data():
    # Existing code to load grouped data
    pass

grouped_df = load_grouped_data()

state = st.session_state

def init_state(key, value):
    if key not in state:
        state[key] = value

# Callback functions and login logic
# ...

def main():
    if not state.logged_in:
        login_page()
    else:
        # Current Client ID
        current_id = state.username
        openai.api_key = os.getenv("OPENAI_API_KEY")
    
        # Initialize global variables if not present
        if 'inbound_total' not in st.session_state:
            st.session_state.inbound_total = 0
        if 'outbound_total' not in st.session_state:
            st.session_state.outbound_total = 0
        if 'number_of_sales' not in st.session_state:
            st.session_state.number_of_sales = 0
        if 'df' not in st.session_state:
            st.session_state.df = None
        
        st.markdown("<h1 style='text-align: center; color: black;'>Painel de Negócios</h1>", unsafe_allow_html=True)
        
        st.markdown(
            """
            <style>
            .stApp {
                background-color: #f0f2f6;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        
        with st.sidebar:
            st.title('📅 Selecione o intervalo de tempo')
        
            start_date = st.date_input(
                'Data de início',
                min_value=datetime(2022, 12, 1),
                max_value=datetime(2023, 5, 31),
                value=datetime(2022, 12, 1)
            )
        
            end_date = st.date_input(
                'Data de término',
                min_value=start_date,
                max_value=datetime(2023, 5, 31),
                value=datetime(2023, 5, 31)
            )
            color_themes = {
                "Original": {"primary": "#4CAF50", "secondary": "green", "background": "#f0f2f6", "text": "black"},
                "Crocodilo": {"primary": "#588157", "secondary": "#a3b18a", "background": "#dad7cd", "text": "#344e41"},
                "Oceano": {"primary": "#48cae4", "secondary": "#00b4d8", "background": "#caf0f8", "text": "#03045e"},
                "Pôr do sol": {"primary": "#ffb703", "secondary": "#fb8500", "background": "#f7d8b2", "text": "#370617"},
            }
            selected_theme = st.selectbox(
                "Selecione o tema de cores",
                options=list(color_themes.keys()),
                index=0
            )
        
        # Loading data function
        @st.cache_data
        def load_data():
            # Existing code to load data
            pass
        
        if not st.session_state.data_loaded:
            st.session_state.df = load_data()
            st.session_state.data_loaded = True
        
        if 'data_loaded' not in st.session_state:
            st.session_state.data_loaded = False
        
        # Define your plotting functions (pieCharts, total_sales_chart, etc.)
        # ...

        # Apply the selected theme
        apply_theme(selected_theme)
        
        # First Row of Data
        colHeader = st.columns(4, gap='small')
        
        if st.session_state.data_loaded:
            # Existing code to calculate metrics
            # ...

            # Display metrics
            for idx, metric in enumerate([
                ('Renda', st.session_state.inbound_total, 'green'),
                ('Despesas', st.session_state.outbound_total, 'red'),
                ('Total Líquido', st.session_state.inbound_total - st.session_state.outbound_total, 'green' if st.session_state.inbound_total >= st.session_state.outbound_total else 'red'),
                ('Número de Vendas', st.session_state.number_of_sales, 'green')
            ]):
                with colHeader[idx]:
                    st.markdown(
                        f"""
                        <div style="border: 2px solid white; padding: 20px; text-align: left; border-radius: 5px;">
                            <p style="color: black; font-size: 16px; margin-bottom: 4px;">{metric[0]}</p>
                            <p style="color: {metric[2]}; font-size: 32px; font-weight: bold;">${metric[1]:,.2f}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            # Use tabs instead of columns for charts
            tab1, tab2 = st.tabs(["Resumo", "Tendências Bancárias"])
            with tab1:
                pieCharts()
                top_industries()
            with tab2:
                bank_trends_chart()
                total_sales_chart()
        
        # AI Analysis Section
        st.markdown("""<h3 style='color: black;'>Insira um Prompt Para Análise de IA:</h3>""", unsafe_allow_html=True)
        prompt = st.text_area(label="")
        if st.button("Execute a Análise de IA"):
            promptrun(prompt)
        
        if st.button("Sair", on_click=_reset_login_cb):
            st.success("Você saiu com sucesso.")

if __name__ == "__main__":
    main()