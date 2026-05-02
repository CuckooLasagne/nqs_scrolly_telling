#packages
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

import pandas as pd
import plotly.graph_objects as go


#Timeseries of % meeting NQS
def plot_nqs_performance(df, show_yoy=True):
    """
    Generates a Plotly visualization of NQS performance over time.
    
    Args:
        df (pd.DataFrame): The source dataframe containing 'Source_Quarter', 
                           'Overall Rating', and 'Service Sub Type'.
        show_yoy (bool): Whether to display the YoY growth bar charts for the 'Combined' group.
    """
    
    # 1. Internal Helper for Calculations
    meeting_or_above = ['Meeting NQS', 'Exceeding NQS', 'Excellent']

    def get_stats(data_subset):
        total_count = data_subset.groupby('Source_Quarter').size()
        meeting_count = data_subset[data_subset['Overall Rating'].isin(meeting_or_above)].groupby('Source_Quarter').size()
        proportion = (meeting_count / total_count).fillna(0) * 100

        res = pd.DataFrame({
            'proportion': proportion,
            'count': total_count
        }).sort_index()

        # Calculate YoY Growth (4 quarters back)
        res['yoy_growth'] = res['proportion'].diff(4)
        res['yoy_growth_str'] = res['yoy_growth'].apply(
            lambda x: f"{x:+.1f}%" if pd.notnull(x) else ""
        )
        return res

    # 2. Define Groups
    groups_data = [
        ('LDC', df[df['Service Sub Type'] == 'LDC'], '#1f77b4', 2),
        ('PSK', df[df['Service Sub Type'] == 'PSK'], '#ff7f0e', 2),
        ('Combined', df[df['Service Sub Type'].isin(['LDC', 'PSK'])], 'black', 4)
    ]

    fig = go.Figure()

    # 3. Plotting Logic
    for name, data, color, width in groups_data:
        stats = get_stats(data)
        if stats.empty: 
            continue

        # --- OPTIONAL BARS (Combined Only) ---
        if name == 'Combined' and show_yoy:
            yoy_data = stats[stats['yoy_growth_str'] != ""]
            fig.add_trace(go.Bar(
                x=yoy_data.index,
                y=yoy_data['yoy_growth'],
                name='YoY Growth',
                marker_color='rgba(150, 150, 150, 0.4)',
                text=yoy_data['yoy_growth_str'],
                textposition='outside',
                textfont=dict(size=14, color='black', family="Arial Black"),
                hovertemplate='%{text}'
            ))

        # --- LINE TRACES ---
        fig.add_trace(go.Scatter(
            x=stats.index,
            y=stats['proportion'],
            mode='lines',
            name=name,
            line=dict(
                color=color, 
                width=width, 
                dash='dash' if name == 'Combined' else 'solid'
            ),
            hovertemplate='%{y:.1f}%'
        ))

        # --- ANNOTATIONS ---
        last_row = stats.iloc[-1]
        current_yshift = -10 if name == 'LDC' else 0

        fig.add_annotation(
            x=stats.index[-1],
            y=last_row['proportion'],
            text=f"<b>{name}</b>: {last_row['proportion']:.1f}% (n={last_row['count']:,})",
            showarrow=False,
            xanchor="left",
            xshift=10,
            yshift=current_yshift,
            font=dict(color=color, size=12 if name == 'Combined' else 11),
            bgcolor="rgba(255, 255, 255, 0.8)"
        )

    # 4. Layout
    fig.update_layout(
        title=f"<b>Proportion of services meeting or exceeding the NQS</b><br>Victoria",
        template="plotly_white",
        showlegend=False,
        xaxis_title="Reporting Quarter",
        yaxis_title="Percentage (%)",
        yaxis=dict(range=[-10, 115], ticksuffix="%"),
        margin=dict(r=200, t=100),
        hovermode="x unified",
        barmode='group',
        uniformtext=dict(mode='hide', minsize=12),
    )

    return fig

