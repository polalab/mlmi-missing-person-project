import matplotlib.lines as mlines
import seaborn as sns
import matplotlib.pyplot as plt


def create_professional_boxplot(df, columns, title, subtitle, inp):

    df_melted = df[columns].melt(var_name='Metric', value_name='Value')

    df_melted['Metric Type'] = df_melted['Metric'].apply(
        lambda x: 'Precision' if 'precision' in x.lower() else 'Recall'
    )

    df_melted['Metric'] = df_melted['Metric'].str.replace('_', ' ').str.title()

    sns.set_theme(style="ticks")
    fig, ax = plt.subplots(figsize=(18, 10))

    palette = {"Precision": "#2c7bb6", "Recall": "#fdae61"}

    sns.boxplot(
        x='Metric',
        y='Value',
        hue='Metric Type',
        data=df_melted,
        palette=palette,
        showmeans=True,
        meanprops={"marker": "D", "markerfacecolor": "white", "markeredgecolor": "black", "markersize": "8"},
        dodge=False,
        ax=ax
    )

    ax.set_ylim(top=ax.get_ylim()[1] * 1.1)  # Increase y-axis limit to make space for text
    ordered_metrics = [tick.get_text() for tick in ax.get_xticklabels()]

    for i, metric in enumerate(ordered_metrics):
        metric_data = df_melted[df_melted['Metric'] == metric]['Value']
        
        mean_val = metric_data.mean()
        std_val = metric_data.std()
        
        annotation_text = f"Mean: {mean_val:.2f}\nStd: {std_val:.2f}"
        
        y_pos = metric_data.max() * 1.02 # Place it slightly above the max value
        
        ax.text(i, y_pos, annotation_text,
                horizontalalignment='center',
                size=23,
                color='black',
                )


    ax.set_xlabel("Metric", fontsize=24, weight='bold', labelpad=15)
    ax.set_ylabel("Score", fontsize=24, weight='bold', labelpad=15)
    plt.xticks(fontsize=30, rotation=15, ha='right') # Rotate for better readability
    plt.yticks(fontsize=30)

    ax.yaxis.grid(True, linestyle='--', which='major', color='lightgrey', alpha=0.7)

    
    handles, _ = ax.get_legend_handles_labels()
    
    mean_handle = mlines.Line2D([], [], color='black', marker='D', linestyle='None',
                              markersize=8, markerfacecolor='white', markeredgecolor='black', label='Mean')
    median_handle = mlines.Line2D([], [], color='black', linestyle='-', linewidth=1)

    combined_handles = handles + [mean_handle, median_handle]
    labels = ['Precision', 'Recall', 'Mean', 'Median']

    ax.legend(handles=combined_handles, labels=labels,
              title='Legend', fontsize=16, title_fontsize=14,
              loc='upper left', bbox_to_anchor=(1.01, 1.0)) 

    sns.despine(trim=True, left=True)
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    plt.savefig(f"utils/plots2/{inp}_boxplot.svg", bbox_inches='tight')
    plt.show()
