import streamlit as st
import pandas as pd
import gdown
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

st.set_page_config(layout="wide")

#global vars
if 'inbound_total' not in st.session_state:
    st.session_state.inbound_total = 0
if 'outbound_total' not in st.session_state:
    st.session_state.outbound_total = 0

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

    # Create subplots
    fig = make_subplots(rows=2, cols=1, specs=[[{'type':'domain'}], [{'type':'domain'}]])

    # Add traces for inbound
    fig.add_trace(go.Pie(
        values=[inbound_percent, 100-inbound_percent],
        labels=['', ''],
        hole=.7,
        marker_colors=['#4CAF50', '#ffffff'],
        textinfo='none',
        hoverinfo='none',
        showlegend=False
    ), 1, 1)

    # Add traces for outbound
    fig.add_trace(go.Pie(
        values=[outbound_percent, 100-outbound_percent],
        labels=['', ''],
        hole=.7,
        marker_colors=['#FF5252', '#ffffff'],
        textinfo='none',
        hoverinfo='none',
        showlegend=False
    ), 2, 1)

    fig.add_annotation(x=0.5, y=0.78, text="Inbound", showarrow=False)
    fig.add_annotation(x=0.5, y=0.83, text=f"{inbound_percent}%", font=dict(size=24, color='#4CAF50'), showarrow=False)
    fig.add_annotation(x=0.5, y=0.15, text="Outbound", showarrow=False)
    fig.add_annotation(x=0.5, y=0.18, text=f"{outbound_percent}%", font=dict(size=24, color='#FF5252'), showarrow=False)

    # Update layout
    fig.update_layout(
        height=600,
        width=400,
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
        """
        <div style="border: 2px solid white; padding: 20px; text-align: left; border-radius: 5px;">
            <p style="color: white; font-size: 16px; margin-bottom: 4px;">ToDo2</p>
        </div>
        """,
        unsafe_allow_html=True
    )

        

col = st.columns((1, 1), gap='large')

with col[0]:
    col2 = st.columns((0.6, 0.4), gap='medium')
    with st.container():
        with col2[0]:
            st.markdown('#### Gains/Losses')
            pieCharts()

with col[1]:
    # st.markdown('#### Total Population')
    st.markdown('#')
    bank_trends_chart()
    st.markdown('#')
    total_sales_chart()