#Rating distribution by provider type
def plot_rating_distribution_1(df, highlight_rating=None):
    """
    Generates a single diverging bar chart for NQS ratings by Provider Management Type
    filtered for LDC and PSK services only.
    """
    # 1. Filter for latest data and relevant Service Sub Types
    latest_q = df['Source_Quarter'].max()
    df_filtered = df[
        (df['Source_Quarter'] == latest_q) & 
        (df['Service Sub Type'].isin(["PSK", "LDC"]))
    ].copy()

    rating_order = [
        'Significant Improvement Required', 'Working Towards NQS', 
        'Meeting NQS', 'Exceeding NQS', 'Excellent'
    ]
    positive_ratings = ['Meeting NQS', 'Exceeding NQS', 'Excellent']

    # 2. Setup Colors
    base_colors = {
        'Significant Improvement Required': '#D73027', 
        'Working Towards NQS': '#FDAE61', 
        'Meeting NQS': '#FFFFBF', 
        'Exceeding NQS': '#A6D96A', 
        'Excellent': '#1A9850'
    }

    if highlight_rating in rating_order:
        color_map = {r: '#E8E8E8' if r != highlight_rating else base_colors[r] for r in rating_order}
    else:
        color_map = base_colors

    # 3. Calculate Proportions (Single Group)
    ct = pd.crosstab(df_filtered['Provider Management Type'], df_filtered['Overall Rating'], normalize='index')
    
    # Ensure all ratings exist in columns
    for rating in rating_order:
        if rating not in ct.columns:
            ct[rating] = 0
    ct = ct[rating_order]

    # 4. Diverging Logic
    neg_cols = [c for c in rating_order if c not in positive_ratings]
    current_offsets = -ct[neg_cols].sum(axis=1)

    fig = go.Figure()

    for rating in rating_order:
        widths = ct[rating]
        
        # Hide labels for greyed-out bars or small segments
        is_highlighted = (highlight_rating is None or rating == highlight_rating)
        text_labels = [f'{w:.0%}' if (w > 0.05 and is_highlighted) else '' for w in widths]

        fig.add_trace(go.Bar(
            y=ct.index,
            x=widths,
            name=rating,
            orientation='h',
            base=current_offsets,
            marker=dict(
                color=color_map[rating], 
                line=dict(color='white', width=0.5)
            ),
            text=text_labels,
            textposition='inside',
            insidetextanchor='middle',
            hovertemplate=f'<b>{rating}</b><br>%{{y}}<br>Proportion: %{{x:.1%}}<extra></extra>'
        ))
        current_offsets += widths

    # 5. Layout
    subtitle = f"Victoria, Q4 2025 | LDC & PSK Services"
    if highlight_rating:
        subtitle = f"Focus: <b>{highlight_rating}</b> | {subtitle}"

    fig.update_layout(
        title=dict(text=f"<b>NQS Rating Distribution by Provider Type</b><br><sup>{subtitle}</sup>", x=0.5),
        barmode='relative',
        template='plotly_white',
        height=600,
        margin=dict(l=220, r=40, t=100, b=100),
        xaxis=dict(
            title="Proportion",
            tickformat='.0%',
            range=[-0.5, 1], # Adjusted to give space for negative side
            zeroline=True,
            zerolinewidth=1.5,
            zerolinecolor='black'
        ),
        yaxis=dict(title="Management Type"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.5, xanchor="center", x=0.5)
    )

    fig.add_vline(x=0, line_width=1.5, line_dash="dash", line_color="black")

    return fig

