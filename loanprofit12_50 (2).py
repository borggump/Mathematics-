def calculate_investment_loan_scenario(
    loan_amount=30000,
    annual_loan_rate=0.07,
    monthly_investment_rate=0.07,
    monthly_payment=500,
    target_monthly_profit=4000,
    annual_withdrawal_percentage=0.50
):
    """
    Calculate investment growth and loan payoff scenarios with annual withdrawals.
    
    Parameters:
    loan_amount: Initial loan amount
    annual_loan_rate: Annual interest rate on loan (as decimal)
    monthly_investment_rate: Monthly return rate on investment (as decimal)
    monthly_payment: Monthly payment towards loan
    target_monthly_profit: Target monthly profit to reach
    annual_withdrawal_percentage: Percentage to withdraw annually (as decimal)
    """
    
    # Initialize variables
    months = 0
    investment = loan_amount
    remaining_loan = loan_amount
    monthly_loan_rate = annual_loan_rate / 12
    months_to_target = None
    months_to_payoff = None
    total_withdrawals = 0
    
    while remaining_loan > 0:
        months += 1
        
        # Calculate investment growth
        investment_return = investment * monthly_investment_rate
        investment += investment_return
        
        # Calculate loan payment and interest
        loan_interest = remaining_loan * monthly_loan_rate
        principal_payment = monthly_payment - loan_interest
        remaining_loan -= principal_payment
        
        # Annual withdrawal (every 12 months)
        if months % 12 == 0:
            withdrawal_amount = investment * annual_withdrawal_percentage
            investment -= withdrawal_amount
            total_withdrawals += withdrawal_amount
            print(f"\n=== ANNUAL WITHDRAWAL AT MONTH {months} ===")
            print(f"Withdrawal Amount: ${withdrawal_amount:,.2f}")
            print(f"Total Withdrawals to Date: ${total_withdrawals:,.2f}")
            print("=====================================")
        
        # Check if we've reached target monthly profit
        if months_to_target is None and investment_return >= target_monthly_profit:
            months_to_target = months
        
        # Store when loan is fully paid
        if remaining_loan <= 0:
            months_to_payoff = months
            
        # Print monthly status
        print(f"\nMonth {months}:")
        print(f"Investment Value: ${investment:,.2f}")
        print(f"Monthly Return: ${investment_return:,.2f}")
        print(f"Remaining Loan: ${remaining_loan:,.2f}")
        print(f"Loan Interest Paid: ${loan_interest:,.2f}")
        print(f"Principal Paid: ${principal_payment:,.2f}")
        
        # Break if it's taking too long
        if months > 360:  # 30 years
            print("\nScenario exceeds 30 years!")
            break
    
    return months_to_target, months_to_payoff, investment, total_withdrawals

# Run the calculation
print("INVESTMENT AND LOAN ANALYSIS (WITH ANNUAL WITHDRAWALS)")
print("===================================================")
months_to_target, months_to_payoff, final_investment, total_withdrawals = calculate_investment_loan_scenario()

if months_to_target:
    print(f"\nResults:")
    print(f"Months until reaching ${4000:,}/month profit: {months_to_target}")
    years_to_target = months_to_target / 12
    print(f"(That's {years_to_target:.1f} years)")

if months_to_payoff:
    print(f"\nMonths until loan is paid off: {months_to_payoff}")
    years_to_payoff = months_to_payoff / 12
    print(f"(That's {years_to_payoff:.1f} years)")
    print(f"\nFinal investment value: ${final_investment:,.2f}")
    print(f"Total amount withdrawn: ${total_withdrawals:,.2f}")