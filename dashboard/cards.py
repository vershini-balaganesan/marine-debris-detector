# dashboard/cards.py
"""
Small matplotlib chart builders sized to sit inside a compact dashboard card.
Pure presentation — takes already-computed data, draws nothing itself.
"""

import matplotlib.pyplot as plt


def mini_trend_chart(values, color="#3b82f6"):
    """Small filled line chart, e.g. total detections over recent history."""
    fig, ax = plt.subplots(figsize=(4, 1.6))
    ax.plot(values, color=color, linewidth=2)
    ax.fill_between(range(len(values)), values, color=color, alpha=0.12)
    ax.axis("off")
    fig.patch.set_alpha(0)
    return fig


def zone_count_bar_chart(zone_labels, zone_counts):
    """Bar chart comparing detection counts across zones."""
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.bar(zone_labels, zone_counts, color="#3b82f6", width=0.5)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_ylabel("Detections", fontsize=9)
    ax.tick_params(axis="both", labelsize=9)
    fig.patch.set_alpha(0)
    return fig


def zone_risk_chart(zones):
    """Rank zones by detections and label each bar with its risk level."""
    ordered_zones = sorted(zones, key=lambda zone: zone["total_count"])
    labels = [zone["zone_id"] for zone in ordered_zones]
    counts = [zone["total_count"] for zone in ordered_zones]
    risk_colors = {"LOW": "#10b981", "MEDIUM": "#f59e0b", "HIGH": "#ef4444"}
    colors = [risk_colors.get(zone["risk_level"], "#64748b") for zone in ordered_zones]

    fig_height = max(2.8, len(ordered_zones) * 0.48)
    fig, ax = plt.subplots(figsize=(5.2, fig_height))
    bars = ax.barh(labels, counts, color=colors, height=0.62)
    max_count = max(counts, default=0)
    label_offset = max(max_count * 0.02, 0.5)
    for bar, zone in zip(bars, ordered_zones):
        ax.text(
            bar.get_width() + label_offset,
            bar.get_y() + bar.get_height() / 2,
            f"{zone['total_count']}  {zone['risk_level']}",
            va="center",
            fontsize=8,
            color="#031716",
            fontweight="bold",
        )
    ax.set_xlabel("Detected objects", fontsize=9)
    ax.tick_params(axis="y", labelsize=8)
    ax.tick_params(axis="x", labelsize=8)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", alpha=0.18)
    ax.set_axisbelow(True)
    ax.set_xlim(0, max_count + label_offset * 14 if max_count else 1)
    fig.tight_layout()
    fig.patch.set_alpha(0)
    return fig
