import numpy as np
from datetime import datetime
import os
import psutil
import gc

class SegmentedSieve:
    def __init__(self, segment_size=10**6):
        self.segment_size = segment_size
        self.small_primes = self._get_small_primes(int(np.sqrt(segment_size)) + 1)
    
    def _get_small_primes(self, limit):
        """Generate initial small primes using basic sieve."""
        if limit < 2:
            return []
        sieve = np.ones(limit, dtype=np.bool_)
        sieve[0] = sieve[1] = False
        for i in range(2, int(np.sqrt(limit)) + 1):
            if sieve[i]:
                sieve[i*i::i] = False
        return np.where(sieve)[0]
    
    def segment_sieve(self, start, limit):
        """Sieve a segment of odd numbers."""
        # Only work with odd numbers in the segment
        segment_start = (start // 2) * 2 + 1
        segment = np.ones(self.segment_size // 2, dtype=np.bool_)
        
        # Apply small primes to the segment
        for prime in self.small_primes[1:]:  # Skip 2 as we only store odd numbers
            # Find first odd multiple of prime in segment
            first_multiple = max(prime * prime, ((segment_start + prime - 1) // prime) * prime)
            if first_multiple % 2 == 0:
                first_multiple += prime
            
            # Calculate index in segment array and mark multiples
            first_index = (first_multiple - segment_start) // 2
            if first_index < len(segment):
                segment[first_index::prime] = False
        
        # Convert boolean mask to prime numbers
        primes = np.where(segment)[0] * 2 + segment_start
        return primes[primes < limit]

def calculate_and_save_prime_gaps(output_dir="prime_gaps", batch_size=10**7, total_primes=10**12):
    """Calculate and save prime gaps using segmented sieve."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize variables
    start_time = datetime.now()
    primes_processed = 0
    batch_number = 0
    last_prime = 2  # First prime
    segment_size = min(batch_size * 20, 10**8)  # Adjust segment size based on batch size
    
    # Initialize sieve
    sieve = SegmentedSieve(segment_size)
    
    # Process checkpoints if they exist
    checkpoint_file = os.path.join(output_dir, 'checkpoint.npy')
    if os.path.exists(checkpoint_file):
        checkpoint = np.load(checkpoint_file, allow_pickle=True).item()
        primes_processed = checkpoint['primes_processed']
        last_prime = checkpoint['last_prime']
        batch_number = checkpoint['batch_number']
        start = last_prime + 1
    else:
        start = 3  # Start from first odd prime
    
    try:
        while primes_processed < total_primes:
            batch_start_time = datetime.now()
            
            # Calculate end of current segment
            end = start + segment_size
            
            # Get primes in current segment
            current_primes = sieve.segment_sieve(start, end)
            
            if len(current_primes) == 0:
                start = end
                continue
            
            # Calculate gaps
            gaps = np.diff(current_primes)
            if last_prime != 2:  # If not first batch
                first_gap = current_primes[0] - last_prime
                gaps = np.insert(gaps, 0, first_gap)
            
            # Save gaps to file
            output_file = os.path.join(output_dir, f'prime_gaps_batch_{batch_number}.npy')
            np.save(output_file, gaps)
            
            # Update progress
            primes_processed += len(gaps)
            last_prime = current_primes[-1]
            start = last_prime + 1
            
            # Save checkpoint
            checkpoint = {
                'batch_number': batch_number,
                'primes_processed': primes_processed,
                'last_prime': last_prime
            }
            np.save(checkpoint_file, checkpoint)
            
            # Print progress
            batch_end_time = datetime.now()
            batch_duration = (batch_end_time - batch_start_time).total_seconds()
            progress = (primes_processed / total_primes) * 100
            
            # Get memory usage
            memory_usage = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # MB
            
            print(f"Batch {batch_number} completed:")
            print(f"Primes processed: {primes_processed:,}")
            print(f"Progress: {progress:.4f}%")
            print(f"Batch duration: {batch_duration:.2f} seconds")
            print(f"Last prime: {last_prime:,}")
            print(f"Memory usage: {memory_usage:.2f} MB")
            print("=" * 50)
            
            batch_number += 1
            
            # Force garbage collection
            gc.collect()
            
    except KeyboardInterrupt:
        print("\nProcess interrupted. Progress has been saved.")
        print(f"Completed up to: {primes_processed:,} primes")
        return
    
    total_duration = (datetime.now() - start_time).total_seconds()
    print(f"\nTotal processing time: {total_duration:.2f} seconds")

def analyze_gaps(output_dir="prime_gaps"):
    """Analyze the saved prime gaps to generate statistics."""
    stats = {
        'min_gap': float('inf'),
        'max_gap': 0,
        'total_gaps': 0,
        'sum_gaps': 0
    }
    
    # Process files in batches to conserve memory
    gap_files = sorted([f for f in os.listdir(output_dir) if f.startswith('prime_gaps_batch_')])
    
    for file in gap_files:
        gaps = np.load(os.path.join(output_dir, file))
        stats['min_gap'] = min(stats['min_gap'], np.min(gaps))
        stats['max_gap'] = max(stats['max_gap'], np.max(gaps))
        stats['total_gaps'] += len(gaps)
        stats['sum_gaps'] += np.sum(gaps)
        del gaps
        gc.collect()
    
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
    # You'll need to install psutil: pip install psutil
    try:
        # Use smaller batch size and adjust based on available memory
        calculate_and_save_prime_gaps(batch_size=10**6)
    except Exception as e:
        print(f"Error occurred: {e}")