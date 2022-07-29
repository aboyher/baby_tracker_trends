import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import altair as alt
import pandas as pd
import zipfile

file = st.file_uploader("Upload File", type="zip", key="file")

if file is not None:
    zf = zipfile.ZipFile(file)
    df = None
    for name in zf.namelist():
        if "pumped" in name or "formula" in name:
            dff = pd.read_csv(zf.open(name))
            dff['file'] = name.strip(".csv").split("_")[-1]
            if df is None:
                df = dff
            else:
                df = pd.concat([df, dff])
    df.fillna("", inplace=True)
    if "Amount (ml)" in df.columns:
        df.rename(columns={"Amount (ml)": "Amount"}, inplace=True)
    df['Volume'] = df['Amount'].apply(lambda x: int(x.split()[0]))
    df['Unit'] = df['Amount'].apply(lambda x: x.split()[-1])
    df['Time'] = pd.to_datetime(df['Time'])
    df = df.sort_values("Time")
    st.write(df)

    st.markdown("### Daily Totals")
    daily_total = df.groupby(df['Time'].dt.date).sum()
    fig = px.bar(daily_total, y="Volume")
    st.plotly_chart(fig, use_container_width=True)

    rolling_24 = df.set_index("Time").rolling('24h').sum()
    fig = px.line(rolling_24)
    st.plotly_chart(fig, use_container_width=True)


    fig = go.Figure()
    fig.add_trace(
        go.Bar(x=daily_total.index, y=daily_total.Volume)
    )
    fig.add_trace(
        go.Line(x=rolling_24.index, y=rolling_24.Volume)
    )
    st.plotly_chart(fig, use_container_width=True)

    rolling_24_mean = rolling_24.rolling('7d', min_periods=1).mean()
    fig = px.line(rolling_24_mean)
    st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        current_volume = int(rolling_24['Volume'].tolist()[-1])
        st.metric("Current Volume:", f"{current_volume} ml")
    with col2:
        current_average = int(rolling_24_mean['Volume'].tolist()[-1])
        st.metric("24hr Average:", f"{current_average} ml")
    with col3:
        losing = df[df['Time'] < (df.iloc[-1]['Time'] - pd.Timedelta(1,'d'))].iloc[-1]['Volume']
        st.metric("Losing Amount: ", f"{losing} ml")
    with col4:
        new_volume_without_feeding = current_volume - losing
        st.metric("New Volume", f"{new_volume_without_feeding} ml")
    with col5:
        feeding_to_match_average = current_average - new_volume_without_feeding
        st.metric("Volume to eat:", f"{feeding_to_match_average} ml", delta=int(feeding_to_match_average - df.iloc[-1]['Volume']))