#NQS by SEIFA
def plot_seifa_distribution(df, highlight_rating=None):
    """
    Plots NQS distribution across SEIFA deciles with an optional focus highlight.
    
    Args:
        df: The source dataframe.
        highlight_rating: String matching a rating (e.g., 'Working Towards NQS'). 
                          If provided, all other ratings are greyed out.
    """
    # 1. Filter for Victoria and latest quarter
    latest_q = df['Source_Quarter'].max()
    df_vic = df[
        (df['Source_Quarter'] == latest_q) & 
        (df['Managing Jurisdiction'] == 'VIC')
    ].copy()

    # 2. Data Cleaning
    df_vic['SEIFA'] = pd.to_numeric(df_vic['SEIFA'], errors='coerce')
    df_vic = df_vic.dropna(subset=['SEIFA', 'Overall Rating'])
    df_vic['SEIFA'] = df_vic['SEIFA'].astype(int)

    rating_order = [
        'Significant Improvement Required', 'Working Towards NQS', 
        'Meeting NQS', 'Exceeding NQS', 'Excellent'
    ]
    positive_ratings = ['Meeting NQS', 'Exceeding NQS', 'Excellent']

    # 3. Handle Color Logic
    base_colors = {
        'Significant Improvement Required': '#D73027',
        'Working Towards NQS': '#FDAE61',
        'Meeting NQS': '#FFFFBF',
        'Exceeding NQS': '#A6D96A',
        'Excellent': '#1A9850'
    }

    if highlight_rating in rating_order:
        # Grey out everything except the target
        color_map = {r: '#E8E8E8' if r != highlight_rating else base_colors[r] for r in rating_order}
    else:
        color_map = base_colors

    # 4. Proportions and Diverging Logic
    ct = pd.crosstab(df_vic['SEIFA'], df_vic['Overall Rating'], normalize='index')
    for rating in rating_order:
        if rating not in ct.columns:
            ct[rating] = 0
    ct = ct[rating_order]

    neg_cols = [c for c in rating_order if c not in positive_ratings]
    current_offsets = -ct[neg_cols].sum(axis=1)

    fig = go.Figure()

    for rating in rating_order:
        widths = ct[rating]
        
        # Hide labels for greyed-out bars to keep focus clean
        is_highlighted = (highlight_rating is None or rating == highlight_rating)
        text_labels = [f'{w:.0%}' if (w > 0.04 and is_highlighted) else '' for w in widths]

        fig.add_trace(go.Bar(
            y=ct.index,
            x=widths,
            name=rating,
            orientation='h',
            base=current_offsets,
            marker=dict(
                color=color_map[rating],
                line=dict(color='white', width=0.5)
            ),
            text=text_labels,
            textposition='inside',
            insidetextanchor='middle',
            hovertemplate='Decile %{y}<br>%{name}: %{x:.1%}<extra></extra>'
        ))
        current_offsets += widths

    # 5. Styling
    subtitle = f"Victoria, Q4 2025 (1 = Most Disadvantaged)"
    if highlight_rating:
        subtitle = f"Focus: <b>{highlight_rating}</b> | {subtitle}"

    fig.update_layout(
        title=dict(text=f'<b>NQS Rating Distribution by SEIFA Decile</b><br><sup>{subtitle}</sup>', x=0.5),
        barmode='relative',
        xaxis=dict(title='Proportion', tickformat='.0%', range=[-0.2, 1], zeroline=True, zerolinewidth=2, zerolinecolor='black'),
        yaxis=dict(title='SEIFA Decile (Advantage →)', tickmode='linear', dtick=1),
        template='plotly_white',
        height=600,
        margin=dict(t=100, b=100),
        legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center")
    )
    fig.add_vline(x=0, line_width=1.5, line_dash="dash", line_color="black")

    return fig


#Service counts jusrisdiction
def plot_service_counts_timeseries(df, filter_ldc_psk=False):
    """
    Plots service counts by jurisdiction and Victoria's YoY growth.
    
    Args:
        df: The source dataframe.
        filter_ldc_psk (bool): If True, filters data for LDC and PSK services only.
    """
    # 1. Prepare Data
    working_df = df.copy()
    
    if filter_ldc_psk:
        working_df = working_df[working_df['Service Sub Type'].isin(['LDC', 'PSK'])]
        type_label = " (LDC & PSK Only)"
    else:
        type_label = " (All Service Types)"

    ts_df = working_df.groupby(['Source_Quarter', 'Managing Jurisdiction']).size().reset_index(name='Count')
    ts_df = ts_df.sort_values('Source_Quarter')

    # Calculate YoY Growth for Victoria specifically
    vic_df = ts_df[ts_df['Managing Jurisdiction'] == 'VIC'].copy()
    vic_df['Prev_Year_Count'] = vic_df['Count'].shift(4)
    vic_df['YoY_Growth'] = ((vic_df['Count'] - vic_df['Prev_Year_Count']) / vic_df['Prev_Year_Count']) * 100

    # 2. Create Subplots
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=(
            f"<b>Service counts by quarter and state</b>{type_label}", 
            f"<b>Victoria Year-on-Year growth (%)</b>{type_label}"
        ),
        row_heights=[0.3, 0.7]
    )

    fig.update_annotations(patch=dict(x=0, xanchor='left'))

    # 3. Add Jurisdiction Lines (Top Plot)
    for jurisdiction in ts_df['Managing Jurisdiction'].unique():
        state_df = ts_df[ts_df['Managing Jurisdiction'] == jurisdiction]
        if state_df.empty: continue
        
        last_row = state_df.iloc[-1]
        is_vic = (jurisdiction == 'VIC')
        color = '#1f77b4' if is_vic else 'lightgrey'
        width = 4 if is_vic else 1.5

        fig.add_trace(
            go.Scatter(
                x=state_df['Source_Quarter'],
                y=state_df['Count'],
                name=jurisdiction,
                line=dict(color=color, width=width),
                mode='lines',
                hovertemplate='%{y}'
            ),
            row=1, col=1
        )

        # End-of-line annotations
        val = last_row['Count']
        formatted_val = f"{val/1000:.1f}k" if val >= 1000 else str(val)
        fig.add_annotation(
            x=last_row['Source_Quarter'],
            y=last_row['Count'],
            text=f"<b>{jurisdiction}</b>: {formatted_val}",
            showarrow=False,
            xanchor="left",
            xshift=10,
            font=dict(color=color, size=13 if is_vic else 10),
            row=1, col=1
        )

    # 4. Add YoY Growth Bars for VIC (Bottom Plot)
    growth_data = vic_df.dropna(subset=['YoY_Growth'])
    
    if not growth_data.empty:
        fig.add_trace(
            go.Bar(
                x=growth_data['Source_Quarter'],
                y=growth_data['YoY_Growth'],
                marker_color='#1f77b4',
                text=growth_data['YoY_Growth'].apply(lambda x: f"{x:.1f}%"),
                textposition='outside',
                name='VIC YoY %',
                hovertemplate='%{y:.2f}%'
            ),
            row=2, col=1
        )
        
        # Adjust Y-axis to fit text labels above bars
        max_growth = growth_data['YoY_Growth'].max()
        fig.update_yaxes(range=[0, max_growth * 1.3], row=2, col=1)

    # 5. Final Layout Polish
    fig.update_layout(
        template="plotly_white",
        showlegend=False,
        margin=dict(r=150, t=100, b=50),
        hovermode="x unified"
    )

    # 6. Policy Event Lines
    # Converting to quarter strings to match the categorical X-axis
    # Note: If your X-axis is datetime, the timestamp * 1000 method works. 
    # If it is string-based (e.g., "2023 Q1"), use the string directly.
    
    policy_lines = [
        dict(x=pd.to_datetime("2018-07-01").timestamp() * 1000, text="CCS introduced", color="red"),
        dict(x=pd.to_datetime("2022-06-01").timestamp() * 1000, text="BSBL announced", color="green")
    ]

    for line in policy_lines:
        fig.add_vline(
            x=line['x'],
            line_width=2,
            line_dash="dash",
            line_color=line['color'],
            annotation_text=line['text'],
            annotation_position="top left",
            annotation_font_color=line['color'],
            row=2, col=1
        )

    fig.update_xaxes(matches='x')
    return fig

