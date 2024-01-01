import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup


def get_annual_index_change():
    # URL you want to fetch
    url = 'https://tradingeconomics.com/israel/inflation-cpi'

    # Define headers to simulate a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    # Send a GET request to the URL with headers
    response = requests.get(url, headers=headers)

    # Initialize a variable to store the last Inflation Rate
    last_inflation_rate = None

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        target_div = soup.find('div', id='ctl00_ContentPlaceHolder1_ctl00_ctl01_Panel1')

        # Check if the div is found
        if target_div:
            # Find all rows in the table
            rows = target_div.find_all('tr', class_='datatable-row')

            # Iterate over rows to find the Inflation Rate
            for row in rows:
                cells = row.find_all('td')
                if len(cells) > 1 and 'Inflation Rate' in cells[0].get_text():
                    last_inflation_rate = cells[1].get_text().strip()
                    break
    else:
        print("Failed to retrieve the webpage")

    return float(last_inflation_rate)


# Function to calculate monthly mortgage payment for fixed rate
def calculate_fixed_mortgage(principal, interest_rate, years):
    monthly_interest_rate = interest_rate / 100 / 12
    payment_number = years * 12
    monthly_payment = principal * (monthly_interest_rate * np.power(1 + monthly_interest_rate, payment_number)) / (
                np.power(1 + monthly_interest_rate, payment_number) - 1)
    return monthly_payment


# Function to create amortization schedule
def create_amortization_schedule(principal, interest_rate, years, mortgage_type, adjustment_period=0, rate_adjustment=0,
                                 index_change=0):
    schedule = []
    outstanding_balance = principal
    monthly_interest_rate = interest_rate / 100 / 12
    monthly_payment = calculate_fixed_mortgage(principal, interest_rate, years)

    # Determine the number of months to iterate over
    total_months = years * 12
    if mortgage_type == "Variable Linked":
        total_months = min(total_months, adjustment_period * 12)

    for month in range(1, total_months + 1):
        if mortgage_type == "Variable Linked":
            if month % (adjustment_period * 12) == 0 and month != 0:
                interest_rate += rate_adjustment
                monthly_interest_rate = interest_rate / 100 / 12
                remaining_years = years - month // 12
                monthly_payment = calculate_fixed_mortgage(outstanding_balance, interest_rate, remaining_years)

            if month % 12 == 0 and month != 0:
                outstanding_balance *= (1 + index_change / 100)

        interest = outstanding_balance * monthly_interest_rate
        principal_paid = monthly_payment - interest
        outstanding_balance -= principal_paid
        schedule.append([month, monthly_payment, principal_paid, interest, outstanding_balance])

    columns = ["Month", "Payment", "Principal", "Interest", "Remaining Balance"]
    return pd.DataFrame(schedule, columns=columns).round(2)


# Function to adjust principal based on index change
def adjust_principal_for_index(principal, index_change):
    return principal * (1 + index_change / 100)


# Function to plot amortization schedule
def plot_amortization_schedule(schedule):
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    plt.plot(schedule['Month'].values, schedule['Remaining Balance'].values, color='blue', label='Remaining Balance')
    plt.title('Remaining Loan Balance Over Time')
    plt.xlabel('Month')
    plt.ylabel('Balance')
    plt.legend()
    plt.grid(True)

    plt.subplot(1, 2, 2)
    plt.stackplot(schedule['Month'], schedule['Principal'], schedule['Interest'], labels=['Principal', 'Interest'],
                  colors=['green', 'orange'])
    plt.title('Principal and Interest Over Time')
    plt.xlabel('Month')
    plt.ylabel('Amount')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    return plt


# Streamlit app
def main():
    st.title("Israeli Mortgage Calculator")

    annual_index_change = get_annual_index_change()

    principal = st.number_input("Loan Amount", min_value=1000, max_value=10000000, value=300000)
    years = st.number_input("Loan Term (Years)", min_value=1, max_value=30, value=20)
    mortgage_type = st.selectbox("Mortgage Type", ["Fixed Unlinked", "Fixed Linked", "Variable Linked"])

    if mortgage_type == "Fixed Unlinked":
        interest_rate = st.number_input("Annual Interest Rate (%)", min_value=0.1, max_value=20.0, value=3.5)
        if st.button("Calculate for Fixed Rate"):
            monthly_payment = calculate_fixed_mortgage(principal, interest_rate, years)
            schedule = create_amortization_schedule(principal, interest_rate, years, mortgage_type)
            st.write(f"Monthly Payment: ₪{monthly_payment:,.2f}")
            st.dataframe(schedule)
            plot = plot_amortization_schedule(schedule)
            st.pyplot(plot)

    elif mortgage_type == "Fixed Linked":
        interest_rate = st.number_input("Annual Interest Rate (%)", min_value=0.1, max_value=20.0, value=3.5)
        index_change = st.number_input("Annual Index Change (%)", min_value=-10.0, max_value=10.0,
                                       value=annual_index_change)
        if st.button("Calculate for Fixed Linked"):
            adjusted_principal = adjust_principal_for_index(principal, index_change)
            monthly_payment = calculate_fixed_mortgage(adjusted_principal, interest_rate, years)
            schedule = create_amortization_schedule(adjusted_principal, interest_rate, years, mortgage_type)
            st.write(f"Monthly Payment: ₪{monthly_payment:,.2f}")
            st.dataframe(schedule)
            plot = plot_amortization_schedule(schedule)
            st.pyplot(plot)

    elif mortgage_type == "Variable Linked":
        variable_years = st.number_input("Adjustment Period (Years)", min_value=1, max_value=years, value=5)
        initial_rate = st.number_input("Initial Annual Interest Rate (%)", min_value=0.1, max_value=20.0, value=3.5)
        rate_adjustment = st.number_input("Rate Adjustment (%)", min_value=-5.0, max_value=5.0, value=0.5)
        index_change = st.number_input("Annual Index Change (%)", min_value=-10.0, max_value=10.0,
                                       value=annual_index_change)

        if st.button("Calculate Mortgage"):
            schedule = create_amortization_schedule(principal, initial_rate, years, mortgage_type, variable_years,
                                                    rate_adjustment, index_change)
            st.dataframe(schedule)
            plot = plot_amortization_schedule(schedule)
            st.pyplot(plot)


if __name__ == "__main__":
    main()
