import streamlit as st
import pandas as pd
import gdown
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

st.title('Insert Title Here')

# Sidebar setup
with st.sidebar:
    st.title('📅 Select Time Interval')

    start_date = st.date_input(
        'Start date',
        min_value=datetime(1900, 1, 1),
        max_value=datetime.now(),
        value=datetime(2020, 1, 1)
    )

    end_date = st.date_input(
        'End date',
        min_value=start_date,
        max_value=datetime.now(),
        value=datetime.now()
    )

    # Display the selected date interval
    st.write(f"Selected interval: {start_date} to {end_date}")

    # Input for Client ID
    current_id = st.text_input('Enter Client ID:', value='6347736874608223396')

# Cache the data loading function
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

    # Calculate inbound and outbound totals
    inbound_total = user_data[user_data['type'] == 'pix_in']['value'].sum()
    outbound_total = user_data[user_data['type'] == 'pix_out']['value'].sum()

    # Display inbound and outbound totals
    st.metric(label="Profit", value=f"${inbound_total:,.2f}")
    st.metric(label="Expenditure", value=f"${outbound_total:,.2f}")

    # Calculate percentages
    total_spending = inbound_total + outbound_total
    inbound_percent = round((inbound_total / total_spending) * 100, 2) if total_spending > 0 else 0
    outbound_percent = round((outbound_total / total_spending) * 100, 2) if total_spending > 0 else 0

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

    # Add annotations
    fig.add_annotation(x=0.5, y=0.78, text="Inbound", showarrow=False)
    fig.add_annotation(x=0.5, y=0.83, text=f"{inbound_percent}%", font=dict(size=24, color='#4CAF50'), showarrow=False)
    fig.add_annotation(x=0.5, y=0.15, text="Outbound", showarrow=False)
    fig.add_annotation(x=0.5, y=0.18, text=f"{outbound_percent}%", font=dict(size=24, color='#FF5252'), showarrow=False)

    # Update layout
    fig.update_layout(
        height=600,
        width=300,
        paper_bgcolor='#263238',
        plot_bgcolor='#263238',
        margin=dict(t=0, b=0, l=0, r=0),
        font=dict(color='white')
    )

    # Show figure
    st.plotly_chart(fig)

def sales_trends_chart():
    # Filter bank data for the specific client ID
    bank_df = df['bank']
    bank_df['document_id'] = bank_df['document_id'].astype(str)
    user_data = bank_df[(bank_df['document_id'] == current_id) & (bank_df['type'] == 'pix_in')]

    user_data['date_time'] = pd.to_datetime(user_data['date_time'])
    user_data = user_data[(user_data['date_time'] >= pd.to_datetime(start_date)) & (user_data['date_time'] <= pd.to_datetime(end_date))]
    daily_incoming = user_data.groupby('date_time')['value'].sum().reset_index()

    # Create line chart
    fig = go.Figure(data=go.Scatter(x=daily_incoming['date_time'], y=daily_incoming['value'], mode='lines+markers'))

    fig.update_layout(
        title='Sales Trends Over Time',
        xaxis_title='Date',
        yaxis_title='Total Incoming Money',
        paper_bgcolor='#263238',
        plot_bgcolor='#263238',
        font=dict(color='white')
    )
    st.plotly_chart(fig, use_container_width=True)

col = st.columns((0.4, 0.6), gap='medium')

with col[0]:
    st.markdown('#### Gains/Losses')
    pieCharts()

with col[1]:
    st.markdown('#### Total Population')
    sales_trends_chart()
