import streamlit as st
import pandas as pd
import gdown
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
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
    # Convert the relative file path to an absolute path based on the current working directory
    file_path = os.path.join(os.getcwd(), relative_file_path)
    
    # Check if the file exists
    if os.path.exists(file_path):
        try:
            # Attempt to read the CSV file
            df = pd.read_csv(file_path)
            return df
        except Exception as e:
            st.error(f"Error reading the file: {e}")
            return pd.DataFrame()  # Return an empty DataFrame if the file cannot be read
    else:
        st.error(f"File not found: {file_path}")
        return pd.DataFrame()  # Return an empty DataFrame if the file does not exist

def display_chart_image():
    image_path = os.path.join('backend', 'data', 'chart.png')
    
    try:
        # Open and display the image using PIL
        image = Image.open(image_path)
        st.image(image, caption="Quem Atendemos", width=None)
    except FileNotFoundError:
        st.error(f"File not found: {image_path}")

# Initialize session state
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

# Load the sales data
df_sales = load_sales_data()

def load_grouped_data():
    # Convert the relative file path to an absolute path based on the current working directory
    file_path = os.path.join(os.getcwd(), grouped_file_path)
    
    # Check if the file exists
    if os.path.exists(file_path):
        try:
            # Attempt to read the CSV file
            df = pd.read_csv(file_path)
            return df
        except Exception as e:
            st.error(f"Error reading the file: {e}")
            return pd.DataFrame()  # Return an empty DataFrame if the file cannot be read
    else:
        st.error(f"File not found: {file_path}")
        return pd.DataFrame()  # Return an empty DataFrame if the file does not exist

grouped_df = load_grouped_data()

state = st.session_state

def init_state(key, value):
    if key not in state:
        state[key] = value

# Generic callback to set state
def _set_state_cb(**kwargs):
    for state_key, widget_key in kwargs.items():
        val = state.get(widget_key, None)
        if val is not None or val == "":
            setattr(state, state_key, state[widget_key])

def _set_login_cb(username, password):
    state.logged_in = login(username, password)
    if state.logged_in:
        state.username = username

def _reset_login_cb():
    state.logged_in = False
    state.username = ""
    state.password = "" 

init_state('logged_in', False)
init_state('username', '')
init_state('password', '')

# -----------------------------------------------------------------------------

# Function to check login credentials
def login(username, password):
    return username in df_sales['document_id'].astype(str).unique() and password == "stoneco"

# Define the login page
def login_page():
    st.markdown("<h1 style='text-align: center;'>Página de Login</h1>", unsafe_allow_html=True)
    if not state.logged_in:
        # Display login form
        st.text_input(
            "Nome de usuário (ID do Documento)", value=state.username, key='username_input',
            on_change=_set_state_cb, kwargs={'username': 'username_input'}
        )
        st.text_input(
            "Senha", type="password", value=state.password, key='password_input',
            on_change=_set_state_cb, kwargs={'password': 'password_input'}
        )
        
        if st.button("O Login", on_click=_set_login_cb, args=(state.username, state.password)):
            if not state.logged_in:
                st.warning("Nome de usuário ou senha incorretos.")
        
        display_chart_image()

    else:
        st.write(f"Bem-vindo, {state.username}!")
        if st.button("Sair", on_click=_reset_login_cb):
            st.success("Você saiu com sucesso.")

