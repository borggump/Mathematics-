def compound_growth(principal=23000, rate=0.022, periods=5, iterations=10):
    """
    Starting amount: principal
    Each cycle: new_total = current * (rate * periods) + current
    Which simplifies to: current * (1 + rate * periods)
    """
    amount = principal
    multiplier = 1 + (rate * periods)  # 1 + (0.022 * 5) = 1.11

    print(f"{'='*55}")
    print(f"  Compound Growth Calculator")
    print(f"{'='*55}")
    print(f"  Starting Amount : ${principal:>12,.2f}")
    print(f"  Rate            : {rate:.3f} ({rate*100}%)")
    print(f"  Periods         : {periods}")
    print(f"  Growth per cycle: {rate * periods * 100:.1f}% (rate × periods)")
    print(f"  Multiplier      : {multiplier}")
    print(f"{'='*55}")
    print(f"  {'Cycle':<8} {'Interest Earned':>15} {'Total Amount':>15}")
    print(f"  {'-'*8} {'-'*15} {'-'*15}")
    print(f"  {'Start':<8} {'':>15} ${amount:>14,.2f}")

    for i in range(1, iterations + 1):
        interest = amount * rate * periods
        amount = amount + interest  # same as amount * multiplier
        print(f"  {i:<8} ${interest:>14,.2f} ${amount:>14,.2f}")

    print(f"{'='*55}")
    print(f"  Final Total after {iterations} cycles: ${amount:,.2f}")
    print(f"  Total Growth: ${amount - principal:,.2f} ({((amount/principal)-1)*100:.1f}%)")
    print(f"{'='*55}")

if __name__ == "__main__":
    compound_growth()
