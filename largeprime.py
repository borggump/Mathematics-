
import random
import math

def miller_rabin(n, k=5):
    if n < 2:
        return False
    for p in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]:
        if n % p == 0:
            return n == p
    s, d = 0, n - 1
    while d % 2 == 0:
        s, d = s + 1, d // 2
    for _ in range(k):
        a = random.randrange(2, n - 1)
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True

def generate_large_prime(bits):
    while True:
        n = random.getrandbits(bits)
        if n % 2 == 0:
            n += 1
        if miller_rabin(n):
            return n

def find_and_store_primes(num_primes, bits, filename):
    with open(filename, 'w') as f:
        for i in range(num_primes):
            prime = generate_large_prime(bits)
            f.write(f"Prime {i+1}: {prime}\n")
            print(f"Found and stored prime {i+1}")

if __name__ == "__main__":
    num_primes = 5
    bits = 1024
    filename = "large_primes.txt"
    find_and_store_primes(num_primes, bits, filename)
    print(f"Finished. {num_primes} large primes have been stored in {filename}") 