#Stacked area by management type
def plot_management_type_stack(df):
    """
    Creates a stacked area chart showing the count and proportion of services 
     by Management Type over time in Victoria (LDC & PSK only).
    """
    # 1. Filter and Prepare Data
    vic_df = df[
        (df['Managing Jurisdiction'] == 'VIC') & 
        (df['Service Sub Type'].isin(["PSK", "LDC"])) &
        (df['Provider Management Type'] != "Other")
    ].copy()

    # Aggregate counts
    ts_data = vic_df.groupby(['Source_Quarter', 'Provider Management Type']).size().reset_index(name='Count')
    ts_data = ts_data.sort_values(['Source_Quarter', 'Provider Management Type'])

    # Calculate Percentages for end-of-line labels
    ts_data['Total_Quarter'] = ts_data.groupby('Source_Quarter')['Count'].transform('sum')
    ts_data['Pct'] = (ts_data['Count'] / ts_data['Total_Quarter']) * 100

    # 2. Setup Figure
    fig = go.Figure()
    mgmt_types = ts_data['Provider Management Type'].unique()
    colors = px.colors.qualitative.Safe

    # Track cumulative height for annotation positioning
    latest_quarter = ts_data['Source_Quarter'].max()
    cumulative_y = 0

    for i, m_type in enumerate(mgmt_types):
        subset = ts_data[ts_data['Provider Management Type'] == m_type]
        if subset.empty: 
            continue

        color = colors[i % len(colors)]
        
        # Add Area Trace
        fig.add_trace(
            go.Scatter(
                x=subset['Source_Quarter'],
                y=subset['Count'],
                name=m_type,
                mode='lines',
                line=dict(width=0.5, color=color),
                stackgroup='one', # This creates the stack
                fillcolor=color,
                hovertemplate=f"<b>{m_type}</b>: %{{y}}<extra></extra>"
            )
        )

        # --- 3. Dynamic Labeling (Count + %) ---
        # Filter for the last quarter
        last_point_df = subset[subset['Source_Quarter'] == latest_quarter]
        
        if not last_point_df.empty:
            # Use .iloc[0] but ensure we extract values clearly
            row_data = last_point_df.iloc[0]
            
            count_val = row_data['Count']
            pct_val = row_data['Pct']
            
            # Center the text in the middle of the specific area segment
            y_center = cumulative_y + (count_val / 2)
            cumulative_y += count_val # Update base for next label

            val_k = f"{count_val/1000:.1f}k" if count_val >= 1000 else f"{count_val}"
            label_text = f"<b>{m_type}</b><br>{val_k} ({pct_val:.1f}%)"

            fig.add_annotation(
                x=latest_quarter,
                y=y_center,
                text=label_text,
                showarrow=False,
                xanchor="left",
                xshift=15,
                font=dict(color=color, size=11),
                align="left"
            )

    # 4. Final Styling
    fig.update_layout(
        title="<b>Service count and proportion by management type</b><br><sup>Victoria | LDC & PSK Services</sup>",
        template='plotly_white',
        hovermode="x unified",
        margin=dict(r=220, t=100, b=50),
        showlegend=False,
        height= 500,
        width = 1000
    )

    fig.update_yaxes(title_text="Total Service Count", showgrid=True, gridcolor='whitesmoke')
    fig.update_xaxes(title_text="Source Quarter", showgrid=False)

    return fig

