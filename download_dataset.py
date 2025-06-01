#!/usr/bin/env python3
"""
Download and examine the Python programming questions dataset from Kaggle.
"""

import kagglehub
import os
import pandas as pd
import json

def download_and_examine_dataset():
    """Download the dataset and examine its structure."""
    print("🔄 Downloading Python programming questions dataset from Kaggle...")
    
    # Download latest version
    path = kagglehub.dataset_download("bhaveshmittal/python-programming-questions-dataset")
    
    print(f"📁 Path to dataset files: {path}")
    
    # List all files in the dataset
    print("\n📋 Files in dataset:")
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            print(f"  - {file_path}")
            
            # If it's a CSV file, examine its structure
            if file.endswith('.csv'):
                try:
                    df = pd.read_csv(file_path)
                    print(f"    📊 Shape: {df.shape}")
                    print(f"    📝 Columns: {list(df.columns)}")
                    print(f"    🔍 First few rows:")
                    print(df.head(3).to_string(index=False))
                    print()
                except Exception as e:
                    print(f"    ❌ Error reading CSV: {e}")
            
            # If it's a JSON file, examine its structure
            elif file.endswith('.json'):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    print(f"    📊 Type: {type(data)}")
                    if isinstance(data, list):
                        print(f"    📊 Length: {len(data)}")
                        if data:
                            print(f"    🔍 First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'Not a dict'}")
                    elif isinstance(data, dict):
                        print(f"    🔍 Keys: {list(data.keys())}")
                    print()
                except Exception as e:
                    print(f"    ❌ Error reading JSON: {e}")
    
    return path

if __name__ == "__main__":
    dataset_path = download_and_examine_dataset() 