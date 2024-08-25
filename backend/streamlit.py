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

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(layout="wide")

#global vars
if 'inbound_total' not in st.session_state:
    st.session_state.inbound_total = 0
if 'outbound_total' not in st.session_state:
    st.session_state.outbound_total = 0
if 'number_of_sales' not in st.session_state:
    st.session_state.number_of_sales = 0

st.markdown("<h1 style='text-align: center; color: black;'>Business Dashboard</h1>", unsafe_allow_html=True)

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
### to run streamlit app `streamlit run backend/streamlit.py`

# Sidebar setup
with st.sidebar:
    st.title('📅 Select Time Interval')

    start_date = st.date_input(
        'Start date',
        min_value=datetime(2022, 12, 1),
        max_value=datetime(2023, 5, 31),
        value=datetime(2022, 12, 1)
    )

    end_date = st.date_input(
        'End date',
        min_value=start_date,
        max_value=datetime(2023, 5, 31),
        value=datetime(2023, 5, 31)
    )

    # Input for Client ID
    current_id = st.text_input('Enter Client ID:', value='6347736874608223396')

# loading function
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

df = load_data()

def pieCharts():
    # Ensure the document_id column is treated as a string to match input
    bank_df = df['bank']
    bank_df['document_id'] = bank_df['document_id'].astype(str)
    user_data = bank_df[bank_df['document_id'] == current_id]

    user_data['date_time'] = pd.to_datetime(user_data['date_time'])
    user_data = user_data[(user_data['date_time'] >= pd.to_datetime(start_date)) & (user_data['date_time'] <= pd.to_datetime(end_date))]

    # Calculate inbound and outbound totals
    st.session_state.inbound_total = user_data[user_data['type'] == 'pix_in']['value'].sum()
    st.session_state.outbound_total = user_data[user_data['type'] == 'pix_out']['value'].sum()

    # Calculate percentages
    total_spending = st.session_state.inbound_total + st.session_state.outbound_total
    inbound_percent = round((st.session_state.inbound_total / total_spending) * 100, 2) if total_spending > 0 else 0
    outbound_percent = round((st.session_state.outbound_total / total_spending) * 100, 2) if total_spending > 0 else 0

    # Create subplots with 1 row and 2 columns
    fig = make_subplots(rows=1, cols=2, specs=[[{'type':'domain'}, {'type':'domain'}]])

    # Add traces for inbound
    fig.add_trace(go.Pie(
        values=[inbound_percent, 100 - inbound_percent],
        labels=['', ''],
        hole=.7,
        marker_colors=['#4CAF50', '#ffffff'],
        textinfo='none',
        hoverinfo='none',
        showlegend=False
    ), 1, 1)

    # Add traces for outbound
    fig.add_trace(go.Pie(
        values=[outbound_percent, 100 - outbound_percent],
        labels=['', ''],
        hole=.7,
        marker_colors=['#FF5252', '#ffffff'],
        textinfo='none',
        hoverinfo='none',
        showlegend=False
    ), 1, 2)

    # Add annotations for the pie charts
    fig.add_annotation(x=0.18, y=0.5, text="Inbound", showarrow=False, font=dict(color="white"))
    fig.add_annotation(x=0.18, y=0.4, text=f"{inbound_percent}%", font=dict(size=24, color='#4CAF50'), showarrow=False)
    fig.add_annotation(x=0.82, y=0.5, text="Outbound", showarrow=False, font=dict(color="white"))
    fig.add_annotation(x=0.82, y=0.4, text=f"{outbound_percent}%", font=dict(size=24, color='#FF5252'), showarrow=False)

    # Update layout
    fig.update_layout(
        height=300,
        width=800,
        margin=dict(t=0, b=0, l=0, r=0),
        font=dict(color='white'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig)

def total_sales_chart():
    # Filter sales data for the specific client ID
    sales_df = df['sales']
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
    fig = go.Figure(data=go.Scatter(x=sales_over_time['Week'], y=sales_over_time['Cumulative Sales'], mode='lines+markers'))

    # Update the layout
    fig.update_layout(
        title={
            'text': 'Total Sales Over Time (Weekly)',
            'font': {'color': 'black'}  # Set the title color to black
        },
        paper_bgcolor='#ffffff', 
        plot_bgcolor='#f0f2f6',
        font=dict(color='black'),
        margin=dict(
            l=100,
            r=50,
            b=50,
            t=100,
        ),
        xaxis=dict(
            title='Week',  # X-axis title
            title_font=dict(color='black'),  # X-axis title color
            tickfont=dict(color='black'),  # X-axis label color
            showgrid=True,
            gridcolor='#444',
            color='white'
        ),
        yaxis=dict(
            title='Cumulative Sales ($)',  # Y-axis title
            title_font=dict(color='black'),  # Y-axis title color
            tickfont=dict(color='black'),  # Y-axis label color
            showgrid=True,
            gridcolor='#444',
            color='white'
        ),
    )

    st.plotly_chart(fig, use_container_width=True)


def bank_trends_chart():
    bank_df = df['bank']
    bank_df['document_id'] = bank_df['document_id'].astype(str)
    user_data = bank_df[(bank_df['document_id'] == current_id) & (bank_df['type'].isin(['pix_in', 'pix_out']))]

    user_data['date_time'] = pd.to_datetime(user_data['date_time'])
    user_data = user_data[(user_data['date_time'] >= pd.to_datetime(start_date)) & 
                          (user_data['date_time'] <= pd.to_datetime(end_date))]

    user_data['value'] = user_data.apply(lambda x: x['value'] if x['type'] == 'pix_in' else -x['value'], axis=1)
    weekly_transactions = user_data.set_index('date_time').resample('W')['value'].sum().reset_index()

    fig = go.Figure(data=go.Scatter(x=weekly_transactions['date_time'], y=weekly_transactions['value'], mode='lines+markers'))

    fig.update_layout(
        title={
            'text': 'Bank Expenses Over Time (Weekly)',
            'font': {'color': 'black'}  # Set the title color to black
        },
        paper_bgcolor='#ffffff', 
        plot_bgcolor='#f0f2f6',
        font=dict(color='white'),
        margin=dict(
            l=100,
            r=50,
            b=50,
            t=100,
        ),
        xaxis=dict(
            title='Week',  # X-axis title
            title_font=dict(color='black'),
            tickfont=dict(color='black'),
            showgrid=True,
            gridcolor='#444',
            color='white'
        ),
        yaxis=dict(
            title='Net Money ($)',  # Y-axis title
            title_font=dict(color='black'),  # Y-axis title color
            tickfont=dict(color='black'),  # Y-axis label color
            showgrid=True,
            gridcolor='#444',
            color='white'
        ),
    )


    st.plotly_chart(fig, use_container_width=True)

#First Row of Data    
colHeader = st.columns((1, 1, 1, 1), gap='small')

with colHeader[0]:
    st.markdown(
        f"""
        <div style="border: 2px solid white; padding: 20px; text-align: left; border-radius: 5px;">
            <p style="color: black; font-size: 16px; margin-bottom: 4px;">Income</p>
            <p style="color: green; font-size: 32px; font-weight: bold;">${st.session_state.inbound_total:,.2f}</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

with colHeader[1]:
    st.markdown(
        f"""
        <div style="border: 2px solid white; padding: 20px; text-align: left; border-radius: 5px;">
            <p style="color: black; font-size: 16px; margin-bottom: 4px;">Expenses</p>
            <p style="color: red; font-size: 32px; font-weight: bold;">${st.session_state.outbound_total:,.2f}</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

with colHeader[2]:
    net_value = st.session_state.inbound_total - st.session_state.outbound_total
    net_color = "green" if net_value >= 0 else "red"
    st.markdown(
        f"""
        <div style="border: 2px solid white; padding: 20px; text-align: left; border-radius: 5px;">
            <p style="color: black; font-size: 16px; margin-bottom: 4px;">Net Total</p>
            <p style="color: {net_color}; font-size: 32px; font-weight: bold;">${net_value:,.2f}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with colHeader[3]:
    st.markdown(
        f"""
        <div style="border: 2px solid white; padding: 20px; text-align: left; border-radius: 5px;">
            <p style="color: black; font-size: 16px; margin-bottom: 4px;">Number of Sales</p>
            <p style="color: green; font-size: 32px; font-weight: bold;">{st.session_state.number_of_sales}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

        

col = st.columns((1, 1), gap='large')

with col[0]:
    with st.container():
        st.markdown(
            """
            <h4 style='color: black;'>Gains/Losses</h4>
            """,
            unsafe_allow_html=True
        )
        pieCharts()

with col[1]:
    st.markdown('##')
    bank_trends_chart()
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
        "model": "gpt-3.5-turbo",  # choose the model
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
            {"role": "user", "content": f"{prompt}"}],  # prompt here
        "max_tokens": 800  # maximum number of tokens for the model
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
    
    # Initialize global variables
    newprompt = ""
    output = ""
    total_tokens_used = 0
    cost = 0.0

    # Define the user query
    user_query = prompt

    # Extract the first five rows of df['sales'] as an example to include in the prompt
    sample_data = df['sales'].head(1).to_string(index=False)

    # Ask the model to generate a prompt that includes the user query and lets it know about the data
    generation_prompt = f"""
    Given the following user query:

    {user_query}

    Please generate code that includes the necessary instructions to analyze the data. The data will be provided, and you can assume that the data is in a Pandas DataFrame. Below are the first five rows of the DataFrame that will be used for analysis:

    {sample_data}

    Please generate the code that does what is requested based on the user's query and the data provided.
    """
    
    with st.spinner("Running AI Analysis..."):
        # Send the request to OpenAI to generate the prompt
        output = openai_prompting(prompt)
    
    if output:
        # Remove unnecessary markdown formatting
        output = output.replace("```python\n", "").replace("\n```", "")
        
        # Calculate the number of lines in the output to determine the height
        num_lines = len(output.split('\n'))
        height = min(max(num_lines * 20, 100), 400)
        
        # Display the generated code
        st.text_area("Generated Code:", value=output, height=height)

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
                last_var_name = list(local_vars.keys())[-1]
                last_var_value = local_vars[last_var_name]

                # Format the result based on its type
                if isinstance(last_var_value, (int, float)):
                    formatted_result = f"\n\nResult: ${last_var_value:,.2f}"
                    st.write(formatted_result)
                elif isinstance(last_var_value, pd.Series):
                    formatted_result = last_var_value.round(2).apply(lambda x: f"{x:.2f}%").to_string()
                    st.write(formatted_result)
                else:
                    formatted_result = str(last_var_value)
                    st.write(formatted_result)
        except Exception as e:
            st.error(f"Error executing the code: {e}")

# AI Input Section in Streamlit
st.markdown("### Enter a prompt for AI analysis:")
prompt = st.text_area(label="")  # Adding a label argument

if st.button("Run AI Analysis"):
    promptrun(prompt)
