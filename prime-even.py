import numpy as np
from datetime import datetime
import os

def sieve_of_eratosthenes(limit):
    """Generate primes up to limit using memory-efficient sieve."""
    sieve = np.ones(limit // 2, dtype=np.bool_)  # Only odd numbers
    for i in range(3, int(np.sqrt(limit)) + 1, 2):
        if sieve[i // 2 - 1]:
            sieve[i * i // 2 - 1::i] = False
    return np.nonzero(sieve)[0] * 2 + 3

def calculate_and_save_prime_gaps(batch_size=10**8, total_primes=10**12):
    """
    Calculate and save prime gaps in batches.
    
    Args:
        batch_size: Size of each batch to process
        total_primes: Total number of primes to process (1 trillion)
    """
    output_dir = "prime_gaps"
    os.makedirs(output_dir, exist_ok=True)
    
    start_time = datetime.now()
    batch_number = 0
    last_prime_of_prev_batch = 2  # First prime number
    primes_processed = 0
    
    while primes_processed < total_primes:
        batch_start_time = datetime.now()
        
        # Generate primes for this batch
        if batch_number == 0:
            limit = batch_size
        else:
            # Estimate limit needed for next batch of primes
            limit = int(batch_size * (np.log(batch_size * (batch_number + 1)) + 1))
        
        primes = sieve_of_eratosthenes(limit)
        
        # Calculate gaps
        gaps = np.diff(primes)
        
        # If not first batch, calculate gap between last prime of previous batch
        # and first prime of current batch
        if batch_number > 0:
            first_gap = primes[0] - last_prime_of_prev_batch
            gaps = np.insert(gaps, 0, first_gap)
        
        # Save gaps to file
        output_file = os.path.join(output_dir, f"prime_gaps_batch_{batch_number}.npy")
        np.save(output_file, gaps)
        
        # Update progress
        primes_processed += len(gaps)
        last_prime_of_prev_batch = primes[-1]
        batch_end_time = datetime.now()
        batch_duration = (batch_end_time - batch_start_time).total_seconds()
        
        # Print progress
        progress = (primes_processed / total_primes) * 100
        print(f"Batch {batch_number} completed:")
        print(f"Primes processed: {primes_processed:,}")
        print(f"Progress: {progress:.2f}%")
        print(f"Batch duration: {batch_duration:.2f} seconds")
        print(f"Last prime in batch: {last_prime_of_prev_batch:,}")
        print("=" * 50)
        
        batch_number += 1
        
        # Save checkpoint
        checkpoint = {
            'batch_number': batch_number,
            'primes_processed': primes_processed,
            'last_prime': last_prime_of_prev_batch
        }
        np.save(os.path.join(output_dir, 'checkpoint.npy'), checkpoint)
    
    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()
    print(f"Total processing time: {total_duration:.2f} seconds")

def analyze_gaps(output_dir="prime_gaps"):
    """
    Analyze the saved prime gaps to generate statistics.
    """
    stats = {
        'min_gap': float('inf'),
        'max_gap': 0,
        'total_gaps': 0,
        'sum_gaps': 0
    }
    
    # Get all gap files
    gap_files = [f for f in os.listdir(output_dir) if f.startswith('prime_gaps_batch_')]
    
    for file in sorted(gap_files):
        gaps = np.load(os.path.join(output_dir, file))
        stats['min_gap'] = min(stats['min_gap'], np.min(gaps))
        stats['max_gap'] = max(stats['max_gap'], np.max(gaps))
        stats['total_gaps'] += len(gaps)
        stats['sum_gaps'] += np.sum(gaps)
    
    stats['average_gap'] = stats['sum_gaps'] / stats['total_gaps']
    
    # Save statistics
    with open(os.path.join(output_dir, 'gap_statistics.txt'), 'w') as f:
        f.write("Prime Gaps Statistics:\n")
        f.write(f"Total gaps analyzed: {stats['total_gaps']:,}\n")
        f.write(f"Minimum gap: {stats['min_gap']}\n")
        f.write(f"Maximum gap: {stats['max_gap']}\n")
        f.write(f"Average gap: {stats['average_gap']:.2f}\n")
    
    return stats

if __name__ == "__main__":
    # Set batch size based on available memory
    BATCH_SIZE = 10**8  # Adjust this based on your system's memory
    
    try:
        # Check for existing checkpoint
        if os.path.exists('prime_gaps/checkpoint.npy'):
            print("Resuming from checkpoint...")
        
        calculate_and_save_prime_gaps(batch_size=BATCH_SIZE)
        stats = analyze_gaps()
        print("\nAnalysis complete! Check gap_statistics.txt for results.")
        
    except KeyboardInterrupt:
        print("\nProcess interrupted. Progress has been saved.")
        print("You can resume from the last checkpoint later.")