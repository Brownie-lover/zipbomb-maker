import os
import time
import zipfile

pattern = "🔥"
pattern_bytes = pattern.encode("utf-8")
pattern_len = len(pattern_bytes)

def format_size(size_in_bytes):
    """Helper function to format bytes into readable units."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size_in_bytes < 1024.0 or unit == 'PB':
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0

def format_time(seconds):
    """Helper function to format seconds into a clean MM:SS or HH:MM:SS string."""
    if seconds < 0 or seconds == float('inf'):
        return "Calculating..."
    mins, secs = divmod(int(seconds), 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours}h {mins}m {secs}s"
    elif mins > 0:
        return f"{mins}m {secs}s"
    else:
        return f"{secs}s"

def parse_size_input(user_input):
    """Parses inputs like '100gb', '500mb', or raw numbers as GB."""
    user_input = user_input.strip().lower()
    if not user_input:
        return 0
    
    multiplier = 1024**3  # Default unit is GB if just a number is typed
    
    if user_input.endswith('tb'):
        multiplier = 1024**4
        user_input = user_input[:-2]
    elif user_input.endswith('gb'):
        multiplier = 1024**3
        user_input = user_input[:-2]
    elif user_input.endswith('mb'):
        multiplier = 1024**2
        user_input = user_input[:-2]
    elif user_input.endswith('kb'):
        multiplier = 1024
        user_input = user_input[:-2]
    elif user_input.endswith('b'):
        multiplier = 1
        user_input = user_input[:-1]
        
    try:
        return int(float(user_input.strip()) * multiplier)
    except ValueError:
        return 0

# Inputs
file_count = int(input("Number of text files (recommended: 1 to 3): "))

while True:
    size_str = input("Target Total Uncompressed Size (e.g., 50 or 100gb, 500mb): ")
    total_uncomp = parse_size_input(size_str)
    
    if total_uncomp > 0:
        break
    print("Invalid size format. Please try again (e.g., 10, 50gb, 500mb).")

# Distribute target characters evenly across the files
single_file_target_bytes = total_uncomp // file_count
characters = single_file_target_bytes // pattern_len
total_uncomp = characters * pattern_len * file_count

est_total_comp = max(total_uncomp / 1000, 1024)
expansion_ratio = total_uncomp / est_total_comp if est_total_comp > 0 else 0

print("\n" + "─"*50)
print("  📊 TARGET SIZE RELATIONSHIP PREVIEW")
print("─"*50)
print(f"  • File Count        : {file_count}")
print(f"  • Total Uncompressed: {format_size(total_uncomp)}")
print(f"  • Est. Compressed   : ~{format_size(est_total_comp)}")
print(f"  • Expansion Ratio   : ~{expansion_ratio:,.0f}x larger when unpacked!")
print("─"*50)

confirm = input("Proceed with creating this archive? (y/n): ").strip().lower()
if confirm not in ['y', 'yes']:
    print("Cancelled.")
    exit()

zip_filename = "massive_files.zip"
grand_total_chars = file_count * characters

print(f"\n[+] Creating archive with {file_count} file(s) using optimized high-speed engine...")

start_time = time.time()

with zipfile.ZipFile(
    zip_filename,
    "w",
    compression=zipfile.ZIP_DEFLATED,
    compresslevel=9,
    allowZip64=True
) as z:

    chunk_char_count = 5_000_000  # 500 million chars per chunk (~500MB)
    chunk_bytes = pattern_bytes * chunk_char_count
    total_written_chars = 0
    chunk_counter = 0
    current_compressed = 0

    for i in range(file_count):
        filename = f"file_{i+1}.txt"
        
        with z.open(filename, "w", force_zip64=True) as f:
            full_blocks = characters // chunk_char_count
            remainder_chars = characters % chunk_char_count

            for _ in range(full_blocks):
                f.write(chunk_bytes)
                total_written_chars += chunk_char_count
                chunk_counter += 1
                
                # OPTIMIZATION: Only flush and query disk size every 10 chunks 
                # to completely eliminate the halfway slowdown bottleneck.
                if chunk_counter % 10 == 0:
                    z.fp.flush()
                    current_compressed = os.path.getsize(zip_filename)
                
                if total_written_chars > 0:
                    # If we haven't queried disk recently, estimate smoothly based on progress
                    if current_compressed == 0:
                        current_compressed = max(total_written_chars * pattern_len / 1000, 1024)
                    real_est_compressed = (current_compressed / total_written_chars) * grand_total_chars
                else:
                    real_est_compressed = 0
                
                # Time Estimation Math
                elapsed_so_far = time.time() - start_time
                fraction_done = total_written_chars / grand_total_chars
                
                if fraction_done > 0:
                    estimated_total_time = elapsed_so_far / fraction_done
                    remaining_time = estimated_total_time - elapsed_so_far
                else:
                    remaining_time = 0

                percent = fraction_done * 100
                bar_length = 12
                filled_length = int(bar_length * total_written_chars // grand_total_chars)
                bar = '█' * filled_length + '-' * (bar_length - filled_length)
                
                # Display status line
                print(
                    f"\r[{bar}] {percent:5.1f}% | "
                    f"ETA: {format_time(remaining_time)} | "
                    f"Uncomp: {format_size(total_written_chars * pattern_len)}/{format_size(total_uncomp)} | "
                    f"Comp: {format_size(current_compressed if current_compressed else 1024)}/~{format_size(real_est_compressed)}",
                    end=""
                )

            if remainder_chars:
                f.write(pattern_bytes * remainder_chars)
                total_written_chars += remainder_chars

# Final flush and size check
z.fp.flush()
elapsed_time = time.time() - start_time
final_compressed_bytes = os.path.getsize(zip_filename)

print("\n\n" + "="*55)
print("                 COMPRESSION COMPLETE")
print("="*55)
print(f"Archive Name       : {zip_filename}")
print(f"Time Elapsed       : {format_time(elapsed_time)}")
print(f"Final Uncompressed : {format_size(total_uncomp)}")
print(f"Final Compressed   : {format_size(final_compressed_bytes)}")
if total_uncomp > 0:
    ratio = (1 - (final_compressed_bytes / total_uncomp)) * 100
    actual_expansion = total_uncomp / max(final_compressed_bytes, 1)
    print(f"Space Saved        : {ratio:.2f}%")
    print(f"Actual Expansion   : {actual_expansion:,.0f}x larger when unpacked!")
print("="*55)
