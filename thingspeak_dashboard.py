import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
from datetime import datetime, timedelta
from pytz import UTC
from PIL import Image
from streamlit_option_menu import option_menu
from plotly.subplots import make_subplots

# Use Streamlit secrets for ThingSpeak credentials
CHANNEL_ID = st.secrets["thingspeak"]["channel_id"]
READ_API_KEY = st.secrets["thingspeak"]["read_api_key"]

# Define the timezone offset
TZ_OFFSET = timedelta(hours=-3)  # UTC-3

def fetch_data():
    try:
        url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json?api_key={READ_API_KEY}&results=15000"
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        data = response.json()
        
        df = pd.DataFrame(data['feeds'])
        df['created_at'] = pd.to_datetime(df['created_at'], utc=True)
        df['created_at'] = df['created_at'] + TZ_OFFSET  # Adjust for UTC-3
        df['field1'] = pd.to_numeric(df['field1'], errors='coerce')  # Temperature Sensor 1
        df['field2'] = pd.to_numeric(df['field2'], errors='coerce')  # Temperature Sensor 2
        
        # Sort the dataframe by date
        df = df.sort_values('created_at')
        
        return df
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from ThingSpeak: {e}")
        return pd.DataFrame()
    except KeyError as e:
        st.error(f"Error processing ThingSpeak data: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return pd.DataFrame()

def create_plot(df, y_col, title, y_label, color):
    fig = make_subplots(rows=1, cols=1, subplot_titles=[title])
    
    fig.add_trace(
        go.Scatter(
            x=df['created_at'], 
            y=df[y_col], 
            mode='lines', 
            name=y_label, 
            line=dict(color=color, width=2),
            fill='tozeroy'
        )
    )
    
    fig.update_layout(
        height=400,
        margin=dict(l=50, r=50, t=50, b=50),
        xaxis_title='Time (UTC-3)',
        yaxis_title=y_label,
        font=dict(family="Arial", size=12),
        plot_bgcolor='white',
        xaxis=dict(showgrid=True, gridcolor='lightgrey'),
        yaxis=dict(showgrid=True, gridcolor='lightgrey'),
    )
    
    fig.update_xaxes(showline=True, linewidth=2, linecolor='black', mirror=True)
    fig.update_yaxes(showline=True, linewidth=2, linecolor='black', mirror=True)
    
    return fig

def main():
    st.set_page_config(page_title="Temperature Monitoring Dashboard", layout="wide", initial_sidebar_state="expanded")

    # Custom CSS to improve the overall look
    st.markdown("""
        <style>
        .stApp {
            background-color: #ffffff;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
        }
        .stProgress .st-bo {
            background-color: #4CAF50;
        }
        </style>
        """, unsafe_allow_html=True)

    with st.sidebar:
        img = Image.open("Logo e-Civil.png")
        st.image(img)
        
        selected = option_menu(
            menu_title="Main Menu",
            options=["Home", "Setup", "Code", "Contact"],
            icons=["house", "gear", "code-slash", "envelope"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "5!important", "background-color": "#fafafa"},
                "icon": {"color": "orange", "font-size": "25px"}, 
                "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
                "nav-link-selected": {"background-color": "#02ab21"},
            }
        )

    if selected == "Home":
        st.title("🌡️ Monitoramento da temperatura com sensor DS18B20")
        st.subheader("Tecomat/UFPE - Monitoramento da temperatura de blocos de concreto")

        df = fetch_data()

        if not df.empty:
            col1, col2 = st.columns(2)

            with col1:
                current_temp1 = df['field1'].iloc[-1]
                st.metric("Temperatura atual - Sensor 1", f"{current_temp1:.2f} °C", 
                         f"{current_temp1 - df['field1'].iloc[-2]:.2f} °C")
                fig_temp1 = create_plot(df, 'field1', '', 'Temperature Sensor 1 (°C)', 'red')
                st.plotly_chart(fig_temp1, use_container_width=True, config={'displayModeBar': False})

            with col2:
                current_temp2 = df['field2'].iloc[-1]
                st.metric("Temperatura atual - Sensor 2", f"{current_temp2:.2f} °C", 
                         f"{current_temp2 - df['field2'].iloc[-2]:.2f} °C")
                fig_temp2 = create_plot(df, 'field2', '', 'Temperature Sensor 2 (°C)', 'blue')
                st.plotly_chart(fig_temp2, use_container_width=True, config={'displayModeBar': False})

            # Display first and last timestamps
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📊 Data Range")
                first_timestamp = df['created_at'].iloc[0]
                last_timestamp = df['created_at'].iloc[-1]
                st.info(f"First Record: {first_timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC-3")
                st.info(f"Last Record: {last_timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC-3")
                days_passed = (last_timestamp - first_timestamp).days
                st.success(f"Total Measurement Interval: {days_passed} days")

            with col2:
                st.subheader("🌡️ Temperature Extremes")
                
                # Sensor 1 extremes
                st.write("**Sensor 1**")
                max_temp1 = df['field1'].max()
                min_temp1 = df['field1'].min()
                max_temp1_time = df.loc[df['field1'].idxmax(), 'created_at']
                min_temp1_time = df.loc[df['field1'].idxmin(), 'created_at']
                st.error(f"Maximum: {max_temp1:.2f} °C, Recorded on {max_temp1_time.strftime('%Y-%m-%d %H:%M:%S')} UTC-3")
                st.success(f"Minimum: {min_temp1:.2f} °C, Recorded on {min_temp1_time.strftime('%Y-%m-%d %H:%M:%S')} UTC-3")
                
                # Sensor 2 extremes
                st.write("**Sensor 2**")
                max_temp2 = df['field2'].max()
                min_temp2 = df['field2'].min()
                max_temp2_time = df.loc[df['field2'].idxmax(), 'created_at']
                min_temp2_time = df.loc[df['field2'].idxmin(), 'created_at']
                st.error(f"Maximum: {max_temp2:.2f} °C, Recorded on {max_temp2_time.strftime('%Y-%m-%d %H:%M:%S')} UTC-3")
                st.success(f"Minimum: {min_temp2:.2f} °C, Recorded on {min_temp2_time.strftime('%Y-%m-%d %H:%M:%S')} UTC-3")
        else:
            st.error("No data available. Please check your ThingSpeak connection.")

    elif selected == "Setup":
        st.title("🔧 Hardware Setup")
        st.subheader("Microcontroller and Sensor Details")
        st.image("esp32_ds18b20.png", use_column_width=True)
        st.write("This setup uses an ESP32 microcontroller connected to two temperature sensors. Data is sent using Thingspeak.")

    elif selected == "Code":
        st.title("💻 Source Code")
        st.markdown("View the source code for this dashboard on GitHub:")
        st.markdown("[GitHub Repository](https://github.com/PM1980/dht22/blob/main/thingspeak_dashboard.py)")
        
        if st.button("Show Sample Code"):
            st.code("""
            def fetch_data():
                try:
                    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json?api_key={READ_API_KEY}&results=15000"
                    response = requests.get(url)
                    response.raise_for_status()
                    data = response.json()
                    
                    df = pd.DataFrame(data['feeds'])
                    df['created_at'] = pd.to_datetime(df['created_at'], utc=True)
                    df['created_at'] = df['created_at'] + TZ_OFFSET
                    df['field1'] = pd.to_numeric(df['field1'], errors='coerce')
                    df['field2'] = pd.to_numeric(df['field2'], errors='coerce')
                    
                    return df.sort_values('created_at')
                except Exception as e:
                    st.error(f"An error occurred: {e}")
                    return pd.DataFrame()
            """, language="python")

    elif selected == "Contact":
        st.title("📬 Contact Us")
        st.write("Follow us on Instagram for updates and more information:")
        st.markdown("[Instagram: projeto_ecivil](https://www.instagram.com/projeto_ecivil/)")
        
        st.write("Or reach out to us directly:")
        contact_form = """
        <form action="https://formsubmit.co/YOUR_EMAIL_HERE" method="POST">
            <input type="hidden" name="_captcha" value="false">
            <input type="text" name="name" placeholder="Your name" required>
            <input type="email" name="email" placeholder="Your email" required>
            <textarea name="message" placeholder="Your message here"></textarea>
            <button type="submit">Send</button>
        </form>
        """
        st.markdown(contact_form, unsafe_allow_html=True)
        
        # Add custom CSS to make the form look nicer
        st.markdown("""
        <style>
        input[type=text], input[type=email], textarea {
            width: 100%;
            padding: 12px;
            border: 1px solid #ccc;
            border-radius: 4px;
            box-sizing: border-box;
            margin-top: 6px;
            margin-bottom: 16px;
            resize: vertical;
        }
        button[type=submit] {
            background-color: #4CAF50;
            color: white;
            padding: 12px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button[type=submit]:hover {
            background-color: #45a049;
        }
        </style>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