#Diverging chart
def plot_management_split_comparison(df):
    """
    Creates a dual-plot: 
    1. Diverging bar chart showing the % split between LDC and PSK.
    2. Heatmap showing the absolute raw counts.
    """
    # 1. Filter and Prepare Data
    latest_q = df['Source_Quarter'].max()
    vic_latest = df[
        (df['Managing Jurisdiction'] == 'VIC') &
        (df['Source_Quarter'] == latest_q) &
        (df['Service Sub Type'].isin(["PSK", "LDC"]))
    ].copy()

    # Prepare Absolute Counts
    pivot_hm = vic_latest.groupby(['Provider Management Type', 'Service Sub Type']).size().unstack(fill_value=0)
    
    # Ensure both columns exist even if data is missing for one
    for col in ['LDC', 'PSK']:
        if col not in pivot_hm.columns:
            pivot_hm[col] = 0

    # Calculate Percentages for Diverging Bar
    row_totals = pivot_hm.sum(axis=1)
    pivot_pct = pivot_hm.div(row_totals, axis=0) * 100

    # 2. Create Subplots
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("", "Total Service Count"),
        shared_yaxes=True,
        horizontal_spacing=0.15,
        column_widths=[0.6, 0.4]
    )

    # 3. Add Diverging Percentage Bar Chart (Left Side)
    # PSK side (Positive / Orange)
    fig.add_trace(
        go.Bar(
            y=pivot_pct.index,
            x=pivot_pct['PSK'],
            name='PSK %',
            orientation='h',
            marker_color='#ff7f0e',
            text=pivot_pct['PSK'].apply(lambda x: f'{x:.1f}%' if x > 0 else ''),
            textposition='outside',
            cliponaxis=False
        ), row=1, col=1
    )

    # LDC side (Negative / Dark Blue)
    fig.add_trace(
        go.Bar(
            y=pivot_pct.index,
            x=-pivot_pct['LDC'],
            name='LDC %',
            orientation='h',
            marker_color='#1f77b4',
            text=pivot_pct['LDC'].apply(lambda x: f'{x:.1f}%' if x > 0 else ''),
            textposition='outside',
            cliponaxis=False
        ), row=1, col=1
    )

    # 4. Add Heatmap (Right Side)
    fig.add_trace(
        go.Heatmap(
            z=pivot_hm.values,
            x=pivot_hm.columns,
            y=pivot_hm.index,
            colorscale='Blues',
            showscale=False,
            text=pivot_hm.values,
            texttemplate="%{text}",
        ), row=1, col=2
    )

    # 5. Styling and Layout
    fig.update_layout(
        title_text=f"<b>Service split and counts by management type</b><br><sup>Victoria, Q4 2025 | LDC vs Sessional</sup>",
        barmode='relative',
        margin=dict(t=120, l=50, r=50, b=80),
        showlegend=False,
        template="plotly_white",
        height= 500,
        width = 1000
    )

    # 6. X-Axis Formatting
    fig.update_xaxes(
        tickvals=[-100, -50, 0, 50, 100],
        ticktext=["100%", "50%", "0", "50%", "100%"],
        range=[-140, 140],
        row=1, col=1
    )

    # 7. Add Directional Annotations
    fig.add_annotation(
        dict(x=-75, y=1.12, xref="x1", yref="paper",
             text="<b>LDC</b>", showarrow=False,
             font=dict(size=14, color="#1f77b4"))
    )
    fig.add_annotation(
        dict(x=75, y=1.12, xref="x1", yref="paper",
             text="<b>Sessional</b>", showarrow=False,
             font=dict(size=14, color="#ff7f0e"))
    )

    return fig