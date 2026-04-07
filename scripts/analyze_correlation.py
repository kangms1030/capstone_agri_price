import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os

def analyze_correlation():
    data_path = 'data/final_dataset/chronos2_preprocessed_v2.csv'
    output_dir = 'data/visuals'
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(data_path):
        print(f"Data not found at {data_path}")
        return

    print("Loading dataset...")
    df = pd.read_csv(data_path)
    
    # Select numeric columns for correlation (excluding date and price/target if we want full)
    # The user wants "각 item_id 별로 피어슨 상관관계를 조사한 후 전체 파일에 대해 평균을 내어 시각화"
    # This usually means feature vs feature or feature vs target.
    # We'll calculate the full correlation matrix per item.
    
    exclude_cols = ['date'] # item_id will be grouped
    numeric_df = df.select_dtypes(include=[np.number]).drop(columns=exclude_cols, errors='ignore')
    numeric_df['item_id'] = df['item_id']
    
    print(f"Calculating correlations for {df['item_id'].nunique()} items...")
    all_corrs = []
    
    for item_id, group in numeric_df.groupby('item_id'):
        # Drop item_id from group before corr
        corr = group.drop(columns=['item_id']).corr()
        all_corrs.append(corr)
    
    if not all_corrs:
        print("No numeric data to correlate.")
        return

    print("Averaging correlations...")
    # Stack and mean
    avg_corr = pd.concat(all_corrs).groupby(level=0).mean()
    
    # Ensure index and columns are identical and in the same order
    # This is crucial for the diagonal to be clear
    all_features = sorted(list(set(avg_corr.index) | set(avg_corr.columns)))
    
    # Prioritize 'target' and then 'price' if they exist
    priority_features = []
    if 'target' in all_features:
        priority_features.append('target')
        all_features.remove('target')
    if 'price' in all_features:
        priority_features.append('price')
        all_features.remove('price')
    
    final_order = priority_features + all_features
    avg_corr = avg_corr.reindex(index=final_order, columns=final_order)

    # Visualization
    print("Generating heatmap...")
    plt.figure(figsize=(20, 16))
    
    # Use a clean, professional theme
    sns.set_theme(style="white")
    
    # Generate a mask for the upper triangle
    mask = np.triu(np.ones_like(avg_corr, dtype=bool))
    
    # Custom diverging colormap
    cmap = sns.diverging_palette(230, 20, as_cmap=True)

    sns.heatmap(avg_corr, 
                mask=mask, 
                cmap=cmap, 
                vmax=1.0, 
                vmin=-1.0, 
                center=0,
                annot=True, 
                fmt=".2f",
                square=True, 
                linewidths=.5, 
                cbar_kws={"shrink": .5},
                annot_kws={"size": 8})

    plt.title('Average Pearson Correlation Matrix across all Items', fontsize=20, pad=20)
    plt.tight_layout()
    
    output_path = os.path.join(output_dir, 'average_correlation_heatmap.png')
    plt.savefig(output_path, dpi=300)
    print(f"Heatmap saved to {output_path}")

if __name__ == "__main__":
    analyze_correlation()