# Main function
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
            /* Make tabs text black */
            div[data-testid="stHorizontalBlock"] button div[data-testid='stMarkdownContainer'] p {
                color: black !important;
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
            data = {
                'bank': "1dzL_SWBkBs5xrUxuGQTm04oe3USgkL9u",
                'sales': "1QK-VgSU3AxXUw330KjYFUj8S9hzKJsG6",
                'mcc': "1JN0bR84sgZ_o4wjKPBUmz45NeEEkVgt7",
            }
        
            df = {}
            for name, file_id in data.items():
                gdown.download(f'https://drive.google.com/uc?id={file_id}', name + '.parquet', quiet=False)
                df[name] = pd.read_parquet(name + '.parquet')
        
            # Preprocess the sales data
            df['sales']['date_time'] = pd.to_datetime(df['sales']['date_time'])  # Convert to datetime
            df['sales']['day_of_week'] = df['sales']['date_time'].dt.day_name()  # Extract day of the week
            df['sales']['hour'] = df['sales']['date_time'].dt.hour              # Extract hour of the day
            
            return df
        
        if not st.session_state.data_loaded:
            st.session_state.df = load_data()
            st.session_state.data_loaded = True
        
        if 'data_loaded' not in st.session_state:
            st.session_state.data_loaded = False
        
        def pieCharts():
            # Ensure the document_id column is treated as a string to match input
            bank_df = st.session_state.df['bank']
            bank_df['document_id'] = bank_df['document_id'].astype(str)
            user_data = bank_df[bank_df['document_id'] == current_id]
        
            user_data['date_time'] = pd.to_datetime(user_data['date_time'])
            user_data = user_data[(user_data['date_time'] >= pd.to_datetime(start_date)) & (user_data['date_time'] <= pd.to_datetime(end_date))]
        
            # Calculate inbound and outbound totals
            st.session_state.inbound_total = user_data[user_data['type'] == 'pix_in']['value'].sum()
            st.session_state.outbound_total = user_data[user_data['type'] == 'pix_out']['value'].sum()
        
            # Create pie chart
            fig = go.Figure(data=[go.Pie(
                labels=['Ganhos', 'Perdas'],
                values=[st.session_state.inbound_total, st.session_state.outbound_total],
                hole=.7,
                marker_colors=[color_themes[selected_theme]['primary'], color_themes[selected_theme]['secondary']],
                textinfo='label+percent',
                hoverinfo='label+value',
                showlegend=False
            )])
        
            # Update layout
            fig.update_layout(
                title= {
                    'font': {'color': color_themes[selected_theme]['text']},
                    'text':'Ganhos vs. Perdas',
                    'x': 0.5,
                    'xanchor': 'center'
                },
                height=400,
                margin=dict(t=100, b=0, l=0, r=0),
                font=dict(color='black'),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
            )
        
            st.plotly_chart(fig, use_container_width=True)
        
        def total_sales_chart():
            # Filter sales data for the specific client ID
            sales_df = st.session_state.df['sales']
            sales_df['document_id'] = sales_df['document_id'].astype(str)
            sales_data = sales_df[(sales_df['document_id'] == current_id)]
        
            # Convert date_time to datetime and filter by date range
            sales_data['date_time'] = pd.to_datetime(sales_data['date_time'])
            filtered_sales = sales_data[(sales_data['date_time'] >= pd.to_datetime(start_date)) & 
                                        (sales_data['date_time'] <= pd.to_datetime(end_date))]
            
            st.session_state.number_of_sales = len(filtered_sales)
        
            # Aggregate sales values by week and calculate cumulative sales
            sales_over_time = filtered_sales.set_index('date_time').resample('W')['value'].sum().reset_index()
            sales_over_time = sales_over_time.rename(columns={'date_time': 'Week', 'value': 'Total Sales'})
            sales_over_time['Cumulative Sales'] = sales_over_time['Total Sales'].cumsum()
        
            # Create the Plotly figure with cumulative sales data
            fig = go.Figure(data=go.Scatter(x=sales_over_time['Week'], y=sales_over_time['Cumulative Sales'], mode='lines+markers', marker=dict(color= color_themes[selected_theme]['secondary']),))
        
            # Update the layout
            fig.update_layout(
                title={
                    'text': 'Vendas Totais ao Longo do Tempo (Semanalmente)',
                    'font': {'color': color_themes[selected_theme]['text']},
                    'x': 0.5,
                    'xanchor': 'center'
                },
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='black'),
                margin=dict(
                    l=100,
                    r=50,
                    b=50,
                    t=100,
                ),
                xaxis=dict(
                    title='Semana',
                    title_font=dict(color='black'),
                    tickfont=dict(color='black'),
                    showgrid=True,
                    gridcolor='#444',
                    color='black'
                ),
                yaxis=dict(
                    title='Vendas Cumulativas ($)',
                    title_font=dict(color='black'),
                    tickfont=dict(color='black'),
                    showgrid=True,
                    gridcolor='#444',
                    color='black'
                ),
                shapes=[
                    dict(
                        type="rect",
                        xref="paper", yref="paper",
                        x0=0, y0=0, x1=1, y1=1,
                        line=dict(color="white", width=2),
                    )
                ]
            )
        
            st.plotly_chart(fig, use_container_width=True)
        
        
        def bank_trends_chart():
            bank_df = st.session_state.df['bank']
            bank_df['document_id'] = bank_df['document_id'].astype(str)
            user_data = bank_df[(bank_df['document_id'] == current_id) & (bank_df['type'].isin(['pix_in', 'pix_out']))]
        
            user_data['date_time'] = pd.to_datetime(user_data['date_time'])
            user_data = user_data[(user_data['date_time'] >= pd.to_datetime(start_date)) & 
                                (user_data['date_time'] <= pd.to_datetime(end_date))]
        
            user_data['value'] = user_data.apply(lambda x: x['value'] if x['type'] == 'pix_in' else -x['value'], axis=1)
            weekly_transactions = user_data.set_index('date_time').resample('W')['value'].sum().reset_index()
        
            fig = go.Figure(data=go.Scatter(x=weekly_transactions['date_time'], y=weekly_transactions['value'], mode='lines+markers', marker=dict(color= color_themes[selected_theme]['secondary'])))
        
            fig.update_layout(
                title={
                    'text': 'Despesas Bancárias ao Longo do Tempo (Semanalmente)',
                    'font': {'color': color_themes[selected_theme]['text']},
                    'x': 0.5,  # Center the title horizontally
                    'xanchor': 'center'
                },
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='black'),
                margin=dict(
                    l=100,
                    r=50,
                    b=50,
                    t=100,
                ),
                xaxis=dict(
                    title='Semana', 
                    title_font=dict(color='black'),
                    tickfont=dict(color='black'),
                    showgrid=True,
                    gridcolor='#444',
                    color='black'
                ),
                yaxis=dict(
                    title='Dinheiro Líquido ($)',
                    title_font=dict(color='black'),
                    tickfont=dict(color='black'),
                    showgrid=True,
                    gridcolor='#444',
                    color='black'
                ),
                shapes=[
                    dict(
                        type="rect",
                        xref="paper", yref="paper",
                        x0=0, y0=0, x1=1, y1=1,
                        line=dict(color="white", width=2),
                    )
                ]
            )
        
        
            st.plotly_chart(fig, use_container_width=True)

        def top_industries():
            # Perform a left join of the MCC dictionary (mcc_df) into sales_df on the 'mcc' column
            sales_df = pd.merge(st.session_state.df['sales'], st.session_state.df['mcc'], on='mcc', how='left')

            # Ensure 'document_id' is a string
            sales_df['document_id'] = sales_df['document_id'].astype(str)
            
            # Filter by the current ID
            sales_data = sales_df[sales_df['document_id'] == current_id]
            
            # Convert 'date_time' to datetime and filter by date range
            sales_data['date_time'] = pd.to_datetime(sales_data['date_time'])
            filtered_sales = sales_data[(sales_data['date_time'] >= pd.to_datetime(start_date)) & 
                                        (sales_data['date_time'] <= pd.to_datetime(end_date))]
            
            # Count occurrences of each industry
            industry_counts = filtered_sales['edited_description'].value_counts()
            
            # Ensure we have at most 5 industries
            industry_counts = industry_counts.head(5)

            # Create a bar chart using Plotly Graph Objects
            fig = go.Figure(
                data=[go.Bar(
                    x=industry_counts.index,
                    y=industry_counts.values,
                    marker=dict(color= color_themes[selected_theme]['secondary']),
                    width=0.3
                )]
            )

            # Update the layout for aesthetics
            fig.update_layout(
                title={
                    'font': {'color': color_themes[selected_theme]['text']},
                    'text': 'Principais Indústrias',
                    'x': 0.55,
                    'xanchor': 'center'
                },
                xaxis=dict(
                    title='Indústria',
                    title_font=dict(color='black'),
                    tickfont=dict(color='black'),
                    showgrid=True,
                    gridcolor='#444',
                    color='black'
                ),
                yaxis=dict(
                    title='Número',
                    title_font=dict(color='black'),
                    tickfont=dict(color='black'),
                    showgrid=True,
                    gridcolor='#444',
                    color='black'
                ),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='black'),
                height=610,  # Increase this value to make the chart taller
                shapes=[
                    dict(
                        type="rect",
                        xref="paper", yref="paper",
                        x0=0, y0=0, x1=1, y1=1,
                        line=dict(color="white", width=2),
                    )
                ]
            )

            # Display the bar chart in Streamlit
            st.plotly_chart(fig, use_container_width=True)

        def apply_theme(theme_name):
            theme = color_themes[theme_name]
            st.markdown(f"""
                <style>
                .stApp {{
                    background-color: {theme['background']};
                }}
                .stSidebar {{
                    background-color: {theme['background']};
                }}
                .stButton>button {{
                    color: {theme['text']};
                    background-color: {theme['primary']};
                    border-color: {theme['primary']};
                }}
                .stTextInput>div>div>input {{
                    color: {theme['text']};
                }}
                h3, h1 {{
                    color: {theme['primary']} !important;
                }}
                /* Make tabs text black */
                button[data-testid="stTab"] div[data-testid="stMarkdownContainer"] p {{
                    color: black !important;
                }}
                </style>
            """, unsafe_allow_html=True)

        # First Row of Data    
        colHeader = st.columns(4, gap='small')
        
        if st.session_state.data_loaded:
            bank_df = st.session_state.df['bank']
            bank_df['document_id'] = bank_df['document_id'].astype(str)

            # Filter data for the current user
            user_data = bank_df[bank_df['document_id'] == st.session_state.username]

            # Convert 'date_time' column to datetime if it's not already
            user_data['date_time'] = pd.to_datetime(user_data['date_time'])

            # Filter by the selected date range
            filtered_user_data = user_data[(user_data['date_time'] >= pd.to_datetime(start_date)) & 
                                        (user_data['date_time'] <= pd.to_datetime(end_date))]

            # Calculate inbound and outbound totals based on the filtered data
            st.session_state.inbound_total = filtered_user_data[filtered_user_data['type'] == 'pix_in']['value'].sum()
            st.session_state.outbound_total = filtered_user_data[filtered_user_data['type'] == 'pix_out']['value'].sum()

            # Update the sales count based on the date range
            sales_df = st.session_state.df['sales']
            sales_df['document_id'] = sales_df['document_id'].astype(str)

            # Filter sales data by the selected date range and user
            filtered_sales_data = sales_df[(sales_df['document_id'] == st.session_state.username) &
                                        (sales_df['date_time'] >= pd.to_datetime(start_date)) &
                                        (sales_df['date_time'] <= pd.to_datetime(end_date))]

            st.session_state.number_of_sales = len(filtered_sales_data)

            # Calculate net value
            net_value = st.session_state.inbound_total - st.session_state.outbound_total
            net_color = "green" if net_value >= 0 else "red"
            
            # Apply the selected theme
            apply_theme(selected_theme)

            # Display metrics
            for idx, metric in enumerate([
                ('Renda', st.session_state.inbound_total, 'green'),
                ('Despesas', st.session_state.outbound_total, 'red'),
                ('Total Líquido', net_value, net_color),
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

            # Use multiple tabs to spread out the graphs
            tab1, tab2, tab3, tab4 = st.tabs(["Ganhos vs. Perdas", "Principais Indústrias", "Despesas Bancárias", "Vendas Totais"])

            with tab1:
                pieCharts()
            with tab2:
                top_industries()
            with tab3:
                bank_trends_chart()
            with tab4:
                total_sales_chart()
        
        def openai_prompting(prompt):
            global newprompt
            global output
            global total_tokens_used
            global cost
            print("\n\nRunning GPT-3.5")
        
            # Define the endpoint URL
            url = "https://api.openai.com/v1/chat/completions"
        
            # Set up the request headers with your API key
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {openai.api_key}"
            }
        
            # Define the request payload (input text and parameters)
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{
                        "role": "system",
                        "content": (
                        "Você é um cientista de dados com o objetivo de analisar dados em resposta a solicitações do usuário e retornar código e texto exclusivamente em português."
                        " Os dados são armazenados em df['sales'], contendo informações sobre vendas, e já foram pré-processados, resultando em df['sales'].shape de (264933, 7), com as colunas: ['document_id', 'date_time', 'value', 'card_number', 'type', 'mcc', 'state'], "
                        " e os tipos de dados: [dtype('int64'), dtype('<M8[us]'), dtype('float64'), dtype('O'), dtype('O'), dtype(' int64 '), dtype('O')]. Por favor, retorne apenas código Python executável para consultar os dados e responder à solicitação do usuário, e nada mais."
                        " Você pode usar numpy, pandas ou plots para completar a tarefa conforme a solicitação do usuário. Anexei a primeira linha de dados como exemplo. O código deve fornecer a resposta ao usuário"
                        " na forma mais simples possível, como um número inteiro acompanhado por um símbolo $. Além disso, quando um gráfico for solicitado, certifique-se de que o gráfico seja exibido com os eixos ajustados adequadamente. Certifique-se de usar os dados armazenados em df['sales']. Lembre-se que todo texto utilizado em gráficos deverá estar somente em português."
                    )
                    },
                    {"role": "user", "content": f"{prompt}"}],
                "max_tokens": 800
            }
            if prompt != "":
                newprompt = prompt
                response = requests.post(url, json=data, headers=headers)
            else:
                print("You have an empty prompt, so printing the previous prompt again or default if first prompt is empty.\n")
                print(f"Prompt: {newprompt}")
                print(f"\nOutput: {output}")
                print("\nTokens Used: " + str(total_tokens_used))
                print("Cost: $" + format(cost, ".8f").rstrip("0").rstrip("."))
                return
        
            # Check if request was successful (status code 200)
            if response.status_code == 200:
                # Parse response to get the text and number of tokens
                output = response.json()['choices'][0]['message']['content']
                output = output.strip().replace("\n\n", "\n")
                prompt_tokens_used = response.json()['usage']['prompt_tokens']
                completion_tokens_used = response.json()['usage']['completion_tokens']
                total_tokens_used = response.json()['usage']['total_tokens']
                
                # Pricing based on gpt-3.5-turbo
                cost_per_input_token = 0.002 / 1_000  # $0.002 per 1,000 tokens for inputs
                cost_per_output_token = 0.002 / 1_000  # $0.002 per 1,000 tokens for outputs
                cost = prompt_tokens_used * cost_per_input_token + completion_tokens_used * cost_per_output_token
        
                # Print the completion text, tokens used, and cost
                print(f"Prompt: {newprompt}")
                print(f"\nOutput: {output}")
                print("\nTokens Used: " + str(total_tokens_used))
                print("Cost: $" + format(cost, ".8f").rstrip("0").rstrip("."))
                return output
            else:
                # Print error message if request was not successful
                print("Error:", response.text)
        
        def promptrun(prompt):
            global output  # Ensure that output is accessible here
            
            # Inject custom CSS to style spinner and error messages
            st.markdown("""
            <style>
            /* Only affect paragraphs inside the AI output container */
            div.ai-output p {
                color: black;
            }
            /* Change the spinner text color to black */
            div.stSpinner div {
                color: black !important;
            }
            /* Change the error message text color to black */
            div.stAlert p {
                color: black;
            }
            </style>
            """, unsafe_allow_html=True)

            # Initialize global variables
            newprompt = ""
            output = ""
            total_tokens_used = 0
            cost = 0.0
        
            # Define the user query
            user_query = prompt
        
            # Extract the first five rows of df['sales'] as an example to include in the prompt
            sample_data = st.session_state.df['sales'].head(1).to_string(index=False)
        
            # Ask the model to generate a prompt that includes the user query and lets it know about the data
            generation_prompt = f"""
            Given the following user query:
        
            {user_query}
        
            Please generate code that includes the necessary instructions to analyze the data. The data will be provided, and you can assume that the data is in a Pandas DataFrame. Below are the first five rows of the DataFrame that will be used for analysis:
        
            {sample_data}
        
            Please generate the code that does what is requested based on the user's query and the data provided.
            """
            with st.spinner("Executando análise de IA..."):
                # Send the request to OpenAI to generate the prompt
                output = openai_prompting(prompt)
            
            if output:
                # Remove unnecessary markdown formatting
                output = output.replace("```python\n", "").replace("\n```", "").replace("df", "st.session_state.df")
                
                # Calculate the number of lines in the output to determine the height
                num_lines = len(output.split('\n'))
                height = min(max(num_lines * 20, 100), 400)
                st.markdown(
                        "<p style='color:black; font-size:16px; margin-bottom: 0px;'>Código Gerado:</p>", 
                        unsafe_allow_html=True
                    )                    
                # Display the generated code
                st.text_area(label="", value=output, height=height)
        
                # Prepare a dictionary to capture the local variables
                local_vars = {}
        
                # Split the output into lines and join them
                lines = output.strip().split('\n')
                joined_lines = "\n".join(lines)
        
                # Debug: Print the joined lines before execution
                print("Executing the following code:\n")
                print(joined_lines)

                # Execute the code and capture the local variables
                try:
                    exec(joined_lines, globals(), local_vars)

                    # Check if plt.show() was used and if there is an active figure
                    if 'plt.show()' in joined_lines:
                        # Capture the current figure
                        fig = plt.gcf()  # Get the current figure
                        st.pyplot(fig)   # Pass the figure to st.pyplot()
                        plt.clf()        # Clear the figure after rendering
                    else:
                        # Get the last variable name and value
                        if local_vars:
                            last_var_name = list(local_vars.keys())[-1]
                            last_var_value = local_vars[last_var_name]
                            # Format the result based on its type
                            if isinstance(last_var_value, (int, float)):
                                formatted_result = f"<div class='ai-output'><p>Resultado: ${last_var_value:,.2f}</p></div>"
                                st.markdown(formatted_result, unsafe_allow_html=True)
                            elif isinstance(last_var_value, pd.Series):
                                formatted_result = last_var_value.round(2).apply(lambda x: f"{x:.2f}%").to_string()
                                formatted_result = f"<div class='ai-output'><p>{formatted_result}</p></div>"
                                st.markdown(formatted_result, unsafe_allow_html=True)
                            else:
                                formatted_result = str(last_var_value)
                                formatted_result = f"<div class='ai-output'><p>{formatted_result}</p></div>"
                                st.markdown(formatted_result, unsafe_allow_html=True)
                        else:
                            st.warning("Nenhum resultado foi gerado pelo código executado.")

                except Exception as e:
                    # Style the error message text to appear in black
                    st.error(f"Erro ao executar o código: {e}")
        
        # AI Input Section in Streamlit
        st.markdown("""<h3 style='color: black;'>Insira um Prompt Para Análise de IA:</h3>""",unsafe_allow_html=True)
        prompt = st.text_area(label="")  # Adding a label argument
        
        if st.button("Execute a Análise de IA"):
            promptrun(prompt)
        
        if st.button("Sair", on_click=_reset_login_cb):
            st.success("Você saiu com sucesso.")

if __name__ == "__main__":
    main()