#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt

SUBPLOT_WIDTH = 6.4
SUBPLOT_HEIGHT = 4.8

PLOT_PARAMS = {
    "figure.dpi": 120,
    "font.size": 9,
    "font.family": "serif",
    "axes.titlesize": 9,
    "axes.labelsize": 9,
    "axes.linewidth": 0.5,
    "grid.alpha": 0.35,
    "grid.linewidth": 0.5,
    "legend.fontsize": 7,
    "lines.linewidth": 1.2,
    "lines.markersize": 4,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "xtick.major.width": 0.5,
    "ytick.major.width": 0.5,
}

def apply_plot_style():
    plt.rcParams.update(PLOT_PARAMS)

def get_cmap(n: int):
    return plt.cm.viridis(np.linspace(0.0, 0.8, n))
