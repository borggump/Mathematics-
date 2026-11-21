def compound_growth(principal=23000, rate1=0.022, rate2=0.028, switch_at=50000, periods=5, iterations=10, deduction=8000, extra_iterations=8):

    amount = principal
    rate_switched = False

    print("=" * 60)
    print("  Compound Growth Calculator (Variable Rate)")
    print("=" * 60)
    print(f"  Starting Amount      : ${principal:>12,.2f}")
    print(f"  Rate below ${switch_at:,.0f}  : {rate1*100:.1f}%  (growth/cycle: {rate1*periods*100:.1f}%)")
    print(f"  Rate above ${switch_at:,.0f}  : {rate2*100:.1f}%  (growth/cycle: {rate2*periods*100:.1f}%)")
    print(f"  Periods per cycle    : {periods}")
    print("=" * 60)
    print(f"  {'Cycle':<8} {'Rate':>6}  {'Interest Earned':>15}  {'Total Amount':>15}")
    print(f"  {'-'*8} {'-'*6}  {'-'*15}  {'-'*15}")
    print(f"  {'Start':<8} {'':>6}  {'':>15}  ${amount:>14,.2f}")

    # --- Phase 1: original 10 iterations ---
    for i in range(1, iterations + 1):
        if amount >= switch_at and not rate_switched:
            rate_switched = True
            print(f"  >>> Balance hit ${amount:,.2f} -- rate now switches to {rate2*100:.1f}%")

        rate = rate2 if rate_switched else rate1
        interest = amount * rate * periods
        amount = amount + interest
        print(f"  {i:<8} {rate*100:.1f}%   ${interest:>14,.2f}  ${amount:>14,.2f}")

    # --- Deduction ---
    print()
    print(f"  *** Deducting ${deduction:,.2f} from ${amount:,.2f} ***")
    amount -= deduction
    print(f"  *** Balance after deduction: ${amount:,.2f} ***")
    print()

    # --- Phase 2: 8 more iterations ---
    print(f"  {'Cycle':<8} {'Rate':>6}  {'Interest Earned':>15}  {'Total Amount':>15}")
    print(f"  {'-'*8} {'-'*6}  {'-'*15}  {'-'*15}")

    for i in range(iterations + 1, iterations + extra_iterations + 1):
        if amount >= switch_at and not rate_switched:
            rate_switched = True
            print(f"  >>> Balance hit ${amount:,.2f} -- rate now switches to {rate2*100:.1f}%")

        rate = rate2 if rate_switched else rate1
        interest = amount * rate * periods
        amount = amount + interest
        print(f"  {i:<8} {rate*100:.1f}%   ${interest:>14,.2f}  ${amount:>14,.2f}")

    print("=" * 60)
    print(f"  Final Total after {iterations + extra_iterations} cycles : ${amount:,.2f}")
    print(f"  Total Growth from start          : ${amount - principal:,.2f}  ({((amount / principal) - 1) * 100:.1f}%)")
    print("=" * 60)


if __name__ == "__main__":
    compound_growth()
