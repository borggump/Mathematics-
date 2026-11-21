principal = 1000
rate = 30 / 100
events = 15

amount = principal
previous_amount = principal

for i in range(1, events + 1):
    amount = amount * (1 + rate)
    cumulative_interest = amount - principal
    period_interest = amount - previous_amount      # Difference between events
    
    print(f"Event {i} -> Amount: {round(amount, 2):>10} | "
          f"Cumulative Interest: {round(cumulative_interest, 2):>10} | "
          f"Period Interest: {round(period_interest, 2):>8}")
    
    previous_amount = amount