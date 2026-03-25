import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from elevate.summarizer import summarize_employee_comments

print("Testing chunking behaviour with a very long string (~100 comments equivalent)...")
sample_comment = (
    "John is an exceptionally hard worker who always goes above and beyond. "
    "He delivers projects on time and never hesitates to mentor junior developers. "
    "His positive attitude brings the whole team up during stressful sprints. "
) * 100

print(f"Original text length: {len(sample_comment)} characters")

try:
    summary = summarize_employee_comments([sample_comment])
    print("\n--- Final Summary ---")
    print(summary)
    print("---------------------\n")
    print("Success: Chunking and local summarization completed without token limit errors!")
except Exception as e:
    print(f"Test Failed: {e}")
