import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess
import pandas as pd

def load_csv(file_path):
    """Load CSV file and return a formatted string."""
    try:
        df = pd.read_csv(file_path)
        return df.to_string(index=False)
    except Exception as e:
        return f"Error loading {file_path}: {e}"

def execute_trades():
    """Execute the main.py script and display the output in the text area."""
    try:
        result = subprocess.run(['python3', 'main.py'], capture_output=True, text=True)
        output_text.delete(1.0, tk.END)  # Clear previous output
        output_text.insert(tk.END, result.stdout)  # Show script output
        if result.stderr:
            messagebox.showerror("Error", result.stderr)
    except Exception as e:
        messagebox.showerror("Execution Error", str(e))

# Initialize the main window
root = tk.Tk()
root.title("Interactive Brokers Equities Interface")

# Create a frame for the CSV displays and execute button
frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

# Display for longs.csv
tk.Label(frame, text="Longs CSV:").grid(row=0, column=0, padx=5, pady=5)
longs_text = scrolledtext.ScrolledText(frame, width=50, height=10)
longs_text.grid(row=1, column=0, padx=5, pady=5)
longs_text.insert(tk.END, load_csv('longs.csv'))  # Load longs.csv content

# Display for shorts.csv
tk.Label(frame, text="Shorts CSV:").grid(row=0, column=1, padx=5, pady=5)
shorts_text = scrolledtext.ScrolledText(frame, width=50, height=10)
shorts_text.grid(row=1, column=1, padx=5, pady=5)
shorts_text.insert(tk.END, load_csv('shorts.csv'))  # Load shorts.csv content

# Button to execute trades
execute_button = tk.Button(frame, text="Execute Trades", command=execute_trades)
execute_button.grid(row=2, column=0, columnspan=2, pady=10)

# Display for output log
tk.Label(frame, text="Output Log:").grid(row=3, column=0, columnspan=2)
output_text = scrolledtext.ScrolledText(frame, width=105, height=15)
output_text.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

# Start the main loop
root.mainloop()