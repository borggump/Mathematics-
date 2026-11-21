
import numpy as np
import matplotlib.pyplot as plt

class ThomsonSampling:
    def __init__(self, n_arms):
        self.n_arms = n_arms
        self.alpha = np.ones(n_arms)  # Success count for each arm
        self.beta = np.ones(n_arms)   # Failure count for each arm

    def select_arm(self):
        samples = np.random.beta(self.alpha, self.beta)
        return np.argmax(samples)

    def update(self, chosen_arm, reward):
        if reward == 1:
            self.alpha[chosen_arm] += 1
        else:
            self.beta[chosen_arm] += 1

def run_simulation(n_arms, n_rounds, true_probabilities):
    ts = ThomsonSampling(n_arms)
    rewards = []
    chosen_arms = []

    for _ in range(n_rounds):
        arm = ts.select_arm()
        reward = np.random.random() < true_probabilities[arm]
        ts.update(arm, reward)
        
        rewards.append(reward)
        chosen_arms.append(arm)

    return rewards, chosen_arms

# Example usage
n_arms = 5
n_rounds = 10000
true_probabilities = [0.1, 0.2, 0.3, 0.8, 0.5]

rewards, chosen_arms = run_simulation(n_arms, n_rounds, true_probabilities)

# Calculate cumulative average reward
cumulative_average = np.cumsum(rewards) / (np.arange(n_rounds) + 1)

# Plotting
plt.figure(figsize=(12, 6))
plt.plot(cumulative_average)
plt.title('Thomson Sampling Performance')
plt.xlabel('Rounds')
plt.ylabel('Cumulative Average Reward')
plt.ylim(0, 1)
plt.show()

print(f"Total reward: {sum(rewards)}")
print(f"Average reward: {sum(rewards) / n_rounds}")
print("Arm selection frequency:")
for i in range(n_arms):
    print(f"Arm {i}: {chosen_arms.count(i) / n_rounds:.2%}")