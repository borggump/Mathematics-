
import math

def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

def to_mersenne(prime):
    return 2**prime - 1

def main():
    input_file = "prime_numbers.txt"
    output_file = "mersenne_numbers.txt"

    try:
        with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
            for line in infile:
                try:
                    num = int(line.strip())
                    if is_prime(num):
                        mersenne = to_mersenne(num)
                        outfile.write(f"{num} -> {mersenne}\n")
                    else:
                        print(f"Warning: {num} is not prime, skipping.")
                except ValueError:
                    print(f"Warning: Invalid input '{line.strip()}', skipping.")

        print(f"Conversion complete. Results written to {output_file}")
    except IOError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 
