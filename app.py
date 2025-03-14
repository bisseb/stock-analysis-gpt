import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import datetime
import PyPDF2
import requests
from bs4 import BeautifulSoup

# Hugging Face API for text summarization
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
HUGGINGFACE_HEADERS = {"Authorization": "Bearer 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"}  # Replace with your HF API Key

def extract_text_from_pdf(pdf_file):
    text = ""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def fetch_stock_data(ticker, start_date, end_date):
    stock = yf.Ticker(ticker)
    df = stock.history(start=start_date, end=end_date)
    return df

def fetch_news(ticker):
    search_url = f"https://www.google.com/search?q={ticker}+stock+news"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    headlines = []
    for item in soup.find_all("h3"):
        headlines.append(item.get_text())
    return headlines[:5]

def generate_ai_summary(text, stock_ticker):
    prompt = f"Analyze this financial document and summarize key impacts on {stock_ticker}:\n{text[:2000]}"
    try:
        response = requests.post(HUGGINGFACE_API_URL, headers=HUGGINGFACE_HEADERS, json={"inputs": prompt})
        summary = response.json()
        return summary[0]['summary_text'] if isinstance(summary, list) else "Error: Invalid response from API"
    except Exception as e:
        return f"Error generating AI summary: {str(e)}"

def plot_stock_chart(df, ticker, annotations):
    plt.figure(figsize=(12, 6))
    plt.plot(df.index, df["Close"], label=f"{ticker} Close Price")
    for date, note in annotations.items():
        if date in df.index:
            plt.axvline(date, color='r', linestyle='--')
            plt.text(date, df.loc[date, "Close"], note, fontsize=9, rotation=45)
    plt.legend()
    plt.title(f"{ticker} Stock Price with Key Events")
    plt.xlabel("Date")
    plt.ylabel("Price")
    st.pyplot(plt)

st.title("📈 AI-Powered Stock Analysis")

uploaded_pdf = st.file_uploader("Upload a PDF (Earnings Report, 10-K, etc.)", type=["pdf"])
stock_ticker = st.text_input("Enter Stock Ticker (e.g., AAPL, TSLA)")
date_range = st.date_input("Select Date Range", [datetime.date(2023, 1, 1), datetime.date.today()])

if st.button("Analyze Stock"):
    if uploaded_pdf and stock_ticker:
        text = extract_text_from_pdf(uploaded_pdf)
        summary = generate_ai_summary(text, stock_ticker)
        st.subheader("🔍 AI Summary")
        st.write(summary)
        
        news = fetch_news(stock_ticker)
        st.subheader("📰 Recent News")
        for n in news:
            st.write(f"- {n}")
        
        df = fetch_stock_data(stock_ticker, date_range[0], date_range[1])
        annotations = {date_range[0]: "Start", date_range[1]: "End"}  # Example annotations
        st.subheader("📊 Stock Chart")
        plot_stock_chart(df, stock_ticker, annotations)
    else:
        st.error("Please upload a PDF and enter a stock ticker!")
